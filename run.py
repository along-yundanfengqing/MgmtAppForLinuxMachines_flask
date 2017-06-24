# -*- coding: utf-8 -*-
from application import app, socketio
from application.modules.bg_thread_manager import BackgroundThreadManager

def main():
    app_host = app.config['APPLICATION_HOST']
    app_port = app.config['APPLICATION_PORT']
    try:
        BackgroundThreadManager.start()
        socketio.run(app, host=app_host, port=app_port)
    except KeyboardInterrupt:
        pass
    #app.run(host=app_host, port=app_port)


if __name__ == '__main__':
    print("Starting the program...\n")
    if app.config['TESTING']:
        app.logger.warning("TESTING = True")
    main()
