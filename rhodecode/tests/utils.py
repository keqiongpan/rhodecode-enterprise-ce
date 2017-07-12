# -*- coding: utf-8 -*-

# Copyright (C) 2010-2017 RhodeCode GmbH
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

import threading
import time
import logging
import os.path
import subprocess32
import tempfile
import urllib2
from lxml.html import fromstring, tostring
from lxml.cssselect import CSSSelector
from urlparse import urlparse, parse_qsl
from urllib import unquote_plus
import webob

from webtest.app import TestResponse, TestApp, string_types
from webtest.compat import print_stderr

import pytest
import rc_testdata

from rhodecode.model.db import User, Repository
from rhodecode.model.meta import Session
from rhodecode.model.scm import ScmModel
from rhodecode.lib.vcs.backends.svn.repository import SubversionRepository
from rhodecode.lib.vcs.backends.base import EmptyCommit


log = logging.getLogger(__name__)


class CustomTestResponse(TestResponse):
    def _save_output(self, out):
        f = tempfile.NamedTemporaryFile(
            delete=False, prefix='rc-test-', suffix='.html')
        f.write(out)
        return f.name

    def mustcontain(self, *strings, **kw):
        """
        Assert that the response contains all of the strings passed
        in as arguments.

        Equivalent to::

            assert string in res
        """
        if 'no' in kw:
            no = kw['no']
            del kw['no']
            if isinstance(no, string_types):
                no = [no]
        else:
            no = []
        if kw:
            raise TypeError(
                "The only keyword argument allowed is 'no'")

        f = self._save_output(str(self))

        for s in strings:
            if not s in self:
                print_stderr("Actual response (no %r):" % s)
                print_stderr(str(self))
                raise IndexError(
                    "Body does not contain string %r, output saved as %s" % (
                    s, f))

        for no_s in no:
            if no_s in self:
                print_stderr("Actual response (has %r)" % no_s)
                print_stderr(str(self))
                raise IndexError(
                    "Body contains bad string %r, output saved as %s" % (
                    no_s, f))

    def assert_response(self):
        return AssertResponse(self)

    def get_session_from_response(self):
        """
        This returns the session from a response object. Pylons has some magic
        to make the session available as `response.session`. But pyramid
        doesn't expose it.
        """
        return self.request.environ['beaker.session']


class TestRequest(webob.BaseRequest):

    # for py.test
    disabled = True
    ResponseClass = CustomTestResponse


class CustomTestApp(TestApp):
    """
    Custom app to make mustcontain more usefull
    """
    RequestClass = TestRequest


def set_anonymous_access(enabled):
    """(Dis)allows anonymous access depending on parameter `enabled`"""
    user = User.get_default_user()
    user.active = enabled
    Session().add(user)
    Session().commit()
    time.sleep(1.5)  # must sleep for cache (1s to expire)
    log.info('anonymous access is now: %s', enabled)
    assert enabled == User.get_default_user().active, (
        'Cannot set anonymous access')


def check_xfail_backends(node, backend_alias):
    # Using "xfail_backends" here intentionally, since this marks work
    # which is "to be done" soon.
    skip_marker = node.get_marker('xfail_backends')
    if skip_marker and backend_alias in skip_marker.args:
        msg = "Support for backend %s to be developed." % (backend_alias, )
        msg = skip_marker.kwargs.get('reason', msg)
        pytest.xfail(msg)


def check_skip_backends(node, backend_alias):
    # Using "skip_backends" here intentionally, since this marks work which is
    # not supported.
    skip_marker = node.get_marker('skip_backends')
    if skip_marker and backend_alias in skip_marker.args:
        msg = "Feature not supported for backend %s." % (backend_alias, )
        msg = skip_marker.kwargs.get('reason', msg)
        pytest.skip(msg)


def extract_git_repo_from_dump(dump_name, repo_name):
    """Create git repo `repo_name` from dump `dump_name`."""
    repos_path = ScmModel().repos_path
    target_path = os.path.join(repos_path, repo_name)
    rc_testdata.extract_git_dump(dump_name, target_path)
    return target_path


