# -*- coding: utf-8 -*-
import pymongo
import subprocess
from datetime import datetime
from flask import abort, flash, jsonify, make_response, redirect, render_template, request, url_for

# my modules
from application import app, mongo
from application.modules.app_manager import AppManager
from application.modules.bg_thread_manager import BackgroundThreadManager
from application.modules.db_cache import DBCache
from application.modules.file_io import FileIO
from application.modules.validation import Validation


app_manager = AppManager()
butterfly = app_manager.check_butterfly()
login_file = app.config['LOGIN_FILENAME']

# Start background thread
BackgroundThreadManager.start()


# Top page
@app.route('/')
def show_top(vms=[]):
    if DBCache.is_updated():     # Has any update in DB entries
        docs = mongo.find({}).sort(
            [["Hostname", pymongo.ASCENDING], ["IP Address", pymongo.ASCENDING]]
            )
        vms = [doc for doc in docs]
        DBCache.update_cache(vms)   # update cache entries
        app.logger.debug("Data loaded from database")

    else:
        cache_contents = DBCache.get_cache()
        if cache_contents:
            vms = cache_contents    # else: vms = []
            app.logger.debug("Data loaded from cache")

    now = datetime.now()
    return render_template('top.html', vms=vms, now=now, butterfly=butterfly)

# Register a new machine page
@app.route('/register', methods=['GET', 'POST'])
def add_vm(error1="", error2="", error3=""):
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
            if app_manager.add_vm(ipaddr, username, password):
                flash('Added the new machine with IP Address "%s" to %s and to the database. It will be marked as "Unknown" until subsequent ssh access succeeds' % (ipaddr, login_file))
                app.logger.info("- ADDED - %s", ipaddr)
            else:
                flash('Failed to added the new machine with IP Address "%s". ' % ipaddr)
            return redirect(url_for('show_top'))

        # validation = NG
        return render_template(
            'add_vm.html', ipaddr=ipaddr, username=username, password="",
            error1=error1, error2=error2, error3=error3)
    elif request.method == 'GET':
        return render_template(
            'add_vm.html', ipaddr="", username="", password="",
            error1=error1, error2=error2, error3=error3)

# Delete machines page
@app.route('/delete', methods=['GET', 'POST'])
def delete_vm():
    docs = mongo.find({}).sort([["Hostname", pymongo.ASCENDING], ["IP Address", pymongo.ASCENDING]])
    vms = [doc for doc in docs]

    if request.method == 'POST':
        del_list_u = request.form.getlist('checkbox')
        del_list = map(str, del_list_u)
        if del_list:
            app_manager.del_vm(del_list)
            del_ip = ", ".join([ip for ip in del_list])
            flash('Deleted the machine with IP Address "%s" from both %s and the database' % (del_ip, login_file))
            app.logger.info("- DELETED - %s", del_ip)
            return redirect(url_for('show_top'))
        else:
            flash('Select machines to delete')
            return render_template('delete_vm.html', ipaddr="", vms=vms)

    elif request.method == 'GET':
        return render_template('delete_vm.html', ipaddr="", vms=vms)

# SSH with butterfly application
@app.route('/terminal', methods=['GET', 'POST'])
def open_terminal():
    if request.method == 'POST':
        ipaddr = request.form['ipaddr']
        username = FileIO.get_username(ipaddr)
        app_manager.kill_butterfly()
        # Check if the ip address is from AWS
        if Validation.is_aws(ipaddr):
            pem_path, ssh_dir = app_manager.search_pem()
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

    elif request.method == 'GET':
        return redirect(url_for('show_top'))

# Export JSON files
@app.route('/export_json', methods=['GET', 'POST'])
def export_json():
    ipaddr = request.form['ipaddr']
    doc = mongo.find_one({'IP Address': ipaddr}, {'_id': 0})

    if request.method == 'POST':
        filename = request.form['InputFilename']
        result, json_dir = app_manager.export_json(filename, doc)
        if result:
            flash('JSON file "%s" was successfully saved in %s/' % (filename, json_dir))
        else:
            flash('Failed to export the JSON file')
        return redirect(url_for('show_top'))
    elif request.method == 'GET':
        return redirect(url_for('show_top'))


######################## RESUful API ######################## 

# Expose each machine's data via REST API
# eg. curl -i http://localhost:5000/api/machines/vm01
@app.route('/api/machines/<hostname>', methods=['GET'])
def show_json_host(hostname):
    doc = mongo.find_one({'Hostname': hostname}, {'_id': 0})
    if doc:
        return jsonify(Data=doc)
    abort(404)

