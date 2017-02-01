import pexpect
from pexpect import pxssh
import pymongo
import os, sys
import re
from datetime import datetime
import threading
# my modules
from validation import *
from functions import *

DIR = os.getcwd()
FILENAME = 'login.txt'
FILEPATH = os.path.join(DIR,FILENAME)

# Shell commands for getting data
cmd_hostname = "echo $HOSTNAME"
cmd_distribution = "cat /etc/*-release"
cmd_mac = "ip addr"
cmd_uptime = "cat /proc/uptime"
cmd_cpu = "uptime"
cmd_mem = "free -h"
cmd_disk = "df -Ph"


class SSHThread(threading.Thread):
    def __init__(self, db, login):
        threading.Thread.__init__(self)
        self.db = db
        self.login = login
    def run(self):
        s = pxssh.pxssh(timeout=30)
        ipaddr = self.login[0].strip()
        username = self.login[1].strip()
        try:
            password = self.login[2].strip()
        except:
            password = None

        # Attempt SSH access
        try:
            if password:    # for password authentication
                s.login(ipaddr, username, password, login_timeout=30)
            else:           # for SSH-key based authentication
                s.login(ipaddr, username)
        # SSH login failure
        except (pexpect.exceptions.EOF, pxssh.ExceptionPxssh) as e:
            if e.args[0] == 'password refused':
                print "Skipped: SSH access to %s failed. Please check username or passord for login" % ipaddr
            else:
                print "Skipped: SSH access to %s failed. Please check network connectivity, or check if ssh service is started on the machine" % ipaddr
            # Check if the IP Address still exists in login.txt and DB when ssh access failed. 
            exist_file = exists_in_file(ipaddr)
            exist_db = self.db.vm.find_one({"IP Address": ipaddr})

            # If SSH access failed when the VM exists in both login.txt and DB, mark it as "Unreachable" and increment the failure count by 1
            if exist_file and exist_db:
                self.db.vm.update_one({'IP Address': ipaddr}, {'$set': {'Status': 'Unreachable'}})
                self.db.vm.update_one({'IP Address': ipaddr}, {'$inc': {'Fail_count': 1}})
                return

            # If the VM is in login.txt but not registerd in DB, mark it as Unknown with N.A parameters and register it in DB
            # = In case users manually add to login.txt but SSH login to the VM fails
            elif exist_file and not exist_db:
                db_write_unreachable(self.db, ipaddr)
                return

        # After SSH login succeeds: Collect data, parse, and store to DB
        try: 
            # get OS type and Release
            output = getOutput(cmd_distribution, s)
            os_dist, release = getOS(output)

            # get hostname
            output = getOutput(cmd_hostname, s)
            hostname = getHostname(output)

            # get MAC Addresss
            output = getOutput(cmd_mac, s)
            mac = getMAC(output, ipaddr)

            # get uptime 
            output = getOutput(cmd_uptime, s)
            uptime = getUptime(output)

            # get CPU load average
            output = getOutput(cmd_cpu, s)
            cpu_load = getCPU(output)

            # get Memory Usage
            output = getOutput(cmd_mem, s)
            memory_usage = getMemory(output)

            # get Disk Usage
            output = getOutput(cmd_disk, s)
            disk_usage = getDisk(output)

            # Write to DB
            output_list = [ipaddr, hostname, mac, os_dist, release, uptime, cpu_load, memory_usage, disk_usage]
            db_write_ok(self.db, output_list)

            s.logout()
            return
        except Exception as e:
#            print e
            print "!! UNKNOWN ERROR OCCURED DURING THE SSH SESSION !!"
            raise
            sys.exit(3)


# Background threads called by main.py for every 30 seconds
def ssh(db):
    # Check a status mismatch between login.txt/DB. Delete entry in DB if the ip is not in login.txt (= Deleted manually by user)
    check_mismatch(db)
    # read login.txt and put credentials into a list
    login_list = file_read()

    if login_list:
        # Assign a thread to each entry
        print "{}: {}".format(datetime.now(), "Started collecting data via SSH")
        threads = []
        for i in range(len(login_list)):
            th = SSHThread(db, login_list[i])
            th.daemon=True
            threads.append(th)
            th.start()
        for thread in threads: 
            thread.join()
        print "{}: {}".format(datetime.now(), "Completed collecting data and updated the database")
        print
    else:   # no entry found in login.txt
        pass
