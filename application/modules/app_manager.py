# -*- coding: utf-8 -*-
import json
import os
import re
import signal

# my modules
from application import mongo


BASE_DIR = os.getcwd()
LOGIN_FILENAME = 'login.txt'
LOGIN_FILEPATH = os.path.join(BASE_DIR, LOGIN_FILENAME)


class AppManager(object):
    def add_vm(self, ipaddr, username, password):
        try:
            with open(LOGIN_FILEPATH, 'a+') as f:
                # add to login.txt
                if password:    # for password authentication
                    output = "{}{},{},{}".format("\n", ipaddr, username, password)
                else:           # for SSH-key based authentication
                    output = "{}{},{}".format("\n", ipaddr, username)
                f.writelines(output)        # write to login.txt
                mongo.write_new(ipaddr)     # write to DB
            return True

        except Exception as e:
            print(e)
            return False

    def del_vm(self, del_list):
        # delete from DB
        for ipaddr in del_list:
            mongo.delete_one({'IP Address': ipaddr})
        # delete from login.txt
            output = []
            with open(LOGIN_FILEPATH, 'r') as f:
                PATTERN = re.compile(r"^%s," % ipaddr)
                for line in f.readlines():
                    if re.match(PATTERN, line):
                        continue
                    else:
                        output.append(line)
            with open(LOGIN_FILEPATH, 'w') as f:
                # strop newline code from the last entry before writing out
                if "\n" in output[-1]:
                    output[-1] = output[-1].strip()
                f.writelines(output)

    # kill existing process before opening another butterfly terminal
    def kill_butterfly(self):
        for line in os.popen("ps -ea | grep butterfly"):
            if re.search('butterfly\.s', line):
                pid = line.split()[0]
                os.kill(int(pid), signal.SIGHUP)

    def export_json(self, filename, doc):
        josn_filename = filename
        json_dir = BASE_DIR + "/application/json_files"
        json_filepath = os.path.join(json_dir, josn_filename)

        try:
            with open(json_filepath, 'w') as f:
                doc['Last Updated'] = str(doc['Last Updated'])
                json.dump(doc, f, indent=4)
                return True, json_dir
        except Exception as e:
            return False, None
