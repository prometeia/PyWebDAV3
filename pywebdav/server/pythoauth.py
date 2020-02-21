import requests
import time
from .fileauth import DAVAuthHandler
from functools import lru_cache
from .. import log

TTL_HASH_PARAM = 'ttl_hash'
TTL_HASH_SECS = 30


def get_ttl_hash(seconds=TTL_HASH_SECS):
    """Return the same value withing `seconds` time period"""
    return int(time.time()) // seconds


class PythoAuthHandler(DAVAuthHandler):
    timeout = 3000

    @lru_cache()
    def _pytho_req(self, method, resource, **args):
        if TTL_HASH_PARAM in args:
            del args[TTL_HASH_PARAM]
        url = self._config.DAV.pythoauthserver + '/api/v0/' + resource
        args = dict(args)
        args.setdefault('timeout', self.timeout)
        try:
            ret = requests.request(method=method, url=url, **args)
        except (requests.ConnectionError, requests.exceptions.ReadTimeout):
            log.exception("Failed pytho request %s %s", method, resource)
            return
        if ret.status_code // 100 not in [2, 4] or not ret.text.strip():
            log.error("Failed auth with request %s %s cause unexpected response, code %s body %s".format(
                method, url, ret.status_code, ret.text.strip()))
            return
        if not ret.status_code // 100 == 2:
            log.info("Failed auth against %s %s with status code %s", method, url, ret.status_code)
            return
        return ret.text.strip()

    def _pytho_ticket(self, username, password):
        return self._pytho_req('POST', 'auth', auth=(username, password), ttl_hash=get_ttl_hash())

    def get_userinfo(self, user, pw, command):
        """ authenticate user """
        self._log(f"{command} from {user}")
        res_useraname = self._pytho_req('GET', 'auth', auth=(user, pw), ttl_hash=get_ttl_hash())
        if user and res_useraname and user == res_useraname:
            self._log(f'Successfully authenticated user {user} for {command}')
            return 1
        self._log(f'Authentication failed for user {user}')
        return

