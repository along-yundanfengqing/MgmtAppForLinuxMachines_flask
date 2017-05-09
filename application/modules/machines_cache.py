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
            self.machine_obj_list.sort(key=lambda x: (x.hostname, x.ip_address_decimal), reverse=False)
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
        socketio.emit('message', {'data': 'created_new', 'ip_address': machine.ip_address})
        app.logger.debug("Sent SocketIO message: created_new")


    def delete(self, delete_ip_list):
        if not isinstance(delete_ip_list, list):
            delete_ip_list = [delete_ip_list]

        for machine in self.machine_obj_list[:]:
            if machine.ip_address in delete_ip_list:
                self.machine_obj_list.remove(machine)
                socketio.emit('message', {'data': 'deleted', "ip_address": machine.ip_address})
                app.logger.debug("Sent SocketIO message: deleted " + machine.ip_address)


    def update_ok(self, machine_data, last_updated):
        ip_address, hostname, mac_address, os_distribution, release, uptime, \
        cpu_load_avg, memory_usage, disk_usage = machine_data

        if len(self.machine_obj_list) > 0:
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
        if len(self.machine_obj_list) > 0:
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
                doc['ip_address'],
                doc['last_updated'],
                doc['status'],
                doc['fail_count'],
                doc['hostname'],
                doc['mac_address'],
                doc['os_distribution'],
                doc['release'],
                doc['uptime'],
                doc['cpu_load_avg'],
                doc['memory_usage'],
                doc['disk_usage'],

            )

            tmp_machine_list.append(machine)

        return tmp_machine_list

    def convert_machine_to_doc(self, ip_address=None):
        if ip_address:
            doc = {}
            machine = self.get(ip_address)
            doc['ip_address'] = machine.ip_address
            doc['last_updated'] = machine.last_updated
            doc['status'] = machine.status
            doc['fail_count'] = machine.fail_count
            doc['hostname'] = machine.hostname
            doc['mac_address'] = machine.mac_address
            doc['os_distribution'] = machine.os_distribution
            doc['release'] = machine.release
            doc['uiptime'] = machine.uptime
            doc['cpu_load_avg'] = machine.cpu_load_avg
            doc['memory_usage'] = machine.memory_usage
            doc['disk_usage'] = machine.disk_usage
            doc['aws'] = Validation.is_aws(machine.ip_address)

            return doc

        else:
            return [self.convert_machine_to_doc(machine.ip_address)  for machine in self.get()]


    def clear(self):    # Unused
        del self.machine_obj_list[:]
