# -*- coding: utf-8 -*-

# Copyright (C) 2010-2019 RhodeCode GmbH
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
py.test config for test suite for making push/pull operations.

.. important::

   You must have git >= 1.8.5 for tests to work fine. With 68b939b git started
   to redirect things to stderr instead of stdout.
"""

import os
import tempfile
import textwrap
import pytest

from rhodecode import events
from rhodecode.model.db import Integration, UserRepoToPerm, Permission, \
    UserToRepoBranchPermission, User
from rhodecode.model.integration import IntegrationModel
from rhodecode.model.db import Repository
from rhodecode.model.meta import Session
from rhodecode.model.settings import SettingsModel
from rhodecode.integrations.types.webhook import WebhookIntegrationType

from rhodecode.tests import GIT_REPO, HG_REPO
from rhodecode.tests.fixture import Fixture
from rhodecode.tests.server_utils import RcWebServer

REPO_GROUP = 'a_repo_group'
HG_REPO_WITH_GROUP = '%s/%s' % (REPO_GROUP, HG_REPO)
GIT_REPO_WITH_GROUP = '%s/%s' % (REPO_GROUP, GIT_REPO)


@pytest.fixture(scope="module")
def rcextensions(request, db_connection, tmpdir_factory):
    """
    Installs a testing rcextensions pack to ensure they work as expected.
    """
    init_content = textwrap.dedent("""
        # Forward import the example rcextensions to make it
        # active for our tests.
        from rhodecode.tests.other.example_rcextensions import *
    """)

    # Note: rcextensions are looked up based on the path of the ini file
    root_path = tmpdir_factory.getbasetemp()
    rcextensions_path = root_path.join('rcextensions')
    init_path = rcextensions_path.join('__init__.py')

    if rcextensions_path.check():
        pytest.fail(
            "Path for rcextensions already exists, please clean up before "
            "test run this path: %s" % (rcextensions_path, ))
        return

    request.addfinalizer(rcextensions_path.remove)
    init_path.write_binary(init_content, ensure=True)


@pytest.fixture(scope="module")
def repos(request, db_connection):
    """Create a copy of each test repo in a repo group."""
    fixture = Fixture()
    repo_group = fixture.create_repo_group(REPO_GROUP)
    repo_group_id = repo_group.group_id
    fixture.create_fork(HG_REPO, HG_REPO,
                        repo_name_full=HG_REPO_WITH_GROUP,
                        repo_group=repo_group_id)
    fixture.create_fork(GIT_REPO, GIT_REPO,
                        repo_name_full=GIT_REPO_WITH_GROUP,
                        repo_group=repo_group_id)

    @request.addfinalizer
    def cleanup():
        fixture.destroy_repo(HG_REPO_WITH_GROUP)
        fixture.destroy_repo(GIT_REPO_WITH_GROUP)
        fixture.destroy_repo_group(repo_group_id)


@pytest.fixture(scope="module")
def rc_web_server_config_modification():
    return []


@pytest.fixture(scope="module")
def rc_web_server_config_factory(testini_factory, rc_web_server_config_modification):
    """
    Configuration file used for the fixture `rc_web_server`.
    """

    def factory(rcweb_port, vcsserver_port):
        custom_params = [
            {'handler_console': {'level': 'DEBUG'}},
            {'server:main': {'port': rcweb_port}},
            {'app:main': {'vcs.server': 'localhost:%s' % vcsserver_port}}
        ]
        custom_params.extend(rc_web_server_config_modification)
        return testini_factory(custom_params)
    return factory


@pytest.fixture(scope="module")
def rc_web_server(
        request, vcsserver_factory, available_port_factory,
        rc_web_server_config_factory, repos, rcextensions):
    """
    Run the web server as a subprocess. with it's own instance of vcsserver
    """
    rcweb_port = available_port_factory()
    print('Using rcweb ops test port {}'.format(rcweb_port))

    vcsserver_port = available_port_factory()
    print('Using vcsserver ops test port {}'.format(vcsserver_port))

    vcs_log = os.path.join(tempfile.gettempdir(), 'rc_op_vcs.log')
    vcsserver_factory(
            request, vcsserver_port=vcsserver_port,
            log_file=vcs_log,
            overrides=(
                {'server:main': {'workers': 2}},
                {'server:main': {'graceful_timeout': 10}},
            ))

    rc_log = os.path.join(tempfile.gettempdir(), 'rc_op_web.log')
    rc_web_server_config = rc_web_server_config_factory(
        rcweb_port=rcweb_port,
        vcsserver_port=vcsserver_port)
    server = RcWebServer(rc_web_server_config, log_file=rc_log)
    server.start()

    @request.addfinalizer
    def cleanup():
        server.shutdown()

    server.wait_until_ready()
    return server


@pytest.fixture()
def disable_locking(baseapp):
    r = Repository.get_by_repo_name(GIT_REPO)
    Repository.unlock(r)
    r.enable_locking = False
    Session().add(r)
    Session().commit()

    r = Repository.get_by_repo_name(HG_REPO)
    Repository.unlock(r)
    r.enable_locking = False
    Session().add(r)
    Session().commit()


@pytest.fixture()
def enable_auth_plugins(request, baseapp, csrf_token):
    """
    Return a factory object that when called, allows to control which
    authentication plugins are enabled.
    """
    def _enable_plugins(plugins_list, override=None):
        override = override or {}
        params = {
            'auth_plugins': ','.join(plugins_list),
        }

        # helper translate some names to others
        name_map = {
            'token': 'authtoken'
        }

        for module in plugins_list:
            plugin_name = module.partition('#')[-1]
            if plugin_name in name_map:
                plugin_name = name_map[plugin_name]
            enabled_plugin = 'auth_%s_enabled' % plugin_name
            cache_ttl = 'auth_%s_cache_ttl' % plugin_name

            # default params that are needed for each plugin,
            # `enabled` and `cache_ttl`
            params.update({
                enabled_plugin: True,
                cache_ttl: 0
            })
            if override.get:
                params.update(override.get(module, {}))

            validated_params = params
            for k, v in validated_params.items():
                setting = SettingsModel().create_or_update_setting(k, v)
                Session().add(setting)
            Session().commit()

        SettingsModel().invalidate_settings_cache()

    def cleanup():
        _enable_plugins(['egg:rhodecode-enterprise-ce#rhodecode'])

    request.addfinalizer(cleanup)

    return _enable_plugins


@pytest.fixture()
def fs_repo_only(request, rhodecode_fixtures):
    def fs_repo_fabric(repo_name, repo_type):
        rhodecode_fixtures.create_repo(repo_name, repo_type=repo_type)
        rhodecode_fixtures.destroy_repo(repo_name, fs_remove=False)

        def cleanup():
            rhodecode_fixtures.destroy_repo(repo_name, fs_remove=True)
            rhodecode_fixtures.destroy_repo_on_filesystem(repo_name)

        request.addfinalizer(cleanup)

    return fs_repo_fabric


@pytest.fixture()
def enable_webhook_push_integration(request):
    integration = Integration()
    integration.integration_type = WebhookIntegrationType.key
    Session().add(integration)

    settings = dict(
        url='http://httpbin.org/post',
        secret_token='secret',
        username=None,
        password=None,
        custom_header_key=None,
        custom_header_val=None,
        method_type='post',
        events=[events.RepoPushEvent.name],
        log_data=True
    )

    IntegrationModel().update_integration(
        integration,
        name='IntegrationWebhookTest',
        enabled=True,
        settings=settings,
        repo=None,
        repo_group=None,
        child_repos_only=False,
    )
    Session().commit()
    integration_id = integration.integration_id

    @request.addfinalizer
    def cleanup():
        integration = Integration.get(integration_id)
        Session().delete(integration)
        Session().commit()


@pytest.fixture()
def branch_permission_setter(request):
    """

    def my_test(branch_permission_setter)
        branch_permission_setter(repo_name, username, pattern='*', permission='branch.push')

    """

    rule_id = None
    write_perm_id = None
    write_perm = None
    rule = None

    def _branch_permissions_setter(
            repo_name, username, pattern='*', permission='branch.push_force'):
        global rule_id, write_perm_id
        global rule, write_perm

        repo = Repository.get_by_repo_name(repo_name)
        repo_id = repo.repo_id

        user = User.get_by_username(username)
        user_id = user.user_id

        rule_perm_obj = Permission.get_by_key(permission)

        # add new entry, based on existing perm entry
        perm = UserRepoToPerm.query() \
            .filter(UserRepoToPerm.repository_id == repo_id) \
            .filter(UserRepoToPerm.user_id == user_id) \
            .first()

        if not perm:
            # such user isn't defined in Permissions for repository
            # we now on-the-fly add new permission

            write_perm = UserRepoToPerm()
            write_perm.permission = Permission.get_by_key('repository.write')
            write_perm.repository_id = repo_id
            write_perm.user_id = user_id
            Session().add(write_perm)
            Session().flush()

            perm = write_perm

        rule = UserToRepoBranchPermission()
        rule.rule_to_perm_id = perm.repo_to_perm_id
        rule.branch_pattern = pattern
        rule.rule_order = 10
        rule.permission = rule_perm_obj
        rule.repository_id = repo_id
        Session().add(rule)
        Session().commit()

        return rule

    @request.addfinalizer
    def cleanup():
        if rule:
            Session().delete(rule)
            Session().commit()
        if write_perm:
            Session().delete(write_perm)
            Session().commit()

    return _branch_permissions_setter