def extract_hg_repo_from_dump(dump_name, repo_name):
    """Create hg repo `repo_name` from dump `dump_name`."""
    repos_path = ScmModel().repos_path
    target_path = os.path.join(repos_path, repo_name)
    rc_testdata.extract_hg_dump(dump_name, target_path)
    return target_path


def extract_svn_repo_from_dump(dump_name, repo_name):
    """Create a svn repo `repo_name` from dump `dump_name`."""
    repos_path = ScmModel().repos_path
    target_path = os.path.join(repos_path, repo_name)
    SubversionRepository(target_path, create=True)
    _load_svn_dump_into_repo(dump_name, target_path)
    return target_path


def assert_message_in_log(log_records, message, levelno, module):
    messages = [
        r.message for r in log_records
        if r.module == module and r.levelno == levelno
    ]
    assert message in messages


def _load_svn_dump_into_repo(dump_name, repo_path):
    """
    Utility to populate a svn repository with a named dump

    Currently the dumps are in rc_testdata. They might later on be
    integrated with the main repository once they stabilize more.
    """
    dump = rc_testdata.load_svn_dump(dump_name)
    load_dump = subprocess32.Popen(
        ['svnadmin', 'load', repo_path],
        stdin=subprocess32.PIPE, stdout=subprocess32.PIPE,
        stderr=subprocess32.PIPE)
    out, err = load_dump.communicate(dump)
    if load_dump.returncode != 0:
        log.error("Output of load_dump command: %s", out)
        log.error("Error output of load_dump command: %s", err)
        raise Exception(
            'Failed to load dump "%s" into repository at path "%s".'
            % (dump_name, repo_path))


class AssertResponse(object):
    """
    Utility that helps to assert things about a given HTML response.
    """

    def __init__(self, response):
        self.response = response

    def get_imports(self):
        return fromstring, tostring, CSSSelector

    def one_element_exists(self, css_selector):
        self.get_element(css_selector)

    def no_element_exists(self, css_selector):
        assert not self._get_elements(css_selector)

    def element_equals_to(self, css_selector, expected_content):
        element = self.get_element(css_selector)
        element_text = self._element_to_string(element)
        assert expected_content in element_text

    def element_contains(self, css_selector, expected_content):
        element = self.get_element(css_selector)
        assert expected_content in element.text_content()

    def element_value_contains(self, css_selector, expected_content):
        element = self.get_element(css_selector)
        assert expected_content in element.value

    def contains_one_link(self, link_text, href):
        fromstring, tostring, CSSSelector = self.get_imports()
        doc = fromstring(self.response.body)
        sel = CSSSelector('a[href]')
        elements = [
            e for e in sel(doc) if e.text_content().strip() == link_text]
        assert len(elements) == 1, "Did not find link or found multiple links"
        self._ensure_url_equal(elements[0].attrib.get('href'), href)

    def contains_one_anchor(self, anchor_id):
        fromstring, tostring, CSSSelector = self.get_imports()
        doc = fromstring(self.response.body)
        sel = CSSSelector('#' + anchor_id)
        elements = sel(doc)
        assert len(elements) == 1, 'cannot find 1 element {}'.format(anchor_id)

    def _ensure_url_equal(self, found, expected):
        assert _Url(found) == _Url(expected)

    def get_element(self, css_selector):
        elements = self._get_elements(css_selector)
        assert len(elements) == 1, 'cannot find 1 element {}'.format(css_selector)
        return elements[0]

    def get_elements(self, css_selector):
        return self._get_elements(css_selector)

    def _get_elements(self, css_selector):
        fromstring, tostring, CSSSelector = self.get_imports()
        doc = fromstring(self.response.body)
        sel = CSSSelector(css_selector)
        elements = sel(doc)
        return elements

    def _element_to_string(self, element):
        fromstring, tostring, CSSSelector = self.get_imports()
        return tostring(element)


