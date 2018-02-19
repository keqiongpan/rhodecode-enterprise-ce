# -*- coding: utf-8 -*-

# Copyright (C) 2011-2018 RhodeCode GmbH
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
    HTTPFound, HTTPNotFound, HTTPForbidden, HTTPBadRequest)
from pyramid.view import view_config
from pyramid.renderers import render

from rhodecode import events
from rhodecode.apps._base import RepoAppView, DataGridAppView

from rhodecode.lib import helpers as h, diffs, codeblocks, channelstream
from rhodecode.lib.base import vcs_operation_context
from rhodecode.lib.ext_json import json
from rhodecode.lib.auth import (
    LoginRequired, HasRepoPermissionAny, HasRepoPermissionAnyDecorator,
    NotAnonymous, CSRFRequired)
from rhodecode.lib.utils2 import str2bool, safe_str, safe_unicode
from rhodecode.lib.vcs.backends.base import EmptyCommit, UpdateFailureReason
from rhodecode.lib.vcs.exceptions import (CommitDoesNotExistError,
    RepositoryRequirementError, NodeDoesNotExistError, EmptyRepositoryError)
from rhodecode.model.changeset_status import ChangesetStatusModel
from rhodecode.model.comment import CommentsModel
from rhodecode.model.db import (func, or_, PullRequest, PullRequestVersion,
    ChangesetComment, ChangesetStatus, Repository)
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
        diffset = self.path_filter.render_patchset_filtered(
            diffset, _parsed, target_commit.raw_id, source_commit.raw_id)

        return diffset

    @LoginRequired()
    @HasRepoPermissionAnyDecorator(
        'repository.read', 'repository.write', 'repository.admin')
    @view_config(
        route_name='pullrequest_show', request_method='GET',
        renderer='rhodecode:templates/pullrequests/pullrequest_show.mako')
    def pull_request_show(self):
        pull_request_id = self.request.matchdict['pull_request_id']

        c = self.load_default_context()

        version = self.request.GET.get('version')
        from_version = self.request.GET.get('from_version') or version
        merge_checks = self.request.GET.get('merge_checks')
        c.fulldiff = str2bool(self.request.GET.get('fulldiff'))

        (pull_request_latest,
         pull_request_at_ver,
         pull_request_display_obj,
         at_version) = PullRequestModel().get_pr_version(
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
         prev_at_version) = PullRequestModel().get_pr_version(
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
            pull_request_latest, user=self._rhodecode_user,
            translator=self.request.translate)
        c.pr_merge_errors = _merge_check.error_details
        c.pr_merge_possible = not _merge_check.failed
        c.pr_merge_message = _merge_check.merge_msg

        c.pr_merge_info = MergeCheck.get_merge_conditions(
            pull_request_latest, translator=self.request.translate)

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

        if source_repo.parent:
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
        route_name='pullrequest_repo_destinations', request_method='GET',
        renderer='json_ext', xhr=True)
    def pull_request_repo_destinations(self):
        _ = self.request.translate
        filter_query = self.request.GET.get('query')

        query = Repository.query() \
            .order_by(func.length(Repository.repo_name)) \
            .filter(
                or_(Repository.repo_name == self.db_repo.repo_name,
                    Repository.fork_id == self.db_repo.repo_id))

        if filter_query:
            ilike_expression = u'%{}%'.format(safe_unicode(filter_query))
            query = query.filter(
                Repository.repo_name.ilike(ilike_expression))

        add_parent = False
        if self.db_repo.parent:
            if filter_query in self.db_repo.parent.repo_name:
                parent_vcs_obj = self.db_repo.parent.scm_instance()
                if parent_vcs_obj and not parent_vcs_obj.is_empty():
                    add_parent = True

        limit = 20 - 1 if add_parent else 20
        all_repos = query.limit(limit).all()
        if add_parent:
            all_repos += [self.db_repo.parent]

        repos = []
        for obj in ScmModel().get_repos(all_repos):
            repos.append({
                'id': obj['name'],
                'text': obj['name'],
                'type': 'repo',
                'obj': obj['dbrepo']
            })

        data = {
            'more': False,
            'results': [{
                'text': _('Repositories'),
                'children': repos
            }] if repos else []
        }
        return data

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

        # find the ancestor for this pr
        source_db_repo = Repository.get_by_repo_name(_form['source_repo'])
        target_db_repo = Repository.get_by_repo_name(_form['target_repo'])

        # re-check permissions again here
        # source_repo we must have read permissions

        source_perm = HasRepoPermissionAny(
            'repository.read',
            'repository.write', 'repository.admin')(source_db_repo.repo_name)
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
            'repository.read',
            'repository.write', 'repository.admin')(target_db_repo.repo_name)
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

        source_commit = source_scm.get_commit(source_ref.split(':')[-1])
        target_commit = target_scm.get_commit(target_ref.split(':')[-1])

        ancestor = source_scm.get_common_ancestor(
            source_commit.raw_id, target_commit.raw_id, target_scm)

        target_ref_type, target_ref_name, __ = _form['target_ref'].split(':')
        target_ref = ':'.join((target_ref_type, target_ref_name, ancestor))

        pullrequest_title = _form['pullrequest_title']
        title_source_ref = source_ref.split(':', 2)[1]
        if not pullrequest_title:
            pullrequest_title = PullRequestModel().generate_pullrequest_title(
                source=source_repo,
                source_ref=title_source_ref,
                target=target_repo
            )

        description = _form['pullrequest_desc']

        get_default_reviewers_data, validate_default_reviewers = \
            PullRequestModel().get_reviewer_functions()

        # recalculate reviewers logic, to make sure we can validate this
        reviewer_rules = get_default_reviewers_data(
            self._rhodecode_db_user, source_db_repo,
            source_commit, target_db_repo, target_commit)

        given_reviewers = _form['review_members']
        reviewers = validate_default_reviewers(given_reviewers, reviewer_rules)

        try:
            pull_request = PullRequestModel().create(
                self._rhodecode_user.user_id, source_repo, source_ref,
                target_repo, target_ref, commit_ids, reviewers,
                pullrequest_title, description, reviewer_rules
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

        self.load_default_context()

        if pull_request.is_closed():
            log.debug('update: forbidden because pull request is closed')
            msg = _(u'Cannot update closed pull requests.')
            h.flash(msg, category='error')
            return True

        # only owner or admin can update it
        allowed_to_update = PullRequestModel().check_user_update(
            pull_request, self._rhodecode_user)
        if allowed_to_update:
            controls = peppercorn.parse(self.request.POST.items())

            if 'review_members' in controls:
                self._update_reviewers(
                    pull_request, controls['review_members'],
                    pull_request.reviewer_data)
            elif str2bool(self.request.POST.get('update_commits', 'false')):
                self._update_commits(pull_request)
            elif str2bool(self.request.POST.get('edit_pull_request', 'false')):
                self._edit_pull_request(pull_request)
            else:
                raise HTTPBadRequest()
            return True
        raise HTTPForbidden()

    def _edit_pull_request(self, pull_request):
        _ = self.request.translate
        try:
            PullRequestModel().edit(
                pull_request, self.request.POST.get('title'),
                self.request.POST.get('description'), self._rhodecode_user)
        except ValueError:
            msg = _(u'Cannot update closed pull requests.')
            h.flash(msg, category='error')
            return
        else:
            Session().commit()

        msg = _(u'Pull request title & description updated.')
        h.flash(msg, category='success')
        return

    def _update_commits(self, pull_request):
        _ = self.request.translate
        resp = PullRequestModel().update_commits(pull_request)

        if resp.executed:

            if resp.target_changed and resp.source_changed:
                changed = 'target and source repositories'
            elif resp.target_changed and not resp.source_changed:
                changed = 'target repository'
            elif not resp.target_changed and resp.source_changed:
                changed = 'source repository'
            else:
                changed = 'nothing'

            msg = _(
                u'Pull request updated to "{source_commit_id}" with '
                u'{count_added} added, {count_removed} removed commits. '
                u'Source of changes: {change_source}')
            msg = msg.format(
                source_commit_id=pull_request.source_ref_parts.commit_id,
                count_added=len(resp.changes.added),
                count_removed=len(resp.changes.removed),
                change_source=changed)
            h.flash(msg, category='success')

            channel = '/repo${}$/pr/{}'.format(
                pull_request.target_repo.repo_name,
                pull_request.pull_request_id)
            message = msg + (
                ' - <a onclick="window.location.reload()">'
                '<strong>{}</strong></a>'.format(_('Reload page')))
            channelstream.post_message(
                channel, message, self._rhodecode_user.username,
                registry=self.request.registry)
        else:
            msg = PullRequestModel.UPDATE_STATUS_MESSAGES[resp.reason]
            warning_reasons = [
                UpdateFailureReason.NO_CHANGE,
                UpdateFailureReason.WRONG_REF_TYPE,
            ]
            category = 'warning' if resp.reason in warning_reasons else 'error'
            h.flash(msg, category=category)

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

        self.load_default_context()
        check = MergeCheck.validate(pull_request, self._rhodecode_db_user,
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
        merge_resp = PullRequestModel().merge(pull_request, user, extras=extras)

        if merge_resp.executed:
            log.debug("The merge was successful, closing the pull request.")
            PullRequestModel().close_pull_request(
                pull_request.pull_request_id, user)
            Session().commit()
            msg = _('Pull request was successfully merged and closed.')
            h.flash(msg, category='success')
        else:
            log.debug(
                "The merge was not successful. Merge response: %s",
                merge_resp)
            msg = PullRequestModel().merge_status_message(
                merge_resp.failure_reason)
            h.flash(msg, category='error')

    def _update_reviewers(self, pull_request, review_members, reviewer_rules):
        _ = self.request.translate
        get_default_reviewers_data, validate_default_reviewers = \
            PullRequestModel().get_reviewer_functions()

        try:
            reviewers = validate_default_reviewers(review_members, reviewer_rules)
        except ValueError as e:
            log.error('Reviewers Validation: {}'.format(e))
            h.flash(e, category='error')
            return

        PullRequestModel().update_reviewers(
            pull_request, reviewers, self._rhodecode_user)
        h.flash(_('Pull request reviewers updated.'), category='success')
        Session().commit()

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
            log.debug(
                'comment: forbidden because pull request is from forbidden repo')
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
            comment, status = PullRequestModel().close_pull_request_with_comment(
                pull_request, self._rhodecode_user, self.db_repo, message=text)
            Session().flush()
            events.trigger(
                events.PullRequestCommentEvent(pull_request, comment))

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
                resolves_comment_id=resolves_comment_id
            )

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

                events.trigger(
                    events.PullRequestCommentEvent(pull_request, comment))

                # we now calculate the status of pull request, and based on that
                # calculation we set the commits status
                calculated_status = pull_request.calculated_review_status()
                if old_calculated_status != calculated_status:
                    PullRequestModel()._trigger_pull_request_hook(
                        pull_request, self._rhodecode_user, 'review_status_change')

        Session().commit()

        data = {
            'target_id': h.safeid(h.safe_unicode(
                self.request.POST.get('f_path'))),
        }
        if comment:
            c.co = comment
            rendered_comment = render(
                'rhodecode:templates/changeset/changeset_comment_block.mako',
                self._get_template_context(c), self.request)

            data.update(comment.get_dict())
            data.update({'rendered_text': rendered_comment})

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
            CommentsModel().delete(comment=comment, user=self._rhodecode_user)
            Session().commit()
            calculated_status = comment.pull_request.calculated_review_status()
            if old_calculated_status != calculated_status:
                PullRequestModel()._trigger_pull_request_hook(
                    comment.pull_request, self._rhodecode_user, 'review_status_change')
            return True
        else:
            log.warning('No permissions for user %s to delete comment_id: %s',
                        self._rhodecode_db_user, comment_id)
            raise HTTPNotFound()
