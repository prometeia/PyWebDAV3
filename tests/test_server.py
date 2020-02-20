import requests


def test_connection(pywebdav_server):
    url, user, password = pywebdav_server
    ret = requests.get(url=url, auth=(user, password))
    assert ret.status_code // 100 == 2
