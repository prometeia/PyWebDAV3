import os
import time
import shutil
import pytest
import tempfile
import threading
from pywebdav.server.server import runserver, setupDummyConfig
from pywebdav.server.fileauth import DAVAuthHandler

USER = 'test'
PASSWORD = 'pass'
PORT = 38028
HOST = '127.0.0.1'
SERVERSCRIPT = os.path.join(os.path.dirname(__file__), '..', 'pywebdav', 'server', 'server.py')


class MyRunner(threading.Thread):

    def __init__(self, serverroot):
        super(MyRunner, self).__init__(name='pywebdav')

        _dc = {
            'verbose': True,
            'directory': serverroot,
            'port': PORT,
            'host': HOST,
            'noauth': False,
            'user': USER,
            'password': PASSWORD,
            'daemonize': False,
            'daemonaction': 'stop',
            'counter': 0,
            'lockemulation': True,
            'mimecheck': True,
            'chunked_http_response': True,
            'http_request_use_iterator': True,
            'http_response_use_iterator': True,
            'baseurl': ''
        }
        handler = DAVAuthHandler
        handler._config = setupDummyConfig(**_dc)
        self.runner = runserver(PORT, HOST, serverroot, doserve=False, handler=handler)

    def run(self):
        self.runner.serve_forever()

    def stop(self):
        self.runner.shutdown()


def pywebdav_server_runner():
    root = tempfile.mkdtemp()
    print('Created temporary root folder {}'.format(root))

    print('Starting webdav server')
    sthread = MyRunner(root)
    sthread.start()
    # Ensure davserver has time to startup
    time.sleep(1)

    yield "http://{}:{}".format(HOST, PORT), USER, PASSWORD

    print('Stopping davserver')
    sthread.stop()
    sthread.join(timeout=1)

    print('Removing temporary folder {}'.format(root))
    shutil.rmtree(root, True)


@pytest.fixture(scope="module")
def pywebdav_server():
    for x in pywebdav_server_runner():
        yield x
