# -*- coding: utf-8 -*-

from application.modules.validation import Validation

class Machine(object):
    def __init__(self, ip_address, last_updated, status="Unknown (Waiting for the first SSH access)",
                 fail_count=0, hostname="#Unknown", mac_address="N.A", os_distribution="N.A", release="N.A",
                 uptime="N.A", cpu_load_avg="N.A", memory_usage="N.A", disk_usage="N.A"):

        self.status = status
        self.fail_count = fail_count
        self.hostname = hostname
        self.ip_address = ip_address
        self.mac_address = mac_address
        self.os_distribution = os_distribution
        self.release = release
        self.uptime = uptime
        self.cpu_load_avg = cpu_load_avg
        self.memory_usage = memory_usage
        self.disk_usage = disk_usage
        self.aws = Validation.is_aws(self.ip_address)
        self.last_updated = last_updated
