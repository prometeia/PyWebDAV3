#!/usr/bin/env python

from __future__ import absolute_import
from io import open
from promebuilder.utils import VERSIONFILE, gen_metadata, setup
import os
import pywebdav


ROOT = os.path.dirname(__file__)
CHANGES = open(os.path.join(ROOT, 'doc/Changes'), 'r', encoding='utf-8').read()
DOC = """\
WebDAV library for python3
==========================

Consists of a *server* that is ready to run
Serve and the DAV package that provides WebDAV server(!) functionality.

Currently supports

    * WebDAV level 1
    * Level 2 (LOCK, UNLOCK)
    * Experimental iterator support

It plays nice with

    * Mac OS X Finder
    * Windows Explorer
    * iCal
    * cadaver
    * Nautilus

This package does *not* provide client functionality.

Installation
============

After installation of this package you will have a new script in you
$PYTHON/bin directory called *davserver*. This serves as the main entry point
to the server.

Examples
========

Example (using pip)::

    pip install PyWebDAV3
    davserver -D /tmp -n

Example (unpacking file locally)::

    tar xvzf PyWebDAV3-$VERSION.tar.gz
    cd pywebdav
    python setup.py develop
    davserver -D /tmp -n

For more information: https://github.com/andrewleech/PyWebDAV3

Changes
=======

%s
""" % CHANGES


# Creating standard long description file
with open(os.path.join(ROOT, 'README.md'), "w", encoding='utf-8') as readme:
    readme.write(DOC)

# Creating standard version file
with open(os.path.join(ROOT, VERSIONFILE), "w", encoding='utf-8') as readme:
    readme.write(pywebdav.__version__)


METADATA = gen_metadata(
    name="pythowebdav",
    description=pywebdav.__doc__,
    email=pywebdav.__email__,
    url="https://github.com/prometeia/pythowebdav",
    keywords=['webdav', 'server', 'dav', 'standalone', 'library', 'gpl', 'http', 'rfc2518', 'rfc 2518'],
    package_data={
        'pywebdav': ['server/config.ini'],
    },
    entry_points={'console_scripts': [
        'davserver = pywebdav.server.server:run'
    ]}
)
METADATA.update(dict(
    author=pywebdav.__author__,
    maintainer="Prometeia",
    maintainer_email="pytho_support@prometeia.com",
    license=pywebdav.__license__,
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Console',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: GNU General Public License (GPL)',
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: POSIX',
        'Programming Language :: Python',
        'Topic :: Software Development :: Libraries',
        ]
))


if __name__ == '__main__':
    setup(METADATA)
