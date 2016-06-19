import os
import pymongo
from datetime import datetime
import json
import re
import signal

DIR = os.getcwd()
FILENAME = 'login.txt'
FILEPATH = os.path.join(DIR,FILENAME)

aws_cache = []  # cache for AWS IP Address
no_aws_cache = []   # cache for non-AWS IP Address

def add_vm(db, ipaddr, username, password):
    try:
        with open(FILEPATH, 'aw') as f:
            # add to login.txt
            if password:    # for password authentication
                output = "{}{},{},{}".format("\n",ipaddr,username,password)
            else:           # for SSH-key based authentication
                output = "{}{},{}".format("\n",ipaddr,username)
            f.writelines(output)
            # add to DB
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
            doc['Disk Usage'] = "NA"
            if is_aws(ipaddr):
                doc['AWS'] = True
            else:
                doc['AWS'] = False
            doc['Last Updated'] = datetime.now()
            db.vm.update_one({'Hostname': "#Unknown", 'IP Address': ipaddr}, {'$set': doc} , upsert=True)
            return True
    except Exception as e:
        print e
        return False
        

def del_vm(db, del_list):
    # delete from DB
    for ipaddr in del_list:
        db.vm.delete_one({'IP Address': ipaddr})
    # delete from login.txt
        output = []
        with open(FILEPATH, 'r') as f:
            PATTERN = re.compile(r"^%s,"%ipaddr)
            for line in f.readlines():
                if re.match(PATTERN, line):
                    continue
                else:
                    output.append(line)
        with open(FILEPATH, 'w') as f:
            # strop newline code from the last entry before writing out
            if "\n" in output[-1]:
                output[-1] = output[-1].strip()
            f.writelines(output)

# kill existing process before opening another butterfly terminal
def kill_butterfly():
    for line in os.popen("ps -ea | grep butterfly"):
        if re.search('butterfly\.s', line):
            pid = line.split()[0]
            os.kill(int(pid), signal.SIGHUP)

# check if the IP Address is from AWS cloud
def is_aws(ipaddr):
    if ipaddr in aws_cache:
        return True
    elif ipaddr in no_aws_cache:
        return False
    else:   # if ipaddr not in chache
        for line in os.popen("nslookup %s " % ipaddr):
            if 'compute.amazonaws.com' in line:
                aws_cache.append(ipaddr)
                return True
        no_aws_cache.append(ipaddr)
        return False

# check if .pem file exists under ~/.ssh/
def search_pem():
    HOME = os.getenv("HOME")
    SSH_DIR = os.path.join(HOME, '.ssh')
    ls = os.listdir(SSH_DIR)
    for item in ls:
        PATTERN = re.compile(r".*\.pem")
        if re.search(PATTERN, item.strip()):
            pem_path = "%s/%s" % (SSH_DIR, item)
            return pem_path, SSH_DIR
    # if .pem not exists
    pem_path = None
    return pem_path, SSH_DIR

def export_json(filename, doc):
    import os
    FILENAME = filename
    JSON_DIR = DIR + "/json_files"
    FILEPATH = os.path.join(JSON_DIR,FILENAME)

    try:
        with open(FILEPATH, 'w') as f:
            doc['Last Updated'] = str(doc['Last Updated'])
            json.dump(doc, f, indent=4)
            return True, JSON_DIR
    except:
        return False, None

def getOutput(cmd, s):
    s.sendline(cmd)
    s.prompt()
    output = s.before
    return output

def getOS(output):
    if "Ubuntu" in output:
        os_dist = "Ubuntu"
    elif "CentOS" in output:
        os_dist = "CentOS"
    elif "Debian" in output:
        os_dist = "Debian"
    else:
        os_dist = "Other"

    for line in output.splitlines():
        if os_dist == "Ubuntu" or os_dist == "Debian":
            if re.search('VERSION=', line):
                PATTERN = re.compile(r"VERSION=|\"")
                release = re.sub(PATTERN, "",line)
                return os_dist, release
            else:
                continue
        elif os_dist == "CentOS":
            if re.search('CentOS release', line):
                tmp = line.split()
                release = tmp[2]
                return os_dist, release
            else:
                continue
        else:
            release = "Unknown"
            return os_dist, release

def getMAC(output, ipaddr):
    lines = output.splitlines()[1:]
    mac = ""
    for line in lines:
        PATTERN = ipaddr + '/'
        if "link/ether" in line:
            mac = line.lstrip().split(" ")[1]
        # return MAC Address only when associated with given IP address(In the case when multiple NICs exist)
        # Note: This logic doesn't work when NAT is used (eg. accessing EC2 from the internet)
        elif PATTERN in line:
            return mac

def getHostname(output):
    lines = output.splitlines()[1:]
    hostname = lines[0]
    return hostname

def getUptime(output):
    lines = output.splitlines()[1:]
    for line in lines:
        seconds = line.split(' ')[0]              
        m, s = divmod(round(float(seconds)), 60)
        h, m = divmod(m, 60)
        d, h = divmod(h, 24)
        break
    return "%dd %dh %dm %ds" % (d, h, m, s)

def getCPU(output):
    cpu_load = {}
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

def getMemory(output):
    memory_usage = {}
    lines = output.splitlines()
    for line in lines[2:]:
        line = line.split()
        if "Mem:" in line:
            memory_usage['Mem'] = {
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
            memory_usage['Swap'] = {
                "total": line[1],
                "used": line[2],
                "free": line[3] 
            }
        else:
            continue
    return memory_usage

def getDisk(output):
    disk_usage = []
    lines = output.splitlines()
    for line in lines[2:]:
        line = line.split()
        disk_usage.append(
            {
                "Filesystem": line[0],
                "Size": line[1],
                "Used": line[2],
                "Avail": line[3],
                "Use%": line[4],
                "Mounted on": line[5] 
            })
    return disk_usage

def getUsername(ipaddr):
    try:
        with open(FILEPATH, 'r') as f:
            for line in f.readlines():
                if line.split(',')[0].strip() == ipaddr:
                    return line.split(',')[1].strip()
    except:
        return False

def file_read():
    login_list = []
    with open(FILEPATH, 'r') as f:
        for line in f.readlines():
            login = []
            login = line.split(',')
            # Skip comment outed or invalid entries in login.txt
            if re.search(r"^#", login[0]) or (len(login) != 2 and len(login) != 3):
                continue
            login_list.append(login)
    if len(login_list) > 0:
        return login_list
    else:
#        raise Exception('ERROR: No entry found in login.txt')
        print 'ERROR: No entry found in login.txt'
        return False

def db_write_unreachable(db, ipaddr):
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
    if is_aws(ipaddr):
        doc['AWS'] = True
    else:
        doc['AWS'] = False
    doc['Last Updated'] = datetime.now()
    db.vm.update({'Hostname': "#Unknown", 'IP Address': ipaddr}, {'$set': doc} , upsert=True)

def db_write_ok(db, output_list):
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
    if is_aws(ipaddr):
        doc['AWS'] = True
    else:
        doc['AWS'] = False
    doc['Last Updated'] = datetime.now()
    # Unmark the old Hostname(#Unknown) entry if exists after SSH succeeds
    if db.vm.find({'Hostname': "#Unknown", 'IP Address': ipaddr}):
        db.vm.delete_one({'Hostname': "#Unknown", 'IP Address': ipaddr})
    db.vm.update({'IP Address': ipaddr}, {'$set': doc} , upsert=True) 
