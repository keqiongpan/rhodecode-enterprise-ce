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

import base64

import mock
import pytest

from rhodecode.lib.utils2 import AttributeDict
from rhodecode.tests.utils import CustomTestApp

from rhodecode.lib.caching_query import FromCache
from rhodecode.lib.hooks_daemon import DummyHooksCallbackDaemon
from rhodecode.lib.middleware import simplevcs
from rhodecode.lib.middleware.https_fixup import HttpsFixup
from rhodecode.lib.middleware.utils import scm_app_http
from rhodecode.model.db import User, _hash_key
from rhodecode.model.meta import Session
from rhodecode.tests import (
    HG_REPO, TEST_USER_ADMIN_LOGIN, TEST_USER_ADMIN_PASS)
from rhodecode.tests.lib.middleware import mock_scm_app


class StubVCSController(simplevcs.SimpleVCS):

    SCM = 'hg'
    stub_response_body = tuple()

    def __init__(self, *args, **kwargs):
        super(StubVCSController, self).__init__(*args, **kwargs)
        self._action = 'pull'
        self._is_shadow_repo_dir = True
        self._name = HG_REPO
        self.set_repo_names(None)

    @property
    def is_shadow_repo_dir(self):
        return self._is_shadow_repo_dir

    def _get_repository_name(self, environ):
        return self._name

    def _get_action(self, environ):
        return self._action

    def _create_wsgi_app(self, repo_path, repo_name, config):
        def fake_app(environ, start_response):
            headers = [
                ('Http-Accept', 'application/mercurial')
            ]
            start_response('200 OK', headers)
            return self.stub_response_body
        return fake_app

    def _create_config(self, extras, repo_name, scheme='http'):
        return None


@pytest.fixture()
def vcscontroller(baseapp, config_stub, request_stub):
    config_stub.testing_securitypolicy()
    config_stub.include('rhodecode.authentication')
    config_stub.include('rhodecode.authentication.plugins.auth_rhodecode')
    config_stub.include('rhodecode.authentication.plugins.auth_token')

    controller = StubVCSController(
        baseapp.config.get_settings(), request_stub.registry)
    app = HttpsFixup(controller, baseapp.config.get_settings())
    app = CustomTestApp(app)

    _remove_default_user_from_query_cache()

    # Sanity checks that things are set up correctly
    app.get('/' + HG_REPO, status=200)

    app.controller = controller
    return app


def _remove_default_user_from_query_cache():
    user = User.get_default_user(cache=True)
    query = Session().query(User).filter(User.username == user.username)
    query = query.options(
        FromCache("sql_cache_short", "get_user_%s" % _hash_key(user.username)))
    query.invalidate()
    Session().expire(user)


def test_handles_exceptions_during_permissions_checks(
        vcscontroller, disable_anonymous_user):
    user_and_pass = '%s:%s' % (TEST_USER_ADMIN_LOGIN, TEST_USER_ADMIN_PASS)
    auth_password = base64.encodestring(user_and_pass).strip()
    extra_environ = {
        'AUTH_TYPE': 'Basic',
        'HTTP_AUTHORIZATION': 'Basic %s' % auth_password,
        'REMOTE_USER': TEST_USER_ADMIN_LOGIN,
    }

    # Verify that things are hooked up correctly
    vcscontroller.get('/', status=200, extra_environ=extra_environ)

    # Simulate trouble during permission checks
    with mock.patch('rhodecode.model.db.User.get_by_username',
                    side_effect=Exception) as get_user:
        # Verify that a correct 500 is returned and check that the expected
        # code path was hit.
        vcscontroller.get('/', status=500, extra_environ=extra_environ)
        assert get_user.called


def test_returns_forbidden_if_no_anonymous_access(
        vcscontroller, disable_anonymous_user):
    vcscontroller.get('/', status=401)


class StubFailVCSController(simplevcs.SimpleVCS):
    def _handle_request(self, environ, start_response):
        raise Exception("BOOM")


@pytest.fixture(scope='module')
def fail_controller(baseapp):
    controller = StubFailVCSController(
        baseapp.config.get_settings(), baseapp.config)
    controller = HttpsFixup(controller, baseapp.config.get_settings())
    controller = CustomTestApp(controller)
    return controller


