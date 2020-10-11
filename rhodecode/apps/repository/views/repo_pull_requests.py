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
import collections

import formencode
import formencode.htmlfill
import peppercorn
from pyramid.httpexceptions import (
    HTTPFound, HTTPNotFound, HTTPForbidden, HTTPBadRequest, HTTPConflict)
from pyramid.view import view_config
from pyramid.renderers import render

from rhodecode.apps._base import RepoAppView, DataGridAppView

from rhodecode.lib import helpers as h, diffs, codeblocks, channelstream
from rhodecode.lib.base import vcs_operation_context
from rhodecode.lib.diffs import load_cached_diff, cache_diff, diff_cache_exist
from rhodecode.lib.exceptions import CommentVersionMismatch
from rhodecode.lib.ext_json import json
from rhodecode.lib.auth import (
    LoginRequired, HasRepoPermissionAny, HasRepoPermissionAnyDecorator,
    NotAnonymous, CSRFRequired)
from rhodecode.lib.utils2 import str2bool, safe_str, safe_unicode, safe_int, aslist
from rhodecode.lib.vcs.backends.base import (
    EmptyCommit, UpdateFailureReason, unicode_to_reference)
from rhodecode.lib.vcs.exceptions import (
    CommitDoesNotExistError, RepositoryRequirementError, EmptyRepositoryError)
from rhodecode.model.changeset_status import ChangesetStatusModel
from rhodecode.model.comment import CommentsModel
from rhodecode.model.db import (
    func, or_, PullRequest, ChangesetComment, ChangesetStatus, Repository,
    PullRequestReviewers)
from rhodecode.model.forms import PullRequestForm
from rhodecode.model.meta import Session
from rhodecode.model.pull_request import PullRequestModel, MergeCheck
from rhodecode.model.scm import ScmModel

log = logging.getLogger(__name__)


