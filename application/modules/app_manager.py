# -*- coding: utf-8 -*-
import json
import os
import pip
import re
import signal
from datetime import datetime

# my modules
from application import app
from application.modules.db_manager import DBManager
from application.modules.file_io import FileIO
from application.modules.machines import Machine
from application.modules.machines_cache import MachinesCache
from application.modules.aws_ec2 import EC2Instance

machines_cache = MachinesCache.get_current_instance()
mongo = DBManager.get_current_instance()

class AppManager(object):
    # Register a machine to (login.txt, database, cache)
    @staticmethod
    def add_machine(ipaddr, username, password):
        try:
            FileIO.add_vm_to_file(ipaddr, username, password)     # write to login.txt
            AppManager.create_machine_obj_and_write_db_new(ipaddr)   # Create a machine object and write to MongoDB
            return True
        except Exception as e:
            print(e)
            return False


    # delete machines from (login.txt, database, cache)
    @staticmethod
    def del_machine(del_ip_list):
        del_result = mongo.remove(del_ip_list)
        if del_result > 0:
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
                doc['last_updated'] = doc['last_updated'].isoformat()
                json.dump(doc, f, indent=4)
                return True, JSON_DIR
        except Exception as e:
            app.logger.error(e)
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
        PEM_PATH = None
        ls = os.listdir(SSH_DIR)
        for item in ls:
            PATTERN = re.compile(r".*\.pem")
            if re.search(PATTERN, item.strip()):
                PEM_PATH = "%s/%s" % (SSH_DIR, item)

        return PEM_PATH, SSH_DIR


    # Check if butterfly module is installed
    @staticmethod
    def is_butterfly_installed():
        installed_packages = pip.get_installed_distributions()
        flat_installed_packages = [package.project_name for package in installed_packages]
        return 'butterfly' in flat_installed_packages


    # create a machine object and write a new entry(status Unknown) to MongoDB
    @staticmethod
    def create_machine_obj_and_write_db_new(ipaddr):
        created_time = datetime.utcnow()
        machine = Machine(ipaddr, created_time)        # create a machine object
        mongo.write_new(ipaddr, created_time)          # Write to MongoDB
        machines_cache.add(machine)


    # update a machine object and update db entry(status OK)
    @staticmethod
    def update_machine_obj_and_update_db_ok(machine_data):
        last_updated = datetime.utcnow()
        machines_cache.update_ok(machine_data, last_updated)           # update machine object
        mongo.update_status_ok(machine_data, last_updated)     # Update MongoDB


    @staticmethod
    def update_machine_obj_and_update_db_unreachable(ipaddr):
        last_updated = datetime.utcnow()
        machines_cache.update_unreachable(ipaddr, last_updated)         # update machine object(increment failure count)
        mongo.update_status_unreachable(ipaddr)


    @staticmethod
    def delete_machine_obj(del_ip_list):
        machines_cache.delete(del_ip_list)


    @staticmethod
    def start_ec2(ipaddr):
        ec2_instance = EC2Instance(ipaddr)
        # Start
        ec2_instance.start()
        mongo.update_ec2_state(ipaddr, "pending")
        machines_cache.update_ec2_state(ipaddr, "pending")

        # Wait
        ec2_instance.wait_until_running()
        mongo.update_ec2_state(ipaddr, "running")
        machines_cache.update_ec2_state(ipaddr, "running")


    @staticmethod
    def stop_ec2(ipaddr):
        ec2_instance = EC2Instance(ipaddr)
        # Stop
        ec2_instance.stop()
        mongo.update_ec2_state(ipaddr, "stopping")
        machines_cache.update_ec2_state(ipaddr, "stopping")

        # Wait
        ec2_instance.wait_until_stopped()
        mongo.update_ec2_state(ipaddr, "stopped")
        machines_cache.update_ec2_state(ipaddr, "stopped")
