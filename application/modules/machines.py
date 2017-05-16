# -*- coding: utf-8 -*-
import ipaddress

from application.modules.validation import Validation
from application.modules.aws_ec2 import EC2Client

class Machine(object):
    def __init__(self, ip_address, last_updated, status="Unknown (Waiting for the first SSH access)",
                 fail_count=0, hostname="#Unknown", mac_address=None, os_distribution=None, release=None,
                 uptime=None, cpu_load_avg=None, memory_usage=None, disk_usage=None):

        self.status = status
        self.fail_count = fail_count
        self.hostname = hostname
        self.ip_address = ip_address
        self.ip_address_decimal = int(ipaddress.IPv4Address(self.ip_address))
        self.mac_address = mac_address
        self.os_distribution = os_distribution
        self.release = release
        self.uptime = uptime
        self.cpu_load_avg = cpu_load_avg
        self.memory_usage = memory_usage
        self.disk_usage = disk_usage
        self.aws = Validation.is_aws(self.ip_address)
        self.last_updated = last_updated

        if self.aws:
            self.ec2 = {
                'instance_id': EC2Client.get_instance_id(ip_address),
                'state': None
            }

