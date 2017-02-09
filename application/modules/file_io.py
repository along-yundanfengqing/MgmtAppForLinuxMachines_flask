import os
import re
from application import app

class FileIO(object):
    __BASE_DIR = os.getcwd()
    __LOGIN_FILENAME = app.config['LOGIN_FILENAME']
    __LOGIN_FILEPATH = os.path.join(__BASE_DIR, __LOGIN_FILENAME)

    @classmethod
    def get_login_list(cls):
        login_list = []
        with open(cls.__LOGIN_FILEPATH, 'r') as f:
            for line in f.readlines():
                login_data = []
                login_data = line.split(',')
                # Skip comment outed or invalid entries in login.txt
                if re.search(r"^#", login_data[0]) or (len(login_data) != 2 and len(login_data) != 3):
                    continue

                ipaddr = login_data[0].strip()
                username = login_data[1].strip()
                try:
                    password = login_data[2].strip()
                except Exception:
                    login_data.append(None)

                login_list.append([ipaddr, username, password])

        if len(login_list) > 0:
            return login_list

        else:
            print("ERROR: No entry found in login.txt")
            return False

    @classmethod
    def get_username(cls, ipaddr):
        try:
            with open(cls.__LOGIN_FILEPATH, 'r') as f:
                for line in f.readlines():
                    if line.split(',')[0].strip() == ipaddr:
                        return line.split(',')[1].strip()
        except Exception:
            return False

    @classmethod
    def exists_in_file(cls, ipaddr):
        try:
            with open(cls.__LOGIN_FILEPATH, 'r') as f:
                PATTERN = re.compile(r"^%s,"%ipaddr)
                for line in f.readlines():
                    if re.match(PATTERN, line):
                        return True
                return False
        except Exception:
            return False

    @classmethod
    def add_vm_to_file(cls, ipaddr, username, password):
        try:
            with open(cls.__LOGIN_FILEPATH, 'a+') as f:
                # add to login.txt
                if password:    # for password authentication
                    output = "{}{},{},{}".format("\n", ipaddr, username, password)
                else:           # for SSH-key based authentication
                    output = "{}{},{}".format("\n", ipaddr, username)
                f.writelines(output)        # write to login.txt

        except Exception as e:
            print(e)
            return

    @classmethod
    def del_vm_from_file(cls, del_ip_list):
        output = []
        try:
            with open(cls.__LOGIN_FILEPATH, 'r+') as f:
                for line in f.readlines():
                    ipaddr = line.split(',')[0].strip()
                    if ipaddr not in del_ip_list:
                        output.append(line)

                f.seek(0)
                f.truncate()

                if "\n" in output[-1]:
                    output[-1] = output[-1].strip()
                
                f.writelines(output)

        except Exception as e:
            print(e)
            return