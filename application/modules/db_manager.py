# -*- coding: utf-8 -*-
import pymongo
import sys
from datetime import datetime

# my modules
from application.modules.file_io import FileIO
from application.modules.validation import Validation


class DBManager(object):
    def __init__(self, app):
        self.__database_name = app.config['MONGO_DATABASE_NAME']
        self.__database_ip = app.config['MONGO_HOST']
        self.__collection_name = app.config['COLLECTION_NAME']
        self.__port = app.config['MONGO_PORT']
        self.db = self.__connect_db()
        self.db.collection = self.db[self.__collection_name]
        
    def __connect_db(self):
        try:
            print("Checking the connectivity to the database(%s)...." % self.__database_ip),
            uri = "mongodb://%s:%s" % (self.__database_ip, self.__port)
            client = pymongo.MongoClient(uri, serverSelectionTimeoutMS=3000)
            mongo_db = pymongo.database.Database(client, self.__database_name)
            if client.server_info():
                print("OK")
                return mongo_db
        except Exception:
            print
            print("ERROR: Unable to connect to %s" % self.__dbserver_ip)
            sys.exit(3)

    def find(self, *args):
        return self.db.collection.find(*args)
#        if len(args) == 1:
#            return self.db.collection.find(args[0])
#        elif len(args) == 2:
#            return self.db.collection.find(args[0], args[1])

    def find_one(self, *args):
        return self.db.collection.find_one(*args)
#        if len(args) == 1:
#            return self.db.collection.find_one(args[0])
#        elif len(args) == 2:
#            return self.db.collection.find_one(args[0], args[1])

    def update(self, *args, **kwargs):
        return self.db.collection.update_one(*args, **kwargs)
#        if kwargs:
#            upsert = kwargs.items()[0][0]
#            flag = kwargs.items()[0][1]
#            return self.db.collection.update(args[0], args[1], upsert=flag)
#        return self.db.collection.update_one(args[0], args[1])

    def update_one(self, *args, **kwargs):
        return self.db.collection.update_one(*args, **kwargs)
#        if kwargs:
#            upsert = kwargs.items()[0][0]
#            flag = kwargs.items()[0][1]
#            return self.db.collection.update_one(args[0], args[1], upsert=flag)
#        return self.db.collection.update_one(args[0], args[1])

    def remove(self, del_ip_list):
        return self.db.collection.remove({'IP Address': {'$in': del_ip_list}})
 
    def delete_one(self, *args):
        return self.db.collection.delete_one(*args)
        #return self.db.collection.delete_one(args[0])

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
        self.update({'Hostname': "#Unknown", 'IP Address': ipaddr}, {'$set': doc}, upsert=True)

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
        if self.find({'Hostname': "#Unknown", 'IP Address': ipaddr}):
            self.delete_one({'Hostname': "#Unknown", 'IP Address': ipaddr})
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
            {'Hostname': "#Unknown", 'IP Address': ipaddr},
            {'$set': doc}, upsert=True)

    def check_mismatch(self):
        docs = self.find({}, {'_id': 0, 'IP Address': 1, 'Hostname': 1})
        for doc in docs:
            if FileIO.exists_in_file(doc['IP Address']):
                continue
            else:
                self.delete_one({'IP Address': doc['IP Address']})
