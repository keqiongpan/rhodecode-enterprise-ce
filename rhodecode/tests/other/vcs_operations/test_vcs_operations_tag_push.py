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

"""
Test suite for making push/pull operations, on specially modified INI files

.. important::

   You must have git >= 1.8.5 for tests to work fine. With 68b939b git started
   to redirect things to stderr instead of stdout.
"""

import pytest
import requests

from rhodecode import events
from rhodecode.model.db import Integration
from rhodecode.model.integration import IntegrationModel
from rhodecode.model.meta import Session

from rhodecode.tests import GIT_REPO, HG_REPO
from rhodecode.tests.other.vcs_operations import Command, _add_files_and_push
from rhodecode.integrations.types.webhook import WebhookIntegrationType


def check_connection():
    try:
        response = requests.get('http://httpbin.org')
        return response.status_code == 200
    except Exception as e:
        print(e)

    return False


connection_available = pytest.mark.skipif(
    not check_connection(), reason="No outside internet connection available")


@pytest.fixture
def enable_webhook_push_integration(request):
    integration = Integration()
    integration.integration_type = WebhookIntegrationType.key
    Session().add(integration)

    settings = dict(
        url='http://httpbin.org',
        secret_token='secret',
        username=None,
        password=None,
        custom_header_key=None,
        custom_header_val=None,
        method_type='get',
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


@pytest.fixture(scope="session")
def vcs_server_config_override():
    return ({'server:main': {'workers': 2}},)


@pytest.mark.usefixtures(
    "disable_locking", "disable_anonymous_user",
    "enable_webhook_push_integration")
class TestVCSOperationsOnCustomIniConfig(object):

    def test_push_tag_with_commit_hg(self, rc_web_server, tmpdir):
        clone_url = rc_web_server.repo_clone_url(HG_REPO)
        stdout, stderr = Command('/tmp').execute(
            'hg clone', clone_url, tmpdir.strpath)

        push_url = rc_web_server.repo_clone_url(HG_REPO)
        _add_files_and_push(
            'hg', tmpdir.strpath, clone_url=push_url,
            tags=[{'name': 'v1.0.0', 'commit': 'added tag v1.0.0'}])

        rc_log = rc_web_server.get_rc_log()
        assert 'ERROR' not in rc_log
        assert "'name': u'v1.0.0'" in rc_log

    def test_push_tag_with_commit_git(
            self, rc_web_server, tmpdir):
        clone_url = rc_web_server.repo_clone_url(GIT_REPO)
        stdout, stderr = Command('/tmp').execute(
            'git clone', clone_url, tmpdir.strpath)

        push_url = rc_web_server.repo_clone_url(GIT_REPO)
        _add_files_and_push(
            'git', tmpdir.strpath, clone_url=push_url,
            tags=[{'name': 'v1.0.0', 'commit': 'added tag v1.0.0'}])

        rc_log = rc_web_server.get_rc_log()
        assert 'ERROR' not in rc_log
        assert "'name': u'v1.0.0'" in rc_log

    def test_push_tag_with_no_commit_git(
            self, rc_web_server, tmpdir):
        clone_url = rc_web_server.repo_clone_url(GIT_REPO)
        stdout, stderr = Command('/tmp').execute(
            'git clone', clone_url, tmpdir.strpath)

        push_url = rc_web_server.repo_clone_url(GIT_REPO)
        _add_files_and_push(
            'git', tmpdir.strpath, clone_url=push_url,
            tags=[{'name': 'v1.0.0', 'commit': 'added tag v1.0.0'}])

        rc_log = rc_web_server.get_rc_log()
        assert 'ERROR' not in rc_log
        assert "'name': u'v1.0.0'" in rc_log