class RepoPullRequestsView(RepoAppView, DataGridAppView):

    def load_default_context(self):
        c = self._get_local_tmpl_context(include_app_defaults=True)
        c.REVIEW_STATUS_APPROVED = ChangesetStatus.STATUS_APPROVED
        c.REVIEW_STATUS_REJECTED = ChangesetStatus.STATUS_REJECTED
        # backward compat., we use for OLD PRs a plain renderer
        c.renderer = 'plain'
        return c

    def _get_pull_requests_list(
            self, repo_name, source, filter_type, opened_by, statuses):

        draw, start, limit = self._extract_chunk(self.request)
        search_q, order_by, order_dir = self._extract_ordering(self.request)
        _render = self.request.get_partial_renderer(
            'rhodecode:templates/data_table/_dt_elements.mako')

        # pagination

        if filter_type == 'awaiting_review':
            pull_requests = PullRequestModel().get_awaiting_review(
                repo_name, search_q=search_q, source=source, opened_by=opened_by,
                statuses=statuses, offset=start, length=limit,
                order_by=order_by, order_dir=order_dir)
            pull_requests_total_count = PullRequestModel().count_awaiting_review(
                repo_name, search_q=search_q, source=source, statuses=statuses,
                opened_by=opened_by)
        elif filter_type == 'awaiting_my_review':
            pull_requests = PullRequestModel().get_awaiting_my_review(
                repo_name, search_q=search_q, source=source, opened_by=opened_by,
                user_id=self._rhodecode_user.user_id, statuses=statuses,
                offset=start, length=limit, order_by=order_by,
                order_dir=order_dir)
            pull_requests_total_count = PullRequestModel().count_awaiting_my_review(
                repo_name, search_q=search_q, source=source, user_id=self._rhodecode_user.user_id,
                statuses=statuses, opened_by=opened_by)
        else:
            pull_requests = PullRequestModel().get_all(
                repo_name, search_q=search_q, source=source, opened_by=opened_by,
                statuses=statuses, offset=start, length=limit,
                order_by=order_by, order_dir=order_dir)
            pull_requests_total_count = PullRequestModel().count_all(
                repo_name, search_q=search_q, source=source, statuses=statuses,
                opened_by=opened_by)

        data = []
        comments_model = CommentsModel()
        for pr in pull_requests:
            comments_count = comments_model.get_all_comments(
                self.db_repo.repo_id, pull_request=pr, count_only=True)

            data.append({
                'name': _render('pullrequest_name',
                                pr.pull_request_id, pr.pull_request_state,
                                pr.work_in_progress, pr.target_repo.repo_name,
                                short=True),
                'name_raw': pr.pull_request_id,
                'status': _render('pullrequest_status',
                                  pr.calculated_review_status()),
                'title': _render('pullrequest_title', pr.title, pr.description),
                'description': h.escape(pr.description),
                'updated_on': _render('pullrequest_updated_on',
                                      h.datetime_to_time(pr.updated_on)),
                'updated_on_raw': h.datetime_to_time(pr.updated_on),
                'created_on': _render('pullrequest_updated_on',
                                      h.datetime_to_time(pr.created_on)),
                'created_on_raw': h.datetime_to_time(pr.created_on),
                'state': pr.pull_request_state,
                'author': _render('pullrequest_author',
                                  pr.author.full_contact, ),
                'author_raw': pr.author.full_name,
                'comments': _render('pullrequest_comments', comments_count),
                'comments_raw': comments_count,
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
        self.load_default_context()

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

    def _is_diff_cache_enabled(self, target_repo):
        caching_enabled = self._get_general_setting(
            target_repo, 'rhodecode_diff_cache')
        log.debug('Diff caching enabled: %s', caching_enabled)
        return caching_enabled

    def _get_diffset(self, source_repo_name, source_repo,
                     ancestor_commit,
                     source_ref_id, target_ref_id,
                     target_commit, source_commit, diff_limit, file_limit,
                     fulldiff, hide_whitespace_changes, diff_context, use_ancestor=True):

        if use_ancestor:
            # we might want to not use it for versions
            target_ref_id = ancestor_commit.raw_id

        vcs_diff = PullRequestModel().get_diff(
            source_repo, source_ref_id, target_ref_id,
            hide_whitespace_changes, diff_context)

        diff_processor = diffs.DiffProcessor(
            vcs_diff, format='newdiff', diff_limit=diff_limit,
            file_limit=file_limit, show_full_diff=fulldiff)

        _parsed = diff_processor.prepare()

        diffset = codeblocks.DiffSet(
            repo_name=self.db_repo_name,
            source_repo_name=source_repo_name,
            source_node_getter=codeblocks.diffset_node_getter(target_commit),
            target_node_getter=codeblocks.diffset_node_getter(source_commit),
        )
        diffset = self.path_filter.render_patchset_filtered(
            diffset, _parsed, target_commit.raw_id, source_commit.raw_id)

        return diffset

    def _get_range_diffset(self, source_scm, source_repo,
                           commit1, commit2, diff_limit, file_limit,
                           fulldiff, hide_whitespace_changes, diff_context):
        vcs_diff = source_scm.get_diff(
            commit1, commit2,
            ignore_whitespace=hide_whitespace_changes,
            context=diff_context)

        diff_processor = diffs.DiffProcessor(
            vcs_diff, format='newdiff', diff_limit=diff_limit,
            file_limit=file_limit, show_full_diff=fulldiff)

        _parsed = diff_processor.prepare()

        diffset = codeblocks.DiffSet(
            repo_name=source_repo.repo_name,
            source_node_getter=codeblocks.diffset_node_getter(commit1),
            target_node_getter=codeblocks.diffset_node_getter(commit2))

        diffset = self.path_filter.render_patchset_filtered(
            diffset, _parsed, commit1.raw_id, commit2.raw_id)

        return diffset

    def register_comments_vars(self, c, pull_request, versions):
        comments_model = CommentsModel()

        # GENERAL COMMENTS with versions #
        q = comments_model._all_general_comments_of_pull_request(pull_request)
        q = q.order_by(ChangesetComment.comment_id.asc())
        general_comments = q

        # pick comments we want to render at current version
        c.comment_versions = comments_model.aggregate_comments(
            general_comments, versions, c.at_version_num)

        # INLINE COMMENTS with versions  #
        q = comments_model._all_inline_comments_of_pull_request(pull_request)
        q = q.order_by(ChangesetComment.comment_id.asc())
        inline_comments = q

        c.inline_versions = comments_model.aggregate_comments(
            inline_comments, versions, c.at_version_num, inline=True)

        # Comments inline+general
        if c.at_version:
            c.inline_comments_flat = c.inline_versions[c.at_version_num]['display']
            c.comments = c.comment_versions[c.at_version_num]['display']
        else:
            c.inline_comments_flat = c.inline_versions[c.at_version_num]['until']
            c.comments = c.comment_versions[c.at_version_num]['until']

        return general_comments, inline_comments

    @LoginRequired()
    @HasRepoPermissionAnyDecorator(
        'repository.read', 'repository.write', 'repository.admin')
    @view_config(
        route_name='pullrequest_show', request_method='GET',
        renderer='rhodecode:templates/pullrequests/pullrequest_show.mako')
    def pull_request_show(self):
        _ = self.request.translate
        c = self.load_default_context()

        pull_request = PullRequest.get_or_404(
            self.request.matchdict['pull_request_id'])
        pull_request_id = pull_request.pull_request_id

        c.state_progressing = pull_request.is_state_changing()
        c.pr_broadcast_channel = channelstream.pr_channel(pull_request)

        _new_state = {
            'created': PullRequest.STATE_CREATED,
        }.get(self.request.GET.get('force_state'))

        if c.is_super_admin and _new_state:
            with pull_request.set_state(PullRequest.STATE_UPDATING, final_state=_new_state):
                h.flash(
                    _('Pull Request state was force changed to `{}`').format(_new_state),
                    category='success')
                Session().commit()

            raise HTTPFound(h.route_path(
                'pullrequest_show', repo_name=self.db_repo_name,
                pull_request_id=pull_request_id))

        version = self.request.GET.get('version')
        from_version = self.request.GET.get('from_version') or version
        merge_checks = self.request.GET.get('merge_checks')
        c.fulldiff = str2bool(self.request.GET.get('fulldiff'))
        force_refresh = str2bool(self.request.GET.get('force_refresh'))
        c.range_diff_on = self.request.GET.get('range-diff') == "1"

        # fetch global flags of ignore ws or context lines
        diff_context = diffs.get_diff_context(self.request)
        hide_whitespace_changes = diffs.get_diff_whitespace_flag(self.request)

        (pull_request_latest,
         pull_request_at_ver,
         pull_request_display_obj,
         at_version) = PullRequestModel().get_pr_version(
            pull_request_id, version=version)

        pr_closed = pull_request_latest.is_closed()

        if pr_closed and (version or from_version):
            # not allow to browse versions for closed PR
            raise HTTPFound(h.route_path(
                'pullrequest_show', repo_name=self.db_repo_name,
                pull_request_id=pull_request_id))

        versions = pull_request_display_obj.versions()
        # used to store per-commit range diffs
        c.changes = collections.OrderedDict()

        c.at_version = at_version
        c.at_version_num = (at_version
                            if at_version and at_version != PullRequest.LATEST_VER
                            else None)

        c.at_version_index = ChangesetComment.get_index_from_version(
            c.at_version_num, versions)

        (prev_pull_request_latest,
         prev_pull_request_at_ver,
         prev_pull_request_display_obj,
         prev_at_version) = PullRequestModel().get_pr_version(
            pull_request_id, version=from_version)

        c.from_version = prev_at_version
        c.from_version_num = (prev_at_version
                              if prev_at_version and prev_at_version != PullRequest.LATEST_VER
                              else None)
        c.from_version_index = ChangesetComment.get_index_from_version(
            c.from_version_num, versions)

        # define if we're in COMPARE mode or VIEW at version mode
        compare = at_version != prev_at_version

        # pull_requests repo_name we opened it against
        # ie. target_repo must match
        if self.db_repo_name != pull_request_at_ver.target_repo.repo_name:
            log.warning('Mismatch between the current repo: %s, and target %s',
                        self.db_repo_name, pull_request_at_ver.target_repo.repo_name)
            raise HTTPNotFound()

        c.shadow_clone_url = PullRequestModel().get_shadow_clone_url(pull_request_at_ver)

        c.pull_request = pull_request_display_obj
        c.renderer = pull_request_at_ver.description_renderer or c.renderer
        c.pull_request_latest = pull_request_latest

        # inject latest version
        latest_ver = PullRequest.get_pr_display_object(pull_request_latest, pull_request_latest)
        c.versions = versions + [latest_ver]

        if compare or (at_version and not at_version == PullRequest.LATEST_VER):
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
                c.forbid_adding_reviewers = rules.get('forbid_adding_reviewers')
                c.forbid_author_to_review = rules.get('forbid_author_to_review')
                c.forbid_commit_author_to_review = rules.get('forbid_commit_author_to_review')
            except Exception:
                pass

        # check merge capabilities
        _merge_check = MergeCheck.validate(
            pull_request_latest, auth_user=self._rhodecode_user,
            translator=self.request.translate,
            force_shadow_repo_refresh=force_refresh)

        c.pr_merge_errors = _merge_check.error_details
        c.pr_merge_possible = not _merge_check.failed
        c.pr_merge_message = _merge_check.merge_msg
        c.pr_merge_source_commit = _merge_check.source_commit
        c.pr_merge_target_commit = _merge_check.target_commit

        c.pr_merge_info = MergeCheck.get_merge_conditions(
            pull_request_latest, translator=self.request.translate)

        c.pull_request_review_status = _merge_check.review_status
        if merge_checks:
            self.request.override_renderer = \
                'rhodecode:templates/pullrequests/pullrequest_merge_checks.mako'
            return self._get_template_context(c)

        c.reviewers_count = pull_request.reviewers_count
        c.observers_count = pull_request.observers_count

        # reviewers and statuses
        c.pull_request_default_reviewers_data_json = json.dumps(pull_request.reviewer_data)
        c.pull_request_set_reviewers_data_json = collections.OrderedDict({'reviewers': []})
        c.pull_request_set_observers_data_json = collections.OrderedDict({'observers': []})

        for review_obj, member, reasons, mandatory, status in pull_request_at_ver.reviewers_statuses():
            member_reviewer = h.reviewer_as_json(
                member, reasons=reasons, mandatory=mandatory,
                role=review_obj.role,
                user_group=review_obj.rule_user_group_data()
            )

            current_review_status = status[0][1].status if status else ChangesetStatus.STATUS_NOT_REVIEWED
            member_reviewer['review_status'] = current_review_status
            member_reviewer['review_status_label'] = h.commit_status_lbl(current_review_status)
            member_reviewer['allowed_to_update'] = c.allowed_to_update
            c.pull_request_set_reviewers_data_json['reviewers'].append(member_reviewer)

        c.pull_request_set_reviewers_data_json = json.dumps(c.pull_request_set_reviewers_data_json)

        for observer_obj, member in pull_request_at_ver.observers():
            member_observer = h.reviewer_as_json(
                member, reasons=[], mandatory=False,
                role=observer_obj.role,
                user_group=observer_obj.rule_user_group_data()
            )
            member_observer['allowed_to_update'] = c.allowed_to_update
            c.pull_request_set_observers_data_json['observers'].append(member_observer)

        c.pull_request_set_observers_data_json = json.dumps(c.pull_request_set_observers_data_json)

        general_comments, inline_comments = \
            self.register_comments_vars(c, pull_request_latest, versions)

        # TODOs
        c.unresolved_comments = CommentsModel() \
            .get_pull_request_unresolved_todos(pull_request_latest)
        c.resolved_comments = CommentsModel() \
            .get_pull_request_resolved_todos(pull_request_latest)

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

        shadow_scm = None
        try:
            shadow_scm = pull_request_latest.get_shadow_repo()
        except Exception:
            log.debug('Failed to get shadow repo', exc_info=True)
        # try first the existing source_repo, and then shadow
        # repo if we can obtain one
        commits_source_repo = source_scm
        if shadow_scm:
            commits_source_repo = shadow_scm

        c.commits_source_repo = commits_source_repo
        c.ancestor = None  # set it to None, to hide it from PR view

        # empty version means latest, so we keep this to prevent
        # double caching
        version_normalized = version or PullRequest.LATEST_VER
        from_version_normalized = from_version or PullRequest.LATEST_VER

        cache_path = self.rhodecode_vcs_repo.get_create_shadow_cache_pr_path(target_repo)
        cache_file_path = diff_cache_exist(
            cache_path, 'pull_request', pull_request_id, version_normalized,
            from_version_normalized, source_ref_id, target_ref_id,
            hide_whitespace_changes, diff_context, c.fulldiff)

        caching_enabled = self._is_diff_cache_enabled(c.target_repo)
        force_recache = self.get_recache_flag()

        cached_diff = None
        if caching_enabled:
            cached_diff = load_cached_diff(cache_file_path)

        has_proper_commit_cache = (
                cached_diff and cached_diff.get('commits')
                and len(cached_diff.get('commits', [])) == 5
                and cached_diff.get('commits')[0]
                and cached_diff.get('commits')[3])

        if not force_recache and not c.range_diff_on and has_proper_commit_cache:
            diff_commit_cache = \
                (ancestor_commit, commit_cache, missing_requirements,
                 source_commit, target_commit) = cached_diff['commits']
        else:
            # NOTE(marcink): we reach potentially unreachable errors when a PR has
            # merge errors resulting in potentially hidden commits in the shadow repo.
            maybe_unreachable = _merge_check.MERGE_CHECK in _merge_check.error_details \
                                and _merge_check.merge_response
            maybe_unreachable = maybe_unreachable \
                                and _merge_check.merge_response.metadata.get('unresolved_files')
            log.debug("Using unreachable commits due to MERGE_CHECK in merge simulation")
            diff_commit_cache = \
                (ancestor_commit, commit_cache, missing_requirements,
                 source_commit, target_commit) = self.get_commits(
                    commits_source_repo,
                    pull_request_at_ver,
                    source_commit,
                    source_ref_id,
                    source_scm,
                    target_commit,
                    target_ref_id,
                    target_scm,
                maybe_unreachable=maybe_unreachable)

        # register our commit range
        for comm in commit_cache.values():
            c.commit_ranges.append(comm)

        c.missing_requirements = missing_requirements
        c.ancestor_commit = ancestor_commit
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
            c.inline_comments = display_inline_comments

            use_ancestor = True
            if from_version_normalized != version_normalized:
                use_ancestor = False

            has_proper_diff_cache = cached_diff and cached_diff.get('commits')
            if not force_recache and has_proper_diff_cache:
                c.diffset = cached_diff['diff']
            else:
                try:
                    c.diffset = self._get_diffset(
                        c.source_repo.repo_name, commits_source_repo,
                        c.ancestor_commit,
                        source_ref_id, target_ref_id,
                        target_commit, source_commit,
                        diff_limit, file_limit, c.fulldiff,
                        hide_whitespace_changes, diff_context,
                        use_ancestor=use_ancestor
                    )

                    # save cached diff
                    if caching_enabled:
                        cache_diff(cache_file_path, c.diffset, diff_commit_cache)
                except CommitDoesNotExistError:
                    log.exception('Failed to generate diffset')
                    c.missing_commits = True

            if not c.missing_commits:

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
                            c.deleted_files_comments[fname]['comments'].extend(comments)

                # maybe calculate the range diff
                if c.range_diff_on:
                    # TODO(marcink): set whitespace/context
                    context_lcl = 3
                    ign_whitespace_lcl = False

                    for commit in c.commit_ranges:
                        commit2 = commit
                        commit1 = commit.first_parent

                        range_diff_cache_file_path = diff_cache_exist(
                            cache_path, 'diff', commit.raw_id,
                            ign_whitespace_lcl, context_lcl, c.fulldiff)

                        cached_diff = None
                        if caching_enabled:
                            cached_diff = load_cached_diff(range_diff_cache_file_path)

                        has_proper_diff_cache = cached_diff and cached_diff.get('diff')
                        if not force_recache and has_proper_diff_cache:
                            diffset = cached_diff['diff']
                        else:
                            diffset = self._get_range_diffset(
                                commits_source_repo, source_repo,
                                commit1, commit2, diff_limit, file_limit,
                                c.fulldiff, ign_whitespace_lcl, context_lcl
                            )

                        # save cached diff
                        if caching_enabled:
                            cache_diff(range_diff_cache_file_path, diffset, None)

                        c.changes[commit.raw_id] = diffset

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

            def mark(cs, fw):
                return list(h.itertools.izip_longest([], cs, fillvalue=fw))

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
            is_reviewer = PullRequestModel().is_user_reviewer(
                pull_request, self._rhodecode_user)
            if is_reviewer:
                for co in general_comments:
                    if co.author.user_id == self._rhodecode_user.user_id:
                        status = co.status_change
                        if status:
                            _ver_pr = status[0].comment.pull_request_version_id
                            c.review_versions[_ver_pr] = status[0]

        return self._get_template_context(c)

    def get_commits(
            self, commits_source_repo, pull_request_at_ver, source_commit,
            source_ref_id, source_scm, target_commit, target_ref_id, target_scm,
            maybe_unreachable=False):

        commit_cache = collections.OrderedDict()
        missing_requirements = False

        try:
            pre_load = ["author", "date", "message", "branch", "parents"]

            pull_request_commits = pull_request_at_ver.revisions
            log.debug('Loading %s commits from %s',
                      len(pull_request_commits), commits_source_repo)

            for rev in pull_request_commits:
                comm = commits_source_repo.get_commit(commit_id=rev, pre_load=pre_load,
                                                      maybe_unreachable=maybe_unreachable)
                commit_cache[comm.raw_id] = comm

            # Order here matters, we first need to get target, and then
            # the source
            target_commit = commits_source_repo.get_commit(
                commit_id=safe_str(target_ref_id))

            source_commit = commits_source_repo.get_commit(
                commit_id=safe_str(source_ref_id), maybe_unreachable=True)
        except CommitDoesNotExistError:
            log.warning('Failed to get commit from `{}` repo'.format(
                commits_source_repo), exc_info=True)
        except RepositoryRequirementError:
            log.warning('Failed to get all required data from repo', exc_info=True)
            missing_requirements = True

        pr_ancestor_id = pull_request_at_ver.common_ancestor_id

        try:
            ancestor_commit = source_scm.get_commit(pr_ancestor_id)
        except Exception:
            ancestor_commit = None

        return ancestor_commit, commit_cache, missing_requirements, source_commit, target_commit

    def assure_not_empty_repo(self):
        _ = self.request.translate

        try:
            self.db_repo.scm_instance().get_commit()
        except EmptyRepositoryError:
            h.flash(h.literal(_('There are no commits yet')),
                    category='warning')
            raise HTTPFound(
                h.route_path('repo_summary', repo_name=self.db_repo.repo_name))

    @LoginRequired()
    @NotAnonymous()
    @HasRepoPermissionAnyDecorator(
        'repository.read', 'repository.write', 'repository.admin')
    @view_config(
        route_name='pullrequest_new', request_method='GET',
        renderer='rhodecode:templates/pullrequests/pullrequest.mako')
    def pull_request_new(self):
        _ = self.request.translate
        c = self.load_default_context()

        self.assure_not_empty_repo()
        source_repo = self.db_repo

        commit_id = self.request.GET.get('commit')
        branch_ref = self.request.GET.get('branch')
        bookmark_ref = self.request.GET.get('bookmark')

        try:
            source_repo_data = PullRequestModel().generate_repo_data(
                source_repo, commit_id=commit_id,
                branch=branch_ref, bookmark=bookmark_ref,
                translator=self.request.translate)
        except CommitDoesNotExistError as e:
            log.exception(e)
            h.flash(_('Commit does not exist'), 'error')
            raise HTTPFound(
                h.route_path('pullrequest_new', repo_name=source_repo.repo_name))

        default_target_repo = source_repo

        if source_repo.parent and c.has_origin_repo_read_perm:
            parent_vcs_obj = source_repo.parent.scm_instance()
            if parent_vcs_obj and not parent_vcs_obj.is_empty():
                # change default if we have a parent repo
                default_target_repo = source_repo.parent

        target_repo_data = PullRequestModel().generate_repo_data(
            default_target_repo, translator=self.request.translate)

        selected_source_ref = source_repo_data['refs']['selected_ref']
        title_source_ref = ''
        if selected_source_ref:
            title_source_ref = selected_source_ref.split(':', 2)[1]
        c.default_title = PullRequestModel().generate_pullrequest_title(
            source=source_repo.repo_name,
            source_ref=title_source_ref,
            target=default_target_repo.repo_name
        )

        c.default_repo_data = {
            'source_repo_name': source_repo.repo_name,
            'source_refs_json': json.dumps(source_repo_data),
            'target_repo_name': default_target_repo.repo_name,
            'target_refs_json': json.dumps(target_repo_data),
        }
        c.default_source_ref = selected_source_ref

        return self._get_template_context(c)

    @LoginRequired()
    @NotAnonymous()
    @HasRepoPermissionAnyDecorator(
        'repository.read', 'repository.write', 'repository.admin')
    @view_config(
        route_name='pullrequest_repo_refs', request_method='GET',
        renderer='json_ext', xhr=True)
    def pull_request_repo_refs(self):
        self.load_default_context()
        target_repo_name = self.request.matchdict['target_repo_name']
        repo = Repository.get_by_repo_name(target_repo_name)
        if not repo:
            raise HTTPNotFound()

        target_perm = HasRepoPermissionAny(
            'repository.read', 'repository.write', 'repository.admin')(
            target_repo_name)
        if not target_perm:
            raise HTTPNotFound()

        return PullRequestModel().generate_repo_data(
            repo, translator=self.request.translate)

    @LoginRequired()
    @NotAnonymous()
    @HasRepoPermissionAnyDecorator(
        'repository.read', 'repository.write', 'repository.admin')
    @view_config(
        route_name='pullrequest_repo_targets', request_method='GET',
        renderer='json_ext', xhr=True)
    def pullrequest_repo_targets(self):
        _ = self.request.translate
        filter_query = self.request.GET.get('query')

        # get the parents
        parent_target_repos = []
        if self.db_repo.parent:
            parents_query = Repository.query() \
                .order_by(func.length(Repository.repo_name)) \
                .filter(Repository.fork_id == self.db_repo.parent.repo_id)

            if filter_query:
                ilike_expression = u'%{}%'.format(safe_unicode(filter_query))
                parents_query = parents_query.filter(
                    Repository.repo_name.ilike(ilike_expression))
            parents = parents_query.limit(20).all()

            for parent in parents:
                parent_vcs_obj = parent.scm_instance()
                if parent_vcs_obj and not parent_vcs_obj.is_empty():
                    parent_target_repos.append(parent)

        # get other forks, and repo itself
        query = Repository.query() \
            .order_by(func.length(Repository.repo_name)) \
            .filter(
                or_(Repository.repo_id == self.db_repo.repo_id,  # repo itself
                    Repository.fork_id == self.db_repo.repo_id)  # forks of this repo
            )  \
            .filter(~Repository.repo_id.in_([x.repo_id for x in parent_target_repos]))

        if filter_query:
            ilike_expression = u'%{}%'.format(safe_unicode(filter_query))
            query = query.filter(Repository.repo_name.ilike(ilike_expression))

        limit = max(20 - len(parent_target_repos), 5)  # not less then 5
        target_repos = query.limit(limit).all()

        all_target_repos = target_repos + parent_target_repos

        repos = []
        # This checks permissions to the repositories
        for obj in ScmModel().get_repos(all_target_repos):
            repos.append({
                'id': obj['name'],
                'text': obj['name'],
                'type': 'repo',
                'repo_id': obj['dbrepo']['repo_id'],
                'repo_type': obj['dbrepo']['repo_type'],
                'private': obj['dbrepo']['private'],

            })

        data = {
            'more': False,
            'results': [{
                'text': _('Repositories'),
                'children': repos
            }] if repos else []
        }
        return data

    def _get_existing_ids(self, post_data):
        return filter(lambda e: e, map(safe_int, aslist(post_data.get('comments'), ',')))

    @LoginRequired()
    @NotAnonymous()
    @HasRepoPermissionAnyDecorator(
        'repository.read', 'repository.write', 'repository.admin')
    @view_config(
        route_name='pullrequest_comments', request_method='POST',
        renderer='string_html', xhr=True)
    def pullrequest_comments(self):
        self.load_default_context()

        pull_request = PullRequest.get_or_404(
            self.request.matchdict['pull_request_id'])
        pull_request_id = pull_request.pull_request_id
        version = self.request.GET.get('version')

        _render = self.request.get_partial_renderer(
            'rhodecode:templates/base/sidebar.mako')
        c = _render.get_call_context()

        (pull_request_latest,
         pull_request_at_ver,
         pull_request_display_obj,
         at_version) = PullRequestModel().get_pr_version(
            pull_request_id, version=version)
        versions = pull_request_display_obj.versions()
        latest_ver = PullRequest.get_pr_display_object(pull_request_latest, pull_request_latest)
        c.versions = versions + [latest_ver]

        c.at_version = at_version
        c.at_version_num = (at_version
                            if at_version and at_version != PullRequest.LATEST_VER
                            else None)

        self.register_comments_vars(c, pull_request_latest, versions)
        all_comments = c.inline_comments_flat + c.comments

        existing_ids = self._get_existing_ids(self.request.POST)
        return _render('comments_table', all_comments, len(all_comments),
                       existing_ids=existing_ids)

    @LoginRequired()
    @NotAnonymous()
    @HasRepoPermissionAnyDecorator(
        'repository.read', 'repository.write', 'repository.admin')
    @view_config(
        route_name='pullrequest_todos', request_method='POST',
        renderer='string_html', xhr=True)
    def pullrequest_todos(self):
        self.load_default_context()

        pull_request = PullRequest.get_or_404(
            self.request.matchdict['pull_request_id'])
        pull_request_id = pull_request.pull_request_id
        version = self.request.GET.get('version')

        _render = self.request.get_partial_renderer(
            'rhodecode:templates/base/sidebar.mako')
        c = _render.get_call_context()
        (pull_request_latest,
         pull_request_at_ver,
         pull_request_display_obj,
         at_version) = PullRequestModel().get_pr_version(
            pull_request_id, version=version)
        versions = pull_request_display_obj.versions()
        latest_ver = PullRequest.get_pr_display_object(pull_request_latest, pull_request_latest)
        c.versions = versions + [latest_ver]

        c.at_version = at_version
        c.at_version_num = (at_version
                            if at_version and at_version != PullRequest.LATEST_VER
                            else None)

        c.unresolved_comments = CommentsModel() \
            .get_pull_request_unresolved_todos(pull_request)
        c.resolved_comments = CommentsModel() \
            .get_pull_request_resolved_todos(pull_request)

        all_comments = c.unresolved_comments + c.resolved_comments
        existing_ids = self._get_existing_ids(self.request.POST)
        return _render('comments_table', all_comments, len(c.unresolved_comments),
                       todo_comments=True, existing_ids=existing_ids)

    @LoginRequired()
    @NotAnonymous()
    @HasRepoPermissionAnyDecorator(
        'repository.read', 'repository.write', 'repository.admin')
    @CSRFRequired()
    @view_config(
        route_name='pullrequest_create', request_method='POST',
        renderer=None)
    def pull_request_create(self):
        _ = self.request.translate
        self.assure_not_empty_repo()
        self.load_default_context()

        controls = peppercorn.parse(self.request.POST.items())

        try:
            form = PullRequestForm(
                self.request.translate, self.db_repo.repo_id)()
            _form = form.to_python(controls)
        except formencode.Invalid as errors:
            if errors.error_dict.get('revisions'):
                msg = 'Revisions: %s' % errors.error_dict['revisions']
            elif errors.error_dict.get('pullrequest_title'):
                msg = errors.error_dict.get('pullrequest_title')
            else:
                msg = _('Error creating pull request: {}').format(errors)
            log.exception(msg)
            h.flash(msg, 'error')

            # would rather just go back to form ...
            raise HTTPFound(
                h.route_path('pullrequest_new', repo_name=self.db_repo_name))

        source_repo = _form['source_repo']
        source_ref = _form['source_ref']
        target_repo = _form['target_repo']
        target_ref = _form['target_ref']
        commit_ids = _form['revisions'][::-1]
        common_ancestor_id = _form['common_ancestor']

        # find the ancestor for this pr
        source_db_repo = Repository.get_by_repo_name(_form['source_repo'])
        target_db_repo = Repository.get_by_repo_name(_form['target_repo'])

        if not (source_db_repo or target_db_repo):
            h.flash(_('source_repo or target repo not found'), category='error')
            raise HTTPFound(
                h.route_path('pullrequest_new', repo_name=self.db_repo_name))

        # re-check permissions again here
        # source_repo we must have read permissions

        source_perm = HasRepoPermissionAny(
            'repository.read', 'repository.write', 'repository.admin')(
            source_db_repo.repo_name)
        if not source_perm:
            msg = _('Not Enough permissions to source repo `{}`.'.format(
                source_db_repo.repo_name))
            h.flash(msg, category='error')
            # copy the args back to redirect
            org_query = self.request.GET.mixed()
            raise HTTPFound(
                h.route_path('pullrequest_new', repo_name=self.db_repo_name,
                             _query=org_query))

        # target repo we must have read permissions, and also later on
        # we want to check branch permissions here
        target_perm = HasRepoPermissionAny(
            'repository.read', 'repository.write', 'repository.admin')(
            target_db_repo.repo_name)
        if not target_perm:
            msg = _('Not Enough permissions to target repo `{}`.'.format(
                target_db_repo.repo_name))
            h.flash(msg, category='error')
            # copy the args back to redirect
            org_query = self.request.GET.mixed()
            raise HTTPFound(
                h.route_path('pullrequest_new', repo_name=self.db_repo_name,
                             _query=org_query))

        source_scm = source_db_repo.scm_instance()
        target_scm = target_db_repo.scm_instance()

        source_ref_obj = unicode_to_reference(source_ref)
        target_ref_obj = unicode_to_reference(target_ref)

        source_commit = source_scm.get_commit(source_ref_obj.commit_id)
        target_commit = target_scm.get_commit(target_ref_obj.commit_id)

        ancestor = source_scm.get_common_ancestor(
            source_commit.raw_id, target_commit.raw_id, target_scm)

        # recalculate target ref based on ancestor
        target_ref = ':'.join((target_ref_obj.type, target_ref_obj.name, ancestor))

        get_default_reviewers_data, validate_default_reviewers, validate_observers = \
            PullRequestModel().get_reviewer_functions()

        # recalculate reviewers logic, to make sure we can validate this
        reviewer_rules = get_default_reviewers_data(
            self._rhodecode_db_user,
            source_db_repo,
            source_ref_obj,
            target_db_repo,
            target_ref_obj,
            include_diff_info=False)

        reviewers = validate_default_reviewers(_form['review_members'], reviewer_rules)
        observers = validate_observers(_form['observer_members'], reviewer_rules)

        pullrequest_title = _form['pullrequest_title']
        title_source_ref = source_ref_obj.name
        if not pullrequest_title:
            pullrequest_title = PullRequestModel().generate_pullrequest_title(
                source=source_repo,
                source_ref=title_source_ref,
                target=target_repo
            )

        description = _form['pullrequest_desc']
        description_renderer = _form['description_renderer']

        try:
            pull_request = PullRequestModel().create(
                created_by=self._rhodecode_user.user_id,
                source_repo=source_repo,
                source_ref=source_ref,
                target_repo=target_repo,
                target_ref=target_ref,
                revisions=commit_ids,
                common_ancestor_id=common_ancestor_id,
                reviewers=reviewers,
                observers=observers,
                title=pullrequest_title,
                description=description,
                description_renderer=description_renderer,
                reviewer_data=reviewer_rules,
                auth_user=self._rhodecode_user
            )
            Session().commit()

            h.flash(_('Successfully opened new pull request'),
                    category='success')
        except Exception:
            msg = _('Error occurred during creation of this pull request.')
            log.exception(msg)
            h.flash(msg, category='error')

            # copy the args back to redirect
            org_query = self.request.GET.mixed()
            raise HTTPFound(
                h.route_path('pullrequest_new', repo_name=self.db_repo_name,
                             _query=org_query))

        raise HTTPFound(
            h.route_path('pullrequest_show', repo_name=target_repo,
                         pull_request_id=pull_request.pull_request_id))

    @LoginRequired()
    @NotAnonymous()
    @HasRepoPermissionAnyDecorator(
        'repository.read', 'repository.write', 'repository.admin')
    @CSRFRequired()
    @view_config(
        route_name='pullrequest_update', request_method='POST',
        renderer='json_ext')
    def pull_request_update(self):
        pull_request = PullRequest.get_or_404(
            self.request.matchdict['pull_request_id'])
        _ = self.request.translate

        c = self.load_default_context()
        redirect_url = None

        if pull_request.is_closed():
            log.debug('update: forbidden because pull request is closed')
            msg = _(u'Cannot update closed pull requests.')
            h.flash(msg, category='error')
            return {'response': True,
                    'redirect_url': redirect_url}

        is_state_changing = pull_request.is_state_changing()
        c.pr_broadcast_channel = channelstream.pr_channel(pull_request)

        # only owner or admin can update it
        allowed_to_update = PullRequestModel().check_user_update(
            pull_request, self._rhodecode_user)

        if allowed_to_update:
            controls = peppercorn.parse(self.request.POST.items())
            force_refresh = str2bool(self.request.POST.get('force_refresh'))

            if 'review_members' in controls:
                self._update_reviewers(
                    c,
                    pull_request, controls['review_members'],
                    pull_request.reviewer_data,
                    PullRequestReviewers.ROLE_REVIEWER)
            elif 'observer_members' in controls:
                self._update_reviewers(
                    c,
                    pull_request, controls['observer_members'],
                    pull_request.reviewer_data,
                    PullRequestReviewers.ROLE_OBSERVER)
            elif str2bool(self.request.POST.get('update_commits', 'false')):
                if is_state_changing:
                    log.debug('commits update: forbidden because pull request is in state %s',
                              pull_request.pull_request_state)
                    msg = _(u'Cannot update pull requests commits in state other than `{}`. '
                            u'Current state is: `{}`').format(
                        PullRequest.STATE_CREATED, pull_request.pull_request_state)
                    h.flash(msg, category='error')
                    return {'response': True,
                            'redirect_url': redirect_url}

                self._update_commits(c, pull_request)
                if force_refresh:
                    redirect_url = h.route_path(
                        'pullrequest_show', repo_name=self.db_repo_name,
                        pull_request_id=pull_request.pull_request_id,
                        _query={"force_refresh": 1})
            elif str2bool(self.request.POST.get('edit_pull_request', 'false')):
                self._edit_pull_request(pull_request)
            else:
                log.error('Unhandled update data.')
                raise HTTPBadRequest()

            return {'response': True,
                    'redirect_url': redirect_url}
        raise HTTPForbidden()

    def _edit_pull_request(self, pull_request):
        """
        Edit title and description
        """
        _ = self.request.translate

        try:
            PullRequestModel().edit(
                pull_request,
                self.request.POST.get('title'),
                self.request.POST.get('description'),
                self.request.POST.get('description_renderer'),
                self._rhodecode_user)
        except ValueError:
            msg = _(u'Cannot update closed pull requests.')
            h.flash(msg, category='error')
            return
        else:
            Session().commit()

        msg = _(u'Pull request title & description updated.')
        h.flash(msg, category='success')
        return

    def _update_commits(self, c, pull_request):
        _ = self.request.translate

        with pull_request.set_state(PullRequest.STATE_UPDATING):
            resp = PullRequestModel().update_commits(
                pull_request, self._rhodecode_db_user)

        if resp.executed:

            if resp.target_changed and resp.source_changed:
                changed = 'target and source repositories'
            elif resp.target_changed and not resp.source_changed:
                changed = 'target repository'
            elif not resp.target_changed and resp.source_changed:
                changed = 'source repository'
            else:
                changed = 'nothing'

            msg = _(u'Pull request updated to "{source_commit_id}" with '
                    u'{count_added} added, {count_removed} removed commits. '
                    u'Source of changes: {change_source}.')
            msg = msg.format(
                source_commit_id=pull_request.source_ref_parts.commit_id,
                count_added=len(resp.changes.added),
                count_removed=len(resp.changes.removed),
                change_source=changed)
            h.flash(msg, category='success')
            channelstream.pr_update_channelstream_push(
                self.request, c.pr_broadcast_channel, self._rhodecode_user, msg)
        else:
            msg = PullRequestModel.UPDATE_STATUS_MESSAGES[resp.reason]
            warning_reasons = [
                UpdateFailureReason.NO_CHANGE,
                UpdateFailureReason.WRONG_REF_TYPE,
            ]
            category = 'warning' if resp.reason in warning_reasons else 'error'
            h.flash(msg, category=category)

    def _update_reviewers(self, c, pull_request, review_members, reviewer_rules, role):
        _ = self.request.translate

        get_default_reviewers_data, validate_default_reviewers, validate_observers = \
            PullRequestModel().get_reviewer_functions()

        if role == PullRequestReviewers.ROLE_REVIEWER:
            try:
                reviewers = validate_default_reviewers(review_members, reviewer_rules)
            except ValueError as e:
                log.error('Reviewers Validation: {}'.format(e))
                h.flash(e, category='error')
                return

            old_calculated_status = pull_request.calculated_review_status()
            PullRequestModel().update_reviewers(
                pull_request, reviewers, self._rhodecode_db_user)

            Session().commit()

            msg = _('Pull request reviewers updated.')
            h.flash(msg, category='success')
            channelstream.pr_update_channelstream_push(
                self.request, c.pr_broadcast_channel, self._rhodecode_user, msg)

            # trigger status changed if change in reviewers changes the status
            calculated_status = pull_request.calculated_review_status()
            if old_calculated_status != calculated_status:
                PullRequestModel().trigger_pull_request_hook(
                    pull_request, self._rhodecode_user, 'review_status_change',
                    data={'status': calculated_status})

        elif role == PullRequestReviewers.ROLE_OBSERVER:
            try:
                observers = validate_observers(review_members, reviewer_rules)
            except ValueError as e:
                log.error('Observers Validation: {}'.format(e))
                h.flash(e, category='error')
                return

            PullRequestModel().update_observers(
                pull_request, observers, self._rhodecode_db_user)

            Session().commit()
            msg = _('Pull request observers updated.')
            h.flash(msg, category='success')
            channelstream.pr_update_channelstream_push(
                self.request, c.pr_broadcast_channel, self._rhodecode_user, msg)

    @LoginRequired()
    @NotAnonymous()
    @HasRepoPermissionAnyDecorator(
        'repository.read', 'repository.write', 'repository.admin')
    @CSRFRequired()
    @view_config(
        route_name='pullrequest_merge', request_method='POST',
        renderer='json_ext')
    def pull_request_merge(self):
        """
        Merge will perform a server-side merge of the specified
        pull request, if the pull request is approved and mergeable.
        After successful merging, the pull request is automatically
        closed, with a relevant comment.
        """
        pull_request = PullRequest.get_or_404(
            self.request.matchdict['pull_request_id'])
        _ = self.request.translate

        if pull_request.is_state_changing():
            log.debug('show: forbidden because pull request is in state %s',
                      pull_request.pull_request_state)
            msg = _(u'Cannot merge pull requests in state other than `{}`. '
                    u'Current state is: `{}`').format(PullRequest.STATE_CREATED,
                                                      pull_request.pull_request_state)
            h.flash(msg, category='error')
            raise HTTPFound(
                h.route_path('pullrequest_show',
                             repo_name=pull_request.target_repo.repo_name,
                             pull_request_id=pull_request.pull_request_id))

        self.load_default_context()

        with pull_request.set_state(PullRequest.STATE_UPDATING):
            check = MergeCheck.validate(
                pull_request, auth_user=self._rhodecode_user,
                translator=self.request.translate)
        merge_possible = not check.failed

        for err_type, error_msg in check.errors:
            h.flash(error_msg, category=err_type)

        if merge_possible:
            log.debug("Pre-conditions checked, trying to merge.")
            extras = vcs_operation_context(
                self.request.environ, repo_name=pull_request.target_repo.repo_name,
                username=self._rhodecode_db_user.username, action='push',
                scm=pull_request.target_repo.repo_type)
            with pull_request.set_state(PullRequest.STATE_UPDATING):
                self._merge_pull_request(
                    pull_request, self._rhodecode_db_user, extras)
        else:
            log.debug("Pre-conditions failed, NOT merging.")

        raise HTTPFound(
            h.route_path('pullrequest_show',
                         repo_name=pull_request.target_repo.repo_name,
                         pull_request_id=pull_request.pull_request_id))

    def _merge_pull_request(self, pull_request, user, extras):
        _ = self.request.translate
        merge_resp = PullRequestModel().merge_repo(pull_request, user, extras=extras)

        if merge_resp.executed:
            log.debug("The merge was successful, closing the pull request.")
            PullRequestModel().close_pull_request(
                pull_request.pull_request_id, user)
            Session().commit()
            msg = _('Pull request was successfully merged and closed.')
            h.flash(msg, category='success')
        else:
            log.debug(
                "The merge was not successful. Merge response: %s", merge_resp)
            msg = merge_resp.merge_status_message
            h.flash(msg, category='error')

    @LoginRequired()
    @NotAnonymous()
    @HasRepoPermissionAnyDecorator(
        'repository.read', 'repository.write', 'repository.admin')
    @CSRFRequired()
    @view_config(
        route_name='pullrequest_delete', request_method='POST',
        renderer='json_ext')
    def pull_request_delete(self):
        _ = self.request.translate

        pull_request = PullRequest.get_or_404(
            self.request.matchdict['pull_request_id'])
        self.load_default_context()

        pr_closed = pull_request.is_closed()
        allowed_to_delete = PullRequestModel().check_user_delete(
            pull_request, self._rhodecode_user) and not pr_closed

        # only owner can delete it !
        if allowed_to_delete:
            PullRequestModel().delete(pull_request, self._rhodecode_user)
            Session().commit()
            h.flash(_('Successfully deleted pull request'),
                    category='success')
            raise HTTPFound(h.route_path('pullrequest_show_all',
                                         repo_name=self.db_repo_name))

        log.warning('user %s tried to delete pull request without access',
                    self._rhodecode_user)
        raise HTTPNotFound()

    @LoginRequired()
    @NotAnonymous()
    @HasRepoPermissionAnyDecorator(
        'repository.read', 'repository.write', 'repository.admin')
    @CSRFRequired()
    @view_config(
        route_name='pullrequest_comment_create', request_method='POST',
        renderer='json_ext')
    def pull_request_comment_create(self):
        _ = self.request.translate

        pull_request = PullRequest.get_or_404(
            self.request.matchdict['pull_request_id'])
        pull_request_id = pull_request.pull_request_id

        if pull_request.is_closed():
            log.debug('comment: forbidden because pull request is closed')
            raise HTTPForbidden()

        allowed_to_comment = PullRequestModel().check_user_comment(
            pull_request, self._rhodecode_user)
        if not allowed_to_comment:
            log.debug('comment: forbidden because pull request is from forbidden repo')
            raise HTTPForbidden()

        c = self.load_default_context()

        status = self.request.POST.get('changeset_status', None)
        text = self.request.POST.get('text')
        comment_type = self.request.POST.get('comment_type')
        resolves_comment_id = self.request.POST.get('resolves_comment_id', None)
        close_pull_request = self.request.POST.get('close_pull_request')

        # the logic here should work like following, if we submit close
        # pr comment, use `close_pull_request_with_comment` function
        # else handle regular comment logic

        if close_pull_request:
            # only owner or admin or person with write permissions
            allowed_to_close = PullRequestModel().check_user_update(
                pull_request, self._rhodecode_user)
            if not allowed_to_close:
                log.debug('comment: forbidden because not allowed to close '
                          'pull request %s', pull_request_id)
                raise HTTPForbidden()

            # This also triggers `review_status_change`
            comment, status = PullRequestModel().close_pull_request_with_comment(
                pull_request, self._rhodecode_user, self.db_repo, message=text,
                auth_user=self._rhodecode_user)
            Session().flush()
            is_inline = comment.is_inline

            PullRequestModel().trigger_pull_request_hook(
                pull_request, self._rhodecode_user, 'comment',
                data={'comment': comment})

        else:
            # regular comment case, could be inline, or one with status.
            # for that one we check also permissions

            allowed_to_change_status = PullRequestModel().check_user_change_status(
                pull_request, self._rhodecode_user)

            if status and allowed_to_change_status:
                message = (_('Status change %(transition_icon)s %(status)s')
                           % {'transition_icon': '>',
                              'status': ChangesetStatus.get_status_lbl(status)})
                text = text or message

            comment = CommentsModel().create(
                text=text,
                repo=self.db_repo.repo_id,
                user=self._rhodecode_user.user_id,
                pull_request=pull_request,
                f_path=self.request.POST.get('f_path'),
                line_no=self.request.POST.get('line'),
                status_change=(ChangesetStatus.get_status_lbl(status)
                               if status and allowed_to_change_status else None),
                status_change_type=(status
                                    if status and allowed_to_change_status else None),
                comment_type=comment_type,
                resolves_comment_id=resolves_comment_id,
                auth_user=self._rhodecode_user
            )
            is_inline = comment.is_inline

            if allowed_to_change_status:
                # calculate old status before we change it
                old_calculated_status = pull_request.calculated_review_status()

                # get status if set !
                if status:
                    ChangesetStatusModel().set_status(
                        self.db_repo.repo_id,
                        status,
                        self._rhodecode_user.user_id,
                        comment,
                        pull_request=pull_request
                    )

                Session().flush()
                # this is somehow required to get access to some relationship
                # loaded on comment
                Session().refresh(comment)

                PullRequestModel().trigger_pull_request_hook(
                    pull_request, self._rhodecode_user, 'comment',
                    data={'comment': comment})

                # we now calculate the status of pull request, and based on that
                # calculation we set the commits status
                calculated_status = pull_request.calculated_review_status()
                if old_calculated_status != calculated_status:
                    PullRequestModel().trigger_pull_request_hook(
                        pull_request, self._rhodecode_user, 'review_status_change',
                        data={'status': calculated_status})

        Session().commit()

        data = {
            'target_id': h.safeid(h.safe_unicode(
                self.request.POST.get('f_path'))),
        }
        if comment:
            c.co = comment
            c.at_version_num = None
            rendered_comment = render(
                'rhodecode:templates/changeset/changeset_comment_block.mako',
                self._get_template_context(c), self.request)

            data.update(comment.get_dict())
            data.update({'rendered_text': rendered_comment})

            comment_broadcast_channel = channelstream.comment_channel(
                self.db_repo_name, pull_request_obj=pull_request)

            comment_data = data
            comment_type = 'inline' if is_inline else 'general'
            channelstream.comment_channelstream_push(
                self.request, comment_broadcast_channel, self._rhodecode_user,
                _('posted a new {} comment').format(comment_type),
                comment_data=comment_data)

        return data

    @LoginRequired()
    @NotAnonymous()
    @HasRepoPermissionAnyDecorator(
        'repository.read', 'repository.write', 'repository.admin')
    @CSRFRequired()
    @view_config(
        route_name='pullrequest_comment_delete', request_method='POST',
        renderer='json_ext')
    def pull_request_comment_delete(self):
        pull_request = PullRequest.get_or_404(
            self.request.matchdict['pull_request_id'])

        comment = ChangesetComment.get_or_404(
            self.request.matchdict['comment_id'])
        comment_id = comment.comment_id

        if comment.immutable:
            # don't allow deleting comments that are immutable
            raise HTTPForbidden()

        if pull_request.is_closed():
            log.debug('comment: forbidden because pull request is closed')
            raise HTTPForbidden()

        if not comment:
            log.debug('Comment with id:%s not found, skipping', comment_id)
            # comment already deleted in another call probably
            return True

        if comment.pull_request.is_closed():
            # don't allow deleting comments on closed pull request
            raise HTTPForbidden()

        is_repo_admin = h.HasRepoPermissionAny('repository.admin')(self.db_repo_name)
        super_admin = h.HasPermissionAny('hg.admin')()
        comment_owner = comment.author.user_id == self._rhodecode_user.user_id
        is_repo_comment = comment.repo.repo_name == self.db_repo_name
        comment_repo_admin = is_repo_admin and is_repo_comment

        if super_admin or comment_owner or comment_repo_admin:
            old_calculated_status = comment.pull_request.calculated_review_status()
            CommentsModel().delete(comment=comment, auth_user=self._rhodecode_user)
            Session().commit()
            calculated_status = comment.pull_request.calculated_review_status()
            if old_calculated_status != calculated_status:
                PullRequestModel().trigger_pull_request_hook(
                    comment.pull_request, self._rhodecode_user, 'review_status_change',
                    data={'status': calculated_status})
            return True
        else:
            log.warning('No permissions for user %s to delete comment_id: %s',
                        self._rhodecode_db_user, comment_id)
            raise HTTPNotFound()

    @LoginRequired()
    @NotAnonymous()
    @HasRepoPermissionAnyDecorator(
        'repository.read', 'repository.write', 'repository.admin')
    @CSRFRequired()
    @view_config(
        route_name='pullrequest_comment_edit', request_method='POST',
        renderer='json_ext')
    def pull_request_comment_edit(self):
        self.load_default_context()

        pull_request = PullRequest.get_or_404(
            self.request.matchdict['pull_request_id']
        )
        comment = ChangesetComment.get_or_404(
            self.request.matchdict['comment_id']
        )
        comment_id = comment.comment_id

        if comment.immutable:
            # don't allow deleting comments that are immutable
            raise HTTPForbidden()

        if pull_request.is_closed():
            log.debug('comment: forbidden because pull request is closed')
            raise HTTPForbidden()

        if not comment:
            log.debug('Comment with id:%s not found, skipping', comment_id)
            # comment already deleted in another call probably
            return True

        if comment.pull_request.is_closed():
            # don't allow deleting comments on closed pull request
            raise HTTPForbidden()

        is_repo_admin = h.HasRepoPermissionAny('repository.admin')(self.db_repo_name)
        super_admin = h.HasPermissionAny('hg.admin')()
        comment_owner = comment.author.user_id == self._rhodecode_user.user_id
        is_repo_comment = comment.repo.repo_name == self.db_repo_name
        comment_repo_admin = is_repo_admin and is_repo_comment

        if super_admin or comment_owner or comment_repo_admin:
            text = self.request.POST.get('text')
            version = self.request.POST.get('version')
            if text == comment.text:
                log.warning(
                    'Comment(PR): '
                    'Trying to create new version '
                    'with the same comment body {}'.format(
                        comment_id,
                    )
                )
                raise HTTPNotFound()

            if version.isdigit():
                version = int(version)
            else:
                log.warning(
                    'Comment(PR): Wrong version type {} {} '
                    'for comment {}'.format(
                        version,
                        type(version),
                        comment_id,
                    )
                )
                raise HTTPNotFound()

            try:
                comment_history = CommentsModel().edit(
                    comment_id=comment_id,
                    text=text,
                    auth_user=self._rhodecode_user,
                    version=version,
                )
            except CommentVersionMismatch:
                raise HTTPConflict()

            if not comment_history:
                raise HTTPNotFound()

            Session().commit()

            PullRequestModel().trigger_pull_request_hook(
                pull_request, self._rhodecode_user, 'comment_edit',
                data={'comment': comment})

            return {
                'comment_history_id': comment_history.comment_history_id,
                'comment_id': comment.comment_id,
                'comment_version': comment_history.version,
                'comment_author_username': comment_history.author.username,
                'comment_author_gravatar': h.gravatar_url(comment_history.author.email, 16),
                'comment_created_on': h.age_component(comment_history.created_on,
                                                      time_is_local=True),
            }
        else:
            log.warning('No permissions for user %s to edit comment_id: %s',
                        self._rhodecode_db_user, comment_id)
            raise HTTPNotFound()
