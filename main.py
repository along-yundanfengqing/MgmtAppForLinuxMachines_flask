from flask import Flask,render_template, request, redirect, url_for, flash, jsonify
import pymongo
import threading, thread
from datetime import datetime
import re
import sys
import logging
import subprocess
import pip
# my modules
from py_modules.background_SSH import ssh
from py_modules.validation import *
from py_modules.functions import *

app = Flask(__name__)
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

print "Starting the program...\n"
# If this program runs with docker test environment
if len(sys.argv) == 2:
    dbserver = sys.argv[1]

# If this program runs with your own infrastructure
else:
    print "Please enter the IP address of your MongoDB server."
    while True:
        try:
            dbserver = raw_input("IP Address of MongoDB: ")
            if dbserver:
                if is_valid_IPv4(dbserver):
                    break
                else:
                    print "%s is not a valid IP address.\n\nPlease enter a valid IP address" % dbserver
                    continue
        except KeyboardInterrupt:
            print
            print "Bye"
            sys.exit(3)

# connect to MongoDB
try:
    client = pymongo.MongoClient('mongodb://%s' % dbserver, serverSelectionTimeoutMS=3000)
    db = client.VM
    print "checking the connectivity to the database(%s)...." % dbserver
    if client.server_info():
        print "OK"
except:
    print "ERROR: Unable to connect to %s" % dbserver
    sys.exit(3)

# Check if butterfly module is installed
installed_packages = pip.get_installed_distributions()
flat_installed_packages = [package.project_name for package in installed_packages]
if 'butterfly' in flat_installed_packages:
    butterfly=1     # Installed
else:
    butterfly=0     # Not installed

# Top screen
@app.route('/')
def showTop():
    docs = db.vm.find({}).sort([["Hostname", pymongo.ASCENDING], ["IP Address", pymongo.ASCENDING]])
    vms = [doc for doc in docs]
    now = datetime.now()
    return render_template('Top.html', vms=vms, now=now, butterfly=butterfly)

# Register a new machine
@app.route('/register', methods=['GET','POST'])
def addVM(error1="", error2="", error3=""):
    if request.method == 'POST':
        ipaddr = request.form['InputIPAddress']
        username = request.form['InputUsername']
        password = request.form['InputPassword']
        if not password:
            password = None

        # validate ip address format and duplication check
        result_dup = exists_in_file(ipaddr)
        valid_ipaddr = is_valid_IPv4(ipaddr)
        valid_username = is_valid_username(username)
        valid_password = is_valid_password(password)

        # IP Address already exists in login.txt
        if result_dup == True:
            flash('The IP Address "%s" already exists in login.txt' % ipaddr)
            return render_template('addVM.html', ipaddr="", username="", password="")        
        # Set error messages in case validation fails
        if not valid_ipaddr:
            ipaddr = ""
            error1 = "Please enter a valid IP address"
        if not valid_username:
            username = ""
            error2 = "Please enter a valid username"
        if not valid_password:
            error3 = "please enter a valid passowrd"

        # validation = OK
        elif valid_ipaddr and valid_username and valid_password:
            if add_vm(db, ipaddr, username, password) == True:
                flash('Added the new machine with IP Address "%s" to login.txt and to the database. It will be marked as "Unknown" until subsequent ssh access succeeds' % ipaddr)
            else:
                flash('Failed to added the new machine with IP Address "%s". ' % ipaddr)
            return redirect(url_for('showTop'))
        # validation = NG
        return render_template('addVM.html', ipaddr=ipaddr, username=username, password="", error1=error1, error2=error2, error3=error3)
    else:
        return render_template('addVM.html', ipaddr="", username="", password="", error1=error1, error2=error2, error3=error3)

# Delete machines
@app.route('/delete', methods=['GET','POST'])
def deleteVM():
    docs = db.vm.find({}).sort([["Hostname", pymongo.ASCENDING], ["IP Address", pymongo.ASCENDING]])
    vms = [doc for doc in docs]
    
    if request.method == 'POST':
        del_list = request.form.getlist('checkbox')
        del_vm(db, del_list)
        del_ip = ", ".join([ip for ip in del_list])
        flash('Deleted the machine with IP Address "%s" from both login.txt and the database' % del_ip)
        return redirect(url_for('showTop'))
    # request.method = GET
    else:
        return render_template('delVM.html', ipaddr="", vms=vms)

# SSH with butterfly application
@app.route('/terminal', methods=['GET', 'POST'])
def openTerminal():
    if request.method == 'POST':
        ipaddr = request.form['ipaddr']
        username = getUsername(ipaddr)
        kill_butterfly()
        # Check if the ip address is from AWS
        if is_aws(ipaddr):
            pem_path, ssh_dir = search_pem()
            if pem_path:
                subprocess.Popen(["butterfly.server.py", "--unsecure", "--motd=/dev/null", "--cmd=ssh -i %s %s@%s" % (pem_path, username, ipaddr), "--one-shot"])
            else:
                flash("SSH access to the AWS instance failed as the program couldn't locate .pem file in %s" % ssh_dir)
                return redirect(url_for('showTop'))
        # if not AWS
        else:
            subprocess.Popen(["butterfly.server.py", "--unsecure", "--motd=/dev/null", "--cmd=ssh %s@%s" % (username, ipaddr), "--one-shot"])
        return redirect(url_for('showTop'))
    else:
        return redirect(url_for('showTop'))

# Export JSON files
@app.route('/exportjson', methods = ['GET','POST'])
def exportJSON():
    ipaddr = request.form['ipaddr']
    doc = db.vm.find_one({'IP Address': ipaddr}, {'_id': 0})
    
    if request.method == 'POST':
        filename = request.form['InputFilename']
        result, json_dir = export_json(filename, doc)
        if result == True:
            flash('JSON file "%s" was successfully saved in %s/' % (filename, json_dir))
            return redirect(url_for('showTop'))
        else:
            flash('Failed to export the JSON file')
            return redirect(url_for('showTop'))
    else:
        return redirect(url_for('showTop'))

# Expose each machine's data via REST API
@app.route('/<hostname>.json')
def showJSON_host(hostname):
    doc = db.vm.find_one({'Hostname': hostname}, {'_id':0})
    return jsonify(Data = doc)

# Expose all machines' data via REST API
@app.route('/json')
def showJSON_all():
    docs = db.vm.find({}, {'_id':0})
    # return all machines except Hostname = #Unknown
    return jsonify(Data = [doc for doc in docs if doc['Hostname'] != '#Unknown'])

# Call the background process
def background_thread():
    try:
        ssh(db)
        # loop the background thread for every 30 seconds
        th = threading.Timer(30, background_thread)
        th.daemon=True
        th.start()
    except Exception as e:
        print e
        print "Stopping the program due to the unexpected error..."
        thread.interrupt_main()

def call_background():
    # Start the backgroud thread for SSH access and DB write/read
    th=threading.Thread(target=background_thread)
    th.daemon=True
    th.start()


if __name__=='__main__':
    call_background()
    app.secret_key = 'super_secret_key'
    app.debug = False
    app.run(host = '0.0.0.0', port = 5000)
