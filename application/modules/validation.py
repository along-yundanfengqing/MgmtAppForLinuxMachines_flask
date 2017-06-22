# -*- coding: utf-8 -*-
import re
import socket
from application import app

class Validation(object):
    __is_connected = None
    __aws_cache = []    # cache for AWS IP Address
    __no_aws_cache = [] # cache for non-AWS IP Address


    @staticmethod
    def is_valid_ipv4(ipaddr):
        match = re.match("^(\d{0,3})\.(\d{0,3})\.(\d{0,3})\.(\d{0,3})$", ipaddr)
        if not match:
            return False

        octets = []
        for number in match.groups():
            octets.append(int(number))
        if octets[0] < 1:     # First octet = 0
            return False
        for number in octets:
            if number > 255 or number < 0:
                return False
        return True


    @staticmethod
    def is_valid_username(username):
        return re.match(r"^[a-zA-Z0-9]+[a-zA-Z0-9_.-]+$", username)


    @staticmethod
    def is_valid_password(password):
        return password is None or ' ' not in password


    # check if the IP Address is from AWS cloud
    @staticmethod
    def is_aws(ipaddr):
        if Validation.check_internet_connection():
            if ipaddr in Validation.__aws_cache:
                return True
            elif ipaddr in Validation.__no_aws_cache:
                return False
            else:   # if ipaddr not in chache
                try:
                    result = socket.gethostbyaddr(ipaddr)
                    for line in result:
                        if 'compute.amazonaws.com' in line:
                            Validation.__aws_cache.append(ipaddr)
                            return True
                except socket.herror:
                    Validation.__no_aws_cache.append(ipaddr)
        return False


    @staticmethod
    def check_internet_connection():
        if Validation.__is_connected is None:
            try:
                socket.setdefaulttimeout(3)
                socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect(("8.8.8.8", 53))
                Validation.__is_connected = True
                return True

            except:
                app.logger.warning("Internet connection is not available")
                Validation.__is_connected = False
        return Validation.__is_connected
