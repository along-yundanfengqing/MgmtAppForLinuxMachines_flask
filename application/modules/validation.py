# -*- coding: utf-8 -*-
import os
import re
import socket


BASE_DIR = os.getcwd()
LOGIN_FILENAME = 'login.txt'
LOGIN_FILEPATH = os.path.join(BASE_DIR, LOGIN_FILENAME)

def is_valid_IPv4(ipaddr):
    try:
        socket.inet_pton(socket.AF_INET, ipaddr)
        return True
    except socket.error:
        return False

def is_valid_username(username):
    return re.match(r"^[a-zA-Z0-9]+[a-zA-Z0-9_.-]+$", username)

def is_valid_password(password):
    return password is None or re.match(r"^[a-zA-Z0-9!@#\$%\^&\*\(\)\-\+\=_\?\{\}\[\]\<\>\/:;\"\']+$", password)

# check if the IP Address is from AWS cloud
def is_aws(ipaddr):
    aws_cache = []  # cache for AWS IP Address
    no_aws_cache = []   # cache for non-AWS IP Address
    if ipaddr in aws_cache:
        return True
    elif ipaddr in no_aws_cache:
        return False
    else:   # if ipaddr not in chache
        for line in os.popen("nslookup %s " % ipaddr):
            if 'compute.amazonaws.com' in line:
                aws_cache.append(ipaddr)
                return True
        no_aws_cache.append(ipaddr)
        return False

def exists_in_file(ipaddr):
    try:
        with open(LOGIN_FILEPATH, 'r') as f:
            PATTERN = re.compile(r"^%s,"%ipaddr)
            for line in f.readlines():
                if re.match(PATTERN, line):
                    return True
            return False
    except Exception as e:
        print(e)
        return
