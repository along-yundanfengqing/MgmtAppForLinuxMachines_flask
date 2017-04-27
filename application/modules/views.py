# -*- coding: utf-8 -*-
import pymongo
import subprocess
from datetime import datetime
from flask import abort, flash, jsonify, make_response, redirect, render_template, request, url_for
from flask.ext.login import login_user, logout_user, login_required, current_user

# my modules
from application import app, login_manager, mongo, machines_cache
from application.modules.app_manager import AppManager
from application.modules.bg_thread_manager import BackgroundThreadManager
from application.modules.file_io import FileIO
from application.modules.form import LoginForm, SignupForm
from application.modules.validation import Validation
from application.modules.users import User


butterfly = AppManager.check_butterfly()
login_file = app.config['LOGIN_FILENAME']
login_manager.login_view = "show_login"

# Start background thread
BackgroundThreadManager.start()


@login_manager.user_loader
def load_user(username):
    user = mongo.db.users.find_one({"Username": username})
    if not user:
        return None
    return User(user['Username'])


# signup page
@app.route('/signup', methods=['GET', 'POST'])
def show_signup():
    form = SignupForm(request.form)
    if request.method == 'POST' and form.validate():
        username = form.username.data
        hash_password = User.hash_password(form.password.data)
        if mongo.db.users.find_one({"Username": username}):
            flash('Username "%s" already exists in the database' % username)
        else:
            mongo.db.users.insert_one({"Username": username, "Password": hash_password})
            app.logger.warning("- ADDED ACCOUNT - %s", username)
            flash("Created a user account (%s)" % username)
            return redirect(url_for('show_login'))

    return render_template('signup.html', form=form)


# root
@app.route('/', methods=['GET', 'POST'])
def root():
    if current_user:
        return redirect(url_for('show_top'))

    return redirect(url_for('show_login'))


# login page
@app.route('/login', methods=['GET', 'POST'])
def show_login():
    form = LoginForm(request.form)
    if request.method == 'POST' and form.validate():
        user = mongo.db.users.find_one({"Username": form.username.data})
        if user and User.validate_login(user['Password'], form.password.data):
            user_obj = User(user['Username'])
            login_user(user_obj, remember=form.remember_me.data)
            flash('Logged in successfully as a user "%s"' % current_user.username)
            return redirect(url_for("show_top"))
        flash("Username or password is not correct")

    return render_template('login.html', form=form)


# logout
@app.route('/logout')
@login_required
def logout():
    flash('Logged out from a user "%s"' % current_user.username)
    logout_user()
    return redirect(url_for('show_login'))


# Top page
@app.route('/top')
@login_required
def show_top():
    machines = machines_cache.get()

    if not machines:    # In case machines_cache is empty, retrieve data from database
        docs = mongo.find({}, {'_id': 0}).sort(
            [["Hostname", pymongo.ASCENDING], ["IP Address", pymongo.ASCENDING]]
        )
        if docs:
            machines = machines_cache.convert_to_machine_list(docs)

    now = datetime.now()
    return render_template('top.html', current_user=current_user, machines=machines, now=now, butterfly=butterfly)


# Register a new machine page
@app.route('/register', methods=['GET', 'POST'])
@login_required
def add_machine(ipaddr="", username="", password="", error1="", error2="", error3=""):
    if request.method == 'POST':
        ipaddr = request.form['InputIPAddress']
        username = request.form['InputUsername']
        password = request.form['InputPassword']
        if not password:
            password = None

        # validate ip address format and duplication check
        is_duplicate = FileIO.exists_in_file(ipaddr)
        is_valid_ipaddr = Validation.is_valid_ipv4(ipaddr)
        is_valid_username = Validation.is_valid_username(username)
        is_valid_password = Validation.is_valid_password(password)

        if not is_valid_ipaddr:
            ipaddr = ""
            error1 = "Please enter a valid IP address"
        if not is_valid_username:
            username = ""
            error2 = "Please enter a valid username"
        if not is_valid_password:
            error3 = "Please enter a valid passowrd"
        if is_duplicate:     # IP Address already exists in the login file
            flash('The IP Address "%s" already exists in %s' % (ipaddr, login_file))
            ipaddr = username = password = error1 = error2 = error3 = ""

        # validation = all OK
        elif (not is_duplicate) and is_valid_ipaddr and is_valid_username and is_valid_password:
            if AppManager.add_machine(ipaddr, username, password):
                flash('Added the new machine with IP Address "%s" to %s and to the database. It will be marked as "Unknown" until subsequent ssh access succeeds' % (ipaddr, login_file))
                app.logger.info("- ADDED - %s", ipaddr)
            else:
                flash('Failed to added the new machine with IP Address "%s". ' % ipaddr)
            return redirect(url_for('show_top'))

    return render_template(
        'add_machine.html', ipaddr=ipaddr, username=username, password="",
        error1=error1, error2=error2, error3=error3)