# Expose all machines' data via REST API
# eg. curl -i http://localhost:5000/api/machines/all
@app.route('/api/machines', methods=['GET'])
@app.route('/api/machines/all', methods=['GET'])
def show_json_all():
    docs = mongo.find({}, {'_id': 0})
    # return all machines except Hostname = #Unknown
    if docs:
        return jsonify(Data=[doc for doc in docs if doc['Hostname'] != '#Unknown'])
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
        if app_manager.add_vm(ipaddr, username, password):
            app.logger.info("- ADDED - %s", ipaddr)
            return jsonify({'success': True})
        
    return jsonify({'success': False, 'reason': error_list}) 

# Add machines via RESTful API (by using -d option)
# eg. curl -H "Content-Type: application/json" -X "POST" http://localhost:5000/api/machines/add -d '[{"IP Address": "1.1.1.1", "Username": "ubuntu", "Password": "test"}, {"IP Address": "2.2.2.2", "Username": "ubuntu"}]'
@app.route('/api/machines/add', methods=['POST'])
def add_vm_api_02():
    if not request.get_json():
        abort(400)

    add_machines = request.get_json()
    if not type(add_machines) == list:
        add_machines = [add_machines]

    error_list = []
    all_success = True
    
    for item in add_machines:
        ipaddr = item['IP Address']
        username = item['Username']
        try:
            password = item['Password']
        except:
            password = None

        error = {}
        error[ipaddr] = []

        # validate ip address format and duplication check
        is_duplicate = FileIO.exists_in_file(ipaddr)
        is_valid_ipaddr = Validation.is_valid_ipv4(ipaddr)
        is_valid_username = Validation.is_valid_username(username)
        is_valid_password = Validation.is_valid_password(password)

        if not is_valid_ipaddr:
            error[ipaddr].append("invalid ip address")
        if not is_valid_username:
            error[ipaddr].append("invalid username")
        if not is_valid_password:
            error[ipaddr].append("invalid password")
        if is_duplicate:     # IP Address already exists in the login file
            error[ipaddr].append("ip duplicate")

        # validation = all OK
        elif (not is_duplicate) and is_valid_ipaddr and is_valid_username and is_valid_password:
            if app_manager.add_vm(ipaddr, username, password):
                app.logger.info("- ADDED - %s", ipaddr)
                continue

        error_list.append(error)
        all_success = False
            
    if all_success:
        return jsonify({'success': True})
    return jsonify({'success': False, 'reason': error_list}) 

# Delete machines via RESTful API
# eg. curl -H "Content-Type: application/json" -X "DELETE" http://localhost:5000/api/machines/delete/1.1.1.1
@app.route('/api/machines/delete/<ipaddresses>', methods=['DELETE'])
def delete_vm_api_01(ipaddresses):
    del_list = filter(lambda x: FileIO.exists_in_file(x), ipaddresses.split(","))
    del_result = app_manager.del_vm(del_list)
    if del_result['ok'] == 1 and del_result['n'] > 0:
        del_ip_list = ", ".join([ip for ip in del_list])
        app.logger.info("- DELETED - %s", del_ip_list)
        return jsonify({'success': True, 'deleted machines': del_result['n']})
    return jsonify({'success': False, 'deleted machines': del_result['n']})

# Delete machines via RESTful API (by using -d option)
# eg. curl -H "Content-Type: application/json" -X "DELETE" http://localhost:5000/api/machines/delete -d '{"IP Address": [ "1.1.1.1", "2.2.2.2", "3.3.3.3" ]}'
@app.route('/api/machines/delete', methods=['DELETE'])
def delete_vm_api_02():
    if not request.get_json() or not 'IP Address' in request.get_json():
        abort(400)
    del_list = request.get_json()['IP Address']

    # convert to list if the data is not
    if not type(del_list) == list:
        del_list = del_list.split()

    # filter ip addresses which are not in text file
    del_list = filter(lambda x: FileIO.exists_in_file(x), del_list)

    del_result = app_manager.del_vm(del_list)
    if del_result['ok'] == 1 and del_result['n'] > 0:
        del_ip_list = ", ".join([ip for ip in del_list])
        app.logger.info("- DELETED - %s", del_ip_list)
        return jsonify({'success': True, 'deleted machines': del_result['n']})
    return jsonify({'success': False, 'deleted machines': del_result['n']})

@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': error.description}), 404)

@app.errorhandler(400)
def bad_request(error):
    return make_response(jsonify({'error': error.description}), 400)