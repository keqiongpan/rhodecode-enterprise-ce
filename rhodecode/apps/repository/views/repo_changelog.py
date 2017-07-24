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


import logging

from pyramid.httpexceptions import HTTPNotFound, HTTPFound
from pyramid.view import view_config
from pyramid.renderers import render
from pyramid.response import Response

from rhodecode.apps._base import RepoAppView
import rhodecode.lib.helpers as h
from rhodecode.lib.auth import (
    LoginRequired, HasRepoPermissionAnyDecorator)

from rhodecode.lib.ext_json import json
from rhodecode.lib.graphmod import _colored, _dagwalker
from rhodecode.lib.helpers import RepoPage
from rhodecode.lib.utils2 import safe_int, safe_str
from rhodecode.lib.vcs.exceptions import (
    RepositoryError, CommitDoesNotExistError,
    CommitError, NodeDoesNotExistError, EmptyRepositoryError)

log = logging.getLogger(__name__)

DEFAULT_CHANGELOG_SIZE = 20


class RepoChangelogView(RepoAppView):

    def _get_commit_or_redirect(self, commit_id, redirect_after=True):
        """
        This is a safe way to get commit. If an error occurs it redirects to
        tip with proper message

        :param commit_id: id of commit to fetch
        :param redirect_after: toggle redirection
        """
        _ = self.request.translate

        try:
            return self.rhodecode_vcs_repo.get_commit(commit_id)
        except EmptyRepositoryError:
            if not redirect_after:
                return None

            h.flash(h.literal(
                _('There are no commits yet')), category='warning')
            raise HTTPFound(
                h.route_path('repo_summary', repo_name=self.db_repo_name))

        except (CommitDoesNotExistError, LookupError):
            msg = _('No such commit exists for this repository')
            h.flash(msg, category='error')
            raise HTTPNotFound()
        except RepositoryError as e:
            h.flash(safe_str(h.escape(e)), category='error')
            raise HTTPNotFound()

    def _graph(self, repo, commits, prev_data=None, next_data=None):
        """
        Generates a DAG graph for repo

        :param repo: repo instance
        :param commits: list of commits
        """
        if not commits:
            return json.dumps([])

        def serialize(commit, parents=True):
            data = dict(
                raw_id=commit.raw_id,
                idx=commit.idx,
                branch=commit.branch,
            )
            if parents:
                data['parents'] = [
                    serialize(x, parents=False) for x in commit.parents]
            return data

        prev_data = prev_data or []
        next_data = next_data or []

        current = [serialize(x) for x in commits]
        commits = prev_data + current + next_data

        dag = _dagwalker(repo, commits)

        data = [[commit_id, vtx, edges, branch]
                for commit_id, vtx, edges, branch in _colored(dag)]
        return json.dumps(data), json.dumps(current)

    def _check_if_valid_branch(self, branch_name, repo_name, f_path):
        if branch_name not in self.rhodecode_vcs_repo.branches_all:
            h.flash('Branch {} is not found.'.format(h.escape(branch_name)),
                    category='warning')
            redirect_url = h.route_path(
                'repo_changelog_file', repo_name=repo_name,
                commit_id=branch_name, f_path=f_path or '')
            raise HTTPFound(redirect_url)

    def _load_changelog_data(
            self, c, collection, page, chunk_size, branch_name=None,
            dynamic=False):

        def url_generator(**kw):
            query_params = {}
            query_params.update(kw)
            return h.route_path(
                'repo_changelog',
                repo_name=c.rhodecode_db_repo.repo_name, _query=query_params)

        c.total_cs = len(collection)
        c.showing_commits = min(chunk_size, c.total_cs)
        c.pagination = RepoPage(collection, page=page, item_count=c.total_cs,
                                items_per_page=chunk_size, branch=branch_name,
                                url=url_generator)

        c.next_page = c.pagination.next_page
        c.prev_page = c.pagination.previous_page

        if dynamic:
            if self.request.GET.get('chunk') != 'next':
                c.next_page = None
            if self.request.GET.get('chunk') != 'prev':
                c.prev_page = None

        page_commit_ids = [x.raw_id for x in c.pagination]
        c.comments = c.rhodecode_db_repo.get_comments(page_commit_ids)
        c.statuses = c.rhodecode_db_repo.statuses(page_commit_ids)

    def load_default_context(self):
        c = self._get_local_tmpl_context(include_app_defaults=True)

        # TODO(marcink): remove repo_info and use c.rhodecode_db_repo instead
        c.repo_info = self.db_repo
        c.rhodecode_repo = self.rhodecode_vcs_repo

        self._register_global_c(c)
        return c

    @LoginRequired()
    @HasRepoPermissionAnyDecorator(
        'repository.read', 'repository.write', 'repository.admin')
    @view_config(
        route_name='repo_changelog', request_method='GET',
        renderer='rhodecode:templates/changelog/changelog.mako')
    @view_config(
        route_name='repo_changelog_file', request_method='GET',
        renderer='rhodecode:templates/changelog/changelog.mako')
    def repo_changelog(self):
        c = self.load_default_context()

        commit_id = self.request.matchdict.get('commit_id')
        f_path = self._get_f_path(self.request.matchdict)

        chunk_size = 20

        c.branch_name = branch_name = self.request.GET.get('branch') or ''
        c.book_name = book_name = self.request.GET.get('bookmark') or ''
        hist_limit = safe_int(self.request.GET.get('limit')) or None

        p = safe_int(self.request.GET.get('page', 1), 1)

        c.selected_name = branch_name or book_name
        if not commit_id and branch_name:
            self._check_if_valid_branch(branch_name, self.db_repo_name, f_path)

        c.changelog_for_path = f_path
        pre_load = ['author', 'branch', 'date', 'message', 'parents']
        commit_ids = []

        partial_xhr = self.request.environ.get('HTTP_X_PARTIAL_XHR')

        try:
            if f_path:
                log.debug('generating changelog for path %s', f_path)
                # get the history for the file !
                base_commit = self.rhodecode_vcs_repo.get_commit(commit_id)
                try:
                    collection = base_commit.get_file_history(
                        f_path, limit=hist_limit, pre_load=pre_load)
                    if collection and partial_xhr:
                        # for ajax call we remove first one since we're looking
                        # at it right now in the context of a file commit
                        collection.pop(0)
                except (NodeDoesNotExistError, CommitError):
                    # this node is not present at tip!
                    try:
                        commit = self._get_commit_or_redirect(commit_id)
                        collection = commit.get_file_history(f_path)
                    except RepositoryError as e:
                        h.flash(safe_str(e), category='warning')
                        redirect_url = h.route_path(
                            'repo_changelog', repo_name=self.db_repo_name)
                        raise HTTPFound(redirect_url)
                collection = list(reversed(collection))
            else:
                collection = self.rhodecode_vcs_repo.get_commits(
                    branch_name=branch_name, pre_load=pre_load)

            self._load_changelog_data(
                c, collection, p, chunk_size, c.branch_name, dynamic=f_path)

        except EmptyRepositoryError as e:
            h.flash(safe_str(h.escape(e)), category='warning')
            raise HTTPFound(
                h.route_path('repo_summary', repo_name=self.db_repo_name))
        except (RepositoryError, CommitDoesNotExistError, Exception) as e:
            log.exception(safe_str(e))
            h.flash(safe_str(h.escape(e)), category='error')
            raise HTTPFound(
                h.route_path('repo_changelog', repo_name=self.db_repo_name))

        if partial_xhr or self.request.environ.get('HTTP_X_PJAX'):
            # loading from ajax, we don't want the first result, it's popped
            # in the code above
            html = render(
                'rhodecode:templates/changelog/changelog_file_history.mako',
                self._get_template_context(c), self.request)
            return Response(html)

        if not f_path:
            commit_ids = c.pagination

        c.graph_data, c.graph_commits = self._graph(
            self.rhodecode_vcs_repo, commit_ids)

        return self._get_template_context(c)

    @LoginRequired()
    @HasRepoPermissionAnyDecorator(
        'repository.read', 'repository.write', 'repository.admin')
    @view_config(
        route_name='repo_changelog_elements', request_method=('GET', 'POST'),
        renderer='rhodecode:templates/changelog/changelog_elements.mako',
        xhr=True)
    def repo_changelog_elements(self):
        c = self.load_default_context()
        chunk_size = 20

        def wrap_for_error(err):
            html = '<tr>' \
                   '<td colspan="9" class="alert alert-error">ERROR: {}</td>' \
                   '</tr>'.format(err)
            return Response(html)

        c.branch_name = branch_name = self.request.GET.get('branch') or ''
        c.book_name = book_name = self.request.GET.get('bookmark') or ''

        c.selected_name = branch_name or book_name
        if branch_name and branch_name not in self.rhodecode_vcs_repo.branches_all:
            return wrap_for_error(
                safe_str('Branch: {} is not valid'.format(branch_name)))

        pre_load = ['author', 'branch', 'date', 'message', 'parents']
        collection = self.rhodecode_vcs_repo.get_commits(
            branch_name=branch_name, pre_load=pre_load)

        p = safe_int(self.request.GET.get('page', 1), 1)
        try:
            self._load_changelog_data(
                c, collection, p, chunk_size, dynamic=True)
        except EmptyRepositoryError as e:
            return wrap_for_error(safe_str(e))
        except (RepositoryError, CommitDoesNotExistError, Exception) as e:
            log.exception('Failed to fetch commits')
            return wrap_for_error(safe_str(e))

        prev_data = None
        next_data = None

        prev_graph = json.loads(self.request.POST.get('graph', ''))

        if self.request.GET.get('chunk') == 'prev':
            next_data = prev_graph
        elif self.request.GET.get('chunk') == 'next':
            prev_data = prev_graph

        c.graph_data, c.graph_commits = self._graph(
            self.rhodecode_vcs_repo, c.pagination,
            prev_data=prev_data, next_data=next_data)

        return self._get_template_context(c)