# -*- coding: utf-8 -*-

# Copyright (C) 2012-2018 RhodeCode GmbH
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

from pyramid.httpexceptions import HTTPBadRequest, HTTPNotFound, HTTPFound
from pyramid.view import view_config
from pyramid.renderers import render
from pyramid.response import Response

from rhodecode.apps._base import RepoAppView
from rhodecode.controllers.utils import parse_path_ref, get_commit_from_ref_name
from rhodecode.lib import helpers as h
from rhodecode.lib import diffs, codeblocks
from rhodecode.lib.auth import LoginRequired, HasRepoPermissionAnyDecorator
from rhodecode.lib.utils import safe_str
from rhodecode.lib.utils2 import safe_unicode, str2bool
from rhodecode.lib.vcs.exceptions import (
    EmptyRepositoryError, RepositoryError, RepositoryRequirementError,
    NodeDoesNotExistError)
from rhodecode.model.db import Repository, ChangesetStatus

log = logging.getLogger(__name__)


class RepoCompareView(RepoAppView):
    def load_default_context(self):
        c = self._get_local_tmpl_context(include_app_defaults=True)

        c.rhodecode_repo = self.rhodecode_vcs_repo


        return c

    def _get_commit_or_redirect(
            self, ref, ref_type, repo, redirect_after=True, partial=False):
        """
        This is a safe way to get a commit. If an error occurs it
        redirects to a commit with a proper message. If partial is set
        then it does not do redirect raise and throws an exception instead.
        """
        _ = self.request.translate
        try:
            return get_commit_from_ref_name(repo, safe_str(ref), ref_type)
        except EmptyRepositoryError:
            if not redirect_after:
                return repo.scm_instance().EMPTY_COMMIT
            h.flash(h.literal(_('There are no commits yet')),
                    category='warning')
            if not partial:
                raise HTTPFound(
                    h.route_path('repo_summary', repo_name=repo.repo_name))
            raise HTTPBadRequest()

        except RepositoryError as e:
            log.exception(safe_str(e))
            h.flash(safe_str(h.escape(e)), category='warning')
            if not partial:
                raise HTTPFound(
                    h.route_path('repo_summary', repo_name=repo.repo_name))
            raise HTTPBadRequest()

    @LoginRequired()
    @HasRepoPermissionAnyDecorator(
        'repository.read', 'repository.write', 'repository.admin')
    @view_config(
        route_name='repo_compare_select', request_method='GET',
        renderer='rhodecode:templates/compare/compare_diff.mako')
    def compare_select(self):
        _ = self.request.translate
        c = self.load_default_context()

        source_repo = self.db_repo_name
        target_repo = self.request.GET.get('target_repo', source_repo)
        c.source_repo = Repository.get_by_repo_name(source_repo)
        c.target_repo = Repository.get_by_repo_name(target_repo)

        if c.source_repo is None or c.target_repo is None:
            raise HTTPNotFound()

        c.compare_home = True
        c.commit_ranges = []
        c.collapse_all_commits = False
        c.diffset = None
        c.limited_diff = False
        c.source_ref = c.target_ref = _('Select commit')
        c.source_ref_type = ""
        c.target_ref_type = ""
        c.commit_statuses = ChangesetStatus.STATUSES
        c.preview_mode = False
        c.file_path = None

        return self._get_template_context(c)

    @LoginRequired()
    @HasRepoPermissionAnyDecorator(
        'repository.read', 'repository.write', 'repository.admin')
    @view_config(
        route_name='repo_compare', request_method='GET',
        renderer=None)
    def compare(self):
        _ = self.request.translate
        c = self.load_default_context()

        source_ref_type = self.request.matchdict['source_ref_type']
        source_ref = self.request.matchdict['source_ref']
        target_ref_type = self.request.matchdict['target_ref_type']
        target_ref = self.request.matchdict['target_ref']

        # source_ref will be evaluated in source_repo
        source_repo_name = self.db_repo_name
        source_path, source_id = parse_path_ref(source_ref)

        # target_ref will be evaluated in target_repo
        target_repo_name = self.request.GET.get('target_repo', source_repo_name)
        target_path, target_id = parse_path_ref(
            target_ref, default_path=self.request.GET.get('f_path', ''))

        # if merge is True
        #   Show what changes since the shared ancestor commit of target/source
        #   the source would get if it was merged with target. Only commits
        #   which are in target but not in source will be shown.
        merge = str2bool(self.request.GET.get('merge'))
        # if merge is False
        #   Show a raw diff of source/target refs even if no ancestor exists

        # c.fulldiff disables cut_off_limit
        c.fulldiff = str2bool(self.request.GET.get('fulldiff'))

        c.file_path = target_path
        c.commit_statuses = ChangesetStatus.STATUSES

        # if partial, returns just compare_commits.html (commits log)
        partial = self.request.is_xhr

        # swap url for compare_diff page
        c.swap_url = h.route_path(
            'repo_compare',
            repo_name=target_repo_name,
            source_ref_type=target_ref_type,
            source_ref=target_ref,
            target_repo=source_repo_name,
            target_ref_type=source_ref_type,
            target_ref=source_ref,
            _query=dict(merge=merge and '1' or '', f_path=target_path))

        source_repo = Repository.get_by_repo_name(source_repo_name)
        target_repo = Repository.get_by_repo_name(target_repo_name)

        if source_repo is None:
            log.error('Could not find the source repo: {}'
                      .format(source_repo_name))
            h.flash(_('Could not find the source repo: `{}`')
                    .format(h.escape(source_repo_name)), category='error')
            raise HTTPFound(
                h.route_path('repo_compare_select', repo_name=self.db_repo_name))

        if target_repo is None:
            log.error('Could not find the target repo: {}'
                      .format(source_repo_name))
            h.flash(_('Could not find the target repo: `{}`')
                    .format(h.escape(target_repo_name)), category='error')
            raise HTTPFound(
                h.route_path('repo_compare_select', repo_name=self.db_repo_name))

        source_scm = source_repo.scm_instance()
        target_scm = target_repo.scm_instance()

        source_alias = source_scm.alias
        target_alias = target_scm.alias
        if source_alias != target_alias:
            msg = _('The comparison of two different kinds of remote repos '
                    'is not available')
            log.error(msg)
            h.flash(msg, category='error')
            raise HTTPFound(
                h.route_path('repo_compare_select', repo_name=self.db_repo_name))

        source_commit = self._get_commit_or_redirect(
            ref=source_id, ref_type=source_ref_type, repo=source_repo,
            partial=partial)
        target_commit = self._get_commit_or_redirect(
            ref=target_id, ref_type=target_ref_type, repo=target_repo,
            partial=partial)

        c.compare_home = False
        c.source_repo = source_repo
        c.target_repo = target_repo
        c.source_ref = source_ref
        c.target_ref = target_ref
        c.source_ref_type = source_ref_type
        c.target_ref_type = target_ref_type

        pre_load = ["author", "branch", "date", "message"]
        c.ancestor = None

        if c.file_path:
            if source_commit == target_commit:
                c.commit_ranges = []
            else:
                c.commit_ranges = [target_commit]
        else:
            try:
                c.commit_ranges = source_scm.compare(
                    source_commit.raw_id, target_commit.raw_id,
                    target_scm, merge, pre_load=pre_load)
                if merge:
                    c.ancestor = source_scm.get_common_ancestor(
                        source_commit.raw_id, target_commit.raw_id, target_scm)
            except RepositoryRequirementError:
                msg = _('Could not compare repos with different '
                        'large file settings')
                log.error(msg)
                if partial:
                    return Response(msg)
                h.flash(msg, category='error')
                raise HTTPFound(
                    h.route_path('repo_compare_select',
                                 repo_name=self.db_repo_name))

        c.statuses = self.db_repo.statuses(
            [x.raw_id for x in c.commit_ranges])

        # auto collapse if we have more than limit
        collapse_limit = diffs.DiffProcessor._collapse_commits_over
        c.collapse_all_commits = len(c.commit_ranges) > collapse_limit

        if partial:  # for PR ajax commits loader
            if not c.ancestor:
                return Response('')  # cannot merge if there is no ancestor

            html = render(
                'rhodecode:templates/compare/compare_commits.mako',
                self._get_template_context(c), self.request)
            return Response(html)

        if c.ancestor:
            # case we want a simple diff without incoming commits,
            # previewing what will be merged.
            # Make the diff on target repo (which is known to have target_ref)
            log.debug('Using ancestor %s as source_ref instead of %s',
                      c.ancestor, source_ref)
            source_repo = target_repo
            source_commit = target_repo.get_commit(commit_id=c.ancestor)

        # diff_limit will cut off the whole diff if the limit is applied
        # otherwise it will just hide the big files from the front-end
        diff_limit = c.visual.cut_off_limit_diff
        file_limit = c.visual.cut_off_limit_file

        log.debug('calculating diff between '
                  'source_ref:%s and target_ref:%s for repo `%s`',
                  source_commit, target_commit,
                  safe_unicode(source_repo.scm_instance().path))

        if source_commit.repository != target_commit.repository:
            msg = _(
                "Repositories unrelated. "
                "Cannot compare commit %(commit1)s from repository %(repo1)s "
                "with commit %(commit2)s from repository %(repo2)s.") % {
                    'commit1': h.show_id(source_commit),
                    'repo1': source_repo.repo_name,
                    'commit2': h.show_id(target_commit),
                    'repo2': target_repo.repo_name,
                }
            h.flash(msg, category='error')
            raise HTTPFound(
                h.route_path('repo_compare_select',
                             repo_name=self.db_repo_name))

        txt_diff = source_repo.scm_instance().get_diff(
            commit1=source_commit, commit2=target_commit,
            path=target_path, path1=source_path)

        diff_processor = diffs.DiffProcessor(
            txt_diff, format='newdiff', diff_limit=diff_limit,
            file_limit=file_limit, show_full_diff=c.fulldiff)
        _parsed = diff_processor.prepare()

        diffset = codeblocks.DiffSet(
            repo_name=source_repo.repo_name,
            source_node_getter=codeblocks.diffset_node_getter(source_commit),
            target_node_getter=codeblocks.diffset_node_getter(target_commit),
        )
        c.diffset = self.path_filter.render_patchset_filtered(
            diffset, _parsed, source_ref, target_ref)

        c.preview_mode = merge
        c.source_commit = source_commit
        c.target_commit = target_commit

        html = render(
            'rhodecode:templates/compare/compare_diff.mako',
            self._get_template_context(c), self.request)
        return Response(html)