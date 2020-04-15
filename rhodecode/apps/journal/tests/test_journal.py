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

import datetime

import pytest

from rhodecode.apps._base import ADMIN_PREFIX
from rhodecode.tests import TestController
from rhodecode.model.db import UserFollowing, Repository


def route_path(name, params=None, **kwargs):
    import urllib

    base_url = {
        'journal': ADMIN_PREFIX + '/journal',
        'journal_rss': ADMIN_PREFIX + '/journal/rss',
        'journal_atom': ADMIN_PREFIX + '/journal/atom',
        'journal_public': ADMIN_PREFIX + '/public_journal',
        'journal_public_atom': ADMIN_PREFIX + '/public_journal/atom',
        'journal_public_atom_old': ADMIN_PREFIX + '/public_journal_atom',
        'journal_public_rss': ADMIN_PREFIX + '/public_journal/rss',
        'journal_public_rss_old': ADMIN_PREFIX + '/public_journal_rss',
        'toggle_following': ADMIN_PREFIX + '/toggle_following',
    }[name].format(**kwargs)

    if params:
        base_url = '{}?{}'.format(base_url, urllib.urlencode(params))
    return base_url


class TestJournalViews(TestController):

    def test_journal(self):
        self.log_user()
        response = self.app.get(route_path('journal'))
        # response.mustcontain(
        #     """<div class="journal_day">%s</div>""" % datetime.date.today())

    @pytest.mark.parametrize("feed_type, content_type", [
        ('rss', "application/rss+xml"),
        ('atom', "application/atom+xml")
    ])
    def test_journal_feed(self, feed_type, content_type):
        self.log_user()
        response = self.app.get(
            route_path(
                'journal_{}'.format(feed_type)),
            status=200)

        assert response.content_type == content_type

    def test_toggle_following_repository(self, backend):
        user = self.log_user()
        repo = Repository.get_by_repo_name(backend.repo_name)
        repo_id = repo.repo_id
        self.app.post(
            route_path('toggle_following'), {'follows_repo_id': repo_id,
                                             'csrf_token': self.csrf_token})

        followings = UserFollowing.query()\
            .filter(UserFollowing.user_id == user['user_id'])\
            .filter(UserFollowing.follows_repo_id == repo_id).all()

        assert len(followings) == 0

        self.app.post(
            route_path('toggle_following'), {'follows_repo_id': repo_id,
                                             'csrf_token': self.csrf_token})

        followings = UserFollowing.query()\
            .filter(UserFollowing.user_id == user['user_id'])\
            .filter(UserFollowing.follows_repo_id == repo_id).all()

        assert len(followings) == 1

    @pytest.mark.parametrize("feed_type, content_type", [
        ('rss', "application/rss+xml"),
        ('atom', "application/atom+xml")
    ])
    def test_public_journal_feed(self, feed_type, content_type):
        self.log_user()
        response = self.app.get(
            route_path(
                'journal_public_{}'.format(feed_type)),
            status=200)

        assert response.content_type == content_type
