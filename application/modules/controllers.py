# -*- coding: utf-8 -*-
import pymongo
import subprocess
from datetime import datetime
from flask import flash, jsonify, redirect, render_template, request, url_for

# my modules
from application import app, mongo
from application.modules.app_manager import AppManager
from application.modules.bg_thread_manager import BackgroundThreadManager
from application.modules.file_io import FileIO
from application.modules.validation import Validation


app_manager = AppManager()
butterfly = app_manager.check_butterfly()

# Start background thread
BackgroundThreadManager.start()


# Top screen
@app.route('/')
def show_top():
    docs = mongo.find({}).sort(
        [["Hostname", pymongo.ASCENDING], ["IP Address", pymongo.ASCENDING]]
        )
    vms = [doc for doc in docs]
    now = datetime.now()
    return render_template('top.html', vms=vms, now=now, butterfly=butterfly)

# Register a new machine
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
            error3 = "please enter a valid passowrd"
        if is_duplicate:     # IP Address already exists in login.txt
            flash('The IP Address "%s" already exists in login.txt' % ipaddr)
            ipaddr = username = password = error1 = error2 = error3 = ""

        # validation = all OK
        elif (not is_duplicate) and is_valid_ipaddr and is_valid_username and is_valid_password:
            if app_manager.add_vm(ipaddr, username, password):
                flash('Added the new machine with IP Address "%s" to login.txt and to the database. It will be marked as "Unknown" until subsequent ssh access succeeds' % ipaddr)
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

# Delete machines
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
            flash('Deleted the machine with IP Address "%s" from both login.txt and the database' % del_ip)
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
            return redirect(url_for('show_top'))
        else:
            flash('Failed to export the JSON file')
            return redirect(url_for('show_top'))
    elif request.method == 'GET':
        return redirect(url_for('show_top'))

# Expose each machine's data via REST API
@app.route('/<hostname>.json')
def show_json_host(hostname):
    doc = mongo.find_one({'Hostname': hostname}, {'_id': 0})
    return jsonify(Data=doc)

# Expose all machines' data via REST API
@app.route('/json')
def show_json_all():
    docs = mongo.find({}, {'_id': 0})
    # return all machines except Hostname = #Unknown
    return jsonify(Data=[doc for doc in docs if doc['Hostname'] != '#Unknown'])
