# -*- coding: utf-8 -*-

# Copyright (C) 2011-2017 RhodeCode GmbH
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

import collections
from pyramid.httpexceptions import HTTPFound, HTTPNotFound
from pyramid.view import view_config

from rhodecode.apps._base import RepoAppView, DataGridAppView
from rhodecode.lib import helpers as h, diffs, codeblocks
from rhodecode.lib.auth import (
    LoginRequired, HasRepoPermissionAnyDecorator)
from rhodecode.lib.utils2 import str2bool, safe_int, safe_str
from rhodecode.lib.vcs.backends.base import EmptyCommit
from rhodecode.lib.vcs.exceptions import CommitDoesNotExistError, \
    RepositoryRequirementError, NodeDoesNotExistError
from rhodecode.model.comment import CommentsModel
from rhodecode.model.db import PullRequest, PullRequestVersion, \
    ChangesetComment, ChangesetStatus
from rhodecode.model.pull_request import PullRequestModel, MergeCheck

log = logging.getLogger(__name__)


class RepoPullRequestsView(RepoAppView, DataGridAppView):

    def load_default_context(self):
        c = self._get_local_tmpl_context(include_app_defaults=True)
        # TODO(marcink): remove repo_info and use c.rhodecode_db_repo instead
        c.repo_info = self.db_repo
        c.REVIEW_STATUS_APPROVED = ChangesetStatus.STATUS_APPROVED
        c.REVIEW_STATUS_REJECTED = ChangesetStatus.STATUS_REJECTED
        self._register_global_c(c)
        return c

    def _get_pull_requests_list(
            self, repo_name, source, filter_type, opened_by, statuses):

        draw, start, limit = self._extract_chunk(self.request)
        search_q, order_by, order_dir = self._extract_ordering(self.request)
        _render = self.request.get_partial_renderer(
            'data_table/_dt_elements.mako')

        # pagination

        if filter_type == 'awaiting_review':
            pull_requests = PullRequestModel().get_awaiting_review(
                repo_name, source=source, opened_by=opened_by,
                statuses=statuses, offset=start, length=limit,
                order_by=order_by, order_dir=order_dir)
            pull_requests_total_count = PullRequestModel().count_awaiting_review(
                repo_name, source=source, statuses=statuses,
                opened_by=opened_by)
        elif filter_type == 'awaiting_my_review':
            pull_requests = PullRequestModel().get_awaiting_my_review(
                repo_name, source=source, opened_by=opened_by,
                user_id=self._rhodecode_user.user_id, statuses=statuses,
                offset=start, length=limit, order_by=order_by,
                order_dir=order_dir)
            pull_requests_total_count = PullRequestModel().count_awaiting_my_review(
                repo_name, source=source, user_id=self._rhodecode_user.user_id,
                statuses=statuses, opened_by=opened_by)
        else:
            pull_requests = PullRequestModel().get_all(
                repo_name, source=source, opened_by=opened_by,
                statuses=statuses, offset=start, length=limit,
                order_by=order_by, order_dir=order_dir)
            pull_requests_total_count = PullRequestModel().count_all(
                repo_name, source=source, statuses=statuses,
                opened_by=opened_by)

        data = []
        comments_model = CommentsModel()
        for pr in pull_requests:
            comments = comments_model.get_all_comments(
                self.db_repo.repo_id, pull_request=pr)

            data.append({
                'name': _render('pullrequest_name',
                                pr.pull_request_id, pr.target_repo.repo_name),
                'name_raw': pr.pull_request_id,
                'status': _render('pullrequest_status',
                                  pr.calculated_review_status()),
                'title': _render(
                    'pullrequest_title', pr.title, pr.description),
                'description': h.escape(pr.description),
                'updated_on': _render('pullrequest_updated_on',
                                      h.datetime_to_time(pr.updated_on)),
                'updated_on_raw': h.datetime_to_time(pr.updated_on),
                'created_on': _render('pullrequest_updated_on',
                                      h.datetime_to_time(pr.created_on)),
                'created_on_raw': h.datetime_to_time(pr.created_on),
                'author': _render('pullrequest_author',
                                  pr.author.full_contact, ),
                'author_raw': pr.author.full_name,
                'comments': _render('pullrequest_comments', len(comments)),
                'comments_raw': len(comments),
                'closed': pr.is_closed(),
            })

        data = ({
            'draw': draw,
            'data': data,
            'recordsTotal': pull_requests_total_count,
            'recordsFiltered': pull_requests_total_count,
        })
        return data

    @LoginRequired()
    @HasRepoPermissionAnyDecorator(
        'repository.read', 'repository.write', 'repository.admin')
    @view_config(
        route_name='pullrequest_show_all', request_method='GET',
        renderer='rhodecode:templates/pullrequests/pullrequests.mako')
    def pull_request_list(self):
        c = self.load_default_context()

        req_get = self.request.GET
        c.source = str2bool(req_get.get('source'))
        c.closed = str2bool(req_get.get('closed'))
        c.my = str2bool(req_get.get('my'))
        c.awaiting_review = str2bool(req_get.get('awaiting_review'))
        c.awaiting_my_review = str2bool(req_get.get('awaiting_my_review'))

        c.active = 'open'
        if c.my:
            c.active = 'my'
        if c.closed:
            c.active = 'closed'
        if c.awaiting_review and not c.source:
            c.active = 'awaiting'
        if c.source and not c.awaiting_review:
            c.active = 'source'
        if c.awaiting_my_review:
            c.active = 'awaiting_my'

        return self._get_template_context(c)

    @LoginRequired()
    @HasRepoPermissionAnyDecorator(
        'repository.read', 'repository.write', 'repository.admin')
    @view_config(
        route_name='pullrequest_show_all_data', request_method='GET',
        renderer='json_ext', xhr=True)
    def pull_request_list_data(self):

        # additional filters
        req_get = self.request.GET
        source = str2bool(req_get.get('source'))
        closed = str2bool(req_get.get('closed'))
        my = str2bool(req_get.get('my'))
        awaiting_review = str2bool(req_get.get('awaiting_review'))
        awaiting_my_review = str2bool(req_get.get('awaiting_my_review'))

        filter_type = 'awaiting_review' if awaiting_review \
            else 'awaiting_my_review' if awaiting_my_review \
            else None

        opened_by = None
        if my:
            opened_by = [self._rhodecode_user.user_id]

        statuses = [PullRequest.STATUS_NEW, PullRequest.STATUS_OPEN]
        if closed:
            statuses = [PullRequest.STATUS_CLOSED]

        data = self._get_pull_requests_list(
            repo_name=self.db_repo_name, source=source,
            filter_type=filter_type, opened_by=opened_by, statuses=statuses)

        return data

    def _get_pr_version(self, pull_request_id, version=None):
        pull_request_id = safe_int(pull_request_id)
        at_version = None

        if version and version == 'latest':
            pull_request_ver = PullRequest.get(pull_request_id)
            pull_request_obj = pull_request_ver
            _org_pull_request_obj = pull_request_obj
            at_version = 'latest'
        elif version:
            pull_request_ver = PullRequestVersion.get_or_404(version)
            pull_request_obj = pull_request_ver
            _org_pull_request_obj = pull_request_ver.pull_request
            at_version = pull_request_ver.pull_request_version_id
        else:
            _org_pull_request_obj = pull_request_obj = PullRequest.get_or_404(
                pull_request_id)

        pull_request_display_obj = PullRequest.get_pr_display_object(
            pull_request_obj, _org_pull_request_obj)

        return _org_pull_request_obj, pull_request_obj, \
               pull_request_display_obj, at_version

    def _get_diffset(self, source_repo_name, source_repo,
                     source_ref_id, target_ref_id,
                     target_commit, source_commit, diff_limit, fulldiff,
                     file_limit, display_inline_comments):

        vcs_diff = PullRequestModel().get_diff(
            source_repo, source_ref_id, target_ref_id)

        diff_processor = diffs.DiffProcessor(
            vcs_diff, format='newdiff', diff_limit=diff_limit,
            file_limit=file_limit, show_full_diff=fulldiff)

        _parsed = diff_processor.prepare()

        def _node_getter(commit):
            def get_node(fname):
                try:
                    return commit.get_node(fname)
                except NodeDoesNotExistError:
                    return None

            return get_node

        diffset = codeblocks.DiffSet(
            repo_name=self.db_repo_name,
            source_repo_name=source_repo_name,
            source_node_getter=_node_getter(target_commit),
            target_node_getter=_node_getter(source_commit),
            comments=display_inline_comments
        )
        diffset = diffset.render_patchset(
            _parsed, target_commit.raw_id, source_commit.raw_id)

        return diffset

    @LoginRequired()
    @HasRepoPermissionAnyDecorator(
        'repository.read', 'repository.write', 'repository.admin')
    # @view_config(
    #     route_name='pullrequest_show', request_method='GET',
    #     renderer='rhodecode:templates/pullrequests/pullrequest_show.mako')
    def pull_request_show(self):
        pull_request_id = safe_int(
            self.request.matchdict.get('pull_request_id'))
        c = self.load_default_context()

        version = self.request.GET.get('version')
        from_version = self.request.GET.get('from_version') or version
        merge_checks = self.request.GET.get('merge_checks')
        c.fulldiff = str2bool(self.request.GET.get('fulldiff'))

        (pull_request_latest,
         pull_request_at_ver,
         pull_request_display_obj,
         at_version) = self._get_pr_version(
            pull_request_id, version=version)
        pr_closed = pull_request_latest.is_closed()

        if pr_closed and (version or from_version):
            # not allow to browse versions
            raise HTTPFound(h.route_path(
                'pullrequest_show', repo_name=self.db_repo_name,
                pull_request_id=pull_request_id))

        versions = pull_request_display_obj.versions()

        c.at_version = at_version
        c.at_version_num = (at_version
                            if at_version and at_version != 'latest'
                            else None)
        c.at_version_pos = ChangesetComment.get_index_from_version(
            c.at_version_num, versions)

        (prev_pull_request_latest,
         prev_pull_request_at_ver,
         prev_pull_request_display_obj,
         prev_at_version) = self._get_pr_version(
            pull_request_id, version=from_version)

        c.from_version = prev_at_version
        c.from_version_num = (prev_at_version
                              if prev_at_version and prev_at_version != 'latest'
                              else None)
        c.from_version_pos = ChangesetComment.get_index_from_version(
            c.from_version_num, versions)

        # define if we're in COMPARE mode or VIEW at version mode
        compare = at_version != prev_at_version

        # pull_requests repo_name we opened it against
        # ie. target_repo must match
        if self.db_repo_name != pull_request_at_ver.target_repo.repo_name:
            raise HTTPNotFound()

        c.shadow_clone_url = PullRequestModel().get_shadow_clone_url(
            pull_request_at_ver)

        c.pull_request = pull_request_display_obj
        c.pull_request_latest = pull_request_latest

        if compare or (at_version and not at_version == 'latest'):
            c.allowed_to_change_status = False
            c.allowed_to_update = False
            c.allowed_to_merge = False
            c.allowed_to_delete = False
            c.allowed_to_comment = False
            c.allowed_to_close = False
        else:
            can_change_status = PullRequestModel().check_user_change_status(
                pull_request_at_ver, self._rhodecode_user)
            c.allowed_to_change_status = can_change_status and not pr_closed

            c.allowed_to_update = PullRequestModel().check_user_update(
                pull_request_latest, self._rhodecode_user) and not pr_closed
            c.allowed_to_merge = PullRequestModel().check_user_merge(
                pull_request_latest, self._rhodecode_user) and not pr_closed
            c.allowed_to_delete = PullRequestModel().check_user_delete(
                pull_request_latest, self._rhodecode_user) and not pr_closed
            c.allowed_to_comment = not pr_closed
            c.allowed_to_close = c.allowed_to_merge and not pr_closed

        c.forbid_adding_reviewers = False
        c.forbid_author_to_review = False
        c.forbid_commit_author_to_review = False

        if pull_request_latest.reviewer_data and \
                        'rules' in pull_request_latest.reviewer_data:
            rules = pull_request_latest.reviewer_data['rules'] or {}
            try:
                c.forbid_adding_reviewers = rules.get(
                    'forbid_adding_reviewers')
                c.forbid_author_to_review = rules.get(
                    'forbid_author_to_review')
                c.forbid_commit_author_to_review = rules.get(
                    'forbid_commit_author_to_review')
            except Exception:
                pass

        # check merge capabilities
        _merge_check = MergeCheck.validate(
            pull_request_latest, user=self._rhodecode_user)
        c.pr_merge_errors = _merge_check.error_details
        c.pr_merge_possible = not _merge_check.failed
        c.pr_merge_message = _merge_check.merge_msg

        c.pull_request_review_status = _merge_check.review_status
        if merge_checks:
            self.request.override_renderer = \
                'rhodecode:templates/pullrequests/pullrequest_merge_checks.mako'
            return self._get_template_context(c)

        comments_model = CommentsModel()

        # reviewers and statuses
        c.pull_request_reviewers = pull_request_at_ver.reviewers_statuses()
        allowed_reviewers = [x[0].user_id for x in c.pull_request_reviewers]

        # GENERAL COMMENTS with versions #
        q = comments_model._all_general_comments_of_pull_request(pull_request_latest)
        q = q.order_by(ChangesetComment.comment_id.asc())
        general_comments = q

        # pick comments we want to render at current version
        c.comment_versions = comments_model.aggregate_comments(
            general_comments, versions, c.at_version_num)
        c.comments = c.comment_versions[c.at_version_num]['until']

        # INLINE COMMENTS with versions  #
        q = comments_model._all_inline_comments_of_pull_request(pull_request_latest)
        q = q.order_by(ChangesetComment.comment_id.asc())
        inline_comments = q

        c.inline_versions = comments_model.aggregate_comments(
            inline_comments, versions, c.at_version_num, inline=True)

        # inject latest version
        latest_ver = PullRequest.get_pr_display_object(
            pull_request_latest, pull_request_latest)

        c.versions = versions + [latest_ver]

        # if we use version, then do not show later comments
        # than current version
        display_inline_comments = collections.defaultdict(
            lambda: collections.defaultdict(list))
        for co in inline_comments:
            if c.at_version_num:
                # pick comments that are at least UPTO given version, so we
                # don't render comments for higher version
                should_render = co.pull_request_version_id and \
                                co.pull_request_version_id <= c.at_version_num
            else:
                # showing all, for 'latest'
                should_render = True

            if should_render:
                display_inline_comments[co.f_path][co.line_no].append(co)

        # load diff data into template context, if we use compare mode then
        # diff is calculated based on changes between versions of PR

        source_repo = pull_request_at_ver.source_repo
        source_ref_id = pull_request_at_ver.source_ref_parts.commit_id

        target_repo = pull_request_at_ver.target_repo
        target_ref_id = pull_request_at_ver.target_ref_parts.commit_id

        if compare:
            # in compare switch the diff base to latest commit from prev version
            target_ref_id = prev_pull_request_display_obj.revisions[0]

        # despite opening commits for bookmarks/branches/tags, we always
        # convert this to rev to prevent changes after bookmark or branch change
        c.source_ref_type = 'rev'
        c.source_ref = source_ref_id

        c.target_ref_type = 'rev'
        c.target_ref = target_ref_id

        c.source_repo = source_repo
        c.target_repo = target_repo

        c.commit_ranges = []
        source_commit = EmptyCommit()
        target_commit = EmptyCommit()
        c.missing_requirements = False

        source_scm = source_repo.scm_instance()
        target_scm = target_repo.scm_instance()

        # try first shadow repo, fallback to regular repo
        try:
            commits_source_repo = pull_request_latest.get_shadow_repo()
        except Exception:
            log.debug('Failed to get shadow repo', exc_info=True)
            commits_source_repo = source_scm

        c.commits_source_repo = commits_source_repo
        commit_cache = {}
        try:
            pre_load = ["author", "branch", "date", "message"]
            show_revs = pull_request_at_ver.revisions
            for rev in show_revs:
                comm = commits_source_repo.get_commit(
                    commit_id=rev, pre_load=pre_load)
                c.commit_ranges.append(comm)
                commit_cache[comm.raw_id] = comm

            # Order here matters, we first need to get target, and then
            # the source
            target_commit = commits_source_repo.get_commit(
                commit_id=safe_str(target_ref_id))

            source_commit = commits_source_repo.get_commit(
                commit_id=safe_str(source_ref_id))

        except CommitDoesNotExistError:
            log.warning(
                'Failed to get commit from `{}` repo'.format(
                    commits_source_repo), exc_info=True)
        except RepositoryRequirementError:
            log.warning(
                'Failed to get all required data from repo', exc_info=True)
            c.missing_requirements = True

        c.ancestor = None  # set it to None, to hide it from PR view

        try:
            ancestor_id = source_scm.get_common_ancestor(
                source_commit.raw_id, target_commit.raw_id, target_scm)
            c.ancestor_commit = source_scm.get_commit(ancestor_id)
        except Exception:
            c.ancestor_commit = None

        c.statuses = source_repo.statuses(
            [x.raw_id for x in c.commit_ranges])

        # auto collapse if we have more than limit
        collapse_limit = diffs.DiffProcessor._collapse_commits_over
        c.collapse_all_commits = len(c.commit_ranges) > collapse_limit
        c.compare_mode = compare

        # diff_limit is the old behavior, will cut off the whole diff
        # if the limit is applied  otherwise will just hide the
        # big files from the front-end
        diff_limit = c.visual.cut_off_limit_diff
        file_limit = c.visual.cut_off_limit_file

        c.missing_commits = False
        if (c.missing_requirements
            or isinstance(source_commit, EmptyCommit)
            or source_commit == target_commit):

            c.missing_commits = True
        else:

            c.diffset = self._get_diffset(
                c.source_repo.repo_name, commits_source_repo,
                source_ref_id, target_ref_id,
                target_commit, source_commit,
                diff_limit, c.fulldiff, file_limit, display_inline_comments)

            c.limited_diff = c.diffset.limited_diff

            # calculate removed files that are bound to comments
            comment_deleted_files = [
                fname for fname in display_inline_comments
                if fname not in c.diffset.file_stats]

            c.deleted_files_comments = collections.defaultdict(dict)
            for fname, per_line_comments in display_inline_comments.items():
                if fname in comment_deleted_files:
                    c.deleted_files_comments[fname]['stats'] = 0
                    c.deleted_files_comments[fname]['comments'] = list()
                    for lno, comments in per_line_comments.items():
                        c.deleted_files_comments[fname]['comments'].extend(
                            comments)

        # this is a hack to properly display links, when creating PR, the
        # compare view and others uses different notation, and
        # compare_commits.mako renders links based on the target_repo.
        # We need to swap that here to generate it properly on the html side
        c.target_repo = c.source_repo

        c.commit_statuses = ChangesetStatus.STATUSES

        c.show_version_changes = not pr_closed
        if c.show_version_changes:
            cur_obj = pull_request_at_ver
            prev_obj = prev_pull_request_at_ver

            old_commit_ids = prev_obj.revisions
            new_commit_ids = cur_obj.revisions
            commit_changes = PullRequestModel()._calculate_commit_id_changes(
                old_commit_ids, new_commit_ids)
            c.commit_changes_summary = commit_changes

            # calculate the diff for commits between versions
            c.commit_changes = []
            mark = lambda cs, fw: list(
                h.itertools.izip_longest([], cs, fillvalue=fw))
            for c_type, raw_id in mark(commit_changes.added, 'a') \
                                + mark(commit_changes.removed, 'r') \
                                + mark(commit_changes.common, 'c'):

                if raw_id in commit_cache:
                    commit = commit_cache[raw_id]
                else:
                    try:
                        commit = commits_source_repo.get_commit(raw_id)
                    except CommitDoesNotExistError:
                        # in case we fail extracting still use "dummy" commit
                        # for display in commit diff
                        commit = h.AttributeDict(
                            {'raw_id': raw_id,
                             'message': 'EMPTY or MISSING COMMIT'})
                c.commit_changes.append([c_type, commit])

            # current user review statuses for each version
            c.review_versions = {}
            if self._rhodecode_user.user_id in allowed_reviewers:
                for co in general_comments:
                    if co.author.user_id == self._rhodecode_user.user_id:
                        # each comment has a status change
                        status = co.status_change
                        if status:
                            _ver_pr = status[0].comment.pull_request_version_id
                            c.review_versions[_ver_pr] = status[0]

        return self._get_template_context(c)
