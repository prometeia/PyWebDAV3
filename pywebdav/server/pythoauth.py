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


class FailedPythoAuth(Exception):
    pass


class PythoAuthHandler(DAVAuthHandler):
    timeout = 3000

    @lru_cache()
    def _pytho_req(self, method, resource, **args):
        if TTL_HASH_PARAM in args:
            del args[TTL_HASH_PARAM]
        url = self._config.DAV.pythoauthserver + '/api/v0/' + resource
        args = dict(args)
        args.setdefault('timeout', self.timeout)
        self._log(f"Pytho request {method} {resource}")
        try:
            ret = requests.request(method=method, url=url, **args)
        except (requests.ConnectionError, requests.exceptions.ReadTimeout):
            log.exception("PythoAuth connection error")
            raise FailedPythoAuth(f"Failed PythoAuth connection {method} {resource}")
        if ret.status_code // 100 not in [2, 4] or not ret.text.strip():
            raise FailedPythoAuth(f"Failed PythoAuth with request {method} {resource} cause "
                                  f"unexpected response, code {ret.status_code} body {ret.text.strip()}")
        if not ret.status_code // 100 == 2:
            log.warning("Unauthorized request %s %s with status code %s", method, url, ret.status_code)
            return
        return ret.text.strip()

    def _pytho_ticket(self, username, password):
        return self._pytho_req('POST', 'auth', auth=(username, password), ttl_hash=get_ttl_hash())

    def is_user_authorized(self, user, path, command):
        # TODO: check command and path against API user details
        if not user or not path:
            return False
        return path.split('/')[:3] == ['', user, 'media']

    def get_userinfo(self, user, pw, command):
        """ authenticate user """
        self._log(f"{command} from {user}")
        if not user or not pw:
            self._log(f'Invalid Authentication parameters')
            return
        try:
            res_useraname = self._pytho_req('GET', 'auth', auth=(user, pw), ttl_hash=get_ttl_hash())
        except FailedPythoAuth as fe:
            log.error(fe)
            res_useraname = None
        if not res_useraname or res_useraname != user:
            self._log(f'Authentication failed for user {user}')
            return
        self._log(f'Successfully authenticated user {user} for {command}')
        if not self.is_user_authorized(user, self.path, command):
            self._log(f'User {user} not authorized for {command} on {self.path}')
            return
        self._log(f'Succesfully authorized {user} for {command} on {self.path}')
        return 1

