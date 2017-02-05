# -*- coding: utf-8 -*-
import logging
from application import app

def main():
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)
    app.run(host='0.0.0.0', port=5000)

if __name__ == '__main__':
    main()
