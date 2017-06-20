# -*- coding: utf-8 -*-
import ipaddress

from application.modules.validation import Validation
from application.modules.aws_ec2 import EC2Client

class Machine(object):
    def __init__(self, hostname="#Unknown", ip_address=None, status="Unknown (Waiting for the first SSH access)",
                 fail_count=0, mac_address=None, os_distribution=None, release=None, uptime=None,
                 cpu_info=None, cpu_load_avg=None, memory_usage=None, disk_usage=None, last_updated=None):

        self.hostname = hostname
        self.ip_address = ip_address
        self.ip_address_decimal = int(ipaddress.IPv4Address(self.ip_address))
        self.status = status
        self.fail_count = fail_count
        self.mac_address = mac_address
        self.os_distribution = os_distribution
        self.release = release
        self.uptime = uptime
        self.cpu_info = cpu_info
        self.cpu_load_avg = cpu_load_avg
        self.memory_usage = memory_usage
        self.disk_usage = disk_usage
        self.aws = Validation.is_aws(self.ip_address)
        if self.aws:
            if self.status == 'OK':
                ec2_state = "running"
            else:
                ec2_state = None

            self.ec2 = {
                'instance_id': EC2Client.get_instance_id(ip_address),
                'state': ec2_state
            }
        self.last_updated = last_updated
