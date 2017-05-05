# -*- coding: utf-8 -*-

from application import socketio, app
from application.modules.validation import Validation
from application.modules.machines import Machine

class MachinesCache(object):
    current_instance = None

    def __init__(self):
        self.machine_obj_list = []      # Cache

    @classmethod
    def get_current_instance(cls):
        if MachinesCache.current_instance is None:
            MachinesCache.current_instance = MachinesCache()
        return MachinesCache.current_instance

    def get(self, ip_address=None):
        # return all machines
        if not ip_address:
            self.machine_obj_list.sort(key=lambda x: (x.hostname, x.ip_address), reverse=False)
            return self.machine_obj_list

        # return specified machine
        for machine in self.machine_obj_list:
            if Validation.is_valid_ipv4(ip_address) and machine.ip_address == ip_address:
                return machine
            elif machine.hostname == ip_address:
                return machine

        return None


    def add(self, machine):
        self.machine_obj_list.append(machine)
        socketio.emit('message', {'data': 'created'})
        app.logger.debug("Sent SocketIO message: created")


    def delete(self, delete_ip_list):
        if not isinstance(delete_ip_list, list):
            delete_ip_list = [delete_ip_list]

        for ip in delete_ip_list:
            for machine in self.machine_obj_list:
                if machine.ip_address == ip:
                    self.machine_obj_list.remove(machine)
                    socketio.emit('message', {'data': 'deleted', "ip_address": machine.ip_address})
                    app.logger.debug("Sent SocketIO message: deleted " + machine.ip_address)


    def update_ok(self, machine_data, last_updated):
        ip_address, hostname, mac_address, os_distribution, release, uptime, \
        cpu_load_avg, memory_usage, disk_usage = machine_data

        if self.machine_obj_list > 0:
            for index, machine in enumerate(self.machine_obj_list):
                if machine.ip_address == ip_address:
                    old_status = machine.status
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
                    if ("Unknown" in old_status or "Unreachable" in old_status):
                        socketio.emit('message', {'data': 'updated'})
                        app.logger.debug("Sent SocketIO message: updated")
                    return

        # machine does not exist in machine_list
        machine = Machine(ip_address, last_updated, 'OK', 0, hostname, mac_address, os_distribution,
                          release, uptime, cpu_load_avg, memory_usage, disk_usage)
        self.machine_obj_list.append(machine)
        socketio.emit('message', {'data': 'created'})
        app.logger.debug("Sent SocketIO message: created")


    def update_unreachable(self, ip_address, last_updated):
        if self.machine_obj_list > 0:
            for index, machine in enumerate(self.machine_obj_list):
                if machine.ip_address == ip_address:
                    machine.status = "Unreachable"
                    machine.fail_count += 1
                    if (machine.hostname != "#Unknown" and machine.fail_count > 1):
                        socketio.emit('message', {'data': 'unreachable', 'ip_address': machine.ip_address})
                        app.logger.debug("Sent SocketIO message: unreachable " + machine.ip_address)
                    self.machine_obj_list[index] = machine  # update machine_list
                    return

        # machine does not exist in machine_list
        machine = Machine(ip_address, last_updated, 'Unreachable', 1)
        self.machine_obj_list.append(machine)
        socketio.emit('message', {'data': 'created'})
        app.logger.debug("Sent SocketIO message: created")


    def convert_docs_to_machine_list(self, docs):
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

    def convert_machine_to_doc(self, ip_address=None):
        if ip_address:
            doc = {}
            machine = self.get(ip_address)
            doc['IP Address'] = machine.ip_address
            doc['Last Updated'] = machine.last_updated
            doc['Status'] = machine.status
            doc['Fail_count'] = machine.fail_count
            doc['Hostname'] = machine.hostname
            doc['MAC Address'] = machine.mac_address
            doc['OS'] = machine.os_distribution
            doc['Release'] = machine.release
            doc['Uptime'] = machine.uptime
            doc['CPU Load Avg'] = machine.cpu_load_avg
            doc['Memory Usage'] = machine.memory_usage
            doc['Disk Usage'] = machine.disk_usage
            doc['AWS'] = Validation.is_aws(machine.ip_address)

            return doc

        else:
            docs = []
            for machine in self.machine_obj_list:
                docs.append(self.convert_machine_to_doc(machine.ip_address))

            return docs


    def clear(self):    # Unused
        del self.machine_obj_list[:]
