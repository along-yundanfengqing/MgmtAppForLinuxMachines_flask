# -*- coding: utf-8 -*-
import thread
import threading
from datetime import datetime

# my modules
from application.modules import utilities
from application.modules.ssh_thread import SSHThread
from application import mongo


class BackgroundThreadManager(object):

    # Start the backgroud thread for SSH access and DB write/read
    @classmethod
    def start(cls):
        th = threading.Thread(target=cls.__repeat_bg_thread)
        th.daemon = True
        th.start()

    # repeat the background process
    @classmethod
    def __repeat_bg_thread(cls):
        try:
            cls.__start_ssh_threads()
            # loop the background thread for every 30 seconds
            th = threading.Timer(30, cls.__repeat_bg_thread)
            th.daemon = True
            th.start()
        except Exception as e:
            print(e)
            print("Stopping the program due to the unexpected error...")
            thread.interrupt_main()

    @classmethod
    def __start_ssh_threads(cls):
        # Check a status mismatch between login.txt/DB.
        # Delete entry in DB if the ip is not in login.txt (= Deleted manually by user)
        mongo.check_mismatch()
        # read login.txt and put credentials into a list
        login_list = utilities.get_login_list()

        if login_list:
            # Assign a thread to each entry
            print("{}: {}".format(datetime.now(), "Started collecting data via SSH"))
            threads = []
            for i in range(len(login_list)):
                ipaddr, username, password = login_list[i]
                th = SSHThread(ipaddr, username, password)
                th.daemon = True
                threads.append(th)
                th.start()

            for th in threads:
                th.join()

            print("{}: {}".format(datetime.now(), "Completed collecting data and updated the database"))
            print
        else:   # no entry found in login.txt
            pass
