# -*- coding: utf-8 -*-
import eventlet
eventlet.monkey_patch()
import subprocess
from datetime import datetime
from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import LoginManager, login_user, logout_user, login_required, current_user

# my modules
from application import app
from application.modules.app_manager import AppManager
from application.modules.db_manager import DBManager
from application.modules.file_io import FileIO
from application.modules.form import LoginForm, SignupForm
from application.modules.users import UserObj
from application.modules.validation import Validation
from application.modules.machines_cache import MachinesCache


view = Blueprint('view', __name__)
machines_cache = MachinesCache.get_current_instance()
mongo = DBManager.get_current_instance()
butterfly = AppManager.is_butterfly_installed()
login_file = app.config['LOGIN_FILENAME']
login_manager = LoginManager(app)
login_manager.login_view = "view.show_login"
login_manager.login_message_category = 'error'


@login_manager.user_loader
def load_user(username):
    user = mongo.find_user(username)
    if user:
        return UserObj(user['username'])
    else:
        return None


# signup page
@view.route('/portal/signup', methods=['GET', 'POST'])
def show_signup():
    form = SignupForm(request.form)
    if request.method == 'POST' and form.validate():
        username = form.username.data
        hashed_password = UserObj.hash_password(form.password.data)
        if mongo.find_user(username):
            flash('Username "%s" already exists in the database' % username, 'error')
        else:
            mongo.add_user(username, hashed_password)
            app.logger.warning("- ADDED ACCOUNT - %s", username)
            flash("Created a user account (%s)" % username, 'success')
            return redirect(url_for('view.show_login'))

    return render_template('signup.html', form=form)


# root
@view.route('/', methods=['GET', 'POST'])
def root():
    if current_user:
        return redirect(url_for('view.show_home'))

    return redirect(url_for('view.show_login'))


# login page
@view.route('/portal/login', methods=['GET', 'POST'])
def show_login():
    form = LoginForm(request.form)
    if request.method == 'POST' and form.validate():
        user = mongo.find_user(form.username.data)
        if user and UserObj.validate_login(user['password'], form.password.data):
            user_obj = UserObj(user['username'])
            login_user(user_obj, remember=form.remember_me.data)
            flash('Logged in successfully as a user "%s"' % current_user.username, 'success')
            return redirect(url_for("view.show_home"))
        flash("Username or password is not correct", 'error')

    return render_template('login.html', form=form)


# logout
@view.route('/portal/logout')
@login_required
def logout():
    flash('Logged out from a user "%s"' % current_user.username, 'success')
    logout_user()
    return redirect(url_for('view.show_login'))


#Home page
@view.route('/'
            'portal/home')
@login_required
def show_home():
    machines = machines_cache.get()

    if not machines:    # In case machines_cache is empty, retrieve data from database
        machines = mongo.find({}).order_by('hostname', 'ip_address_decimal')

    now = datetime.utcnow()
    return render_template('home.html', current_user=current_user, machines=machines, now=now, butterfly=butterfly)


# Register a new machine page
@view.route('/portal/register', methods=['GET', 'POST'])
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
            flash('The IP Address "%s" already exists in %s' % (ipaddr, login_file), 'error')
            ipaddr = username = password = error1 = error2 = error3 = ""

        # validation = all OK
        elif (not is_duplicate) and is_valid_ipaddr and is_valid_username and is_valid_password:
            if AppManager.add_machine(ipaddr, username, password):
                flash('Added the new machine with IP Address "%s" to %s and to the database. It will be marked as "Unknown" until subsequent ssh access succeeds' % (ipaddr, login_file), 'success')
                app.logger.info("- ADDED - %s", ipaddr)
            else:
                flash('Failed to added the new machine with IP Address "%s". ' % ipaddr, 'error')
            return redirect(url_for('view.show_home'))

    return render_template(
        'add_machine.html', ipaddr=ipaddr, username=username, password="",
        error1=error1, error2=error2, error3=error3)


# Delete machines page
@view.route('/portal/delete', methods=['GET', 'POST'])
@login_required
def delete_machine():
    machines = machines_cache.get()

    if not machines:    # In case machine_list in memory is empty, retrieve data from database
        machines = mongo.find({}).order_by("+hostname", "+ip_address_decimal")

    if request.method == 'POST':
        del_list_u = request.form.getlist('checkbox')
        del_list = list(map(str, del_list_u))
        if del_list:
            AppManager.del_machine(del_list)
            del_ip = ", ".join([ip for ip in del_list])
            flash('Deleted the machine with IP Address "%s" from both %s and the database' % (del_ip, login_file), 'success')
            app.logger.info("- DELETED - %s", del_ip)
            return redirect(url_for('view.show_home'))
        else:
            flash('Select machines to delete', 'error')

    return render_template('delete_machine.html', machines=machines)


# SSH with butterfly application
@view.route('/portal/terminal', methods=['GET', 'POST'])
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
                flash("SSH access to the AWS instance failed as the program couldn't locate .pem file in %s" % ssh_dir, 'error')
                app.logger.warning("Unable to locate .pem file in ~/.ssh")

        else:   # if not AWS
            subprocess.Popen([
                "butterfly.server.py", "--unsecure", "--motd=/dev/null",
                "--cmd=ssh %s@%s" % (username, ipaddr), "--one-shot"])

    return redirect(url_for('view.show_home'))


# Export JSON files
@view.route('/portal/export_json', methods=['GET', 'POST'])
@login_required
def export_json():
    ipaddr = request.form['ipaddr']
    if machines_cache.get(ipaddr):
        doc = machines_cache.convert_machine_to_doc(ipaddr)
    else:
        machine_data = mongo.find_one({'ip_address': ipaddr})
        doc = machine_data.to_mongo().to_dict()

    if request.method == 'POST':
        filename = request.form['InputFilename']
        result, json_dir = AppManager.export_json(filename, doc)
        if result:
            flash('JSON file "%s" was successfully saved in %s/' % (filename, json_dir), 'success')
        else:
            flash('Failed to export the JSON file', 'error')

    return redirect(url_for('view.show_home'))


# Start EC2 Instance
@view.route('/portal/start_ec2/<ipaddr>', methods=['GET', 'POST'])
@login_required
def start_ec2(ipaddr):
    eventlet.spawn_n(AppManager.start_ec2, ipaddr)
    return redirect(url_for('view.show_home'))


# Stop EC2 Instance
@view.route('/portal/stop_ec2/<ipaddr>', methods=['GET', 'POST'])
@login_required
def stop_ec2(ipaddr):
    eventlet.spawn_n(AppManager.stop_ec2, ipaddr)
    return redirect(url_for('view.show_home'))

