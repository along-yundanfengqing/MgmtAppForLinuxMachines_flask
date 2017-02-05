# -*- coding: utf-8 -*-
import os
import pip
import re


BASE_DIR = os.getcwd()
LOGIN_FILENAME = 'login.txt'
LOGIN_FILEPATH = os.path.join(BASE_DIR, LOGIN_FILENAME)

def check_butterfly():
    # Check if butterfly module is installed
    print("Checking if butterfly module is installed..."),
    installed_packages = pip.get_installed_distributions()
    flat_installed_packages = [package.project_name for package in installed_packages]
    if 'butterfly' in flat_installed_packages:
        #butterfly=1     # Installed
        print("OK")
        return True
    else:
        #butterfly=0     # Not installed
        print("Not Installed")
        return False

def get_login_list():
    login_list = []
    with open(LOGIN_FILEPATH, 'r') as f:
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
            except Exception as e:
                login_data.append(None)

            login_list.append([ipaddr, username, password])

    if len(login_list) > 0:
        return login_list

    else:
        #raise Exception('ERROR: No entry found in login.txt')
        print("ERROR: No entry found in login.txt")
        return False

# check if .pem file exists under ~/.ssh/
def search_pem():
    home_dir = os.getenv("HOME")
    ssh_dir = os.path.join(home_dir, '.ssh')
    ls = os.listdir(ssh_dir)
    for item in ls:
        PATTERN = re.compile(r".*\.pem")
        if re.search(PATTERN, item.strip()):
            pem_path = "%s/%s" % (ssh_dir, item)
            return pem_path, ssh_dir
    # if .pem not exists
    pem_path = None
    return pem_path, ssh_dir

def get_username(ipaddr):
    try:
        with open(LOGIN_FILEPATH, 'r') as f:
            for line in f.readlines():
                if line.split(',')[0].strip() == ipaddr:
                    return line.split(',')[1].strip()
    except Exception as e:
        return False