class _Url(object):
    """
    A url object that can be compared with other url orbjects
    without regard to the vagaries of encoding, escaping, and ordering
    of parameters in query strings.

    Inspired by
    http://stackoverflow.com/questions/5371992/comparing-two-urls-in-python
    """

    def __init__(self, url):
        parts = urlparse(url)
        _query = frozenset(parse_qsl(parts.query))
        _path = unquote_plus(parts.path)
        parts = parts._replace(query=_query, path=_path)
        self.parts = parts

    def __eq__(self, other):
        return self.parts == other.parts

    def __hash__(self):
        return hash(self.parts)


def run_test_concurrently(times, raise_catched_exc=True):
    """
    Add this decorator to small pieces of code that you want to test
    concurrently

    ex:

    @test_concurrently(25)
    def my_test_function():
        ...
    """
    def test_concurrently_decorator(test_func):
        def wrapper(*args, **kwargs):
            exceptions = []

            def call_test_func():
                try:
                    test_func(*args, **kwargs)
                except Exception as e:
                    exceptions.append(e)
                    if raise_catched_exc:
                        raise
            threads = []
            for i in range(times):
                threads.append(threading.Thread(target=call_test_func))
            for t in threads:
                t.start()
            for t in threads:
                t.join()
            if exceptions:
                raise Exception(
                    'test_concurrently intercepted %s exceptions: %s' % (
                        len(exceptions), exceptions))
        return wrapper
    return test_concurrently_decorator


def wait_for_url(url, timeout=10):
    """
    Wait until URL becomes reachable.

    It polls the URL until the timeout is reached or it became reachable.
    If will call to `py.test.fail` in case the URL is not reachable.
    """
    timeout = time.time() + timeout
    last = 0
    wait = 0.1

    while timeout > last:
        last = time.time()
        if is_url_reachable(url):
            break
        elif (last + wait) > time.time():
            # Go to sleep because not enough time has passed since last check.
            time.sleep(wait)
    else:
        pytest.fail("Timeout while waiting for URL {}".format(url))


def is_url_reachable(url):
    try:
        urllib2.urlopen(url)
    except urllib2.URLError:
        return False
    return True


def repo_on_filesystem(repo_name):
    from rhodecode.lib import vcs
    from rhodecode.tests import TESTS_TMP_PATH
    repo = vcs.get_vcs_instance(
        os.path.join(TESTS_TMP_PATH, repo_name), create=False)
    return repo is not None


def commit_change(
        repo, filename, content, message, vcs_type, parent=None, newfile=False):
    from rhodecode.tests import TEST_USER_ADMIN_LOGIN

    repo = Repository.get_by_repo_name(repo)
    _commit = parent
    if not parent:
        _commit = EmptyCommit(alias=vcs_type)

    if newfile:
        nodes = {
            filename: {
                'content': content
            }
        }
        commit = ScmModel().create_nodes(
            user=TEST_USER_ADMIN_LOGIN, repo=repo,
            message=message,
            nodes=nodes,
            parent_commit=_commit,
            author=TEST_USER_ADMIN_LOGIN,
        )
    else:
        commit = ScmModel().commit_change(
            repo=repo.scm_instance(), repo_name=repo.repo_name,
            commit=parent, user=TEST_USER_ADMIN_LOGIN,
            author=TEST_USER_ADMIN_LOGIN,
            message=message,
            content=content,
            f_path=filename
        )
    return commit


def add_test_routes(config):
    """
    Adds test routing that can be used in different functional tests

    """
    config.add_route(name='home', pattern='/')
    config.add_route(name='repo_summary', pattern='/{repo_name}')
    config.add_route(name='repo_summary_explicit', pattern='/{repo_name}/summary')
    config.add_route(name='repo_group_home', pattern='/{repo_group_name}')

    config.add_route(name='pullrequest_show',
                     pattern='/{repo_name}/pull-request/{pull_request_id}')
    config.add_route(name='pull_requests_global',
                     pattern='/pull-request/{pull_request_id}')
    config.add_route(name='repo_commit',
                     pattern='/{repo_name}/changeset/{commit_id}')
