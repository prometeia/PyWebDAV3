import requests
import os


def test_connection(pywebdav_server):
    url, user, password, root = pywebdav_server
    assert root
    ret = requests.get(url=url, auth=(user, password))
    assert ret.status_code // 100 == 2


def test_get(pywebdav_server):
    url, user, password, root = pywebdav_server
    fname = 'testfile.txt'
    testdata = "TEST BODY " * 100
    with open(os.path.join(root, fname), 'w') as tgfile:
        tgfile.write(testdata)
    ret = requests.get(url=f'{url}/{fname}', auth=(user, password))
    assert ret.status_code // 100 == 2
    assert ret.text == testdata


def test_big_download(pywebdav_server):
    url, user, password, root = pywebdav_server
    fname = 'bigtestfile.txt'
    testdata = "BIG TEST BODY X\n" * 2**12
    fullname = os.path.join(root, fname)
    with open(fullname, 'w') as tgfile:
        for _ in range(10):
            tgfile.write(testdata)
    thesize = os.stat(fullname).st_size
    print(f'{fullname} weights {thesize / 2**20}MB')
    ret = requests.get(url=f'{url}/{fname}', auth=(user, password))
    assert ret.status_code // 100 == 2
    fullsize = 0
    assert thesize == fullsize
