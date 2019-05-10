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


import logging
import itertools

from webhelpers.feedgenerator import Atom1Feed, Rss201rev2Feed

from pyramid.view import view_config
from pyramid.httpexceptions import HTTPBadRequest
from pyramid.response import Response
from pyramid.renderers import render

from rhodecode.apps._base import BaseAppView
from rhodecode.model.db import (
    or_, joinedload, UserLog, UserFollowing, User, UserApiKeys)
from rhodecode.model.meta import Session
import rhodecode.lib.helpers as h
from rhodecode.lib.helpers import Page
from rhodecode.lib.user_log_filter import user_log_filter
from rhodecode.lib.auth import LoginRequired, NotAnonymous, CSRFRequired
from rhodecode.lib.utils2 import safe_int, AttributeDict, md5_safe
from rhodecode.model.scm import ScmModel

log = logging.getLogger(__name__)


class JournalView(BaseAppView):

    def load_default_context(self):
        c = self._get_local_tmpl_context(include_app_defaults=True)

        self._load_defaults(c.rhodecode_name)

        # TODO(marcink): what is this, why we need a global register ?
        c.search_term = self.request.GET.get('filter') or ''
        return c

    def _get_config(self, rhodecode_name):
        import rhodecode
        config = rhodecode.CONFIG

        return {
            'language': 'en-us',
            'feed_ttl': '5',  # TTL of feed,
            'feed_items_per_page':
                safe_int(config.get('rss_items_per_page', 20)),
            'rhodecode_name': rhodecode_name
        }

    def _load_defaults(self, rhodecode_name):
        config = self._get_config(rhodecode_name)
        # common values for feeds
        self.language = config["language"]
        self.ttl = config["feed_ttl"]
        self.feed_items_per_page = config['feed_items_per_page']
        self.rhodecode_name = config['rhodecode_name']

    def _get_daily_aggregate(self, journal):
        groups = []
        for k, g in itertools.groupby(journal, lambda x: x.action_as_day):
            user_group = []
            # groupby username if it's a present value, else
            # fallback to journal username
            for _, g2 in itertools.groupby(
                    list(g), lambda x: x.user.username if x.user else x.username):
                l = list(g2)
                user_group.append((l[0].user, l))

            groups.append((k, user_group,))

        return groups

    def _get_journal_data(self, following_repos, search_term):
        repo_ids = [x.follows_repository.repo_id for x in following_repos
                    if x.follows_repository is not None]
        user_ids = [x.follows_user.user_id for x in following_repos
                    if x.follows_user is not None]

        filtering_criterion = None

        if repo_ids and user_ids:
            filtering_criterion = or_(UserLog.repository_id.in_(repo_ids),
                                      UserLog.user_id.in_(user_ids))
        if repo_ids and not user_ids:
            filtering_criterion = UserLog.repository_id.in_(repo_ids)
        if not repo_ids and user_ids:
            filtering_criterion = UserLog.user_id.in_(user_ids)
        if filtering_criterion is not None:
            journal = Session().query(UserLog)\
                .options(joinedload(UserLog.user))\
                .options(joinedload(UserLog.repository))
            # filter
            try:
                journal = user_log_filter(journal, search_term)
            except Exception:
                # we want this to crash for now
                raise
            journal = journal.filter(filtering_criterion)\
                .order_by(UserLog.action_date.desc())
        else:
            journal = []

        return journal

    def feed_uid(self, entry_id):
        return '{}:{}'.format('journal', md5_safe(entry_id))

    def _atom_feed(self, repos, search_term, public=True):
        _ = self.request.translate
        journal = self._get_journal_data(repos, search_term)
        if public:
            _link = h.route_url('journal_public_atom')
            _desc = '%s %s %s' % (self.rhodecode_name, _('public journal'),
                                  'atom feed')
        else:
            _link = h.route_url('journal_atom')
            _desc = '%s %s %s' % (self.rhodecode_name, _('journal'), 'atom feed')

        feed = Atom1Feed(
            title=_desc, link=_link, description=_desc,
            language=self.language, ttl=self.ttl)

        for entry in journal[:self.feed_items_per_page]:
            user = entry.user
            if user is None:
                # fix deleted users
                user = AttributeDict({'short_contact': entry.username,
                                      'email': '',
                                      'full_contact': ''})
            action, action_extra, ico = h.action_parser(
                self.request, entry, feed=True)
            title = "%s - %s %s" % (user.short_contact, action(),
                                    entry.repository.repo_name)
            desc = action_extra()
            _url = h.route_url('home')
            if entry.repository is not None:
                _url = h.route_url('repo_changelog',
                                   repo_name=entry.repository.repo_name)

            feed.add_item(
                unique_id=self.feed_uid(entry.user_log_id),
                title=title,
                pubdate=entry.action_date,
                link=_url,
                author_email=user.email,
                author_name=user.full_contact,
                description=desc)

        response = Response(feed.writeString('utf-8'))
        response.content_type = feed.mime_type
        return response

    def _rss_feed(self, repos, search_term, public=True):
        _ = self.request.translate
        journal = self._get_journal_data(repos, search_term)
        if public:
            _link = h.route_url('journal_public_atom')
            _desc = '%s %s %s' % (
                self.rhodecode_name, _('public journal'), 'rss feed')
        else:
            _link = h.route_url('journal_atom')
            _desc = '%s %s %s' % (
                self.rhodecode_name, _('journal'), 'rss feed')

        feed = Rss201rev2Feed(
            title=_desc, link=_link, description=_desc,
            language=self.language, ttl=self.ttl)

        for entry in journal[:self.feed_items_per_page]:
            user = entry.user
            if user is None:
                # fix deleted users
                user = AttributeDict({'short_contact': entry.username,
                                      'email': '',
                                      'full_contact': ''})
            action, action_extra, ico = h.action_parser(
                self.request, entry, feed=True)
            title = "%s - %s %s" % (user.short_contact, action(),
                                    entry.repository.repo_name)
            desc = action_extra()
            _url = h.route_url('home')
            if entry.repository is not None:
                _url = h.route_url('repo_changelog',
                                   repo_name=entry.repository.repo_name)

            feed.add_item(
                unique_id=self.feed_uid(entry.user_log_id),
                title=title,
                pubdate=entry.action_date,
                link=_url,
                author_email=user.email,
                author_name=user.full_contact,
                description=desc)

        response = Response(feed.writeString('utf-8'))
        response.content_type = feed.mime_type
        return response

    @LoginRequired()
    @NotAnonymous()
    @view_config(
        route_name='journal', request_method='GET',
        renderer=None)
    def journal(self):
        c = self.load_default_context()

        p = safe_int(self.request.GET.get('page', 1), 1)
        c.user = User.get(self._rhodecode_user.user_id)
        following = Session().query(UserFollowing)\
            .filter(UserFollowing.user_id == self._rhodecode_user.user_id)\
            .options(joinedload(UserFollowing.follows_repository))\
            .all()

        journal = self._get_journal_data(following, c.search_term)

        def url_generator(**kw):
            query_params = {
                'filter': c.search_term
            }
            query_params.update(kw)
            return self.request.current_route_path(_query=query_params)

        c.journal_pager = Page(
            journal, page=p, items_per_page=20, url=url_generator)
        c.journal_day_aggreagate = self._get_daily_aggregate(c.journal_pager)

        c.journal_data = render(
            'rhodecode:templates/journal/journal_data.mako',
            self._get_template_context(c), self.request)

        if self.request.is_xhr:
            return Response(c.journal_data)

        html = render(
            'rhodecode:templates/journal/journal.mako',
            self._get_template_context(c), self.request)
        return Response(html)

    @LoginRequired(auth_token_access=[UserApiKeys.ROLE_FEED])
    @NotAnonymous()
    @view_config(
        route_name='journal_atom', request_method='GET',
        renderer=None)
    def journal_atom(self):
        """
        Produce an atom-1.0 feed via feedgenerator module
        """
        c = self.load_default_context()
        following_repos = Session().query(UserFollowing)\
            .filter(UserFollowing.user_id == self._rhodecode_user.user_id)\
            .options(joinedload(UserFollowing.follows_repository))\
            .all()
        return self._atom_feed(following_repos, c.search_term, public=False)

    @LoginRequired(auth_token_access=[UserApiKeys.ROLE_FEED])
    @NotAnonymous()
    @view_config(
        route_name='journal_rss', request_method='GET',
        renderer=None)
    def journal_rss(self):
        """
        Produce an rss feed via feedgenerator module
        """
        c = self.load_default_context()
        following_repos = Session().query(UserFollowing)\
            .filter(UserFollowing.user_id == self._rhodecode_user.user_id)\
            .options(joinedload(UserFollowing.follows_repository))\
            .all()
        return self._rss_feed(following_repos, c.search_term, public=False)

    @LoginRequired()
    @NotAnonymous()
    @CSRFRequired()
    @view_config(
        route_name='toggle_following', request_method='POST',
        renderer='json_ext')
    def toggle_following(self):
        user_id = self.request.POST.get('follows_user_id')
        if user_id:
            try:
                ScmModel().toggle_following_user(user_id, self._rhodecode_user.user_id)
                Session().commit()
                return 'ok'
            except Exception:
                raise HTTPBadRequest()

        repo_id = self.request.POST.get('follows_repo_id')
        if repo_id:
            try:
                ScmModel().toggle_following_repo(repo_id, self._rhodecode_user.user_id)
                Session().commit()
                return 'ok'
            except Exception:
                raise HTTPBadRequest()

        raise HTTPBadRequest()

    @LoginRequired()
    @view_config(
        route_name='journal_public', request_method='GET',
        renderer=None)
    def journal_public(self):
        c = self.load_default_context()
        # Return a rendered template
        p = safe_int(self.request.GET.get('page', 1), 1)

        c.following = Session().query(UserFollowing)\
            .filter(UserFollowing.user_id == self._rhodecode_user.user_id)\
            .options(joinedload(UserFollowing.follows_repository))\
            .all()

        journal = self._get_journal_data(c.following, c.search_term)

        def url_generator(**kw):
            query_params = {}
            query_params.update(kw)
            return self.request.current_route_path(_query=query_params)

        c.journal_pager = Page(
            journal, page=p, items_per_page=20, url=url_generator)
        c.journal_day_aggreagate = self._get_daily_aggregate(c.journal_pager)

        c.journal_data = render(
            'rhodecode:templates/journal/journal_data.mako',
            self._get_template_context(c), self.request)

        if self.request.is_xhr:
            return Response(c.journal_data)

        html = render(
            'rhodecode:templates/journal/public_journal.mako',
            self._get_template_context(c), self.request)
        return Response(html)

    @LoginRequired(auth_token_access=[UserApiKeys.ROLE_FEED])
    @view_config(
        route_name='journal_public_atom', request_method='GET',
        renderer=None)
    def journal_public_atom(self):
        """
        Produce an atom-1.0 feed via feedgenerator module
        """
        c = self.load_default_context()
        following_repos = Session().query(UserFollowing)\
            .filter(UserFollowing.user_id == self._rhodecode_user.user_id)\
            .options(joinedload(UserFollowing.follows_repository))\
            .all()

        return self._atom_feed(following_repos, c.search_term)

    @LoginRequired(auth_token_access=[UserApiKeys.ROLE_FEED])
    @view_config(
        route_name='journal_public_rss', request_method='GET',
        renderer=None)
    def journal_public_rss(self):
        """
        Produce an rss2 feed via feedgenerator module
        """
        c = self.load_default_context()
        following_repos = Session().query(UserFollowing)\
            .filter(UserFollowing.user_id == self._rhodecode_user.user_id)\
            .options(joinedload(UserFollowing.follows_repository))\
            .all()

        return self._rss_feed(following_repos, c.search_term)