# Delete machines page
@app.route('/delete', methods=['GET', 'POST'])
@login_required
def delete_machine():

    machines = machines_cache.get()

    if not machines:    # In case machine_list in memory is empty, retrieve data from database
        docs = mongo.find({}, {'_id': 0}).sort(
            [["Hostname", pymongo.ASCENDING], ["IP Address", pymongo.ASCENDING]]
        )
        if docs:
            machines = machines_cache.convert_to_machine_list(docs)

    if request.method == 'POST':
        del_list_u = request.form.getlist('checkbox')
        del_list = map(str, del_list_u)
        if del_list:
            AppManager.del_machine(del_list)
            del_ip = ", ".join([ip for ip in del_list])
            flash('Deleted the machine with IP Address "%s" from both %s and the database' % (del_ip, login_file))
            app.logger.info("- DELETED - %s", del_ip)
            return redirect(url_for('show_top'))
        else:
            flash('Select machines to delete')

    return render_template('delete_machine.html', ipaddr="", machines=machines)


# SSH with butterfly application
@app.route('/terminal', methods=['GET', 'POST'])
@login_required
def open_terminal():
    if request.method == 'POST':
        ipaddr = request.form['ipaddr']
        username = FileIO.get_username(ipaddr)
        AppManager.kill_butterfly()
        # Check if the ip address is from AWS
        if Validation.is_aws(ipaddr):
            pem_path, ssh_dir = AppManager.search_pem()
            if pem_path:
                subprocess.Popen([
                    "butterfly.server.py", "--unsecure", "--motd=/dev/null",
                    "--cmd=ssh -i %s %s@%s" % (pem_path, username, ipaddr), "--one-shot"])
            else:
                flash("SSH access to the AWS instance failed as the program couldn't locate .pem file in %s" % ssh_dir)
                app.logger.warning("Unable to locate .pem file in ~/.ssh")

        else:   # if not AWS
            subprocess.Popen([
                "butterfly.server.py", "--unsecure", "--motd=/dev/null",
                "--cmd=ssh %s@%s" % (username, ipaddr), "--one-shot"])

    return redirect(url_for('show_top'))


# Export JSON files
@app.route('/export_json', methods=['GET', 'POST'])
@login_required
def export_json():
    ipaddr = request.form['ipaddr']
    doc = mongo.find_one({'IP Address': ipaddr}, {'_id': 0})

    if request.method == 'POST':
        filename = request.form['InputFilename']
        result, json_dir = AppManager.export_json(filename, doc)
        if result:
            flash('JSON file "%s" was successfully saved in %s/' % (filename, json_dir))
        else:
            flash('Failed to export the JSON file')

    return redirect(url_for('show_top'))



######################## RESUful API ########################

# Expose each machine's data via REST API
# eg. curl -i http://localhost:5000/api/machines/vm01
@app.route('/api/machines/<hostname>', methods=['GET'])
def show_json_host(hostname):
    doc = mongo.find_one({'Hostname': hostname}, {'_id': 0})
    if doc:
        return jsonify(data=doc)
    abort(404)


# Expose all machines' data via REST API
# eg. curl -i http://localhost:5000/api/machines/all
@app.route('/api/machines', methods=['GET'])
@app.route('/api/machines/all', methods=['GET'])
def show_json_all():
    docs = mongo.find({}, {'_id': 0}).sort(
            [["Hostname", pymongo.ASCENDING], ["IP Address", pymongo.ASCENDING]]
            )
    # return all machines except Hostname = #Unknown
    if docs:
        return jsonify(data=[doc for doc in docs if doc['Hostname'] != '#Unknown'])
    abort(404)


# Add machines via RESTful API
# eg. curl -H "Content-Type: application/json" -X "POST" http://localhost:5000/api/machines/add/1.1.1.1:ubuntu
@app.route('/api/machines/add/<ipaddr>:<username>', defaults={'password': None}, methods=['POST'])
@app.route('/api/machines/add/<ipaddr>:<username>:<password>', methods=['POST'])
def add_vm_api_01(ipaddr, username, password):
    error_list = []

    # validate ip address format and duplication check
    is_duplicate = FileIO.exists_in_file(ipaddr)
    is_valid_ipaddr = Validation.is_valid_ipv4(ipaddr)
    is_valid_username = Validation.is_valid_username(username)
    is_valid_password = Validation.is_valid_password(password)

    if not is_valid_ipaddr:
        error_list.append("invalid ip address")
    if not is_valid_username:
        error_list.append("invalid username")
    if not is_valid_password:
        error_list.append("invalid password")
    if is_duplicate:     # IP Address already exists in the login file
        error_list.append("ip duplicate")

    # validation = all OK
    elif (not is_duplicate) and is_valid_ipaddr and is_valid_username and is_valid_password:
        if AppManager.add_machine(ipaddr, username, password):
            app.logger.info("- ADDED - %s", ipaddr)
            return make_response(jsonify(result={'success': True}), 201)
    return make_response(jsonify(result={'success': False, 'reason': error_list}), 422)


