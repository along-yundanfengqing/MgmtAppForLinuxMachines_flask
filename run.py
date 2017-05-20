# -*- coding: utf-8 -*-
from application import app, socketio

def main():
    app_host = app.config['APPLICATION_HOST']
    app_port = app.config['APPLICATION_PORT']
    try:
        socketio.run(app, host=app_host, port=app_port)
    except KeyboardInterrupt:
        pass
    #app.run(host=app_host, port=app_port)


if __name__ == '__main__':
    main()
