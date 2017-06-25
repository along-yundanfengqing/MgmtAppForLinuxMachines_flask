# -*- coding: utf-8 -*-
import pexpect
import re
import subprocess
import threading
from pexpect import pxssh

# my modules
from application import app, mongo
from application.modules.app_manager import AppManager
from application.modules.file_io import FileIO
from application.modules.validation import Validation


class SSHThread(threading.Thread):
    __CMD_HOSTNAME = "echo $HOSTNAME"
    __CMD_DISTRIBUTION = "cat /etc/*-release"
    __CMD_MAC = "ip addr"
    __CMD_UPTIME = "cat /proc/uptime"
    __CMD_CPU_INFO = "cat /proc/cpuinfo"
    __CMD_CPU_LOAD = "uptime"
    __CMD_MEMORY = "free -h"
    __CMD_DISK = "df -Ph"


    def __init__(self, ipaddr, username, password):
        threading.Thread.__init__(self, name="SSH_" + ipaddr)
        self.__ipaddr = ipaddr
        self.__username = username
        self.__password = password


    def run(self):
        # Check IP reachability before attempting SSH
        if self.__check_ip_reachability() != 0:
            app.logger.warning("IP Address %s is not reachable" % self.__ipaddr)
            self.__update_cache_and_db()
            return

        else:
            s = pxssh.pxssh(timeout=10)

            # Attempt SSH access
            try:
                if self.__password:    # for password authentication
                    s.login(self.__ipaddr, self.__username, self.__password, login_timeout=10)
                else:           # for SSH-key based authentication
                    s.login(self.__ipaddr, self.__username, login_timeout=10)

            # SSH login failure
            except KeyboardInterrupt:
                return
            except OSError as e:
                print(type(e))
                return
            except (pexpect.exceptions.EOF, pxssh.ExceptionPxssh) as e:
                if e.args[0] == 'password refused':
                    app.logger.warning("SSH access to %s failed. Please check username or password for login" % self.__ipaddr)

                else:
                    app.logger.warning("SSH access to %s failed. Please check network connectivity, or check if ssh service is started on the machine" % self.__ipaddr)

                self.__update_cache_and_db()
                return
            except Exception as e:
                print(type(e))
                return

            # After SSH login succeeds: Collect data, parse, and store to DB
            try:
                # get OS type and Release
                output = self.__get_output(SSHThread.__CMD_DISTRIBUTION, s)
                os_dist, release = self.__get_os(output)

                # get hostname
                output = self.__get_output(SSHThread.__CMD_HOSTNAME, s)
                hostname = self.__get_hostname(output)

                # get MAC Addresss
                output = self.__get_output(SSHThread.__CMD_MAC, s)
                mac = self.__get_mac(output, self.__ipaddr)

                # get uptime
                output = self.__get_output(SSHThread.__CMD_UPTIME, s)
                uptime = self.__get_uptime(output)

                # get CPU info (CPU model, CPU Mhz, CPU cores, )
                output = self.__get_output(SSHThread.__CMD_CPU_INFO, s)
                cpu_info = self.__get_cpu_info(output)

                # get CPU load average
                output = self.__get_output(SSHThread.__CMD_CPU_LOAD, s)
                cpu_load = self.__get_cpu(output)

                # get Memory Usage
                output = self.__get_output(SSHThread.__CMD_MEMORY, s)
                memory_usage = self.__get_memory(output)

                # get Disk Usage
                output = self.__get_output(SSHThread.__CMD_DISK, s)
                disk_usage = self.__get_disk(output)

                # Write to DB
                output_list = [
                    self.__ipaddr, hostname, mac, os_dist, release, uptime, cpu_info, cpu_load,
                    memory_usage, disk_usage
                    ]
                AppManager.update_machine_obj_and_update_db_ok(output_list)

            except KeyboardInterrupt:
                pass
            except OSError as e:
                app.logger.error(type(e))
                return
            except Exception as e:
                app.logger.critical("UNKNOWN ERROR OCCURRED DURING THE SSH SESSION")
                app.logger.critical(type(e))
                app.logger.critical(e)
            finally:
                s.logout()


    def get_ip_address(self):
        return self.__ipaddr


    def __check_ip_reachability(self):
        if not Validation.is_aws(self.__ipaddr):
            return subprocess.Popen(['ping', '-c', '1', '-W', '1', self.__ipaddr], stdout=subprocess.PIPE).wait()

        else:   # Skip checking for AWS instances as it depends on the security-group
            return 0


    def __update_cache_and_db(self):
        # Check if the IP Address still exists in login.txt and DB when ssh access failed.
        exists_in_file = FileIO.exists_in_file(self.__ipaddr)
        exists_in_db = mongo.find_one({"ip_address": self.__ipaddr})

        # If SSH access failed when the VM exists in both login.txt and DB,
        # mark the status as "Unreachable" and increment the failure count by 1
        if exists_in_file and exists_in_db:
            AppManager.update_machine_obj_and_update_db_unreachable(self.__ipaddr)

        # If the VM is in login.txt but not registered in DB, mark it as Unknown with N.A parameters
        # and register it in DB = In case users manually add to login.txt but SSH login to the VM fails
        elif exists_in_file and not exists_in_db:
            AppManager.create_machine_obj_and_write_db_new(self.__ipaddr)


    def __get_output(self, cmd, s):
        s.sendline(cmd)
        s.prompt()
        output = s.before.decode('ascii')
        return output


    def __get_os(self, output):
        if "Ubuntu" in output:
            os_dist = "Ubuntu"
        elif "CentOS" in output:
            os_dist = "CentOS"
        elif "Debian" in output:
            os_dist = "Debian"
        elif "Red Hat" in output:
            os_dist = "Redhat"
        else:
            os_dist = "Other(Not supported)"
        for line in output.splitlines():
            if os_dist == "Ubuntu" or os_dist == "Debian" or os_dist == "Redhat":
                if re.search('VERSION=', line):
                    PATTERN = re.compile(r"VERSION=|\"")
                    release = re.sub(PATTERN, "", line)
                    return os_dist, release

            elif os_dist == "CentOS":
                if re.search('CentOS release', line):
                    tmp = line.split()
                    release = tmp[2]
                    return os_dist, release

            else:
                release = "Unknown"
                return os_dist, release


    def __get_mac(self, output, ipaddr):
        lines = output.splitlines()[1:]
        mac = ""
        for line in lines:
            #PATTERN = ipaddr + '/'
            if "link/ether" in line:
                mac = line.lstrip().split(" ")[1]
                return mac


    def __get_hostname(self, output):
        lines = output.splitlines()[1:]
        hostname = lines[0]
        return hostname


    def __get_uptime(self, output):
        lines = output.splitlines()[1:]
        for line in lines:
            seconds = line.split(' ')[0]
            m, s = divmod(round(float(seconds)), 60)
            h, m = divmod(m, 60)
            d, h = divmod(h, 24)
            break

        return "%dd %dh %dm %ds" % (d, h, m, s)


    def __get_cpu_info(self, output):
        cpu_info = {}
        for line in output.splitlines():
            try:
                key, value = line.split(":")[0].rstrip(), line.split(":")[1].lstrip()
                if key == "model name":
                    cpu_info['model_name'] = value
                if key == "cpu MHz":
                    cpu_info['cpu_mhz'] = value
                if key == "cpu cores":
                    cpu_info['cpu_cores'] = value
            except IndexError:
                continue

        return cpu_info


    def __get_cpu(self, output):
        cpu_load = {}
        cpu_1, cpu_2, cpu_3 = "", "", ""
        for line in output.splitlines()[1:]:
            PATTERN = re.compile(r".+load average: ")
            if re.search(PATTERN, line):
                line = re.sub(PATTERN, "", line)
                cpu_1 = line.split(',')[0].strip()
                cpu_2 = line.split(',')[1].strip()
                cpu_3 = line.split(',')[2].strip()
                break

        cpu_load['1min'] = cpu_1
        cpu_load['5min'] = cpu_2
        cpu_load['15min'] = cpu_3

        return cpu_load


    def __get_memory(self, output):
        memory_usage = {}
        lines = output.splitlines()

        if lines[1].split()[4].strip() == "buffers":
            for line in lines[2:]:
                line = line.split()
                if "Mem:" in line:
                    memory_usage['mem'] = {
                        "total": line[1],
                        "used": line[2],
                        "free": line[3],
                        "shared": line[4],
                        "buffers": line[5],
                        "cached": line[6]
                    }
                elif "buffers/cache:" in line:
                    memory_usage['buffers/cache'] = {
                        "used": line[2],
                        "free": line[3]
                    }
                elif "Swap:" in line:
                    memory_usage['swap'] = {
                        "total": line[1],
                        "used": line[2],
                        "free": line[3]
                    }

        elif lines[1].split()[4].strip() == "buff/cache":
            for line in lines[2:]:
                line = line.split()
                if "Mem:" in line:
                    memory_usage['mem'] = {
                        "total": line[1],
                        "used": line[2],
                        "free": line[3],
                        "shared": line[4],
                        "buff/cache": line[5],
                        "available": line[6]
                    }
                elif "Swap:" in line:
                    memory_usage['swap'] = {
                        "total": line[1],
                        "used": line[2],
                        "free": line[3]
                    }

        return memory_usage


    def __get_disk(self, output):
        disk_usage = []
        lines = output.splitlines()
        for line in lines[2:]:
            line = line.split()
            disk_usage.append(
                {
                    "filesystem": line[0],
                    "size": line[1],
                    "used": line[2],
                    "avail": line[3],
                    "use%": line[4],
                    "mounted_on": line[5]
                })

        return disk_usage