def test_handles_exceptions_as_internal_server_error(fail_controller):
    fail_controller.get('/', status=500)


def test_provides_traceback_for_appenlight(fail_controller):
    response = fail_controller.get(
        '/', status=500, extra_environ={'appenlight.client': 'fake'})
    assert 'appenlight.__traceback' in response.request.environ


def test_provides_utils_scm_app_as_scm_app_by_default(baseapp, request_stub):
    controller = StubVCSController(baseapp.config.get_settings(), request_stub.registry)
    assert controller.scm_app is scm_app_http


def test_allows_to_override_scm_app_via_config(baseapp, request_stub):
    config = baseapp.config.get_settings().copy()
    config['vcs.scm_app_implementation'] = (
        'rhodecode.tests.lib.middleware.mock_scm_app')
    controller = StubVCSController(config, request_stub.registry)
    assert controller.scm_app is mock_scm_app


@pytest.mark.parametrize('query_string, expected', [
    ('cmd=stub_command', True),
    ('cmd=listkeys', False),
])
def test_should_check_locking(query_string, expected):
    result = simplevcs._should_check_locking(query_string)
    assert result == expected


class TestShadowRepoRegularExpression(object):
    pr_segment = 'pull-request'
    shadow_segment = 'repository'

    @pytest.mark.parametrize('url, expected', [
        # repo with/without groups
        ('My-Repo/{pr_segment}/1/{shadow_segment}', True),
        ('Group/My-Repo/{pr_segment}/2/{shadow_segment}', True),
        ('Group/Sub-Group/My-Repo/{pr_segment}/3/{shadow_segment}', True),
        ('Group/Sub-Group1/Sub-Group2/My-Repo/{pr_segment}/3/{shadow_segment}', True),

        # pull request ID
        ('MyRepo/{pr_segment}/1/{shadow_segment}', True),
        ('MyRepo/{pr_segment}/1234567890/{shadow_segment}', True),
        ('MyRepo/{pr_segment}/-1/{shadow_segment}', False),
        ('MyRepo/{pr_segment}/invalid/{shadow_segment}', False),

        # unicode
        (u'Sp€çîál-Repö/{pr_segment}/1/{shadow_segment}', True),
        (u'Sp€çîál-Gröüp/Sp€çîál-Repö/{pr_segment}/1/{shadow_segment}', True),

        # trailing/leading slash
        ('/My-Repo/{pr_segment}/1/{shadow_segment}', False),
        ('My-Repo/{pr_segment}/1/{shadow_segment}/', False),
        ('/My-Repo/{pr_segment}/1/{shadow_segment}/', False),

        # misc
        ('My-Repo/{pr_segment}/1/{shadow_segment}/extra', False),
        ('My-Repo/{pr_segment}/1/{shadow_segment}extra', False),
    ])
    def test_shadow_repo_regular_expression(self, url, expected):
        from rhodecode.lib.middleware.simplevcs import SimpleVCS
        url = url.format(
            pr_segment=self.pr_segment,
            shadow_segment=self.shadow_segment)
        match_obj = SimpleVCS.shadow_repo_re.match(url)
        assert (match_obj is not None) == expected


