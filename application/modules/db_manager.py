# -*- coding: utf-8 -*-
import pymongo
import sys
from datetime import datetime

# my modules
from application.modules.db_cache import DBCache
from application.modules.file_io import FileIO
from application.modules.validation import Validation


class DBManager(object):

    def __init__(self, app):
        self.__app = app
        self.__database_name = app.config['MONGO_DATABASE_NAME']
        self.__database_ip = app.config['MONGO_HOST']
        self.__collection_name = app.config['MONGO_COLLECTION_NAME']
        self.__port = app.config['MONGO_PORT']
        self.db = self.__connect_db()
        self.db.collection = self.db[self.__collection_name]
        self.db.collection.create_index([("IP Address", pymongo.ASCENDING), ("Hostname", pymongo.ASCENDING)])

    def __connect_db(self):
        try:
            self.__app.logger.info("Checking the connectivity to the database(%s)...." % self.__database_ip)
            uri = "mongodb://%s:%d" % (self.__database_ip, self.__port)
            client = pymongo.MongoClient(uri, serverSelectionTimeoutMS=3000)
            mongo_db = pymongo.database.Database(client, self.__database_name)
            if client.server_info():
                self.__app.logger.info("...OK")
                return mongo_db
        except pymongo.errors.ServerSelectionTimeoutError as e:
            self.__app.logger.error("Unable to connect to %s:%s" % (self.__database_ip, self.__port))
            sys.exit(3)
        except Exception as e:
            self.__app.logger.critical(e.message)
            sys.exit(3)

    def find(self, *args):
        return self.db.collection.find(*args)

    def find_one(self, *args):
        return self.db.collection.find_one(*args)

    def update(self, *args, **kwargs):
        DBCache.set_update_flag(True)
        return self.db.collection.update_one(*args, **kwargs)

    def update_one(self, *args, **kwargs):
        DBCache.set_update_flag(True)
        return self.db.collection.update_one(*args, **kwargs)

    def remove(self, del_ip_list):
        DBCache.set_update_flag(True)
        return self.db.collection.remove({'IP Address': {'$in': del_ip_list}})

    def delete_one(self, *args):
        DBCache.set_update_flag(True)
        return self.db.collection.delete_one(*args)

    def write_unreachable(self, ipaddr):
        doc = {}
        doc['Status'] = "Unreachable"
        doc['Fail_count'] = 1
        doc['Hostname'] = "#Unknown"
        doc['IP Address'] = ipaddr
        doc['MAC Address'] = "N.A"
        doc['OS'] = "N.A"
        doc['Release'] = "N.A"
        doc['Uptime'] = "N.A"
        doc['CPU Load Avg'] = "N.A"
        doc['Memory Usage'] = "N.A"
        doc['Disk Usage'] = "N.A"
        if Validation.is_aws(ipaddr):
            doc['AWS'] = True
        else:
            doc['AWS'] = False
        doc['Last Updated'] = datetime.now()
        self.update({'IP Address': ipaddr, 'Hostname': "#Unknown"} {'$set': doc}, upsert=True)

    def write_ok(self, output_list):
        ipaddr, hostname, mac, os_dist, release, uptime, cpu_load, memory_usage, disk_usage = output_list
        doc = {}
        doc['Status'] = "OK"
        doc['Fail_count'] = 0
        doc['Hostname'] = hostname
        doc['IP Address'] = ipaddr
        doc['MAC Address'] = mac
        doc['OS'] = os_dist
        doc['Release'] = release
        doc['Uptime'] = uptime
        doc['CPU Load Avg'] = cpu_load
        doc['Memory Usage'] = memory_usage
        doc['Disk Usage'] = disk_usage
        if Validation.is_aws(ipaddr):
            doc['AWS'] = True
        else:
            doc['AWS'] = False
        doc['Last Updated'] = datetime.now()
        # Unmark the old Hostname(#Unknown) entry if exists after SSH succeeds
        if self.find({'IP Address': ipaddr, 'Hostname': "#Unknown"}):
            self.delete_one({'IP Address': ipaddr, 'Hostname': "#Unknown"})
        self.update({'IP Address': ipaddr}, {'$set': doc}, upsert=True)

    def write_new(self, ipaddr):
        doc = {}
        doc['Status'] = "Unknown (Waiting for the first SSH access)"
        doc['Fail_count'] = 0
        doc['Hostname'] = "#Unknown"
        doc['IP Address'] = ipaddr
        doc['MAC Address'] = "N.A"
        doc['OS'] = "N.A"
        doc['Release'] = "N.A"
        doc['Uptime'] = "N.A"
        doc['CPU Load Avg'] = "N.A"
        doc['Memory Usage'] = "N.A"
        doc['Disk Usage'] = "N.A"
        if Validation.is_aws(ipaddr):
            doc['AWS'] = True
        else:
            doc['AWS'] = False
        doc['Last Updated'] = datetime.now()
        self.update_one(
            {'IP Address': ipaddr, 'Hostname': "#Unknown"},
            {'$set': doc}, upsert=True)

    def check_mismatch(self):
        docs = self.find({}, {'_id': 0, 'IP Address': 1, 'Hostname': 1})
        for doc in docs:
            ipaddr = doc['IP Address']
            if FileIO.exists_in_file(ipaddr):
                continue
            else:
                self.delete_one({'IP Address': ipaddr})
                DBCache.set_update_flag(True)


