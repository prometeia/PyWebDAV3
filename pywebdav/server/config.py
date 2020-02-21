from typing import List
import logging, getopt, sys, os
from .. import __version__, __author__, log
from ..lib.INI_Parse import Configuration


USAGE = f"""PyWebDAV server (version {__version__})
Standalone WebDAV server

Make sure to activate LOCK, UNLOCK using parameter -J if you want
to use clients like Windows Explorer or Mac OS X Finder that expect
LOCK working for write support.

Usage: ./server.py [OPTIONS]
Parameters:
    -c, --config    Specify a file where configuration is specified. In this
                    file you can specify options for a running server.
                    For an example look at the config.ini in this directory.
    -D, --directory Directory where to serve data from
                    The user that runs this server must have permissions
                    on that directory. NEVER run as root!
                    Default directory is /tmp
    -B, --baseurl   Behind a proxy pywebdav needs to generate other URIs for PROPFIND.
                    If you are experiencing problems with links or such when behind
                    a proxy then just set this to a sensible default (e.g. http://dav.domain.com).
                    Make sure that you include the protocol.
    -H, --host      Host where to listen on (default: localhost)
    -P, --port      Port to bind server to  (default: 8008)
    -u, --user      Username for authentication
    -p, --password  Password for given user
    -n, --noauth    Pass parameter if server should not ask for authentication
                    This means that every user has access
    -m, --mysql     Pass this parameter if you want MySQL based authentication.
                    If you want to use MySQL then the usage of a configuration
                    file is mandatory.
    -J, --nolock    Deactivate LOCK and UNLOCK mode (WebDAV Version 2).
    -M, --nomime    Deactivate mimetype sniffing. Sniffing is based on magic numbers
                    detection but can be slow under heavy load. If you are experiencing
                    speed problems try to use this parameter.
    -T, --noiter    Deactivate iterator. Use this if you encounter file corruption during 
                    download. Also disables chunked body response.
    -i, --icounter  If you want to run multiple instances then you have to
                    give each instance it own number so that logfiles and such
                    can be identified. Default is 0
    -d, --daemon    Make server act like a daemon. That means that it is going
                    to background mode. All messages are redirected to
                    logfiles (default: /tmp/pydav.log and /tmp/pydav.err).
                    You need to pass one of the following values to this parameter
                        start   - Start daemon
                        stop    - Stop daemon
                        restart - Restart complete server
                        status  - Returns status of server

    -v, --verbose   Be verbose.
    -l, --loglevel  Select the log level : DEBUG, INFO, WARNING, ERROR, CRITICAL
                    Default is WARNING
    -h, --help      Show this screen

Please send bug reports and feature requests to {__author__}
"""


