# -*- coding: utf-8 -*-

# Copyright (C) 2012-2017 RhodeCode GmbH
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
pull requests controller for rhodecode for initializing pull requests
"""
import types

import peppercorn
import formencode
import logging
import collections

from webob.exc import HTTPNotFound, HTTPForbidden, HTTPBadRequest
from pylons import request, tmpl_context as c, url
from pylons.controllers.util import redirect
from pylons.i18n.translation import _
from pyramid.threadlocal import get_current_registry
from sqlalchemy.sql import func
from sqlalchemy.sql.expression import or_

from rhodecode import events
from rhodecode.lib import auth, diffs, helpers as h, codeblocks
from rhodecode.lib.ext_json import json
from rhodecode.lib.base import (
    BaseRepoController, render, vcs_operation_context)
from rhodecode.lib.auth import (
    LoginRequired, HasRepoPermissionAnyDecorator, NotAnonymous,
    HasAcceptedRepoType, XHRRequired)
from rhodecode.lib.channelstream import channelstream_request
from rhodecode.lib.utils import jsonify
from rhodecode.lib.utils2 import (
    safe_int, safe_str, str2bool, safe_unicode)
from rhodecode.lib.vcs.backends.base import (
    EmptyCommit, UpdateFailureReason, EmptyRepository)
from rhodecode.lib.vcs.exceptions import (
    EmptyRepositoryError, CommitDoesNotExistError, RepositoryRequirementError,
    NodeDoesNotExistError)

from rhodecode.model.changeset_status import ChangesetStatusModel
from rhodecode.model.comment import CommentsModel
from rhodecode.model.db import (PullRequest, ChangesetStatus, ChangesetComment,
    Repository, PullRequestVersion)
from rhodecode.model.forms import PullRequestForm
from rhodecode.model.meta import Session
from rhodecode.model.pull_request import PullRequestModel, MergeCheck

log = logging.getLogger(__name__)


class PullrequestsController(BaseRepoController):

    def __before__(self):
        super(PullrequestsController, self).__before__()
        c.REVIEW_STATUS_APPROVED = ChangesetStatus.STATUS_APPROVED
        c.REVIEW_STATUS_REJECTED = ChangesetStatus.STATUS_REJECTED

    @LoginRequired()
    @NotAnonymous()
    @HasRepoPermissionAnyDecorator('repository.read', 'repository.write',
                                   'repository.admin')
    @HasAcceptedRepoType('git', 'hg')
    def index(self):
        source_repo = c.rhodecode_db_repo

        try:
            source_repo.scm_instance().get_commit()
        except EmptyRepositoryError:
            h.flash(h.literal(_('There are no commits yet')),
                    category='warning')
            redirect(url('summary_home', repo_name=source_repo.repo_name))

        commit_id = request.GET.get('commit')
        branch_ref = request.GET.get('branch')
        bookmark_ref = request.GET.get('bookmark')

        try:
            source_repo_data = PullRequestModel().generate_repo_data(
                source_repo, commit_id=commit_id,
                branch=branch_ref, bookmark=bookmark_ref)
        except CommitDoesNotExistError as e:
            log.exception(e)
            h.flash(_('Commit does not exist'), 'error')
            redirect(url('pullrequest_home', repo_name=source_repo.repo_name))

        default_target_repo = source_repo

        if source_repo.parent:
            parent_vcs_obj = source_repo.parent.scm_instance()
            if parent_vcs_obj and not parent_vcs_obj.is_empty():
                # change default if we have a parent repo
                default_target_repo = source_repo.parent

        target_repo_data = PullRequestModel().generate_repo_data(
            default_target_repo)

        selected_source_ref = source_repo_data['refs']['selected_ref']

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

        return render('/pullrequests/pullrequest.mako')

    @LoginRequired()
    @NotAnonymous()
    @XHRRequired()
    @HasRepoPermissionAnyDecorator('repository.read', 'repository.write',
                                   'repository.admin')
    @jsonify
    def get_repo_refs(self, repo_name, target_repo_name):
        repo = Repository.get_by_repo_name(target_repo_name)
        if not repo:
            raise HTTPNotFound
        return PullRequestModel().generate_repo_data(repo)

    @LoginRequired()
    @NotAnonymous()
    @XHRRequired()
    @HasRepoPermissionAnyDecorator('repository.read', 'repository.write',
                                   'repository.admin')
    @jsonify
    def get_repo_destinations(self, repo_name):
        repo = Repository.get_by_repo_name(repo_name)
        if not repo:
            raise HTTPNotFound
        filter_query = request.GET.get('query')

        query = Repository.query() \
            .order_by(func.length(Repository.repo_name)) \
            .filter(or_(
            Repository.repo_name == repo.repo_name,
            Repository.fork_id == repo.repo_id))

        if filter_query:
            ilike_expression = u'%{}%'.format(safe_unicode(filter_query))
            query = query.filter(
                Repository.repo_name.ilike(ilike_expression))

        add_parent = False
        if repo.parent:
            if filter_query in repo.parent.repo_name:
                parent_vcs_obj = repo.parent.scm_instance()
                if parent_vcs_obj and not parent_vcs_obj.is_empty():
                    add_parent = True

        limit = 20 - 1 if add_parent else 20
        all_repos = query.limit(limit).all()
        if add_parent:
            all_repos += [repo.parent]

        repos = []
        for obj in self.scm_model.get_repos(all_repos):
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
    @HasRepoPermissionAnyDecorator('repository.read', 'repository.write',
                                   'repository.admin')
    @HasAcceptedRepoType('git', 'hg')
    @auth.CSRFRequired()
    def create(self, repo_name):
        repo = Repository.get_by_repo_name(repo_name)
        if not repo:
            raise HTTPNotFound

        controls = peppercorn.parse(request.POST.items())

        try:
            _form = PullRequestForm(repo.repo_id)().to_python(controls)
        except formencode.Invalid as errors:
            if errors.error_dict.get('revisions'):
                msg = 'Revisions: %s' % errors.error_dict['revisions']
            elif errors.error_dict.get('pullrequest_title'):
                msg = _('Pull request requires a title with min. 3 chars')
            else:
                msg = _('Error creating pull request: {}').format(errors)
            log.exception(msg)
            h.flash(msg, 'error')

            # would rather just go back to form ...
            return redirect(url('pullrequest_home', repo_name=repo_name))

        source_repo = _form['source_repo']
        source_ref = _form['source_ref']
        target_repo = _form['target_repo']
        target_ref = _form['target_ref']
        commit_ids = _form['revisions'][::-1]
        reviewers = [
            (r['user_id'], r['reasons']) for r in _form['review_members']]

        # find the ancestor for this pr
        source_db_repo = Repository.get_by_repo_name(_form['source_repo'])
        target_db_repo = Repository.get_by_repo_name(_form['target_repo'])

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
        try:
            pull_request = PullRequestModel().create(
                c.rhodecode_user.user_id, source_repo, source_ref, target_repo,
                target_ref, commit_ids, reviewers, pullrequest_title,
                description
            )
            Session().commit()
            h.flash(_('Successfully opened new pull request'),
                    category='success')
        except Exception as e:
            msg = _('Error occurred during sending pull request')
            log.exception(msg)
            h.flash(msg, category='error')
            return redirect(url('pullrequest_home', repo_name=repo_name))

        return redirect(url('pullrequest_show', repo_name=target_repo,
                            pull_request_id=pull_request.pull_request_id))

    @LoginRequired()
    @NotAnonymous()
    @HasRepoPermissionAnyDecorator('repository.read', 'repository.write',
                                   'repository.admin')
    @auth.CSRFRequired()
    @jsonify
    def update(self, repo_name, pull_request_id):
        pull_request_id = safe_int(pull_request_id)
        pull_request = PullRequest.get_or_404(pull_request_id)
        # only owner or admin can update it
        allowed_to_update = PullRequestModel().check_user_update(
            pull_request, c.rhodecode_user)
        if allowed_to_update:
            controls = peppercorn.parse(request.POST.items())

            if 'review_members' in controls:
                self._update_reviewers(
                    pull_request_id, controls['review_members'])
            elif str2bool(request.POST.get('update_commits', 'false')):
                self._update_commits(pull_request)
            elif str2bool(request.POST.get('close_pull_request', 'false')):
                self._reject_close(pull_request)
            elif str2bool(request.POST.get('edit_pull_request', 'false')):
                self._edit_pull_request(pull_request)
            else:
                raise HTTPBadRequest()
            return True
        raise HTTPForbidden()

    def _edit_pull_request(self, pull_request):
        try:
            PullRequestModel().edit(
                pull_request, request.POST.get('title'),
                request.POST.get('description'))
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

            registry = get_current_registry()
            rhodecode_plugins = getattr(registry, 'rhodecode_plugins', {})
            channelstream_config = rhodecode_plugins.get('channelstream', {})
            if channelstream_config.get('enabled'):
                message = msg + (
                    ' - <a onclick="window.location.reload()">'
                    '<strong>{}</strong></a>'.format(_('Reload page')))
                channel = '/repo${}$/pr/{}'.format(
                    pull_request.target_repo.repo_name,
                    pull_request.pull_request_id
                )
                payload = {
                    'type': 'message',
                    'user': 'system',
                    'exclude_users': [request.user.username],
                    'channel': channel,
                    'message': {
                        'message': message,
                        'level': 'success',
                        'topic': '/notifications'
                    }
                }
                channelstream_request(
                    channelstream_config, [payload], '/message',
                    raise_exc=False)
        else:
            msg = PullRequestModel.UPDATE_STATUS_MESSAGES[resp.reason]
            warning_reasons = [
                UpdateFailureReason.NO_CHANGE,
                UpdateFailureReason.WRONG_REF_TYPE,
            ]
            category = 'warning' if resp.reason in warning_reasons else 'error'
            h.flash(msg, category=category)

    @auth.CSRFRequired()
    @LoginRequired()
    @NotAnonymous()
    @HasRepoPermissionAnyDecorator('repository.read', 'repository.write',
                                   'repository.admin')
    def merge(self, repo_name, pull_request_id):
        """
        POST /{repo_name}/pull-request/{pull_request_id}

        Merge will perform a server-side merge of the specified
        pull request, if the pull request is approved and mergeable.
        After successful merging, the pull request is automatically
        closed, with a relevant comment.
        """
        pull_request_id = safe_int(pull_request_id)
        pull_request = PullRequest.get_or_404(pull_request_id)
        user = c.rhodecode_user

        check = MergeCheck.validate(pull_request, user)
        merge_possible = not check.failed

        for err_type, error_msg in check.errors:
            h.flash(error_msg, category=err_type)

        if merge_possible:
            log.debug("Pre-conditions checked, trying to merge.")
            extras = vcs_operation_context(
                request.environ, repo_name=pull_request.target_repo.repo_name,
                username=user.username, action='push',
                scm=pull_request.target_repo.repo_type)
            self._merge_pull_request(pull_request, user, extras)

        return redirect(url(
            'pullrequest_show',
            repo_name=pull_request.target_repo.repo_name,
            pull_request_id=pull_request.pull_request_id))

    def _merge_pull_request(self, pull_request, user, extras):
        merge_resp = PullRequestModel().merge(
            pull_request, user, extras=extras)

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

    def _update_reviewers(self, pull_request_id, review_members):
        reviewers = [
            (int(r['user_id']), r['reasons']) for r in review_members]
        PullRequestModel().update_reviewers(pull_request_id, reviewers)
        Session().commit()

    def _reject_close(self, pull_request):
        if pull_request.is_closed():
            raise HTTPForbidden()

        PullRequestModel().close_pull_request_with_comment(
            pull_request, c.rhodecode_user, c.rhodecode_db_repo)
        Session().commit()

    @LoginRequired()
    @NotAnonymous()
    @HasRepoPermissionAnyDecorator('repository.read', 'repository.write',
                                   'repository.admin')
    @auth.CSRFRequired()
    @jsonify
    def delete(self, repo_name, pull_request_id):
        pull_request_id = safe_int(pull_request_id)
        pull_request = PullRequest.get_or_404(pull_request_id)

        pr_closed = pull_request.is_closed()
        allowed_to_delete = PullRequestModel().check_user_delete(
            pull_request, c.rhodecode_user) and not pr_closed

        # only owner can delete it !
        if allowed_to_delete:
            PullRequestModel().delete(pull_request)
            Session().commit()
            h.flash(_('Successfully deleted pull request'),
                    category='success')
            return redirect(url('my_account_pullrequests'))

        h.flash(_('Your are not allowed to delete this pull request'),
                category='error')
        raise HTTPForbidden()

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
            _org_pull_request_obj = pull_request_obj = PullRequest.get_or_404(pull_request_id)

        pull_request_display_obj = PullRequest.get_pr_display_object(
            pull_request_obj, _org_pull_request_obj)

        return _org_pull_request_obj, pull_request_obj, \
               pull_request_display_obj, at_version

    def _get_diffset(
            self, source_repo, source_ref_id, target_ref_id, target_commit,
            source_commit, diff_limit, file_limit, display_inline_comments):
        vcs_diff = PullRequestModel().get_diff(
            source_repo, source_ref_id, target_ref_id)

        diff_processor = diffs.DiffProcessor(
            vcs_diff, format='newdiff', diff_limit=diff_limit,
            file_limit=file_limit, show_full_diff=c.fulldiff)

        _parsed = diff_processor.prepare()

        def _node_getter(commit):
            def get_node(fname):
                try:
                    return commit.get_node(fname)
                except NodeDoesNotExistError:
                    return None

            return get_node

        diffset = codeblocks.DiffSet(
            repo_name=c.repo_name,
            source_repo_name=c.source_repo.repo_name,
            source_node_getter=_node_getter(target_commit),
            target_node_getter=_node_getter(source_commit),
            comments=display_inline_comments
        )
        diffset = diffset.render_patchset(
            _parsed, target_commit.raw_id, source_commit.raw_id)

        return diffset

    @LoginRequired()
    @HasRepoPermissionAnyDecorator('repository.read', 'repository.write',
                                   'repository.admin')
    def show(self, repo_name, pull_request_id):
        pull_request_id = safe_int(pull_request_id)
        version = request.GET.get('version')
        from_version = request.GET.get('from_version') or version
        merge_checks = request.GET.get('merge_checks')
        c.fulldiff = str2bool(request.GET.get('fulldiff'))

        (pull_request_latest,
         pull_request_at_ver,
         pull_request_display_obj,
         at_version) = self._get_pr_version(
            pull_request_id, version=version)
        pr_closed = pull_request_latest.is_closed()

        if pr_closed and (version or from_version):
            # not allow to browse versions
            return redirect(h.url('pullrequest_show', repo_name=repo_name,
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
        if repo_name != pull_request_at_ver.target_repo.repo_name:
            raise HTTPNotFound

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
            c.allowed_to_change_status = PullRequestModel(). \
                check_user_change_status(pull_request_at_ver, c.rhodecode_user) \
                                         and not pr_closed

            c.allowed_to_update = PullRequestModel().check_user_update(
                pull_request_latest, c.rhodecode_user) and not pr_closed
            c.allowed_to_merge = PullRequestModel().check_user_merge(
                pull_request_latest, c.rhodecode_user) and not pr_closed
            c.allowed_to_delete = PullRequestModel().check_user_delete(
                pull_request_latest, c.rhodecode_user) and not pr_closed
            c.allowed_to_comment = not pr_closed
            c.allowed_to_close = c.allowed_to_merge and not pr_closed

        # check merge capabilities
        _merge_check = MergeCheck.validate(
            pull_request_latest, user=c.rhodecode_user)
        c.pr_merge_errors = _merge_check.error_details
        c.pr_merge_possible = not _merge_check.failed
        c.pr_merge_message = _merge_check.merge_msg

        c.pull_request_review_status = _merge_check.review_status
        if merge_checks:
            return render('/pullrequests/pullrequest_merge_checks.mako')

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

        # diff_limit is the old behavior, will cut off the whole diff
        # if the limit is applied  otherwise will just hide the
        # big files from the front-end
        diff_limit = self.cut_off_limit_diff
        file_limit = self.cut_off_limit_file

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

            target_commit = commits_source_repo.get_commit(
                commit_id=safe_str(target_ref_id))
            source_commit = commits_source_repo.get_commit(
                commit_id=safe_str(source_ref_id))
        except CommitDoesNotExistError:
            pass
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

        c.missing_commits = False
        if (c.missing_requirements or isinstance(source_commit, EmptyCommit)
            or source_commit == target_commit):

            c.missing_commits = True
        else:

            c.diffset = self._get_diffset(
                commits_source_repo, source_ref_id, target_ref_id,
                target_commit, source_commit,
                diff_limit, file_limit, display_inline_comments)

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
            if c.rhodecode_user.user_id in allowed_reviewers:
                for co in general_comments:
                    if co.author.user_id == c.rhodecode_user.user_id:
                        # each comment has a status change
                        status = co.status_change
                        if status:
                            _ver_pr = status[0].comment.pull_request_version_id
                            c.review_versions[_ver_pr] = status[0]

        return render('/pullrequests/pullrequest_show.mako')

    @LoginRequired()
    @NotAnonymous()
    @HasRepoPermissionAnyDecorator(
        'repository.read', 'repository.write', 'repository.admin')
    @auth.CSRFRequired()
    @jsonify
    def comment(self, repo_name, pull_request_id):
        pull_request_id = safe_int(pull_request_id)
        pull_request = PullRequest.get_or_404(pull_request_id)
        if pull_request.is_closed():
            raise HTTPForbidden()

        status = request.POST.get('changeset_status', None)
        text = request.POST.get('text')
        comment_type = request.POST.get('comment_type')
        resolves_comment_id = request.POST.get('resolves_comment_id', None)
        close_pull_request = request.POST.get('close_pull_request')

        close_pr = False
        # only owner or admin or person with write permissions
        allowed_to_close = PullRequestModel().check_user_update(
            pull_request, c.rhodecode_user)

        if close_pull_request and allowed_to_close:
            close_pr = True
            pull_request_review_status = pull_request.calculated_review_status()
            if pull_request_review_status == ChangesetStatus.STATUS_APPROVED:
                # approved only if we have voting consent
                status = ChangesetStatus.STATUS_APPROVED
            else:
                status = ChangesetStatus.STATUS_REJECTED

        allowed_to_change_status = PullRequestModel().check_user_change_status(
            pull_request, c.rhodecode_user)

        if status and allowed_to_change_status:
            message = (_('Status change %(transition_icon)s %(status)s')
                       % {'transition_icon': '>',
                          'status': ChangesetStatus.get_status_lbl(status)})
            if close_pr:
                message = _('Closing with') + ' ' + message
            text = text or message
        comm = CommentsModel().create(
            text=text,
            repo=c.rhodecode_db_repo.repo_id,
            user=c.rhodecode_user.user_id,
            pull_request=pull_request_id,
            f_path=request.POST.get('f_path'),
            line_no=request.POST.get('line'),
            status_change=(ChangesetStatus.get_status_lbl(status)
                           if status and allowed_to_change_status else None),
            status_change_type=(status
                                if status and allowed_to_change_status else None),
            closing_pr=close_pr,
            comment_type=comment_type,
            resolves_comment_id=resolves_comment_id
        )

        if allowed_to_change_status:
            old_calculated_status = pull_request.calculated_review_status()
            # get status if set !
            if status:
                ChangesetStatusModel().set_status(
                    c.rhodecode_db_repo.repo_id,
                    status,
                    c.rhodecode_user.user_id,
                    comm,
                    pull_request=pull_request_id
                )

            Session().flush()
            events.trigger(events.PullRequestCommentEvent(pull_request, comm))
            # we now calculate the status of pull request, and based on that
            # calculation we set the commits status
            calculated_status = pull_request.calculated_review_status()
            if old_calculated_status != calculated_status:
                PullRequestModel()._trigger_pull_request_hook(
                    pull_request, c.rhodecode_user, 'review_status_change')

            calculated_status_lbl = ChangesetStatus.get_status_lbl(
                calculated_status)

            if close_pr:
                status_completed = (
                    calculated_status in [ChangesetStatus.STATUS_APPROVED,
                                          ChangesetStatus.STATUS_REJECTED])
                if close_pull_request or status_completed:
                    PullRequestModel().close_pull_request(
                        pull_request_id, c.rhodecode_user)
                else:
                    h.flash(_('Closing pull request on other statuses than '
                              'rejected or approved is forbidden. '
                              'Calculated status from all reviewers '
                              'is currently: %s') % calculated_status_lbl,
                            category='warning')

        Session().commit()

        if not request.is_xhr:
            return redirect(h.url('pullrequest_show', repo_name=repo_name,
                                  pull_request_id=pull_request_id))

        data = {
            'target_id': h.safeid(h.safe_unicode(request.POST.get('f_path'))),
        }
        if comm:
            c.co = comm
            c.inline_comment = True if comm.line_no else False
            data.update(comm.get_dict())
            data.update({'rendered_text':
                             render('changeset/changeset_comment_block.mako')})

        return data

    @LoginRequired()
    @NotAnonymous()
    @HasRepoPermissionAnyDecorator('repository.read', 'repository.write',
                                   'repository.admin')
    @auth.CSRFRequired()
    @jsonify
    def delete_comment(self, repo_name, comment_id):
        return self._delete_comment(comment_id)

    def _delete_comment(self, comment_id):
        comment_id = safe_int(comment_id)
        co = ChangesetComment.get_or_404(comment_id)
        if co.pull_request.is_closed():
            # don't allow deleting comments on closed pull request
            raise HTTPForbidden()

        is_owner = co.author.user_id == c.rhodecode_user.user_id
        is_repo_admin = h.HasRepoPermissionAny('repository.admin')(c.repo_name)
        if h.HasPermissionAny('hg.admin')() or is_repo_admin or is_owner:
            old_calculated_status = co.pull_request.calculated_review_status()
            CommentsModel().delete(comment=co)
            Session().commit()
            calculated_status = co.pull_request.calculated_review_status()
            if old_calculated_status != calculated_status:
                PullRequestModel()._trigger_pull_request_hook(
                    co.pull_request, c.rhodecode_user, 'review_status_change')
            return True
        else:
            raise HTTPForbidden()
