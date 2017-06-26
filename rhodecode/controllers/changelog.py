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
changelog controller for rhodecode
"""

import logging

from pylons import request, url, session, tmpl_context as c
from pylons.controllers.util import redirect
from pylons.i18n.translation import _
from webob.exc import HTTPNotFound, HTTPBadRequest

import rhodecode.lib.helpers as h
from rhodecode.lib.auth import (
    LoginRequired, HasRepoPermissionAnyDecorator, XHRRequired)
from rhodecode.lib.base import BaseRepoController, render
from rhodecode.lib.ext_json import json
from rhodecode.lib.graphmod import _colored, _dagwalker
from rhodecode.lib.helpers import RepoPage
from rhodecode.lib.utils2 import safe_int, safe_str
from rhodecode.lib.vcs.exceptions import (
    RepositoryError, CommitDoesNotExistError,
    CommitError, NodeDoesNotExistError, EmptyRepositoryError)

log = logging.getLogger(__name__)

DEFAULT_CHANGELOG_SIZE = 20


class ChangelogController(BaseRepoController):

    def __before__(self):
        super(ChangelogController, self).__before__()
        c.affected_files_cut_off = 60

    def __get_commit_or_redirect(
            self, commit_id, repo, redirect_after=True, partial=False):
        """
        This is a safe way to get a commit. If an error occurs it
        redirects to a commit with a proper message. If partial is set
        then it does not do redirect raise and throws an exception instead.

        :param commit_id: commit to fetch
        :param repo: repo instance
        """
        try:
            return c.rhodecode_repo.get_commit(commit_id)
        except EmptyRepositoryError:
            if not redirect_after:
                return None
            h.flash(_('There are no commits yet'), category='warning')
            redirect(url('changelog_home', repo_name=repo.repo_name))
        except RepositoryError as e:
            log.exception(safe_str(e))
            h.flash(safe_str(h.escape(e)), category='warning')
            if not partial:
                redirect(h.url('changelog_home', repo_name=repo.repo_name))
            raise HTTPBadRequest()

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
        if branch_name not in c.rhodecode_repo.branches_all:
            h.flash('Branch {} is not found.'.format(h.escape(branch_name)),
                    category='warning')
            redirect(url('changelog_file_home', repo_name=repo_name,
                         revision=branch_name, f_path=f_path or ''))

    def _load_changelog_data(self, collection, page, chunk_size, branch_name=None, dynamic=False):
        c.total_cs = len(collection)
        c.showing_commits = min(chunk_size, c.total_cs)
        c.pagination = RepoPage(collection, page=page, item_count=c.total_cs,
                                items_per_page=chunk_size, branch=branch_name)

        c.next_page = c.pagination.next_page
        c.prev_page = c.pagination.previous_page

        if dynamic:
            if request.GET.get('chunk') != 'next':
                c.next_page = None
            if request.GET.get('chunk') != 'prev':
                c.prev_page = None

        page_commit_ids = [x.raw_id for x in c.pagination]
        c.comments = c.rhodecode_db_repo.get_comments(page_commit_ids)
        c.statuses = c.rhodecode_db_repo.statuses(page_commit_ids)

    @LoginRequired()
    @HasRepoPermissionAnyDecorator('repository.read', 'repository.write',
                                   'repository.admin')
    def index(self, repo_name, revision=None, f_path=None):
        commit_id = revision
        chunk_size = 20

        c.branch_name = branch_name = request.GET.get('branch', None)
        c.book_name = book_name = request.GET.get('bookmark', None)
        hist_limit = safe_int(request.GET.get('limit')) or None

        p = safe_int(request.GET.get('page', 1), 1)

        c.selected_name = branch_name or book_name
        if not commit_id and branch_name:
            self._check_if_valid_branch(branch_name, repo_name, f_path)

        c.changelog_for_path = f_path
        pre_load = ['author', 'branch', 'date', 'message', 'parents']
        commit_ids = []

        try:
            if f_path:
                log.debug('generating changelog for path %s', f_path)
                # get the history for the file !
                base_commit = c.rhodecode_repo.get_commit(revision)
                try:
                    collection = base_commit.get_file_history(
                        f_path, limit=hist_limit, pre_load=pre_load)
                    if (collection
                            and request.environ.get('HTTP_X_PARTIAL_XHR')):
                        # for ajax call we remove first one since we're looking
                        # at it right now in the context of a file commit
                        collection.pop(0)
                except (NodeDoesNotExistError, CommitError):
                    # this node is not present at tip!
                    try:
                        commit = self.__get_commit_or_redirect(
                            commit_id, repo_name)
                        collection = commit.get_file_history(f_path)
                    except RepositoryError as e:
                        h.flash(safe_str(e), category='warning')
                        redirect(h.url('changelog_home', repo_name=repo_name))
                collection = list(reversed(collection))
            else:
                collection = c.rhodecode_repo.get_commits(
                    branch_name=branch_name, pre_load=pre_load)

            self._load_changelog_data(
                collection, p, chunk_size, c.branch_name, dynamic=f_path)

        except EmptyRepositoryError as e:
            h.flash(safe_str(h.escape(e)), category='warning')
            return redirect(h.route_path('repo_summary', repo_name=repo_name))
        except (RepositoryError, CommitDoesNotExistError, Exception) as e:
            log.exception(safe_str(e))
            h.flash(safe_str(h.escape(e)), category='error')
            return redirect(url('changelog_home', repo_name=repo_name))

        if (request.environ.get('HTTP_X_PARTIAL_XHR')
                or request.environ.get('HTTP_X_PJAX')):
            # loading from ajax, we don't want the first result, it's popped
            return render('changelog/changelog_file_history.mako')

        if not f_path:
            commit_ids = c.pagination

        c.graph_data, c.graph_commits = self._graph(
            c.rhodecode_repo, commit_ids)

        return render('changelog/changelog.mako')

    @LoginRequired()
    @XHRRequired()
    @HasRepoPermissionAnyDecorator(
        'repository.read', 'repository.write', 'repository.admin')
    def changelog_elements(self, repo_name):
        commit_id = None
        chunk_size = 20

        def wrap_for_error(err):
            return '<tr><td colspan="9" class="alert alert-error">ERROR: {}</td></tr>'.format(err)

        c.branch_name = branch_name = request.GET.get('branch', None)
        c.book_name = book_name = request.GET.get('bookmark', None)

        p = safe_int(request.GET.get('page', 1), 1)

        c.selected_name = branch_name or book_name
        if not commit_id and branch_name:
            if branch_name not in c.rhodecode_repo.branches_all:
                return wrap_for_error(
                    safe_str('Missing branch: {}'.format(branch_name)))

        pre_load = ['author', 'branch', 'date', 'message', 'parents']
        collection = c.rhodecode_repo.get_commits(
            branch_name=branch_name, pre_load=pre_load)

        try:
            self._load_changelog_data(collection, p, chunk_size, dynamic=True)
        except EmptyRepositoryError as e:
            return wrap_for_error(safe_str(e))
        except (RepositoryError, CommitDoesNotExistError, Exception) as e:
            log.exception('Failed to fetch commits')
            return wrap_for_error(safe_str(e))

        prev_data = None
        next_data = None

        prev_graph = json.loads(request.POST.get('graph', ''))

        if request.GET.get('chunk') == 'prev':
            next_data = prev_graph
        elif request.GET.get('chunk') == 'next':
            prev_data = prev_graph

        c.graph_data, c.graph_commits = self._graph(
            c.rhodecode_repo, c.pagination,
            prev_data=prev_data, next_data=next_data)
        return render('changelog/changelog_elements.mako')