@pytest.mark.backends('git', 'hg')
class TestShadowRepoExposure(object):

    def test_pull_on_shadow_repo_propagates_to_wsgi_app(
            self, baseapp, request_stub):
        """
        Check that a pull action to a shadow repo is propagated to the
        underlying wsgi app.
        """
        controller = StubVCSController(
            baseapp.config.get_settings(), request_stub.registry)
        controller._check_ssl = mock.Mock()
        controller.is_shadow_repo = True
        controller._action = 'pull'
        controller._is_shadow_repo_dir = True
        controller.stub_response_body = 'dummy body value'
        controller._get_default_cache_ttl = mock.Mock(
            return_value=(False, 0))

        environ_stub = {
            'HTTP_HOST': 'test.example.com',
            'HTTP_ACCEPT': 'application/mercurial',
            'REQUEST_METHOD': 'GET',
            'wsgi.url_scheme': 'http',
        }

        response = controller(environ_stub, mock.Mock())
        response_body = ''.join(response)

        # Assert that we got the response from the wsgi app.
        assert response_body == controller.stub_response_body

    def test_pull_on_shadow_repo_that_is_missing(self, baseapp, request_stub):
        """
        Check that a pull action to a shadow repo is propagated to the
        underlying wsgi app.
        """
        controller = StubVCSController(
            baseapp.config.get_settings(), request_stub.registry)
        controller._check_ssl = mock.Mock()
        controller.is_shadow_repo = True
        controller._action = 'pull'
        controller._is_shadow_repo_dir = False
        controller.stub_response_body = 'dummy body value'
        environ_stub = {
            'HTTP_HOST': 'test.example.com',
            'HTTP_ACCEPT': 'application/mercurial',
            'REQUEST_METHOD': 'GET',
            'wsgi.url_scheme': 'http',
        }

        response = controller(environ_stub, mock.Mock())
        response_body = ''.join(response)

        # Assert that we got the response from the wsgi app.
        assert '404 Not Found' in response_body

    def test_push_on_shadow_repo_raises(self, baseapp, request_stub):
        """
        Check that a push action to a shadow repo is aborted.
        """
        controller = StubVCSController(
            baseapp.config.get_settings(), request_stub.registry)
        controller._check_ssl = mock.Mock()
        controller.is_shadow_repo = True
        controller._action = 'push'
        controller.stub_response_body = 'dummy body value'
        environ_stub = {
            'HTTP_HOST': 'test.example.com',
            'HTTP_ACCEPT': 'application/mercurial',
            'REQUEST_METHOD': 'GET',
            'wsgi.url_scheme': 'http',
        }

        response = controller(environ_stub, mock.Mock())
        response_body = ''.join(response)

        assert response_body != controller.stub_response_body
        # Assert that a 406 error is returned.
        assert '406 Not Acceptable' in response_body

    def test_set_repo_names_no_shadow(self, baseapp, request_stub):
        """
        Check that the set_repo_names method sets all names to the one returned
        by the _get_repository_name method on a request to a non shadow repo.
        """
        environ_stub = {}
        controller = StubVCSController(
            baseapp.config.get_settings(), request_stub.registry)
        controller._name = 'RepoGroup/MyRepo'
        controller.set_repo_names(environ_stub)
        assert not controller.is_shadow_repo
        assert (controller.url_repo_name ==
                controller.acl_repo_name ==
                controller.vcs_repo_name ==
                controller._get_repository_name(environ_stub))

    def test_set_repo_names_with_shadow(
            self, baseapp, pr_util, config_stub, request_stub):
        """
        Check that the set_repo_names method sets correct names on a request
        to a shadow repo.
        """
        from rhodecode.model.pull_request import PullRequestModel

        pull_request = pr_util.create_pull_request()
        shadow_url = '{target}/{pr_segment}/{pr_id}/{shadow_segment}'.format(
            target=pull_request.target_repo.repo_name,
            pr_id=pull_request.pull_request_id,
            pr_segment=TestShadowRepoRegularExpression.pr_segment,
            shadow_segment=TestShadowRepoRegularExpression.shadow_segment)
        controller = StubVCSController(
            baseapp.config.get_settings(), request_stub.registry)
        controller._name = shadow_url
        controller.set_repo_names({})

        # Get file system path to shadow repo for assertions.
        workspace_id = PullRequestModel()._workspace_id(pull_request)
        vcs_repo_name = pull_request.target_repo.get_shadow_repository_path(workspace_id)

        assert controller.vcs_repo_name == vcs_repo_name
        assert controller.url_repo_name == shadow_url
        assert controller.acl_repo_name == pull_request.target_repo.repo_name
        assert controller.is_shadow_repo

    def test_set_repo_names_with_shadow_but_missing_pr(
            self, baseapp, pr_util, config_stub, request_stub):
        """
        Checks that the set_repo_names method enforces matching target repos
        and pull request IDs.
        """
        pull_request = pr_util.create_pull_request()
        shadow_url = '{target}/{pr_segment}/{pr_id}/{shadow_segment}'.format(
            target=pull_request.target_repo.repo_name,
            pr_id=999999999,
            pr_segment=TestShadowRepoRegularExpression.pr_segment,
            shadow_segment=TestShadowRepoRegularExpression.shadow_segment)
        controller = StubVCSController(
            baseapp.config.get_settings(), request_stub.registry)
        controller._name = shadow_url
        controller.set_repo_names({})

        assert not controller.is_shadow_repo
        assert (controller.url_repo_name ==
                controller.acl_repo_name ==
                controller.vcs_repo_name)


