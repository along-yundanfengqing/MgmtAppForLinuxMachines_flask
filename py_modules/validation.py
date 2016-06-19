import socket
import os
import re

DIR = os.getcwd()
FILENAME = 'login.txt'
FILEPATH = os.path.join(DIR,FILENAME)

def is_valid_IPv4(ipaddr):
    try:
        socket.inet_pton(socket.AF_INET, ipaddr)
        return True
    except socket.error:
        return False

def is_valid_username(username):
    if re.match(r"^[a-zA-Z0-9]+[a-zA-Z0-9_.-]+$", username):
        return True
    else:
        return False

def is_valid_password(password):
    if password == None or re.match(r"^[a-zA-Z0-9!@#\$%\^&\*\(\)\-\+\=_\?\{\}\[\]\<\>\/:;\"\']+$", password):
        return True
    else:
        return False

def exists_in_file(ipaddr):
    try:
        with open(FILEPATH, 'r') as f:
            PATTERN = re.compile(r"^%s,"%ipaddr)
            for line in f.readlines():
                if re.match(PATTERN, line):
                    return True
            return False
    except Exception as e:
        print e
        return

def check_mismatch(db):
    docs = db.vm.find({}, {'_id': 0, 'IP Address': 1, 'Hostname': 1})
    for doc in docs:
        if exists_in_file(doc['IP Address']):
            continue
        else:
            db.vm.delete_one({'IP Address': doc['IP Address']})

