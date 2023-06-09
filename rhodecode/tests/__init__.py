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

import os
import time
import logging
import datetime
import hashlib
import tempfile
from os.path import join as jn

from tempfile import _RandomNameSequence

import pytest

from rhodecode.model.db import User
from rhodecode.lib import auth
from rhodecode.lib import helpers as h
from rhodecode.lib.helpers import flash
from rhodecode.lib.utils2 import safe_str


log = logging.getLogger(__name__)

__all__ = [
    'get_new_dir', 'TestController', 'route_path_generator',
    'clear_cache_regions',
    'assert_session_flash', 'login_user', 'no_newline_id_generator',
    'TESTS_TMP_PATH', 'HG_REPO', 'GIT_REPO', 'SVN_REPO',
    'NEW_HG_REPO', 'NEW_GIT_REPO',
    'HG_FORK', 'GIT_FORK', 'TEST_USER_ADMIN_LOGIN', 'TEST_USER_ADMIN_PASS',
    'TEST_USER_REGULAR_LOGIN', 'TEST_USER_REGULAR_PASS',
    'TEST_USER_REGULAR_EMAIL', 'TEST_USER_REGULAR2_LOGIN',
    'TEST_USER_REGULAR2_PASS', 'TEST_USER_REGULAR2_EMAIL', 'TEST_HG_REPO',
    'TEST_HG_REPO_CLONE', 'TEST_HG_REPO_PULL', 'TEST_GIT_REPO',
    'TEST_GIT_REPO_CLONE', 'TEST_GIT_REPO_PULL', 'SCM_TESTS',
]


# SOME GLOBALS FOR TESTS
TEST_DIR = tempfile.gettempdir()

TESTS_TMP_PATH = jn(TEST_DIR, 'rc_test_%s' % _RandomNameSequence().next())
TEST_USER_ADMIN_LOGIN = 'test_admin'
TEST_USER_ADMIN_PASS = 'test12'
TEST_USER_ADMIN_EMAIL = 'test_admin@mail.com'

TEST_USER_REGULAR_LOGIN = 'test_regular'
TEST_USER_REGULAR_PASS = 'test12'
TEST_USER_REGULAR_EMAIL = 'test_regular@mail.com'

TEST_USER_REGULAR2_LOGIN = 'test_regular2'
TEST_USER_REGULAR2_PASS = 'test12'
TEST_USER_REGULAR2_EMAIL = 'test_regular2@mail.com'

HG_REPO = 'vcs_test_hg'
GIT_REPO = 'vcs_test_git'
SVN_REPO = 'vcs_test_svn'

NEW_HG_REPO = 'vcs_test_hg_new'
NEW_GIT_REPO = 'vcs_test_git_new'

HG_FORK = 'vcs_test_hg_fork'
GIT_FORK = 'vcs_test_git_fork'

## VCS
SCM_TESTS = ['hg', 'git']
uniq_suffix = str(int(time.mktime(datetime.datetime.now().timetuple())))

TEST_GIT_REPO = jn(TESTS_TMP_PATH, GIT_REPO)
TEST_GIT_REPO_CLONE = jn(TESTS_TMP_PATH, 'vcsgitclone%s' % uniq_suffix)
TEST_GIT_REPO_PULL = jn(TESTS_TMP_PATH, 'vcsgitpull%s' % uniq_suffix)

TEST_HG_REPO = jn(TESTS_TMP_PATH, HG_REPO)
TEST_HG_REPO_CLONE = jn(TESTS_TMP_PATH, 'vcshgclone%s' % uniq_suffix)
TEST_HG_REPO_PULL = jn(TESTS_TMP_PATH, 'vcshgpull%s' % uniq_suffix)

TEST_REPO_PREFIX = 'vcs-test'


def clear_cache_regions(regions=None):
    # dogpile
    from rhodecode.lib.rc_cache import region_meta
    for region_name, region in region_meta.dogpile_cache_regions.items():
        if not regions or region_name in regions:
            region.invalidate()


