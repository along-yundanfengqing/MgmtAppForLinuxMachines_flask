# -*- coding: utf-8 -*-
import boto3

# my modules
from application import app


class EC2Client(object):
    ec2_client = boto3.client('ec2')
    ip_instance_map = {}

    @staticmethod
    def get_instance_id(ip_address):
        response = EC2Client.ec2_client.describe_instances()
        for r in response['Reservations']:
            for instance in r['Instances']:
                try:
                    if instance['PublicIpAddress'] == ip_address:
                        _instance_id = instance['InstanceId']
                        EC2Client.ip_instance_map[ip_address] = _instance_id
                        return _instance_id
                except KeyError:
                    pass


class EC2Instance(object):
    def __init__(self, ip_address):
        self.ec2 = boto3.resource('ec2')
        self._instance_id = EC2Client.get_instance_id(ip_address)
        self.instance = self.ec2.Instance(self._instance_id)


    def start(self):    # stopped -> pending
        current_state = self.instance.state['Name']
        response = self.instance.start()
        new_state = self.get_new_state()
        app.logger.info("EC2(InstanceID=%s) state changed: %s -> %s" % (self.instance.id, current_state, new_state))

        return response


    def stop(self):     # running -> stopping
        current_state = self.instance.state['Name']
        response = self.instance.stop()
        new_state = self.get_new_state()
        app.logger.info("EC2(InstanceID=%s) state changed: %s -> %s" % (self.instance.id, current_state, new_state))

        return response


    def wait_until_running(self):      # pending -> running
        current_state = self.instance.state['Name']
        self.instance.wait_until_running()
        new_state = self.get_new_state()
        app.logger.info("EC2(InstanceID=%s) state changed: %s -> %s" % (self.instance.id, current_state, new_state))


    def wait_until_stopped(self):   # stopping -> stopped
        current_state = self.instance.state['Name']
        self.instance.wait_until_stopped()
        new_state = self.get_new_state()
        app.logger.info("EC2(InstanceID=%s) state changed: %s -> %s" % (self.instance.id, current_state, new_state))


    def get_new_state(self):
        self.instance = self.ec2.Instance(self.instance.id)
        return self.instance.state['Name']
