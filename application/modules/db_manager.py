# -*- coding: utf-8 -*-
import ipaddress
import pymongo
import sys

# my modules
from application import app
from application.modules.file_io import FileIO
from application.modules.validation import Validation
from application.modules.machines_cache import MachinesCache

machines_cache = MachinesCache.get_current_instance()

class DBManager(object):

    current_instance = None

    def __init__(self):
        self.__database_name = app.config['MONGO_DATABASE_NAME']
        self.__database_ip = app.config['MONGO_HOST']
        self.__collection_name = app.config['MONGO_COLLECTION_NAME']
        self.__port = app.config['MONGO_PORT']
        self.db = self.__connect_db()
        self.db.collection = self.db[self.__collection_name]
        self.db.collection.create_index([('ip_address', pymongo.ASCENDING), ('hostname', pymongo.ASCENDING)])
        self.db.collection.create_index([('hostname', pymongo.ASCENDING), ('ip_address_decimal', pymongo.ASCENDING)])

    @classmethod
    def get_current_instance(cls):
        if DBManager.current_instance is None:
            DBManager.current_instance = DBManager()
        return DBManager.current_instance


    def __connect_db(self):
        try:
            app.logger.info("Checking the connectivity to the database(%s)...." % self.__database_ip)
            uri = "mongodb://%s:%d" % (self.__database_ip, self.__port)
            client = pymongo.MongoClient(uri, serverSelectionTimeoutMS=3000)
            mongo_db = pymongo.database.Database(client, self.__database_name)
            if client.server_info():
                app.logger.info("...OK")
                return mongo_db
        except pymongo.errors.ServerSelectionTimeoutError as e:
            app.logger.error("Unable to connect to %s:%s" % (self.__database_ip, self.__port))
            sys.exit(3)
        except Exception as e:
            app.logger.critical(e)
            sys.exit(3)


    def find(self, *args):
        return self.db.collection.find(*args)


    def find_one(self, *args):
        return self.db.collection.find_one(*args)


    def update(self, *args, **kwargs):
        return self.db.collection.update_one(*args, **kwargs)


    def update_one(self, *args, **kwargs):
        return self.db.collection.update_one(*args, **kwargs)


    def remove(self, del_ip_list):
        return self.db.collection.remove({'ip_address': {'$in': del_ip_list}})


    def delete_one(self, *args):
        return self.db.collection.delete_one(*args)


    # When registered from GUI or RESTful API
    def write_new(self, ipaddr, last_updated):
        doc = {}
        doc['status'] = "Unknown (Waiting for the first SSH access)"
        doc['fail_count'] = 0
        doc['hostname'] = "#Unknown"
        doc['ip_address'] = ipaddr
        doc['ip_address_decimal'] = int(ipaddress.IPv4Address(ipaddr))
        doc['mac_address'] = "N.A"
        doc['os_distribution'] = "N.A"
        doc['release'] = "N.A"
        doc['uptime'] = "N.A"
        doc['cpu_load_avg'] = "N.A"
        doc['memory_usage'] = "N.A"
        doc['disk_usage'] = "N.A"
        doc['aws'] = Validation.is_aws(ipaddr)
        doc['last_updated'] = last_updated
        self.update_one(
            {'ip_address': ipaddr, 'hostname': "#Unknown"},
            {'$set': doc}, upsert=True)


    # When SSH succeeds to new or existing machines
    def update_status_ok(self, machine_data, last_updated):
        ipaddr, hostname, mac, os_dist, release, uptime, cpu_load, memory_usage, disk_usage = machine_data
        doc = {}
        doc['status'] = "OK"
        doc['fail_count'] = 0
        doc['hostname'] = hostname
        doc['ip_address'] = ipaddr
        doc['ip_address_decimal'] = int(ipaddress.IPv4Address(ipaddr))
        doc['mac_address'] = mac
        doc['os_distribution'] = os_dist
        doc['release'] = release
        doc['uptime'] = uptime
        doc['cpu_load_avg'] = cpu_load
        doc['memory_usage'] = memory_usage
        doc['disk_usage'] = disk_usage
        doc['aws'] = Validation.is_aws(ipaddr)
        doc['last_updated'] = last_updated
        # Unmark the old Hostname(#Unknown) entry if exists after SSH succeeds
        if self.find({'ip_address': ipaddr, 'hostname': "#Unknown"}):
            self.delete_one({'ip_address': ipaddr, 'hostname': "#Unknown"})
        self.update({'ip_address': ipaddr}, {'$set': doc}, upsert=True)


    # When SSH fails to existing machines whose status was previously ok
    def update_status_unreachable(self, ipaddr):
        self.update_one({'ip_address': ipaddr}, {'$set': {'status': 'Unreachable'}})
        self.update_one({'ip_address': ipaddr}, {'$inc': {'fail_count': 1}})


    # Check mismatch between login.txt and database
    def check_mismatch(self):
        docs = self.find({}, {'_id': 0, 'ip_address': 1, 'hostname': 1})
        for doc in docs:
            ipaddr = doc['ip_address']
            if not FileIO.exists_in_file(ipaddr):
                self.delete_one({'ip_address': ipaddr})
                machines_cache.delete(ipaddr)
