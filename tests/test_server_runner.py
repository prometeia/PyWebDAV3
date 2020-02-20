from .conftest import pywebdav_server_runner

def test_run():
    for val in pywebdav_server_runner():
        print(val)
