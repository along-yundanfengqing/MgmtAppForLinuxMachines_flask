import ipaddress
import logging
import unittest
from datetime import datetime
from mongoengine.queryset import DoesNotExist

from application import app, mongo
from application.models import MachineData, User
from application.modules.validation import Validation

test_ip1 = "1.1.1.1"
test_ip2 = "2.2.2.2"
test_ip_aws = "52.52.224.126"
test_ip1_decimal = int(ipaddress.IPv4Address(test_ip1))
test_ip2_decimal = int(ipaddress.IPv4Address(test_ip2))
test_ip_aws_decimal = int(ipaddress.IPv4Address(test_ip_aws))
test_username = "test_user"
test_password = "test_password"
created_time = datetime.now()

class DBManagerTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        logging.disable(logging.CRITICAL)
        assert(app.testing)
        assert(Validation.check_internet_connection())

    @classmethod
    def tearDownClass(cls):
        pass

    def setUp(self):
        MachineData.drop_collection()
        User.drop_collection()
        self.assertTrue(len(MachineData.objects.all()) == 0)
        self.assertTrue(len(User.objects.all()) == 0)


    def tearDown(self):
        MachineData.drop_collection()
        User.drop_collection()


    def test_find(self):
        self.create_test_machine(test_ip1)
        self.create_test_machine(test_ip2)

        # without filter
        machines = mongo.find({})
        for machine in machines:
            self.assertIn(machine.ip_address, [test_ip1, test_ip2])

        # with filter
        machines = mongo.find({'hostname': "#Unknown"})
        for machine in machines:
            self.assertIn(machine.ip_address, [test_ip1, test_ip2])


    def test_find_one(self):
        self.create_test_machine(test_ip1)

        # exists
        machine = mongo.find_one({'ip_address': test_ip1})
        self.assertEqual(machine.ip_address, test_ip1)

        # does not exist
        machine = mongo.find_one({'ip_address': '8.8.8.8'})
        self.assertIsNone(machine)


    def test_remove(self):
        self.create_test_machine(test_ip1)
        self.create_test_machine(test_ip2)

        mongo.remove([test_ip1, test_ip2])
        with self.assertRaises(DoesNotExist):
            MachineData.objects.get(ip_address=test_ip1)
            MachineData.objects.get(ip_address=test_ip2)


    def test_find_user(self):
        self.create_test_user(test_username)

        # exists
        user = mongo.find_user(test_username)
        self.assertEqual(user.username, test_username)

        # does not exist
        user = mongo.find_user("INVALID_USERNAME")
        self.assertIsNone(user)


    def test_add_user(self):
        mongo.add_user(test_username, test_password)
        user = User.objects.get(username=test_username)
        self.assertEqual(user.username, test_username)


    def test_delete_user(self):
        self.create_test_user(test_username)
        mongo.delete_user(test_username)
        with self.assertRaises(DoesNotExist):
            User.objects.get(username=test_username)


    def test_write_new(self):
        mongo.write_new(test_ip1, created_time)
        machine = MachineData.objects.get(ip_address=test_ip1)
        self.assertEqual(machine.hostname, "#Unknown")
        self.assertEqual(machine.ip_address, test_ip1)
        self.assertEqual(machine.ip_address_decimal, test_ip1_decimal)
        self.assertEqual(machine.status, "Unknown (Waiting for the first SSH access)")
        self.assertEqual(machine.fail_count, 0)
        self.assertIsNone(machine.mac_address)
        self.assertIsNone(machine.os_distribution)
        self.assertIsNone(machine.release)
        self.assertIsNone(machine.uptime)
        self.assertIsNone(machine.cpu_info)
        self.assertIsNone(machine.cpu_load_avg)
        self.assertIsNone(machine.memory_usage)
        self.assertIsNone(machine.disk_usage)
        self.assertIsNotNone(machine.aws)
        self.assertIsNone(machine.ec2)
        self.assertEqual(machine.last_updated, created_time)

    def test_write_new_aws(self):
        mongo.write_new(test_ip_aws, created_time)
        machine = MachineData.objects.get(ip_address=test_ip_aws)
        self.assertEqual(machine.hostname, "#Unknown")
        self.assertEqual(machine.ip_address, test_ip_aws)
        self.assertEqual(machine.ip_address_decimal, test_ip_aws_decimal)
        self.assertEqual(machine.status, "Unknown (Waiting for the first SSH access)")
        self.assertEqual(machine.fail_count, 0)
        self.assertIsNone(machine.mac_address)
        self.assertIsNone(machine.os_distribution)
        self.assertIsNone(machine.release)
        self.assertIsNone(machine.uptime)
        self.assertIsNone(machine.cpu_info)
        self.assertIsNone(machine.cpu_load_avg)
        self.assertIsNone(machine.memory_usage)
        self.assertIsNone(machine.disk_usage)
        self.assertTrue(machine.aws)
        self.assertIsNotNone(machine.ec2['instance_id'])
        self.assertIsNone(machine.ec2['state'])
        self.assertEqual(machine.last_updated, created_time)


    def test_update_status_ok(self):
        # ipaddr, hostname, mac, os_dist, release, uptime, cpu_info, cpu_load, memory_usage, disk_usage
        machine_data1 = [
            test_ip1,
            "test_hostname1",
            "test_mac",
            "test_os_dist",
            "test_release",
            "test_uptime",
            {"test_cpu_info": "test"},
            {"test_cpu_load": "test"},
            {"test_memory_usage": "test"},
            [{"test_disk_usage": "test"}]
        ]

        machine_data2 = [
            test_ip2,
            "test_hostname2",
            "test_mac",
            "test_os_dist",
            "test_release",
            "test_uptime",
            {"test_cpu_info": "test"},
            {"test_cpu_load": "test"},
            {"test_memory_usage": "test"},
            [{"test_disk_usage": "test"}]
        ]

        self.create_test_machine(test_ip1)      # test_ip2 does not exist in database
        mongo.update_status_ok(machine_data1, created_time)
        mongo.update_status_ok(machine_data2, created_time)

        # Updated
        machine1 = MachineData.objects.get(ip_address=test_ip1)
        self.assertEqual(machine1.hostname, "test_hostname1")
        self.assertEqual(machine1.ip_address, test_ip1)
        self.assertEqual(machine1.ip_address_decimal, test_ip1_decimal)
        self.assertEqual(machine1.status, "OK")
        self.assertEqual(machine1.fail_count, 0)
        self.assertEqual(machine1.mac_address, "test_mac")
        self.assertEqual(machine1.os_distribution, "test_os_dist")
        self.assertEqual(machine1.release, "test_release")
        self.assertEqual(machine1.uptime, "test_uptime")
        self.assertEqual(machine1.cpu_info, {"test_cpu_info": "test"})
        self.assertEqual(machine1.cpu_load_avg, {"test_cpu_load": "test"},)
        self.assertEqual(machine1.memory_usage, {"test_memory_usage": "test"})
        self.assertEqual(machine1.disk_usage, [{"test_disk_usage": "test"}])
        self.assertIsNotNone(machine1.aws)
        self.assertIsNone(machine1.ec2)
        self.assertEqual(machine1.last_updated, created_time)

        # Upserted
        machine2 = MachineData.objects.get(ip_address=test_ip2)
        self.assertEqual(machine2.hostname, "test_hostname2")
        self.assertEqual(machine2.ip_address, test_ip2)
        self.assertEqual(machine2.ip_address_decimal, test_ip2_decimal)
        self.assertEqual(machine2.status, "OK")
        self.assertEqual(machine2.fail_count, 0)
        self.assertEqual(machine2.mac_address, "test_mac")
        self.assertEqual(machine2.os_distribution, "test_os_dist")
        self.assertEqual(machine2.release, "test_release")
        self.assertEqual(machine2.uptime, "test_uptime")
        self.assertEqual(machine2.cpu_info, {"test_cpu_info": "test"})
        self.assertEqual(machine2.cpu_load_avg, {"test_cpu_load": "test"},)
        self.assertEqual(machine2.memory_usage, {"test_memory_usage": "test"})
        self.assertEqual(machine2.disk_usage, [{"test_disk_usage": "test"}])
        self.assertIsNotNone(machine2.aws)
        self.assertIsNone(machine2.ec2)
        self.assertEqual(machine2.last_updated, created_time)


    def test_update_status_unreachable(self):
        self.create_test_machine(test_ip1)

        mongo.update_status_unreachable(test_ip1)
        machine = MachineData.objects.get(ip_address=test_ip1)
        self.assertEqual(machine.status, "Unreachable")
        self.assertEqual(machine.fail_count, 1)


    def test_update_ec2_state(self):
        machine_data = [
            test_ip_aws,
            "test_hostname1",
            "test_mac",
            "test_os_dist",
            "test_release",
            "test_uptime",
            {"test_cpu_info": "test"},
            {"test_cpu_load": "test"},
            {"test_memory_usage": "test"},
            [{"test_disk_usage": "test"}]
        ]
        mongo.update_status_ok(machine_data, created_time)
        machine = MachineData.objects.get(ip_address=test_ip_aws)
        self.assertEqual(machine.ec2['state'], "running")

        mongo.update_ec2_state(test_ip_aws, "stopping")
        machine = MachineData.objects.get(ip_address=test_ip_aws)
        self.assertEqual(machine.ec2['state'], "stopping")


    def test_check_mismatch(self):
        self.create_test_machine(test_ip1)
        machine = MachineData.objects.get(ip_address=test_ip1)
        self.assertIsNotNone(machine)

        mongo.check_mismatch()

        with self.assertRaises(DoesNotExist):
            MachineData.objects.get(ip_address=test_ip1)


    def create_test_machine(self, ip_address):
        MachineData(ip_address=ip_address, last_updated=created_time).save()
        
    def create_test_user(self, test_username):
        User(username=test_username, password=test_password).save()


if __name__ == '__main__':
    unittest.main()