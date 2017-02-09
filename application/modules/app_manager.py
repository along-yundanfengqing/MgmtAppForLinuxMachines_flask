# -*- coding: utf-8 -*-
import json
import os
import pip
import re
import signal

# my modules
from application import mongo
from application.modules.file_io import FileIO


class AppManager(object):
    def add_vm(self, ipaddr, username, password):
        try:
            FileIO.add_vm_to_file(ipaddr, username, password)   # write to login.txt
            mongo.write_new(ipaddr)     # write to DB
            return True
        except Exception:
            return False

    def del_vm(self, del_ip_list):
        mongo.remove(del_ip_list)
        FileIO.del_vm_from_file(del_ip_list)

    def export_json(self, filename, doc):
        BASE_DIR = os.getcwd()
        JSON_FILENAME = filename
        JSON_DIR = BASE_DIR + "/application/json_files"
        JSON_FILEPATH = os.path.join(JSON_DIR, JSON_FILENAME)

        try:
            with open(JSON_FILEPATH, 'w') as f:
                doc['Last Updated'] = str(doc['Last Updated'])
                json.dump(doc, f, indent=4)
                return True, JSON_DIR
        except Exception as e:
            print(e.message)
            return False, None

    # kill existing process before opening another butterfly terminal
    def kill_butterfly(self):
        for line in os.popen("ps -ea | grep butterfly"):
            if re.search('butterfly\.s', line):
                pid = line.split()[0]
                os.kill(int(pid), signal.SIGHUP)

    # check if .pem file exists under ~/.ssh/
    def search_pem(self):
        HOME_DIR = os.getenv("HOME")
        SSH_DIR = os.path.join(HOME_DIR, '.ssh')
        ls = os.listdir(SSH_DIR)
        for item in ls:
            PATTERN = re.compile(r".*\.pem")
            if re.search(PATTERN, item.strip()):
                PEM_PATH = "%s/%s" % (SSH_DIR, item)
                return PEM_PATH, SSH_DIR
        # if .pem not exists
        PEM_PATH = None
        return PEM_PATH, SSH_DIR

    def check_butterfly(self):
        # Check if butterfly module is installed
        print("Checking if butterfly module is installed..."),
        installed_packages = pip.get_installed_distributions()
        flat_installed_packages = [package.project_name for package in installed_packages]
        if 'butterfly' in flat_installed_packages:      # Installed
            print("OK\n")
            return True
        else:       # Not installed
            print("Not Installed\n")
            return False
