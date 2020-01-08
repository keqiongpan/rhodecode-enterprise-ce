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

import pytest

from rhodecode import events
from rhodecode.lib.utils2 import AttributeDict
from rhodecode.integrations.types.webhook import WebhookDataHandler


@pytest.fixture()
def base_data():
    return {
        'name': 'event',
        'repo': {
            'repo_name': 'foo',
            'repo_type': 'hg',
            'repo_id': '12',
            'url': 'http://repo.url/foo',
            'extra_fields': {},
        },
        'actor': {
            'username': 'actor_name',
            'user_id': 1
        }
    }


def test_webhook_parse_url_invalid_event():
    template_url = 'http://server.com/${repo_name}/build'
    handler = WebhookDataHandler(
        template_url, {'exmaple-header': 'header-values'})
    event = events.RepoDeleteEvent('')
    with pytest.raises(ValueError) as err:
        handler(event, {})

    err = str(err.value)
    assert err.startswith(
        'event type `%s` not in supported list' % event.__class__)


@pytest.mark.parametrize('template,expected_urls', [
    ('http://server.com/${repo_name}/build',
     ['http://server.com/foo/build']),
    ('http://server.com/${repo_name}/${repo_type}',
     ['http://server.com/foo/hg']),
    ('http://${server}.com/${repo_name}/${repo_id}',
     ['http://${server}.com/foo/12']),
    ('http://server.com/${branch}/build',
     ['http://server.com/${branch}/build']),
])
def test_webook_parse_url_for_create_event(base_data, template, expected_urls):
    headers = {'exmaple-header': 'header-values'}
    handler = WebhookDataHandler(template, headers)
    urls = handler(events.RepoCreateEvent(''), base_data)
    assert urls == [
        (url, headers, base_data) for url in expected_urls]


@pytest.mark.parametrize('template,expected_urls', [
    ('http://server.com/${repo_name}/${pull_request_id}',
     ['http://server.com/foo/999']),
    ('http://server.com/${repo_name}/${pull_request_url}',
     ['http://server.com/foo/http%3A//pr-url.com']),
    ('http://server.com/${repo_name}/${pull_request_url}/?TITLE=${pull_request_title}',
     ['http://server.com/foo/http%3A//pr-url.com/?TITLE=example-pr-title%20Ticket%20%23123']),
    ('http://server.com/${repo_name}/?SHADOW_URL=${pull_request_shadow_url}',
     ['http://server.com/foo/?SHADOW_URL=http%3A//pr-url.com/repository']),
])
def test_webook_parse_url_for_pull_request_event(base_data, template, expected_urls):

    base_data['pullrequest'] = {
        'pull_request_id': 999,
        'url': 'http://pr-url.com',
        'title': 'example-pr-title Ticket #123',
        'commits_uid': 'abcdefg1234',
        'shadow_url': 'http://pr-url.com/repository'
    }
    headers = {'exmaple-header': 'header-values'}
    handler = WebhookDataHandler(template, headers)
    urls = handler(events.PullRequestCreateEvent(
        AttributeDict({'target_repo': 'foo'})), base_data)
    assert urls == [
        (url, headers, base_data) for url in expected_urls]


@pytest.mark.parametrize('template,expected_urls', [
    ('http://server.com/${branch}/build',
        ['http://server.com/stable/build',
         'http://server.com/dev/build']),
    ('http://server.com/${branch}/${commit_id}',
        ['http://server.com/stable/stable-xxx',
         'http://server.com/stable/stable-yyy',
         'http://server.com/dev/dev-xxx',
         'http://server.com/dev/dev-yyy']),
    ('http://server.com/${branch_head}',
     ['http://server.com/stable-yyy',
      'http://server.com/dev-yyy']),
    ('http://server.com/${commit_id}',
     ['http://server.com/stable-xxx',
      'http://server.com/stable-yyy',
      'http://server.com/dev-xxx',
      'http://server.com/dev-yyy']),
])
def test_webook_parse_url_for_push_event(
        baseapp, repo_push_event, base_data, template, expected_urls):
    base_data['push'] = {
        'branches': [{'name': 'stable'}, {'name': 'dev'}],
        'commits': [{'branch': 'stable', 'raw_id': 'stable-xxx'},
                    {'branch': 'stable', 'raw_id': 'stable-yyy'},
                    {'branch': 'dev', 'raw_id': 'dev-xxx'},
                    {'branch': 'dev', 'raw_id': 'dev-yyy'}]
    }
    headers = {'exmaple-header': 'header-values'}
    handler = WebhookDataHandler(template, headers)
    urls = handler(repo_push_event, base_data)
    assert urls == [
        (url, headers, base_data) for url in expected_urls]
