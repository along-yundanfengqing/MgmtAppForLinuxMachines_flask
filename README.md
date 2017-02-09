Management Application for Linux Machines
=========================================

## Table of Contents
1. [Introduction](#1-introduction)
2. [Supported environment](#2-supported-environment) 
3. [Install packages](#3-install-packages)
4. [Try it out](#4-try-it-out)
    - [With test infrastructure with Docker containers (Demo purpose only)](#1-with-the-test-docker-environment-demo-purpose-only)
    - [With your own infrastructure](#2-if-you-run-with-your-own-infrastructure)
5. [Documentation](#5-documentation)


<br>
## 1. Introduction
This program is a simple management application for Linux machines that automatically and periodically collects basic machine data including some performance data (CPU, Memory, Disk) via SSH, and lets administrators view them on the management portal (GUI). As it was developed with an approach of Responsive Web Design, administrators can access to the GUI from any devices such as laptops, tablets, and mobile phones.  
By using this application, administrators can manage their varied Linux machines (Ubuntu, Debian, Red Hat, CentOS etc.) on Docker containers, AWS cloud, and/or on-premise physical/virtual environment from the central management portal without manually logging in to each machine from the console.

![Program Overview](application/static/images/ProgramOverview.png)  

For more details, please see the demo documentation [here](#5-documentation).  
All features are demonstrated with screenshots in the document.

**Key Features**
- Manage Linux machines on Docker containers, AWS cloud, and/or on-premise environment
- Provide an optimal viewing and interaction experience to varied devices such as laptops, tablets, and mobile devices
- Present basic machine data on the central management portal  
   (Hostname, IP Address, MAC Address, OS/Version, uptime, CPU load, memory usage, disk usage) 
- Register/Delete machines to be managed from GUI and/or a text file 
- Track machine status and display it with icons 
- Incident alarms with icons when a reachability to machines is lost 
- Export machine data as a JSON file 
- Expose machine data via RESTful API (JSON) 
- SSH access to machines from web browsers (*Only for local machine setup)   


**Technology Stack**  
- Python programming 
- Flask web framework
- HTML/CSS + Twitter bootstrap
- MongoDB
- Docker containers (Docker Engine + Docker Compose)
- Bash shell script


## 2. Supported environment
This program supports only Python 2.x on Linux or OS X platforms.  
Python 3.x and Windows platforms are not supported.  

## 3. Install packages

Following python modules are required to run this program.
- flask
- pymongo
- pexpect
- butterfly (Optional)

To install:

```
$ sudo pip install flask pymongo pexpect butterfly
```

> [Butterfly](https://github.com/paradoxxxzero/butterfly) is an xterm compatible external terminal application that runs in your browser.  
> Current release supports the integration with butterfly only on the local machine setup environment. It does not work when you install the program on a remote server.


## 4. Try it out
This program requires any physical/virtual infrastructure with Linux machines to be managed, and a MongoDB server for storing the machine data.   
You can execute the program either by:

**1. Using test environment with docker containers**    
    This program provides test environment with docker containers for the demonstration purpose.
    A shell script provided with the program automatically deploys the following containers on your local machine:  
- MongoDB server * 1  
- Linux machines * 10 (Ubuntu * 5, CentOS * 3, Debian * 2)

**2. Using your own pysical/virtual infrastructure with Linux machines/VMs/containers**  
    You can also use your production infrastructure, but please make sure that this program is aimed for demonstrating my classwork and the use of this software is AT YOUR OWN RISK.

>Using the docker test environment will be much simple and easier.


### (1) With test infrastructure with Docker containers (Demo purpose only)
#### Step 1. Install docker on your machine 

To deploy the test environment, Docker Engine and Docker Compose are required.

**For OS X:**   
- Install Docker toolbox  
    https://www.docker.com/products/docker-toolbox  


**For Linux:**  
- Install Docker Engine  
    https://docs.docker.com/engine/installation/  

- Install Docker Compose  
    https://docs.docker.com/compose/install/

- Create a Docker group and add your user  
    https://docs.docker.com/engine/installation/linux/ubuntulinux/#create-a-docker-group

        $ sudo groupadd docker
        $ sudo usermod -aG docker USERNAME


#### Step 2. Run docker_setup.sh  
Run the shell script from the program directory.

```
$ cd ~/PATH_TO_THE_PROGRAM_DIRECTORY
$ ./docker_setup.sh
```

>(OS X only) You will be asked to enter your admin password to add the static route to the test network.


#### Step 3. Access to web server from your web browser
Access to `http://IPADDRESS:5000` from any web browser.  

>If you execute the program on your local machine, _IPADDRESS_ is localhost or 127.0.0.1

<br>
**Test containers to be deployed**  

Hostname | Container name  | IP Address  | Username | Password | OS/Version
----     | ---             | ----        | ---      | ---      | ---
 vm01    | vm01            | 172.30.0.1  | ubuntu   | ubuntu   | Ubuntu 14.04.4
 vm02    | vm02            | 172.30.0.2  | ubuntu   | ubuntu   | Ubuntu 14.04.4
 vm03    | vm03            | 172.30.0.3  | centos   | centos   | CentOS 6.7
 vm04    | vm04            | 172.30.0.4  | debian   | debian   | Debian 8
 vm05    | vm05            | 172.30.0.5  | centos   | centos   | CentOS 6.7
 vm06    | vm06            | 172.30.0.6  | ubuntu   | ubuntu   | Ubuntu 14.04.4
 vm07    | vm07            | 172.30.0.7  | debian   | debian   | Debian 8
 vm08    | vm08            | 172.30.0.8  | ubuntu   | ubuntu   | Ubuntu 14.04.4
 vm09    | vm09            | 172.30.0.9  | ubuntu   | ubuntu   | Ubuntu 14.04.4
 vm10    | vm10            | 172.30.0.10 | centos   | centos   | CentOS 6.7
 _N.A_   | mongo           | 172.30.0.99 | _N.A_    | _N.A_    | MongoDB 3.2
 \* MongoDB: port = TCP/27017, db = LinuxServer, collection = vm


#### Step 4. Destroying the demo environment
The shell script shutdowns and deletes all containers and settings on your local machine.

1. Stop the program (CTRL + C)
2. Run docker_destroy.sh from the program directory

        $ ./docker_destroy.sh



### (2) With your own infrastructure
1. Prepare a MongoDB server which can be accessed from the machine this program will be executed
2. Prepare your infrastructure with linux servers and/or virtual machines (SSH access must be permitted on each machine)   
    If you manage EC2 instances on AWS, please place .pem file under ~/.ssh/ and run below command.

        $ ssh-add ~/.ssh/KEY_PAIR_NAME.pem

3. (Optional) Add IP Address, username, password of each Linux machine in "login.txt". You can also operate this step later through GUI 
4. Start the python program (run.py)

        $ cd ~/PATH_TO_THE_PROGRAM_DIRECTORY
        $ python run.py        

> You will be asked to enter the IP addres of your MongoDB server

5. Access to `http://IPADDRESS:5000` from any web browser  

>If you execute on your local machine, _IPADDRESS_ is localhost or 127.0.0.1.  
>The program will ask you to enter the IP address of your MongoDB Server at the beginning


## 5. Documentation
See the demo documentation [here](https://1drv.ms/b/s!AkRAr6rw0sUWgShAMcE-nZJyUIz5) for more details.  
All features are demonstrated with screenshots.





