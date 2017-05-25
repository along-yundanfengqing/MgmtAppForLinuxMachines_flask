# -*- coding: utf-8 -*-
import sys

from mongoengine import connect
from mongoengine.queryset import DoesNotExist

from application import app
from application.models import MachineData, User
from application.modules.file_io import FileIO
from application.modules.machines_cache import MachinesCache

machines_cache = MachinesCache.get_current_instance()


class DBManager(object):

    current_instance = None

    def __init__(self):
        self.__database_name = app.config['MONGO_DATABASE_NAME']
        self.__database_ip = app.config['MONGO_HOST']
        self.__port = app.config['MONGO_PORT']
        self.db = self.__connect_db()


    @classmethod
    def get_current_instance(cls):
        if DBManager.current_instance is None:
            DBManager.current_instance = DBManager()
        return DBManager.current_instance


    def __connect_db(self):
        try:
            app.logger.info(("Checking the connectivity to the database(%s)...." % self.__database_ip))
            connect(self.__database_name, host=self.__database_ip, port=self.__port, serverSelectionTimeoutMS=3000)
            app.logger.info("...OK")
        except Exception as e:
            app.logger.critical(type(e))
            sys.exit(1)


    def find(self, *args):
        return MachineData.objects(__raw__=args)


    def find_one(self, *args):
        try:
            return MachineData.objects.get(__raw__=args[0])
        except DoesNotExist:
            return False


    def remove(self, del_ip_list):
        return MachineData.objects(__raw__={'ip_address': {'$in': del_ip_list}}).delete()


    def find_user(self, data):
        try:
            return User.objects.get(username=data['username'])
        except DoesNotExist:
            return None


    def add_user(self, data):
        user = User(username=data['username'], password=data['password'])
        user.save()


    def delete_user(self, data):
        return User.objects(username=data['username']).delete()


    # When registered from GUI or RESTful API
    def write_new(self, ipaddr, last_updated):
        machine = MachineData(
            hostname="#Unknown",
            ip_address=ipaddr,
            status="Unknown (Waiting for the first SSH access)",
            fail_count=0,
            last_updated=last_updated
        )
        machine.save()  # call clean()


    # When SSH succeeds to new or existing machines
    def update_status_ok(self, machine_data, last_updated):
        ipaddr, hostname, mac, os_dist, release, uptime, cpu_load, memory_usage, disk_usage = machine_data

        MachineData.objects(ip_address=ipaddr).update(
            upsert=True,
            hostname=hostname,
            status="OK",
            fail_count=0,
            mac_address=mac,
            os_distribution=os_dist,
            release=release,
            uptime=uptime,
            cpu_load_avg=cpu_load,
            memory_usage=memory_usage,
            disk_usage=disk_usage,
            last_updated=last_updated
        )


    # When SSH fails to existing machines whose status was previously ok
    def update_status_unreachable(self, ipaddr):
        MachineData.objects(ip_address=ipaddr).update_one(set__status="Unreachable")
        MachineData.objects(ip_address=ipaddr).update_one(inc__fail_count=1)


    def update_ec2_state(self, ipaddr, state):
        MachineData.objects(ip_address=ipaddr).update_one(set__ec2__state=state)


    # Check mismatch between login.txt and database
    def check_mismatch(self):
        machines_data = MachineData.objects
        for machine_data in machines_data:
            ipaddr = machine_data.ip_address
            if not FileIO.exists_in_file(ipaddr):
                MachineData.objects(ip_address=ipaddr).delete()
                machines_cache.delete(ipaddr)
