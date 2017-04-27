# -*- coding: utf-8 -*-

from application.modules.validation import Validation
from application.modules.machines import Machine

class MachinesCache(object):
    def __init__(self):
        self.machine_obj_list = []      # Cache


    def get(self, ip_address=None):
        # return all machines
        if not ip_address:
            self.machine_obj_list.sort(key=lambda x: (x.hostname, x.ip_address), reverse=False)
            return self.machine_obj_list

        # return specified machine
        for machine in self.machine_obj_list:
            if machine.ip_address == ip_address:
                return machine

        return None


    def add(self, machine):
        self.machine_obj_list.append(machine)


    def delete(self, delete_ip_list):
        for ip in delete_ip_list:
            for machine in self.machine_obj_list:
                if machine.ip_address == ip:
                    self.machine_obj_list.remove(machine)


    def update_ok(self, machine_data, last_updated):
        ip_address, hostname, mac_address, os_distribution, release, uptime, \
        cpu_load_avg, memory_usage, disk_usage = machine_data

        if self.machine_obj_list > 0:
            for index, machine in enumerate(self.machine_obj_list):
                if machine.ip_address == ip_address:
                    machine.status = 'OK'
                    machine.fail_count = 0
                    machine.hostname = hostname
                    machine.mac_address = mac_address
                    machine.os_distribution = os_distribution
                    machine.release = release
                    machine.uptime = uptime
                    machine.cpu_load_avg = cpu_load_avg
                    machine.memory_usage = memory_usage
                    machine.disk_usage = disk_usage
                    machine.aws = Validation.is_aws(ip_address)
                    machine.last_updated = last_updated
                    self.machine_obj_list[index] = machine      # update machine_list
                    return

        # machine does not exist in machine_list
        machine = Machine(ip_address, last_updated, 'OK', 0, hostname, mac_address, os_distribution,
                          release, uptime, cpu_load_avg, memory_usage, disk_usage)
        self.machine_obj_list.append(machine)


    def update_unreachable(self, ip_address, last_updated):
        if self.machine_obj_list > 0:
            for index, machine in enumerate(self.machine_obj_list):
                if machine.ip_address == ip_address:
                    machine.status = "Unreachable"
                    machine.fail_count += 1
                    self.machine_obj_list[index] = machine  # update machine_list
                    return

        # machine does not exist in machine_list
        machine = Machine(ip_address, last_updated, 'Unreachable', 1)
        self.machine_obj_list.append(machine)


    def convert_to_machine_list(self, docs):
        tmp_machine_list = []
        for doc in docs:
            machine = Machine(
                doc['IP Address'],
                doc['Last Updated'],
                doc['Status'],
                doc['Fail_count'],
                doc['Hostname'],
                doc['MAC Address'],
                doc['OS'],
                doc['Release'],
                doc['Uptime'],
                doc['CPU Load Avg'],
                doc['Memory Usage'],
                doc['Disk Usage'],
            )

            tmp_machine_list.append(machine)

        return tmp_machine_list


    def clear(self):    # Unused
        del self.machine_obj_list[:]
