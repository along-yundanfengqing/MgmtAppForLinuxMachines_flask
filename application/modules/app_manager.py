# -*- coding: utf-8 -*-
import json
import os
import pip
import re
import signal
from datetime import datetime

# my modules
from application import app, mongo, machines_cache
from application.modules.file_io import FileIO
from application.modules.machines import Machine


class AppManager(object):
    # Register a machine to (login.txt, database, cache)
    @staticmethod
    def add_machine(ipaddr, username, password):
        try:
            FileIO.add_vm_to_file(ipaddr, username, password)     # write to login.txt
            AppManager.create_machine_obj_and_write_db_new(ipaddr)   # Create a machine object and write to MongoDB
            return True
        except Exception:
            return False


    # delete machines from (login.txt, database, cache)
    @staticmethod
    def del_machine(del_ip_list):
        del_result = mongo.remove(del_ip_list)
        if del_result['ok'] == 1 and del_result['n'] > 0:
            FileIO.del_vm_from_file(del_ip_list)
            AppManager.delete_machine_obj(del_ip_list)
        return del_result


    @staticmethod
    def export_json(filename, doc):
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
            app.logger.error(e.message)
            return False, None


    # kill existing process before opening another butterfly terminal
    @staticmethod
    def kill_butterfly():
        for line in os.popen("ps -ea | grep butterfly"):
            if re.search('butterfly\.s', line):
                pid = line.split()[0]
                os.kill(int(pid), signal.SIGHUP)


    # check if .pem file exists under ~/.ssh/
    @staticmethod
    def search_pem():
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


    # Check if butterfly module is installed
    @staticmethod
    def check_butterfly():
        app.logger.info("Checking if butterfly module is installed...")
        installed_packages = pip.get_installed_distributions()
        flat_installed_packages = [package.project_name for package in installed_packages]
        if 'butterfly' in flat_installed_packages:      # Installed
            app.logger.info("...OK")
            return True
        else:       # Not installed
            app.logger.warning("...Not Installed")
            return False

    # create a machine object and write a new entry(status Unknoqn) to MongoDB
    @staticmethod
    def create_machine_obj_and_write_db_new(ipaddr):
        created_time = datetime.now()
        machine = Machine(ipaddr, created_time)        # create a machine object
        mongo.write_new(ipaddr, created_time)          # Write to MongoDB
        machines_cache.add(machine)


    # update a machine object and update db entry(status OK)
    @staticmethod
    def update_machine_obj_and_update_db_ok(machine_data):
        last_updated = datetime.now()
        machines_cache.update_ok(machine_data, last_updated)           # update machine object
        mongo.update_status_ok(machine_data, last_updated)     # Update MongoDB


    @staticmethod
    def update_machine_obj_and_update_db_unreachable(ipaddr):
        last_updated = datetime.now()
        machines_cache.update_unreachable(ipaddr, last_updated)         # update machine object(increment failure count)
        mongo.update_status_unreachable(ipaddr)


    @staticmethod
    def create_machine_obj_and_write_db_unreachable(ipaddr):
        last_updated = datetime.now()
        machines_cache.write_unreachable(ipaddr, last_updated)  # update machine object(increment failure count)
        mongo.write_status_unreachable(ipaddr)


    @staticmethod
    def delete_machine_obj(del_ip_list):
        machines_cache.delete(del_ip_list)