# Add machines via RESTful API (by using -d option)
## eg. curl -H "Content-Type: application/json" -X "POST" http://localhost:5000/api/machines/add -d '[{"IP Address": "1.1.1.1", "Username": "ubuntu", "Password": "test"}, {"IP Address": "2.2.2.2", "Username": "ubuntu"}]'
@app.route('/api/machines/add', methods=['POST'])
def add_vm_api_02():
    if not request.get_json():
        abort(400)

    add_machines = request.get_json()
    if type(add_machines) != list:
        add_machines = [add_machines]

    errors = {}
    all_success = True

    for item in add_machines:
        ipaddr = item['IP Address']
        username = item['Username']
        try:
            password = item['Password']
        except:
            password = None

        errors[ipaddr] = []

        # validate ip address format and duplication check
        is_duplicate = FileIO.exists_in_file(ipaddr)
        is_valid_ipaddr = Validation.is_valid_ipv4(ipaddr)
        is_valid_username = Validation.is_valid_username(username)
        is_valid_password = Validation.is_valid_password(password)

        if not is_valid_ipaddr:
            errors[ipaddr].append("invalid ip address")
        if not is_valid_username:
            errors[ipaddr].append("invalid username")
        if not is_valid_password:
            errors[ipaddr].append("invalid password")
        if is_duplicate:     # IP Address already exists in the login file
            errors[ipaddr].append("ip duplicate")

        # validation = all OK
        elif (not is_duplicate) and is_valid_ipaddr and is_valid_username and is_valid_password:
            errors.pop(ipaddr, None)
            if AppManager.add_machine(ipaddr, username, password):
                app.logger.info("- ADDED - %s", ipaddr)
                continue

        all_success = False

    if all_success:
        return make_response(jsonify(result={'success': True}), 201)
    return make_response(jsonify(result={'success': False, 'reason': errors}), 422)


# Delete machines via RESTful API
# eg. curl -H "Content-Type: application/json" -X "DELETE" http://localhost:5000/api/machines/delete/1.1.1.1
@app.route('/api/machines/delete/<ipaddresses>', methods=['DELETE'])
def delete_vm_api_01(ipaddresses):
    del_list = filter(lambda x: FileIO.exists_in_file(x), ipaddresses.split(","))
    del_result = AppManager.del_machine(del_list)
    if del_result['ok'] == 1 and del_result['n'] > 0:
        del_ip_list = ", ".join([ip for ip in del_list])
        app.logger.info("- DELETED - %s", del_ip_list)
        return jsonify(result={'success': True, 'deleted machines': del_result['n']})
    return make_response(jsonify(result={'success': False, 'deleted machines': del_result['n']}), 422)


# Delete machines via RESTful API (by using -d option)
# eg. curl -H "Content-Type: application/json" -X "DELETE" http://localhost:5000/api/machines/delete -d '{"IP Address": [ "1.1.1.1", "2.2.2.2", "3.3.3.3" ]}'
@app.route('/api/machines/delete', methods=['DELETE'])
def delete_vm_api_02():
    if not request.get_json() or not 'IP Address' in request.get_json():
        abort(400)
    del_list = request.get_json()['IP Address']

    # convert to list if the data is not
    if type(del_list) != list:
        del_list = del_list.split()

    # filter ip addresses which are not in text file
    del_list = filter(lambda x: FileIO.exists_in_file(x), del_list)

    del_result = AppManager.del_machine(del_list)
    if del_result['ok'] == 1 and del_result['n'] > 0:
        del_ip_list = ", ".join([ip for ip in del_list])
        app.logger.info("- DELETED - %s", del_ip_list)
        return jsonify(result={'success': True, 'deleted machines': del_result['n']})
    return make_response(jsonify(result={'success': False, 'deleted machines': del_result['n']}), 422)


# for tests only
@app.route('/api/users/add', methods=['POST'])
def add_user_api():
    if not request.get_json():
        abort(400)

    username = request.get_json()['Username']
    password = request.get_json()['Password']

    if mongo.db.users.find_one({"Username": username}):
        return make_response(jsonify(result={'success': False, 'error': "User already exists"}), 422)
    else:
        hash_password = User.hash_password(password)
        mongo.db.users.insert_one({"Username": username, "Password": hash_password})
        app.logger.warning("- ADDED ACCOUNT - %s", username)
        return jsonify(result={'success': True, 'added_users': 1})


# for tests only
@app.route('/api/users/delete/<username>', methods=['DELETE'])
def delete_user_api(username):
    del_result = mongo.db.users.remove({"Username": username})
    app.logger.warning("- DELETED ACCOUNT - %s", username)
    if del_result['ok'] == 1 and del_result['n'] > 0:
        return jsonify(result={'success': True, 'deleted users': del_result['n']})
    return make_response(jsonify(result={'success': False, 'deleted users': del_result['n']}), 422)


@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify(result={'error': error.description}), 404)


@app.errorhandler(400)
def bad_request(error):
    return make_response(jsonify(result={'error': error.description}), 400)


@app.errorhandler(405)
def not_allowed(error):
    return make_response(jsonify(result={'error': error.description}), 405)
