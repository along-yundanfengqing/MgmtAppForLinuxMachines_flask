# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import os
import re

# my modules
from application import app
from application.modules.validation import Validation


class FileIO(object):
    __BASE_DIR = os.getcwd()

    if app.testing:
        __LOGIN_FILENAME = "test_login.txt"
        __LOGIN_FILEPATH = os.path.join(__BASE_DIR, "tests/unittest", __LOGIN_FILENAME)
    else:
        __LOGIN_FILENAME = app.config['LOGIN_FILENAME']
        __LOGIN_FILEPATH = os.path.join(__BASE_DIR, __LOGIN_FILENAME)

    @staticmethod
    def get_login_list():
        login_list = []
        try:
            with open(FileIO.__LOGIN_FILEPATH, 'r') as f:
                for line in f.readlines():
                    login_data = line.split(',')
                    # Skip comment outed or invalid entries in login.txt
                    if re.search(r"^#", login_data[0]) or (len(login_data) != 2 and len(login_data) != 3):
                        continue

                    ipaddr = login_data[0].strip()
                    if not Validation.is_valid_ipv4(ipaddr):
                        app.logger.error("%s in %s is an invalid IP Address" % (ipaddr, FileIO.__LOGIN_FILENAME ))
                        continue

                    username = login_data[1].strip()
                    try:
                        password = login_data[2].strip()
                    except Exception:   # no password
                        password = None

                    login_list.append((ipaddr, username, password))

            if len(login_list) > 0:
                return login_list

            else:
                app.logger.warning("No entry found in %s" % FileIO.__LOGIN_FILENAME)
                return False

        except IOError:
            app.logger.error("Unable to open %s. Please check if the file exists" % FileIO.__LOGIN_FILENAME)
            return False


    @staticmethod
    def get_username(ipaddr):
        try:
            with open(FileIO.__LOGIN_FILEPATH, 'r') as f:
                for line in f.readlines():
                    if line.split(',')[0].strip() == ipaddr:
                        return line.split(',')[1].strip()

        except IOError:
            app.logger.error("Unable to open %s. Please check if the file exists" % FileIO.__LOGIN_FILENAME)
            return False


    @staticmethod
    def exists_in_file(ipaddr):
        try:
            with open(FileIO.__LOGIN_FILEPATH, 'r') as f:
                PATTERN = re.compile(r"^%s,"%ipaddr)
                for line in f.readlines():
                    if re.match(PATTERN, line):
                        return True
                return False

        except IOError:
            app.logger.error("Unable to open %s. Please check if the file exists" % FileIO.__LOGIN_FILENAME)
            return False


    @staticmethod
    def add_vm_to_file(ipaddr, username, password):
        try:
            with open(FileIO.__LOGIN_FILEPATH, 'a+') as f:
                # add to login.txt
                if password:    # for password authentication
                    output = "{}{},{},{}".format("\n", ipaddr, username, password)
                else:           # for SSH-key based authentication
                    output = "{}{},{}".format("\n", ipaddr, username)
                f.writelines(output)        # write to login.txt

        except IOError:
            app.logger.error("Unable to open %s. Please check if the file exists" % FileIO.__LOGIN_FILENAME)
            return False


    @staticmethod
    def del_vm_from_file(del_ip_list):
        output = []
        try:
            with open(FileIO.__LOGIN_FILEPATH, 'r+') as f:
                for line in f.readlines():
                    ipaddr = line.split(',')[0].strip()
                    if ipaddr not in del_ip_list:
                        output.append(line)

                f.seek(0)
                f.truncate()

                if "\n" in output[-1]:
                    output[-1] = output[-1].strip()

                f.writelines(output)

        except IOError:
            app.logger.error("Unable to open %s. Please check if the file exists" % FileIO.__LOGIN_FILENAME)
            return False
