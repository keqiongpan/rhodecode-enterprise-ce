# -*- coding: utf-8 -*-

# Copyright (C) 2010-2020 RhodeCode GmbH
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License, version 3
# (only), as published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# This program is dual-licensed. If you wish to learn more about the
# RhodeCode Enterprise Edition, including its added features, Support services,
# and proprietary license terms, please see https://rhodecode.com/licenses/

"""
Test for crawling a project for memory usage
This should be runned just as regular script together
with a watch script that will show memory usage.

watch -n1 ./rhodecode/tests/mem_watch
"""


import cookielib
import urllib
import urllib2
import time
import os
import sys
from os.path import join as jn
from os.path import dirname as dn
from pyramid import compat
from sqlalchemy.util import OrderedSet

__here__ = os.path.abspath(__file__)
__root__ = dn(dn(dn(__here__)))
sys.path.append(__root__)

from rhodecode.lib import vcs
from rhodecode.lib.vcs.exceptions import RepositoryError

PASES = 3
HOST = 'http://127.0.0.1'
PORT = 5001
BASE_URI = '%s:%s/' % (HOST, PORT)

if len(sys.argv) == 2:
    BASE_URI = sys.argv[1]

if not BASE_URI.endswith('/'):
    BASE_URI += '/'

print('Crawling @ %s' % BASE_URI)
BASE_URI += '%s'
PROJECT_PATH = jn('/', 'home', 'marcink', 'repos')
PROJECTS = [
    #'linux-magx-pbranch',
    'CPython',
    'rhodecode_tip',
]


cj = cookielib.FileCookieJar('/tmp/rc_test_cookie.txt')
o = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
o.addheaders = [
    ('User-agent', 'rhodecode-crawler'),
    ('Accept-Language', 'en - us, en;q = 0.5')
]

urllib2.install_opener(o)


def _get_repo(proj):
    if isinstance(proj, compat.string_types):
        repo = vcs.get_repo(jn(PROJECT_PATH, proj))
        proj = proj
    else:
        repo = proj
        proj = repo.name

    return repo, proj


def test_changelog_walk(proj, pages=100):
    repo, proj = _get_repo(proj)

    total_time = 0
    for i in range(1, pages):

        page = '/'.join((proj, 'changelog',))

        full_uri = (BASE_URI % page) + '?' + urllib.urlencode({'page': i})
        s = time.time()
        f = o.open(full_uri)

        assert f.url == full_uri, 'URL:%s does not match %s' % (f.url, full_uri)

        size = len(f.read())
        e = time.time() - s
        total_time += e
        print('visited %s size:%s req:%s ms' % (full_uri, size, e))

    print('total_time {}'.format(total_time))
    print('average on req {}'.format(total_time / float(pages)))


def test_commit_walk(proj, limit=None):
    repo, proj = _get_repo(proj)

    print('processing', jn(PROJECT_PATH, proj))
    total_time = 0

    cnt = 0
    for i in repo:
        cnt += 1
        raw_cs = '/'.join((proj, 'changeset', i.raw_id))
        if limit and limit == cnt:
            break

        full_uri = (BASE_URI % raw_cs)
        print('%s visiting %s\%s' % (cnt, full_uri, i))
        s = time.time()
        f = o.open(full_uri)
        size = len(f.read())
        e = time.time() - s
        total_time += e
        print('%s visited %s\%s size:%s req:%s ms' % (cnt, full_uri, i, size, e))

    print('total_time {}'.format(total_time))
    print('average on req {}'.format(total_time / float(cnt)))


def test_files_walk(proj, limit=100):
    repo, proj = _get_repo(proj)

    print('processing {}'.format(jn(PROJECT_PATH, proj)))
    total_time = 0

    paths_ = OrderedSet([''])
    try:
        tip = repo.get_commit('tip')
        for topnode, dirs, files in tip.walk('/'):

            for dir in dirs:
                paths_.add(dir.path)
                for f in dir:
                    paths_.add(f.path)

            for f in files:
                paths_.add(f.path)

    except RepositoryError as e:
        pass

    cnt = 0
    for f in paths_:
        cnt += 1
        if limit and limit == cnt:
            break

        file_path = '/'.join((proj, 'files', 'tip', f))
        full_uri = (BASE_URI % file_path)
        print('%s visiting %s' % (cnt, full_uri))
        s = time.time()
        f = o.open(full_uri)
        size = len(f.read())
        e = time.time() - s
        total_time += e
        print('%s visited OK size:%s req:%s ms' % (cnt, size, e))

    print('total_time {}'.format(total_time))
    print('average on req {}'.format(total_time / float(cnt)))

if __name__ == '__main__':
    for path in PROJECTS:
        repo = vcs.get_repo(jn(PROJECT_PATH, path))
        for i in range(PASES):
            print('PASS %s/%s' % (i, PASES))
            test_changelog_walk(repo, pages=80)
            test_commit_walk(repo, limit=100)
            test_files_walk(repo, limit=100)
