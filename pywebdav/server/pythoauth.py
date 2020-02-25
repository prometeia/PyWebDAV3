import requests
import time
from urllib.parse import unquote, urlsplit
from functools import lru_cache
from .. import log
from .fileauth import DAVAuthHandler

TTL_HASH_PARAM = 'ttl_hash'
TTL_HASH_SECS = 30
PYTHO_REQ_TIMEOUT = 30


def get_ttl_hash(seconds=TTL_HASH_SECS):
    """Return the same value withing <seconds> time period"""
    return int(time.time()) // seconds


@lru_cache()
def _pytho_rest_req(method, url, ttl_hash, retjson=False, ticket=None, **args):
    assert ttl_hash
    log.debug(f"Pytho request {method} {url}")
    args = dict(args)
    args.setdefault('timeout', PYTHO_REQ_TIMEOUT)
    if ticket:
        args.setdefault('headers', {'doob-tkt': ticket})
    try:
        ret = requests.request(method=method, url=url, **args)
    except (requests.ConnectionError, requests.exceptions.ReadTimeout):
        log.exception("PythoAuth connection error")
        raise FailedPythoAuth(f"Failed PythoAuth connection {method}")
    if ret.status_code // 100 not in [2, 4] or not ret.text.strip():
        raise FailedPythoAuth(f"Failed PythoAuth with request {method} {url} cause "
                              f"unexpected response, code {ret.status_code} body {ret.text.strip()}")
    if not ret.status_code // 100 == 2:
        log.warning("Unauthorized request %s %s with status code %s", method, url, ret.status_code)
        return
    if retjson:
        return ret.json()
    return ret.text.strip()


class FailedPythoAuth(Exception):
    pass


class PythoAuthHandler(DAVAuthHandler):
    timeout = 3000

    def _pytho_api_uri(self, resource='auth'):
        return self._config.DAV.pythoauthserver + '/api/v0/' + resource

    def _pytho_auth_check(self, username, password):
        tkt = _pytho_rest_req('POST', self._pytho_api_uri('auth'), get_ttl_hash(),
                              auth=(username, password))
        if not tkt:
            return
        assert isinstance(tkt, str)
        userobj = _pytho_rest_req('GET', self._pytho_api_uri(f'users/{username}'),
                                  get_ttl_hash(), retjson=True, ticket=tkt)
        return userobj

    def _pytho_ticket_gen(self, username, password):
        url = self._config.DAV.pythoauthserver + '/api/v0/auth'
        return self._pytho_req('POST', url, get_ttl_hash(), auth=(username, password))

    def is_user_authorized(self, userobj: dict, path, command):
        # TODO: check command and path against API user details
        if not userobj or not isinstance(userobj, dict) or not userobj.get('user_dir'):
            return False
        isadmin = userobj['is_superuser']

        def is_my_area(tgpath):
            if not tgpath:
                return False
            tgpp = tgpath.rstrip('/').split('/')
            target = self.IFACE_CLASS.basepath.split('/') + userobj['user_dir'].rstrip('/').split('/')
            return tgpp[:len(target)] == target \
                   or isadmin and len(tgpp) == len(target) and tgpp[-1] == target[-1]

        if command in ('MKCOL'):
            return False
        if command in ('MOVE', 'COPY'):
            # Checking destination
            dest_uri = urlsplit(unquote(self.headers.get('Destination') or '')).path
            return is_my_area(dest_uri)
        return is_my_area(path)

    def get_userinfo(self, user, pw, command):
        """ authenticate user """
        self._log(f"{command} from {user}")
        if not user or not pw:
            self._log(f'Invalid Authentication parameters')
            return
        try:
            userobj = self._pytho_auth_check(user, pw)
        except FailedPythoAuth as fe:
            log.error(fe)
            userobj = None
        if not userobj or userobj.get('username') != user:
            self._log(f'Authentication failed for user {user}')
            return 401
        self._log(f'Successfully authenticated user {user} for {command}')
        if not self.is_user_authorized(userobj, self.path, command):
            self._log(f'User {user} not authorized for {command} on {self.path}')
            return 403
        self._log(f'Succesfully authorized {user} for {command} on {self.path}')
        return True
