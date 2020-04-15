# -*- coding: utf-8 -*-

# Copyright (C) 2011-2020 RhodeCode GmbH
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
import string
import time

import rhodecode

from pyramid.view import view_config

from rhodecode.lib.view_utils import get_format_ref_id
from rhodecode.apps._base import RepoAppView
from rhodecode.config.conf import (LANGUAGES_EXTENSIONS_MAP)
from rhodecode.lib import helpers as h, rc_cache
from rhodecode.lib.utils2 import safe_str, safe_int
from rhodecode.lib.auth import LoginRequired, HasRepoPermissionAnyDecorator
from rhodecode.lib.ext_json import json
from rhodecode.lib.vcs.backends.base import EmptyCommit
from rhodecode.lib.vcs.exceptions import (
    CommitError, EmptyRepositoryError, CommitDoesNotExistError)
from rhodecode.model.db import Statistics, CacheKey, User
from rhodecode.model.meta import Session
from rhodecode.model.scm import ScmModel

log = logging.getLogger(__name__)


class RepoSummaryView(RepoAppView):

    def load_default_context(self):
        c = self._get_local_tmpl_context(include_app_defaults=True)
        c.rhodecode_repo = None
        if not c.repository_requirements_missing:
            c.rhodecode_repo = self.rhodecode_vcs_repo
        return c

    def _load_commits_context(self, c):
        p = safe_int(self.request.GET.get('page'), 1)
        size = safe_int(self.request.GET.get('size'), 10)

        def url_generator(page_num):
            query_params = {
                'page': page_num,
                'size': size
            }
            return h.route_path(
                'repo_summary_commits',
                repo_name=c.rhodecode_db_repo.repo_name, _query=query_params)

        pre_load = ['author', 'branch', 'date', 'message']
        try:
            collection = self.rhodecode_vcs_repo.get_commits(
                pre_load=pre_load, translate_tags=False)
        except EmptyRepositoryError:
            collection = self.rhodecode_vcs_repo

        c.repo_commits = h.RepoPage(
            collection, page=p, items_per_page=size, url_maker=url_generator)
        page_ids = [x.raw_id for x in c.repo_commits]
        c.comments = self.db_repo.get_comments(page_ids)
        c.statuses = self.db_repo.statuses(page_ids)

    def _prepare_and_set_clone_url(self, c):
        username = ''
        if self._rhodecode_user.username != User.DEFAULT_USER:
            username = safe_str(self._rhodecode_user.username)

        _def_clone_uri = _def_clone_uri_id = c.clone_uri_tmpl
        _def_clone_uri_ssh = c.clone_uri_ssh_tmpl

        if '{repo}' in _def_clone_uri:
            _def_clone_uri_id = _def_clone_uri.replace('{repo}', '_{repoid}')
        elif '{repoid}' in _def_clone_uri:
            _def_clone_uri_id = _def_clone_uri.replace('_{repoid}', '{repo}')

        c.clone_repo_url = self.db_repo.clone_url(
            user=username, uri_tmpl=_def_clone_uri)
        c.clone_repo_url_id = self.db_repo.clone_url(
            user=username, uri_tmpl=_def_clone_uri_id)
        c.clone_repo_url_ssh = self.db_repo.clone_url(
            uri_tmpl=_def_clone_uri_ssh, ssh=True)

    @LoginRequired()
    @HasRepoPermissionAnyDecorator(
        'repository.read', 'repository.write', 'repository.admin')
    @view_config(
        route_name='repo_summary_commits', request_method='GET',
        renderer='rhodecode:templates/summary/summary_commits.mako')
    def summary_commits(self):
        c = self.load_default_context()
        self._prepare_and_set_clone_url(c)
        self._load_commits_context(c)
        return self._get_template_context(c)

    @LoginRequired()
    @HasRepoPermissionAnyDecorator(
        'repository.read', 'repository.write', 'repository.admin')
    @view_config(
        route_name='repo_summary', request_method='GET',
        renderer='rhodecode:templates/summary/summary.mako')
    @view_config(
        route_name='repo_summary_slash', request_method='GET',
        renderer='rhodecode:templates/summary/summary.mako')
    @view_config(
        route_name='repo_summary_explicit', request_method='GET',
        renderer='rhodecode:templates/summary/summary.mako')
    def summary(self):
        c = self.load_default_context()

        # Prepare the clone URL
        self._prepare_and_set_clone_url(c)

        # If enabled, get statistics data
        c.show_stats = bool(self.db_repo.enable_statistics)

        stats = Session().query(Statistics) \
            .filter(Statistics.repository == self.db_repo) \
            .scalar()

        c.stats_percentage = 0

        if stats and stats.languages:
            c.no_data = False is self.db_repo.enable_statistics
            lang_stats_d = json.loads(stats.languages)

            # Sort first by decreasing count and second by the file extension,
            # so we have a consistent output.
            lang_stats_items = sorted(lang_stats_d.iteritems(),
                                      key=lambda k: (-k[1], k[0]))[:10]
            lang_stats = [(x, {"count": y,
                               "desc": LANGUAGES_EXTENSIONS_MAP.get(x)})
                          for x, y in lang_stats_items]

            c.trending_languages = json.dumps(lang_stats)
        else:
            c.no_data = True
            c.trending_languages = json.dumps({})

        scm_model = ScmModel()
        c.enable_downloads = self.db_repo.enable_downloads
        c.repository_followers = scm_model.get_followers(self.db_repo)
        c.repository_forks = scm_model.get_forks(self.db_repo)

        # first interaction with the VCS instance after here...
        if c.repository_requirements_missing:
            self.request.override_renderer = \
                'rhodecode:templates/summary/missing_requirements.mako'
            return self._get_template_context(c)

        c.readme_data, c.readme_file = \
            self._get_readme_data(self.db_repo, c.visual.default_renderer)

        # loads the summary commits template context
        self._load_commits_context(c)

        return self._get_template_context(c)

    @LoginRequired()
    @HasRepoPermissionAnyDecorator(
        'repository.read', 'repository.write', 'repository.admin')
    @view_config(
        route_name='repo_stats', request_method='GET',
        renderer='json_ext')
    def repo_stats(self):
        show_stats = bool(self.db_repo.enable_statistics)
        repo_id = self.db_repo.repo_id

        landing_commit = self.db_repo.get_landing_commit()
        if isinstance(landing_commit, EmptyCommit):
            return {'size': 0, 'code_stats': {}}

        cache_seconds = safe_int(rhodecode.CONFIG.get('rc_cache.cache_repo.expiration_time'))
        cache_on = cache_seconds > 0

        log.debug(
            'Computing REPO STATS for repo_id %s commit_id `%s` '
            'with caching: %s[TTL: %ss]' % (
                repo_id, landing_commit, cache_on, cache_seconds or 0))

        cache_namespace_uid = 'cache_repo.{}'.format(repo_id)
        region = rc_cache.get_or_create_region('cache_repo', cache_namespace_uid)

        @region.conditional_cache_on_arguments(namespace=cache_namespace_uid,
                                               condition=cache_on)
        def compute_stats(repo_id, commit_id, _show_stats):
            code_stats = {}
            size = 0
            try:
                commit = self.db_repo.get_commit(commit_id)

                for node in commit.get_filenodes_generator():
                    size += node.size
                    if not _show_stats:
                        continue
                    ext = string.lower(node.extension)
                    ext_info = LANGUAGES_EXTENSIONS_MAP.get(ext)
                    if ext_info:
                        if ext in code_stats:
                            code_stats[ext]['count'] += 1
                        else:
                            code_stats[ext] = {"count": 1, "desc": ext_info}
            except (EmptyRepositoryError, CommitDoesNotExistError):
                pass
            return {'size': h.format_byte_size_binary(size),
                    'code_stats': code_stats}

        stats = compute_stats(self.db_repo.repo_id, landing_commit.raw_id, show_stats)
        return stats

    @LoginRequired()
    @HasRepoPermissionAnyDecorator(
        'repository.read', 'repository.write', 'repository.admin')
    @view_config(
        route_name='repo_refs_data', request_method='GET',
        renderer='json_ext')
    def repo_refs_data(self):
        _ = self.request.translate
        self.load_default_context()

        repo = self.rhodecode_vcs_repo
        refs_to_create = [
            (_("Branch"), repo.branches, 'branch'),
            (_("Tag"), repo.tags, 'tag'),
            (_("Bookmark"), repo.bookmarks, 'book'),
        ]
        res = self._create_reference_data(repo, self.db_repo_name, refs_to_create)
        data = {
            'more': False,
            'results': res
        }
        return data

    @LoginRequired()
    @HasRepoPermissionAnyDecorator(
        'repository.read', 'repository.write', 'repository.admin')
    @view_config(
        route_name='repo_refs_changelog_data', request_method='GET',
        renderer='json_ext')
    def repo_refs_changelog_data(self):
        _ = self.request.translate
        self.load_default_context()

        repo = self.rhodecode_vcs_repo

        refs_to_create = [
            (_("Branches"), repo.branches, 'branch'),
            (_("Closed branches"), repo.branches_closed, 'branch_closed'),
            # TODO: enable when vcs can handle bookmarks filters
            # (_("Bookmarks"), repo.bookmarks, "book"),
        ]
        res = self._create_reference_data(
            repo, self.db_repo_name, refs_to_create)
        data = {
            'more': False,
            'results': res
        }
        return data

    def _create_reference_data(self, repo, full_repo_name, refs_to_create):
        format_ref_id = get_format_ref_id(repo)

        result = []
        for title, refs, ref_type in refs_to_create:
            if refs:
                result.append({
                    'text': title,
                    'children': self._create_reference_items(
                        repo, full_repo_name, refs, ref_type,
                        format_ref_id),
                })
        return result

    def _create_reference_items(self, repo, full_repo_name, refs, ref_type, format_ref_id):
        result = []
        is_svn = h.is_svn(repo)
        for ref_name, raw_id in refs.iteritems():
            files_url = self._create_files_url(
                repo, full_repo_name, ref_name, raw_id, is_svn)
            result.append({
                'text': ref_name,
                'id': format_ref_id(ref_name, raw_id),
                'raw_id': raw_id,
                'type': ref_type,
                'files_url': files_url,
                'idx': 0,
            })
        return result

    def _create_files_url(self, repo, full_repo_name, ref_name, raw_id, is_svn):
        use_commit_id = '/' in ref_name or is_svn
        return h.route_path(
            'repo_files',
            repo_name=full_repo_name,
            f_path=ref_name if is_svn else '',
            commit_id=raw_id if use_commit_id else ref_name,
            _query=dict(at=ref_name))