@pytest.mark.usefixtures('baseapp')
class TestGenerateVcsResponse(object):

    def test_ensures_that_start_response_is_called_early_enough(self):
        self.call_controller_with_response_body(iter(['a', 'b']))
        assert self.start_response.called

    def test_invalidates_cache_after_body_is_consumed(self):
        result = self.call_controller_with_response_body(iter(['a', 'b']))
        assert not self.was_cache_invalidated()
        # Consume the result
        list(result)
        assert self.was_cache_invalidated()

    def test_raises_unknown_exceptions(self):
        result = self.call_controller_with_response_body(
            self.raise_result_iter(vcs_kind='unknown'))
        with pytest.raises(Exception):
            list(result)

    def test_prepare_callback_daemon_is_called(self):
        def side_effect(extras, environ, action, txn_id=None):
            return DummyHooksCallbackDaemon(), extras

        prepare_patcher = mock.patch.object(
            StubVCSController, '_prepare_callback_daemon')
        with prepare_patcher as prepare_mock:
            prepare_mock.side_effect = side_effect
            self.call_controller_with_response_body(iter(['a', 'b']))
        assert prepare_mock.called
        assert prepare_mock.call_count == 1

    def call_controller_with_response_body(self, response_body):
        settings = {
            'base_path': 'fake_base_path',
            'vcs.hooks.protocol': 'http',
            'vcs.hooks.direct_calls': False,
        }
        registry = AttributeDict()
        controller = StubVCSController(settings, registry)
        controller._invalidate_cache = mock.Mock()
        controller.stub_response_body = response_body
        self.start_response = mock.Mock()
        result = controller._generate_vcs_response(
            environ={}, start_response=self.start_response,
            repo_path='fake_repo_path',
            extras={}, action='push')
        self.controller = controller
        return result

    def raise_result_iter(self, vcs_kind='repo_locked'):
        """
        Simulates an exception due to a vcs raised exception if kind vcs_kind
        """
        raise self.vcs_exception(vcs_kind=vcs_kind)
        yield "never_reached"

    def vcs_exception(self, vcs_kind='repo_locked'):
        locked_exception = Exception('TEST_MESSAGE')
        locked_exception._vcs_kind = vcs_kind
        return locked_exception

    def was_cache_invalidated(self):
        return self.controller._invalidate_cache.called


class TestInitializeGenerator(object):

    def test_drains_first_element(self):
        gen = self.factory(['__init__', 1, 2])
        result = list(gen)
        assert result == [1, 2]

    @pytest.mark.parametrize('values', [
        [],
        [1, 2],
    ])
    def test_raises_value_error(self, values):
        with pytest.raises(ValueError):
            self.factory(values)

    @simplevcs.initialize_generator
    def factory(self, iterable):
        for elem in iterable:
            yield elem


class TestPrepareHooksDaemon(object):
    def test_calls_imported_prepare_callback_daemon(self, app_settings, request_stub):
        expected_extras = {'extra1': 'value1'}
        daemon = DummyHooksCallbackDaemon()

        controller = StubVCSController(app_settings, request_stub.registry)
        prepare_patcher = mock.patch.object(
            simplevcs, 'prepare_callback_daemon',
            return_value=(daemon, expected_extras))
        with prepare_patcher as prepare_mock:
            callback_daemon, extras = controller._prepare_callback_daemon(
                expected_extras.copy(), {}, 'push')
        prepare_mock.assert_called_once_with(
            expected_extras,
            protocol=app_settings['vcs.hooks.protocol'],
            host=app_settings['vcs.hooks.host'],
            txn_id=None,
            use_direct_calls=app_settings['vcs.hooks.direct_calls'])

        assert callback_daemon == daemon
        assert extras == extras