class DummyConfig(object):
    verbose = False
    directory = '/tmp'
    port = 8008
    host = 'localhost'
    noauth = False
    user = ''
    password = ''
    daemonize = False
    daemonaction = 'start'
    counter = 0
    mysql = False
    lockemulation = True
    http_response_use_iterator = True
    http_request_use_iterator = True
    chunked_http_response = True
    configfile = ''
    mimecheck = True
    loglevel = 'warning'
    baseurl = ''
    pythoauthserver = ''

    @property
    def loglevelnum(self):
        return getattr(logging, self.loglevel.upper())

    def __init__(self, **kw):
        self.update(**kw)

    def update(self, **kw):
        for thekey, val in kw.items():
            setattr(self, thekey, val)

    def __setattr__(self, name, value):
        if not hasattr(self, name):
            raise AttributeError(f"Unknown configuration {name}")
        self.__dict__[name] = value

    def getboolean(self, name):
        return (str(getattr(self, name, 0)) in ('1', "yes", "true", "on", "True"))

    def validate(self):
        if self.pythoauthserver and (self.noauth or  self.user or  self.password or self.mysql):
            raise ValueError("'pythoauthserver' config is incompatibile with 'user', "
                             "'password', 'noauth' and 'mysql.")
        if self.mysql and not self.configfile:
            raise ValueError('You can only use MySQL with configuration file!')
        if self.daemonaction == 'status':
            log.info('Checking for state...')
        elif self.daemonaction != 'stop':
            log.info('Starting up PyWebDAV server (version %s)', __version__)
        else:
            log.info('Stopping PyWebDAV server (version %s)',__version__)
        if not self.noauth and self.daemonaction not in ['status', 'stop'] and (not self.user or not self.password):
            raise ValueError("Missing user/password")
        for logme in ('chunked_http_response', 'http_request_use_iterator', 'http_request_use_iterator'):
            value = 'ON' if self.getboolean(logme) else 'OFF'
            log.info(f"Feature {logme} {value}")

        self.directory = self.directory.strip().rstrip('/')
        if not os.path.isdir(self.directory):
            raise OSError(f"Invalid directory {self.directory}")
        if self.directory == '/':
            raise ValueError('Root directory not allowed!')

        self.host = self.host.strip()
        # basic checks against wrong hosts
        if self.host.find('/') != -1 or self.host.find(':') != -1:
            raise ValueError(f'Malformed host {self.host}')

        self.port = int(self.port)
        for fname in ('verbose', 'noauth', 'lockemulation', 'mimecheck'):
            setattr(self, fname, self.getboolean(fname))

        if self.noauth:
            log.warning('Authentication disabled!')
        if not self.lockemulation:
            log.info('Deactivated LOCK, UNLOCK (WebDAV level 2) support')
        if not self.mimecheck:
            log.info('Disabled mimetype sniffing (All files will have type application/octet-stream)')
        if self.baseurl:
            log.info('Using %s as base url for PROPFIND requests', self.baseurl)


    def update_from_file(self):
        log.info('Reading configuration from %s', self.configfile)
        dv = Configuration(self.configfile).DAV
        if dv is None:
            raise RuntimeError(f"Configuration file {self.configfile} missing, empty or invalid")
        self.update(**dv)

    def update_from_args(self, args: List[str] = None):
        if not args:
            args = sys.argv[1:]
        try:
            opts, args = getopt.getopt(
                args, 'P:D:H:d:u:p:nvhmJi:c:Ml:TB:',
                ['host=', 'port=', 'directory=', 'user=', 'password=',
                 'daemon=', 'noauth', 'help', 'verbose', 'mysql',
                 'icounter=', 'config=', 'nolock', 'nomime', 'loglevel', 'noiter',
                 'baseurl=', 'pythoauthserver='])
        except getopt.GetoptError as e:
            print(USAGE)
            print('>>>> ERROR: %s' % str(e))
            sys.exit(2)

        odict = dict(opts)
        self.configfile = odict.get('-c') or odict.get('--config') or ''
        if self.configfile:
            self.update_from_file()

        for o, a in opts:
            if o in ['-i', '--icounter']:
                self.counter = int(str(a).strip())
            elif o in ['-m', '--mysql']:
                self.mysql = True
            elif o in ['-M', '--nomime']:
                self.mimecheck = False
            elif o in ['-J', '--nolock']:
                self.lockemulation = False
            elif o in ['-T', '--noiter']:
                self.http_response_use_iterator = False
                self.chunked_http_response = False
            elif o in ['-D', '--directory']:
                self.directory = a
            elif o in ['-H', '--host']:
                self.host = a
            elif o in ['-P', '--port']:
                self.port = a
            elif o in ['-v', '--verbose']:
                self.verbose = True
            elif o in ['-l', '--loglevel']:
                self.loglevel = a.lower()
            if o in ['-h', '--help']:
                print(USAGE)
            elif o in ['-n', '--noauth']:
                self.noauth = True
            elif o in ['-u', '--user']:
                self.user = a
            elif o in ['-p', '--password']:
                self.password = a
            elif o in ['-d', '--daemon']:
                self.daemonize = True
                self.daemonaction = a
            elif o in ['-B', '--baseurl']:
                self.baseurl = a.lower()
            elif o in ['--pythoauthserver']:
                self.pythoauthserver = a


class DAVConfig(object):
    def __init__(self, ):
        self.DAV = DummyConfig()
        self.DAV.update_from_args()