def get_new_dir(title):
    """
    Returns always new directory path.
    """
    from rhodecode.tests.vcs.utils import get_normalized_path
    name_parts = [TEST_REPO_PREFIX]
    if title:
        name_parts.append(title)
    hex_str = hashlib.sha1('%s %s' % (os.getpid(), time.time())).hexdigest()
    name_parts.append(hex_str)
    name = '-'.join(name_parts)
    path = os.path.join(TEST_DIR, name)
    return get_normalized_path(path)


def repo_id_generator(name):
    numeric_hash = 0
    for char in name:
        numeric_hash += (ord(char))
    return numeric_hash


@pytest.mark.usefixtures('app', 'index_location')
class TestController(object):

    maxDiff = None

    def log_user(self, username=TEST_USER_ADMIN_LOGIN,
                 password=TEST_USER_ADMIN_PASS):
        self._logged_username = username
        self._session = login_user_session(self.app, username, password)
        self.csrf_token = auth.get_csrf_token(self._session)

        return self._session['rhodecode_user']

    def logout_user(self):
        logout_user_session(self.app, auth.get_csrf_token(self._session))
        self.csrf_token = None
        self._logged_username = None
        self._session = None

    def _get_logged_user(self):
        return User.get_by_username(self._logged_username)


def login_user_session(
        app, username=TEST_USER_ADMIN_LOGIN, password=TEST_USER_ADMIN_PASS):

    response = app.post(
        h.route_path('login'),
        {'username': username, 'password': password})
    if 'invalid user name' in response.body:
        pytest.fail('could not login using %s %s' % (username, password))

    assert response.status == '302 Found'
    response = response.follow()
    assert response.status == '200 OK'

    session = response.get_session_from_response()
    assert 'rhodecode_user' in session
    rc_user = session['rhodecode_user']
    assert rc_user.get('username') == username
    assert rc_user.get('is_authenticated')

    return session


def logout_user_session(app, csrf_token):
    app.post(h.route_path('logout'), {'csrf_token': csrf_token}, status=302)


def login_user(app, username=TEST_USER_ADMIN_LOGIN,
               password=TEST_USER_ADMIN_PASS):
    return login_user_session(app, username, password)['rhodecode_user']


def assert_session_flash(response, msg=None, category=None, no_=None):
    """
    Assert on a flash message in the current session.

    :param response: Response from give calll, it will contain flash
        messages or bound session with them.
    :param msg: The expected message. Will be evaluated if a
        :class:`LazyString` is passed in.
    :param category: Optional. If passed, the message category will be
        checked as well.
    :param no_: Optional. If passed, the message will be checked to NOT
        be in the flash session
    """
    if msg is None and no_ is None:
        raise ValueError("Parameter msg or no_ is required.")

    if msg and no_:
        raise ValueError("Please specify either msg or no_, but not both")

    session = response.get_session_from_response()
    messages = flash.pop_messages(session=session)
    msg = _eval_if_lazy(msg)

    if no_:
        error_msg = 'unable to detect no_ message `%s` in empty flash list' % no_
    else:
        error_msg = 'unable to find message `%s` in empty flash list' % msg
    assert messages, error_msg
    message = messages[0]

    message_text = _eval_if_lazy(message.message) or ''

    if no_:
        if no_ in message_text:
            msg = u'msg `%s` found in session flash.' % (no_,)
            pytest.fail(safe_str(msg))
    else:
        if msg not in message_text:
            fail_msg = u'msg `%s` not found in session ' \
                       u'flash: got `%s` (type:%s) instead' % (
                msg, message_text, type(message_text))

            pytest.fail(safe_str(fail_msg))
        if category:
            assert category == message.category


def _eval_if_lazy(value):
    return value.eval() if hasattr(value, 'eval') else value


def no_newline_id_generator(test_name):
    """
    Generates a test name without spaces or newlines characters. Used for
    nicer output of progress of test
    """
    org_name = test_name
    test_name = safe_str(test_name)\
        .replace('\n', '_N') \
        .replace('\r', '_N') \
        .replace('\t', '_T') \
        .replace(' ', '_S')

    return test_name or 'test-with-empty-name'


def route_path_generator(url_defs, name, params=None, **kwargs):
    import urllib

    base_url = url_defs[name].format(**kwargs)

    if params:
        base_url = '{}?{}'.format(base_url, urllib.urlencode(params))
    return base_url
