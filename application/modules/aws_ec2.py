# -*- coding: utf-8 -*-
import boto3
import pprint

# my modules
#from application import app, socketio


class EC2Client(object):
    ec2_client = boto3.client('ec2')
    #waiter = ec2_client.get_waiter('bundle_task_complete')
    ip_instance_map = {}

    @staticmethod
    def get_instance_id(ip_address):
        response = EC2Client.ec2_client.describe_instances()
        for r in response['Reservations']:
            for instance in r['Instances']:
                try:
                    if instance['PublicIpAddress'] == ip_address:
                        instance_id = instance['InstanceId']
                        EC2Client.ip_instance_map[ip_address] = instance_id
                        return instance_id
                except KeyError:
                    pass


class EC2Instance(object):
    def __init__(self, ip_address):
        self.ec2 = boto3.resource('ec2')
        self.instance_id = EC2Client.get_instance_id(ip_address)
        self.instance = self.ec2.Instance(self.instance_id)


    def start(self):
        response = self.instance.start()
        #app.logger.info("Starting the EC2 instance(InstanceID=%s)" % instance_ids[0])
        #socketio.emit('message', {'data': 'ec2_starting'})

        # Wait

        pprint.pprint(response)
        return response


    def stop(self):
        response = self.instance.stop()
        #app.logger.info("Stopping the EC2 instance(InstanceID=%s)" % instance_ids[0])
        #socketio.emit('message', {'data': 'ec2_stopping'})

        pprint.pprint(response)
        return response
