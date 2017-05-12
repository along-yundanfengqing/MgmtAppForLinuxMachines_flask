# -*- coding: utf-8 -*-
try:
    import _thread as thread    #for python 3.x
except ImportError:
    import thread   # for python 2.x
import threading

# my modules
from application import app, socketio
from application.modules.file_io import FileIO
from application.modules.ssh_thread import SSHThread
from application.modules.db_manager import DBManager

mongo = DBManager.get_current_instance()


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
            # loop the background thread (default = every 30 seconds)
            timer = app.config['BG_THREAD_TIMER']
            th = threading.Timer(timer, cls.__repeat_bg_thread)
            th.daemon = True
            th.start()
        except Exception as e:
            app.logger.critical("Stopping the program due to the unexpected error...")
            app.logger.critical(e)
            thread.interrupt_main()


    @classmethod
    def __start_ssh_threads(cls):
        socketio.emit('message', {'data': 'started'})
        app.logger.debug("Sent SocketIO message: started")
        app.logger.info("Started collecting data via SSH")
        # Check status mismatches between login.txt and DB.
        # Delete entry in DB if the ip is not in login.txt (= Deleted manually by user)
        mongo.check_mismatch()
        login_list = FileIO.get_login_list()

        if login_list:
            # Assign a thread to each entry
            threads = []
            for i in range(len(login_list)):
                ipaddr, username, password = login_list[i]
                th = SSHThread(ipaddr, username, password)
                th.daemon = True
                threads.append(th)
                th.start()

            for th in threads:
                th.join()

            socketio.emit('message', {'data': 'completed'})
            app.logger.debug("Sent SocketIO message: completed")
            app.logger.info("Completed collecting data and updated the database")

        else:   # no entry found in login.txt
            return
