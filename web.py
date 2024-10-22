from gevent import monkey ; monkey.patch_all()
import os
import sys

from gevent.pool import Pool
from gevent.pywsgi import WSGIServer

# Put sqlite_web on our python-path.
cur_dir = os.path.dirname(__file__)
sys.path.insert(0, os.path.realpath(os.path.join(cur_dir, '../sqlite_web')))

from sqlite_web import sqlite_web

port = os.getenv("PORT", "8080")
password = os.getenv("SQLITE_WEB_UI_PASSWORD")

def main(db_file):
    sqlite_web.initialize_app(db_file, password=password)

    pool = Pool(50)
    server = WSGIServer(('0.0.0.0', int(port)), sqlite_web.app, log=None, spawn=pool)
    server.serve_forever()


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print('missing required database file.')
        sys.exit(1)

    main(sys.argv[1])