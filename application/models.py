# -*- coding: utf-8 -*-
import ipaddress
from mongoengine import Document, DynamicDocument
from mongoengine import BooleanField, DictField, IntField, ListField, LongField, StringField, DateTimeField

# my modules
from application import app
from application.modules.validation import Validation
from application.modules.aws_ec2 import EC2Client


class User(Document):
    username = StringField(required=True)
    password = StringField(required=True)
    meta = {'collection': 'users'}


class MachineData(DynamicDocument):
    hostname = StringField(default="#Unknown")
    ip_address = StringField(required=True, unique=True)
    ip_address_decimal = LongField(default=None)
    status = StringField(default="Unknown")
    fail_count = IntField(default=0)
    mac_address = StringField(default=None)
    os_distribution = StringField(default=None)
    release = StringField(default=None)
    uptime = StringField(default=None)
    cpu_load_avg = DictField(default=None)
    memory_usage = DictField(default=None)
    disk_usage = ListField(default=None)
    aws = BooleanField(default=None)
    ec2 = DictField(default=None)
    last_updated = DateTimeField(required=True)
    meta = {
        'collection': app.config['MONGO_COLLECTION_NAME'],
        'indexes': [
            ('ip_address', 'hostname'),
            ('hostname', 'ip_address_decimal')
        ]
    }

    def clean(self):
        # delete existing entry if exists
        machine = MachineData.objects(ip_address=self.ip_address)
        if machine:
            machine.delete()

        # add ip_address_decimal, aws, ec2 fields depending on the ip_address
        if self.ip_address_decimal is None:
            self.ip_address_decimal = int(ipaddress.IPv4Address(self.ip_address))
        if self.aws is None:
            self.aws = Validation.is_aws(self.ip_address)
        if self.aws:
            if self.status == 'OK':
                self.ec2 = {
                    'instance_id': EC2Client.ip_instance_map.get(self.ip_address, EC2Client.get_instance_id(self.ip_address)),
                    'state': "running"
                }
            else:
                self.ec2 = {
                    'instance_id': EC2Client.ip_instance_map.get(self.ip_address, EC2Client.get_instance_id(self.ip_address)),
                    'state': None
                }
