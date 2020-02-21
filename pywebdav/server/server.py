#!/usr/bin/env python

"""
Python WebDAV Server.

This is an example implementation of a DAVserver using the DAV package.

"""

import os
import logging
from http.server import ThreadingHTTPServer
from pywebdav import log
from pywebdav.server.config import DAVConfig
from pywebdav.server.fileauth import DAVAuthHandler
from pywebdav.server.mysqlauth import MySQLAuthHandler
from pywebdav.server.pythoauth import PythoAuthHandler
from pywebdav.server.fshandler import FilesystemHandler
from pywebdav.server.daemonize import startstop


def runserver(conf, doserve=True):
    conf.DAV.validate()
    dv = conf.DAV
    if dv.pythoauthserver:
        handler = PythoAuthHandler
    elif dv.mysql:
        handler = MySQLAuthHandler
    else:
        handler = DAVAuthHandler
    handler.inject_config(conf)

    # dispatch directory and host to the filesystem handler
    # This handler is responsible from where to take the data
    handler.IFACE_CLASS = FilesystemHandler(dv.directory, f'http://{dv.host}:{dv.port}/', dv.verbose)
    handler.IFACE_CLASS.mimecheck = dv.mimecheck
    handler.IFACE_CLASS.baseurl = dv.baseurl

    log.info(f'Serving data from {dv.directory}')

    runner = ThreadingHTTPServer((dv.host, dv.port), handler)
    if doserve:
        # initialize server on specified port
        print(f'Listening on {dv.host}:{dv.port}')
        try:
            runner.serve_forever()
        except KeyboardInterrupt:
            log.info('Killed by user')
    else:
        return runner



def run():
    conf = DAVConfig()
    dv = conf.DAV
    if dv.verbose and dv.loglevelnum > logging.INFO:
        dv.loglevel = 'info'
    logging.getLogger().setLevel(dv.loglevelnum)
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
    for handler in logging.getLogger().handlers:
        handler.setFormatter(formatter)

    if dv.daemonize:
        # check if pid file exists
        if os.path.exists('/tmp/pydav%s.pid' % dv.counter) and dv.daemonaction not in ['status', 'stop']:
            raise RuntimeError(f'Found another instance! Either use -i to specifiy another instance'
                               f'number or remove /tmp/pydav{dv.counter}.pid!')
        startstop(
            stdout=f'/tmp/pydav{dv.counter}.log',
            stderr=f'/tmp/pydav{dv.counter}.err',
            pidfile=f'/tmp/pydav{dv.counter}.pid',
            startmsg='>> Started PyWebDAV (PID: %s)',
            action=dv.daemonaction)

    runserver(conf)

if __name__ == '__main__':
    run()
