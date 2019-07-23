# -*- coding: utf-8 -*-

# Copyright (C) 2012-2019 RhodeCode GmbH
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
pull request model for RhodeCode
"""


import json
import logging
import datetime
import urllib
import collections

from pyramid import compat
from pyramid.threadlocal import get_current_request

from rhodecode import events
from rhodecode.translation import lazy_ugettext
from rhodecode.lib import helpers as h, hooks_utils, diffs
from rhodecode.lib import audit_logger
from rhodecode.lib.compat import OrderedDict
from rhodecode.lib.hooks_daemon import prepare_callback_daemon
from rhodecode.lib.markup_renderer import (
    DEFAULT_COMMENTS_RENDERER, RstTemplateRenderer)
from rhodecode.lib.utils2 import safe_unicode, safe_str, md5_safe
from rhodecode.lib.vcs.backends.base import (
    Reference, MergeResponse, MergeFailureReason, UpdateFailureReason)
from rhodecode.lib.vcs.conf import settings as vcs_settings
from rhodecode.lib.vcs.exceptions import (
    CommitDoesNotExistError, EmptyRepositoryError)
from rhodecode.model import BaseModel
from rhodecode.model.changeset_status import ChangesetStatusModel
from rhodecode.model.comment import CommentsModel
from rhodecode.model.db import (
    or_, PullRequest, PullRequestReviewers, ChangesetStatus,
    PullRequestVersion, ChangesetComment, Repository, RepoReviewRule)
from rhodecode.model.meta import Session
from rhodecode.model.notification import NotificationModel, \
    EmailNotificationModel
from rhodecode.model.scm import ScmModel
from rhodecode.model.settings import VcsSettingsModel


log = logging.getLogger(__name__)


# Data structure to hold the response data when updating commits during a pull
# request update.
UpdateResponse = collections.namedtuple('UpdateResponse', [
    'executed', 'reason', 'new', 'old', 'changes',
    'source_changed', 'target_changed'])


class PullRequestModel(BaseModel):

    cls = PullRequest

    DIFF_CONTEXT = diffs.DEFAULT_CONTEXT

    UPDATE_STATUS_MESSAGES = {
        UpdateFailureReason.NONE: lazy_ugettext(
            'Pull request update successful.'),
        UpdateFailureReason.UNKNOWN: lazy_ugettext(
            'Pull request update failed because of an unknown error.'),
        UpdateFailureReason.NO_CHANGE: lazy_ugettext(
            'No update needed because the source and target have not changed.'),
        UpdateFailureReason.WRONG_REF_TYPE: lazy_ugettext(
            'Pull request cannot be updated because the reference type is '
            'not supported for an update. Only Branch, Tag or Bookmark is allowed.'),
        UpdateFailureReason.MISSING_TARGET_REF: lazy_ugettext(
            'This pull request cannot be updated because the target '
            'reference is missing.'),
        UpdateFailureReason.MISSING_SOURCE_REF: lazy_ugettext(
            'This pull request cannot be updated because the source '
            'reference is missing.'),
    }
    REF_TYPES = ['bookmark', 'book', 'tag', 'branch']
    UPDATABLE_REF_TYPES = ['bookmark', 'book', 'branch']

    def __get_pull_request(self, pull_request):
        return self._get_instance((
            PullRequest, PullRequestVersion), pull_request)

    def _check_perms(self, perms, pull_request, user, api=False):
        if not api:
            return h.HasRepoPermissionAny(*perms)(
                user=user, repo_name=pull_request.target_repo.repo_name)
        else:
            return h.HasRepoPermissionAnyApi(*perms)(
                user=user, repo_name=pull_request.target_repo.repo_name)

    def check_user_read(self, pull_request, user, api=False):
        _perms = ('repository.admin', 'repository.write', 'repository.read',)
        return self._check_perms(_perms, pull_request, user, api)

    def check_user_merge(self, pull_request, user, api=False):
        _perms = ('repository.admin', 'repository.write', 'hg.admin',)
        return self._check_perms(_perms, pull_request, user, api)

    def check_user_update(self, pull_request, user, api=False):
        owner = user.user_id == pull_request.user_id
        return self.check_user_merge(pull_request, user, api) or owner

    def check_user_delete(self, pull_request, user):
        owner = user.user_id == pull_request.user_id
        _perms = ('repository.admin',)
        return self._check_perms(_perms, pull_request, user) or owner

    def check_user_change_status(self, pull_request, user, api=False):
        reviewer = user.user_id in [x.user_id for x in
                                    pull_request.reviewers]
        return self.check_user_update(pull_request, user, api) or reviewer

    def check_user_comment(self, pull_request, user):
        owner = user.user_id == pull_request.user_id
        return self.check_user_read(pull_request, user) or owner

    def get(self, pull_request):
        return self.__get_pull_request(pull_request)

    def _prepare_get_all_query(self, repo_name, source=False, statuses=None,
                               opened_by=None, order_by=None,
                               order_dir='desc', only_created=False):
        repo = None
        if repo_name:
            repo = self._get_repo(repo_name)

        q = PullRequest.query()

        # source or target
        if repo and source:
            q = q.filter(PullRequest.source_repo == repo)
        elif repo:
            q = q.filter(PullRequest.target_repo == repo)

        # closed,opened
        if statuses:
            q = q.filter(PullRequest.status.in_(statuses))

        # opened by filter
        if opened_by:
            q = q.filter(PullRequest.user_id.in_(opened_by))

        # only get those that are in "created" state
        if only_created:
            q = q.filter(PullRequest.pull_request_state == PullRequest.STATE_CREATED)

        if order_by:
            order_map = {
                'name_raw': PullRequest.pull_request_id,
                'id': PullRequest.pull_request_id,
                'title': PullRequest.title,
                'updated_on_raw': PullRequest.updated_on,
                'target_repo': PullRequest.target_repo_id
            }
            if order_dir == 'asc':
                q = q.order_by(order_map[order_by].asc())
            else:
                q = q.order_by(order_map[order_by].desc())

        return q

    def count_all(self, repo_name, source=False, statuses=None,
                  opened_by=None):
        """
        Count the number of pull requests for a specific repository.

        :param repo_name: target or source repo
        :param source: boolean flag to specify if repo_name refers to source
        :param statuses: list of pull request statuses
        :param opened_by: author user of the pull request
        :returns: int number of pull requests
        """
        q = self._prepare_get_all_query(
            repo_name, source=source, statuses=statuses, opened_by=opened_by)

        return q.count()

    def get_all(self, repo_name, source=False, statuses=None, opened_by=None,
                offset=0, length=None, order_by=None, order_dir='desc'):
        """
        Get all pull requests for a specific repository.

        :param repo_name: target or source repo
        :param source: boolean flag to specify if repo_name refers to source
        :param statuses: list of pull request statuses
        :param opened_by: author user of the pull request
        :param offset: pagination offset
        :param length: length of returned list
        :param order_by: order of the returned list
        :param order_dir: 'asc' or 'desc' ordering direction
        :returns: list of pull requests
        """
        q = self._prepare_get_all_query(
            repo_name, source=source, statuses=statuses, opened_by=opened_by,
            order_by=order_by, order_dir=order_dir)

        if length:
            pull_requests = q.limit(length).offset(offset).all()
        else:
            pull_requests = q.all()

        return pull_requests

    def count_awaiting_review(self, repo_name, source=False, statuses=None,
                              opened_by=None):
        """
        Count the number of pull requests for a specific repository that are
        awaiting review.

        :param repo_name: target or source repo
        :param source: boolean flag to specify if repo_name refers to source
        :param statuses: list of pull request statuses
        :param opened_by: author user of the pull request
        :returns: int number of pull requests
        """
        pull_requests = self.get_awaiting_review(
            repo_name, source=source, statuses=statuses, opened_by=opened_by)

        return len(pull_requests)

    def get_awaiting_review(self, repo_name, source=False, statuses=None,
                            opened_by=None, offset=0, length=None,
                            order_by=None, order_dir='desc'):
        """
        Get all pull requests for a specific repository that are awaiting
        review.

        :param repo_name: target or source repo
        :param source: boolean flag to specify if repo_name refers to source
        :param statuses: list of pull request statuses
        :param opened_by: author user of the pull request
        :param offset: pagination offset
        :param length: length of returned list
        :param order_by: order of the returned list
        :param order_dir: 'asc' or 'desc' ordering direction
        :returns: list of pull requests
        """
        pull_requests = self.get_all(
            repo_name, source=source, statuses=statuses, opened_by=opened_by,
            order_by=order_by, order_dir=order_dir)

        _filtered_pull_requests = []
        for pr in pull_requests:
            status = pr.calculated_review_status()
            if status in [ChangesetStatus.STATUS_NOT_REVIEWED,
                          ChangesetStatus.STATUS_UNDER_REVIEW]:
                _filtered_pull_requests.append(pr)
        if length:
            return _filtered_pull_requests[offset:offset+length]
        else:
            return _filtered_pull_requests

    def count_awaiting_my_review(self, repo_name, source=False, statuses=None,
                                 opened_by=None, user_id=None):
        """
        Count the number of pull requests for a specific repository that are
        awaiting review from a specific user.

        :param repo_name: target or source repo
        :param source: boolean flag to specify if repo_name refers to source
        :param statuses: list of pull request statuses
        :param opened_by: author user of the pull request
        :param user_id: reviewer user of the pull request
        :returns: int number of pull requests
        """
        pull_requests = self.get_awaiting_my_review(
            repo_name, source=source, statuses=statuses, opened_by=opened_by,
            user_id=user_id)

        return len(pull_requests)

    def get_awaiting_my_review(self, repo_name, source=False, statuses=None,
                               opened_by=None, user_id=None, offset=0,
                               length=None, order_by=None, order_dir='desc'):
        """
        Get all pull requests for a specific repository that are awaiting
        review from a specific user.

        :param repo_name: target or source repo
        :param source: boolean flag to specify if repo_name refers to source
        :param statuses: list of pull request statuses
        :param opened_by: author user of the pull request
        :param user_id: reviewer user of the pull request
        :param offset: pagination offset
        :param length: length of returned list
        :param order_by: order of the returned list
        :param order_dir: 'asc' or 'desc' ordering direction
        :returns: list of pull requests
        """
        pull_requests = self.get_all(
            repo_name, source=source, statuses=statuses, opened_by=opened_by,
            order_by=order_by, order_dir=order_dir)

        _my = PullRequestModel().get_not_reviewed(user_id)
        my_participation = []
        for pr in pull_requests:
            if pr in _my:
                my_participation.append(pr)
        _filtered_pull_requests = my_participation
        if length:
            return _filtered_pull_requests[offset:offset+length]
        else:
            return _filtered_pull_requests

    def get_not_reviewed(self, user_id):
        return [
            x.pull_request for x in PullRequestReviewers.query().filter(
                PullRequestReviewers.user_id == user_id).all()
        ]

    def _prepare_participating_query(self, user_id=None, statuses=None,
                                     order_by=None, order_dir='desc'):
        q = PullRequest.query()
        if user_id:
            reviewers_subquery = Session().query(
                PullRequestReviewers.pull_request_id).filter(
                PullRequestReviewers.user_id == user_id).subquery()
            user_filter = or_(
                PullRequest.user_id == user_id,
                PullRequest.pull_request_id.in_(reviewers_subquery)
            )
            q = PullRequest.query().filter(user_filter)

        # closed,opened
        if statuses:
            q = q.filter(PullRequest.status.in_(statuses))

        if order_by:
            order_map = {
                'name_raw': PullRequest.pull_request_id,
                'title': PullRequest.title,
                'updated_on_raw': PullRequest.updated_on,
                'target_repo': PullRequest.target_repo_id
            }
            if order_dir == 'asc':
                q = q.order_by(order_map[order_by].asc())
            else:
                q = q.order_by(order_map[order_by].desc())

        return q

    def count_im_participating_in(self, user_id=None, statuses=None):
        q = self._prepare_participating_query(user_id, statuses=statuses)
        return q.count()

    def get_im_participating_in(
            self, user_id=None, statuses=None, offset=0,
            length=None, order_by=None, order_dir='desc'):
        """
        Get all Pull requests that i'm participating in, or i have opened
        """

        q = self._prepare_participating_query(
            user_id, statuses=statuses, order_by=order_by,
            order_dir=order_dir)

        if length:
            pull_requests = q.limit(length).offset(offset).all()
        else:
            pull_requests = q.all()

        return pull_requests

    def get_versions(self, pull_request):
        """
        returns version of pull request sorted by ID descending
        """
        return PullRequestVersion.query()\
            .filter(PullRequestVersion.pull_request == pull_request)\
            .order_by(PullRequestVersion.pull_request_version_id.asc())\
            .all()

    def get_pr_version(self, pull_request_id, version=None):
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

    def create(self, created_by, source_repo, source_ref, target_repo,
               target_ref, revisions, reviewers, title, description=None,
               description_renderer=None,
               reviewer_data=None, translator=None, auth_user=None):
        translator = translator or get_current_request().translate

        created_by_user = self._get_user(created_by)
        auth_user = auth_user or created_by_user.AuthUser()
        source_repo = self._get_repo(source_repo)
        target_repo = self._get_repo(target_repo)

        pull_request = PullRequest()
        pull_request.source_repo = source_repo
        pull_request.source_ref = source_ref
        pull_request.target_repo = target_repo
        pull_request.target_ref = target_ref
        pull_request.revisions = revisions
        pull_request.title = title
        pull_request.description = description
        pull_request.description_renderer = description_renderer
        pull_request.author = created_by_user
        pull_request.reviewer_data = reviewer_data
        pull_request.pull_request_state = pull_request.STATE_CREATING
        Session().add(pull_request)
        Session().flush()

        reviewer_ids = set()
        # members / reviewers
        for reviewer_object in reviewers:
            user_id, reasons, mandatory, rules = reviewer_object
            user = self._get_user(user_id)

            # skip duplicates
            if user.user_id in reviewer_ids:
                continue

            reviewer_ids.add(user.user_id)

            reviewer = PullRequestReviewers()
            reviewer.user = user
            reviewer.pull_request = pull_request
            reviewer.reasons = reasons
            reviewer.mandatory = mandatory

            # NOTE(marcink): pick only first rule for now
            rule_id = list(rules)[0] if rules else None
            rule = RepoReviewRule.get(rule_id) if rule_id else None
            if rule:
                review_group = rule.user_group_vote_rule(user_id)
                # we check if this particular reviewer is member of a voting group
                if review_group:
                    # NOTE(marcink):
                    # can be that user is member of more but we pick the first same,
                    # same as default reviewers algo
                    review_group = review_group[0]

                    rule_data = {
                        'rule_name':
                            rule.review_rule_name,
                        'rule_user_group_entry_id':
                            review_group.repo_review_rule_users_group_id,
                        'rule_user_group_name':
                            review_group.users_group.users_group_name,
                        'rule_user_group_members':
                            [x.user.username for x in review_group.users_group.members],
                        'rule_user_group_members_id':
                            [x.user.user_id for x in review_group.users_group.members],
                    }
                    # e.g {'vote_rule': -1, 'mandatory': True}
                    rule_data.update(review_group.rule_data())

                    reviewer.rule_data = rule_data

            Session().add(reviewer)
            Session().flush()

        # Set approval status to "Under Review" for all commits which are
        # part of this pull request.
        ChangesetStatusModel().set_status(
            repo=target_repo,
            status=ChangesetStatus.STATUS_UNDER_REVIEW,
            user=created_by_user,
            pull_request=pull_request
        )
        # we commit early at this point. This has to do with a fact
        # that before queries do some row-locking. And because of that
        # we need to commit and finish transaction before below validate call
        # that for large repos could be long resulting in long row locks
        Session().commit()

        # prepare workspace, and run initial merge simulation. Set state during that
        # operation
        pull_request = PullRequest.get(pull_request.pull_request_id)

        # set as merging, for simulation, and if finished to created so we mark
        # simulation is working fine
        with pull_request.set_state(PullRequest.STATE_MERGING,
                                    final_state=PullRequest.STATE_CREATED):
            MergeCheck.validate(
                pull_request, auth_user=auth_user, translator=translator)

        self.notify_reviewers(pull_request, reviewer_ids)
        self.trigger_pull_request_hook(
            pull_request, created_by_user, 'create')

        creation_data = pull_request.get_api_data(with_merge_state=False)
        self._log_audit_action(
            'repo.pull_request.create', {'data': creation_data},
            auth_user, pull_request)

        return pull_request

    def trigger_pull_request_hook(self, pull_request, user, action, data=None):
        pull_request = self.__get_pull_request(pull_request)
        target_scm = pull_request.target_repo.scm_instance()
        if action == 'create':
            trigger_hook = hooks_utils.trigger_log_create_pull_request_hook
        elif action == 'merge':
            trigger_hook = hooks_utils.trigger_log_merge_pull_request_hook
        elif action == 'close':
            trigger_hook = hooks_utils.trigger_log_close_pull_request_hook
        elif action == 'review_status_change':
            trigger_hook = hooks_utils.trigger_log_review_pull_request_hook
        elif action == 'update':
            trigger_hook = hooks_utils.trigger_log_update_pull_request_hook
        elif action == 'comment':
            # dummy hook ! for comment. We want this function to handle all cases
            def trigger_hook(*args, **kwargs):
                pass
            comment = data['comment']
            events.trigger(events.PullRequestCommentEvent(pull_request, comment))
        else:
            return

        trigger_hook(
            username=user.username,
            repo_name=pull_request.target_repo.repo_name,
            repo_alias=target_scm.alias,
            pull_request=pull_request,
            data=data)

    def _get_commit_ids(self, pull_request):
        """
        Return the commit ids of the merged pull request.

        This method is not dealing correctly yet with the lack of autoupdates
        nor with the implicit target updates.
        For example: if a commit in the source repo is already in the target it
        will be reported anyways.
        """
        merge_rev = pull_request.merge_rev
        if merge_rev is None:
            raise ValueError('This pull request was not merged yet')

        commit_ids = list(pull_request.revisions)
        if merge_rev not in commit_ids:
            commit_ids.append(merge_rev)

        return commit_ids

    def merge_repo(self, pull_request, user, extras):
        log.debug("Merging pull request %s", pull_request.pull_request_id)
        extras['user_agent'] = 'internal-merge'
        merge_state = self._merge_pull_request(pull_request, user, extras)
        if merge_state.executed:
            log.debug("Merge was successful, updating the pull request comments.")
            self._comment_and_close_pr(pull_request, user, merge_state)

            self._log_audit_action(
                'repo.pull_request.merge',
                {'merge_state': merge_state.__dict__},
                user, pull_request)

        else:
            log.warn("Merge failed, not updating the pull request.")
        return merge_state

    def _merge_pull_request(self, pull_request, user, extras, merge_msg=None):
        target_vcs = pull_request.target_repo.scm_instance()
        source_vcs = pull_request.source_repo.scm_instance()

        message = safe_unicode(merge_msg or vcs_settings.MERGE_MESSAGE_TMPL).format(
            pr_id=pull_request.pull_request_id,
            pr_title=pull_request.title,
            source_repo=source_vcs.name,
            source_ref_name=pull_request.source_ref_parts.name,
            target_repo=target_vcs.name,
            target_ref_name=pull_request.target_ref_parts.name,
        )

        workspace_id = self._workspace_id(pull_request)
        repo_id = pull_request.target_repo.repo_id
        use_rebase = self._use_rebase_for_merging(pull_request)
        close_branch = self._close_branch_before_merging(pull_request)

        target_ref = self._refresh_reference(
            pull_request.target_ref_parts, target_vcs)

        callback_daemon, extras = prepare_callback_daemon(
            extras, protocol=vcs_settings.HOOKS_PROTOCOL,
            host=vcs_settings.HOOKS_HOST,
            use_direct_calls=vcs_settings.HOOKS_DIRECT_CALLS)

        with callback_daemon:
            # TODO: johbo: Implement a clean way to run a config_override
            # for a single call.
            target_vcs.config.set(
                'rhodecode', 'RC_SCM_DATA', json.dumps(extras))

            user_name = user.short_contact
            merge_state = target_vcs.merge(
                repo_id, workspace_id, target_ref, source_vcs,
                pull_request.source_ref_parts,
                user_name=user_name, user_email=user.email,
                message=message, use_rebase=use_rebase,
                close_branch=close_branch)
        return merge_state

    def _comment_and_close_pr(self, pull_request, user, merge_state, close_msg=None):
        pull_request.merge_rev = merge_state.merge_ref.commit_id
        pull_request.updated_on = datetime.datetime.now()
        close_msg = close_msg or 'Pull request merged and closed'

        CommentsModel().create(
            text=safe_unicode(close_msg),
            repo=pull_request.target_repo.repo_id,
            user=user.user_id,
            pull_request=pull_request.pull_request_id,
            f_path=None,
            line_no=None,
            closing_pr=True
        )

        Session().add(pull_request)
        Session().flush()
        # TODO: paris: replace invalidation with less radical solution
        ScmModel().mark_for_invalidation(
            pull_request.target_repo.repo_name)
        self.trigger_pull_request_hook(pull_request, user, 'merge')

    def has_valid_update_type(self, pull_request):
        source_ref_type = pull_request.source_ref_parts.type
        return source_ref_type in self.REF_TYPES

    def update_commits(self, pull_request):
        """
        Get the updated list of commits for the pull request
        and return the new pull request version and the list
        of commits processed by this update action
        """
        pull_request = self.__get_pull_request(pull_request)
        source_ref_type = pull_request.source_ref_parts.type
        source_ref_name = pull_request.source_ref_parts.name
        source_ref_id = pull_request.source_ref_parts.commit_id

        target_ref_type = pull_request.target_ref_parts.type
        target_ref_name = pull_request.target_ref_parts.name
        target_ref_id = pull_request.target_ref_parts.commit_id

        if not self.has_valid_update_type(pull_request):
            log.debug("Skipping update of pull request %s due to ref type: %s",
                      pull_request, source_ref_type)
            return UpdateResponse(
                executed=False,
                reason=UpdateFailureReason.WRONG_REF_TYPE,
                old=pull_request, new=None, changes=None,
                source_changed=False, target_changed=False)

        # source repo
        source_repo = pull_request.source_repo.scm_instance()

        try:
            source_commit = source_repo.get_commit(commit_id=source_ref_name)
        except CommitDoesNotExistError:
            return UpdateResponse(
                executed=False,
                reason=UpdateFailureReason.MISSING_SOURCE_REF,
                old=pull_request, new=None, changes=None,
                source_changed=False, target_changed=False)

        source_changed = source_ref_id != source_commit.raw_id

        # target repo
        target_repo = pull_request.target_repo.scm_instance()

        try:
            target_commit = target_repo.get_commit(commit_id=target_ref_name)
        except CommitDoesNotExistError:
            return UpdateResponse(
                executed=False,
                reason=UpdateFailureReason.MISSING_TARGET_REF,
                old=pull_request, new=None, changes=None,
                source_changed=False, target_changed=False)
        target_changed = target_ref_id != target_commit.raw_id

        if not (source_changed or target_changed):
            log.debug("Nothing changed in pull request %s", pull_request)
            return UpdateResponse(
                executed=False,
                reason=UpdateFailureReason.NO_CHANGE,
                old=pull_request, new=None, changes=None,
                source_changed=target_changed, target_changed=source_changed)

        change_in_found = 'target repo' if target_changed else 'source repo'
        log.debug('Updating pull request because of change in %s detected',
                  change_in_found)

        # Finally there is a need for an update, in case of source change
        # we create a new version, else just an update
        if source_changed:
            pull_request_version = self._create_version_from_snapshot(pull_request)
            self._link_comments_to_version(pull_request_version)
        else:
            try:
                ver = pull_request.versions[-1]
            except IndexError:
                ver = None

            pull_request.pull_request_version_id = \
                ver.pull_request_version_id if ver else None
            pull_request_version = pull_request

        try:
            if target_ref_type in self.REF_TYPES:
                target_commit = target_repo.get_commit(target_ref_name)
            else:
                target_commit = target_repo.get_commit(target_ref_id)
        except CommitDoesNotExistError:
            return UpdateResponse(
                executed=False,
                reason=UpdateFailureReason.MISSING_TARGET_REF,
                old=pull_request, new=None, changes=None,
                source_changed=source_changed, target_changed=target_changed)

        # re-compute commit ids
        old_commit_ids = pull_request.revisions
        pre_load = ["author", "date", "message", "branch"]
        commit_ranges = target_repo.compare(
            target_commit.raw_id, source_commit.raw_id, source_repo, merge=True,
            pre_load=pre_load)

        ancestor = source_repo.get_common_ancestor(
            source_commit.raw_id, target_commit.raw_id, target_repo)

        pull_request.source_ref = '%s:%s:%s' % (
            source_ref_type, source_ref_name, source_commit.raw_id)
        pull_request.target_ref = '%s:%s:%s' % (
            target_ref_type, target_ref_name, ancestor)

        pull_request.revisions = [
            commit.raw_id for commit in reversed(commit_ranges)]
        pull_request.updated_on = datetime.datetime.now()
        Session().add(pull_request)
        new_commit_ids = pull_request.revisions

        old_diff_data, new_diff_data = self._generate_update_diffs(
            pull_request, pull_request_version)

        # calculate commit and file changes
        changes = self._calculate_commit_id_changes(
            old_commit_ids, new_commit_ids)
        file_changes = self._calculate_file_changes(
            old_diff_data, new_diff_data)

        # set comments as outdated if DIFFS changed
        CommentsModel().outdate_comments(
            pull_request, old_diff_data=old_diff_data,
            new_diff_data=new_diff_data)

        commit_changes = (changes.added or changes.removed)
        file_node_changes = (
            file_changes.added or file_changes.modified or file_changes.removed)
        pr_has_changes = commit_changes or file_node_changes

        # Add an automatic comment to the pull request, in case
        # anything has changed
        if pr_has_changes:
            update_comment = CommentsModel().create(
                text=self._render_update_message(changes, file_changes),
                repo=pull_request.target_repo,
                user=pull_request.author,
                pull_request=pull_request,
                send_email=False, renderer=DEFAULT_COMMENTS_RENDERER)

            # Update status to "Under Review" for added commits
            for commit_id in changes.added:
                ChangesetStatusModel().set_status(
                    repo=pull_request.source_repo,
                    status=ChangesetStatus.STATUS_UNDER_REVIEW,
                    comment=update_comment,
                    user=pull_request.author,
                    pull_request=pull_request,
                    revision=commit_id)

        log.debug(
            'Updated pull request %s, added_ids: %s, common_ids: %s, '
            'removed_ids: %s', pull_request.pull_request_id,
            changes.added, changes.common, changes.removed)
        log.debug(
            'Updated pull request with the following file changes: %s',
            file_changes)

        log.info(
            "Updated pull request %s from commit %s to commit %s, "
            "stored new version %s of this pull request.",
            pull_request.pull_request_id, source_ref_id,
            pull_request.source_ref_parts.commit_id,
            pull_request_version.pull_request_version_id)
        Session().commit()
        self.trigger_pull_request_hook(pull_request, pull_request.author, 'update')

        return UpdateResponse(
            executed=True, reason=UpdateFailureReason.NONE,
            old=pull_request, new=pull_request_version, changes=changes,
            source_changed=source_changed, target_changed=target_changed)

    def _create_version_from_snapshot(self, pull_request):
        version = PullRequestVersion()
        version.title = pull_request.title
        version.description = pull_request.description
        version.status = pull_request.status
        version.pull_request_state = pull_request.pull_request_state
        version.created_on = datetime.datetime.now()
        version.updated_on = pull_request.updated_on
        version.user_id = pull_request.user_id
        version.source_repo = pull_request.source_repo
        version.source_ref = pull_request.source_ref
        version.target_repo = pull_request.target_repo
        version.target_ref = pull_request.target_ref

        version._last_merge_source_rev = pull_request._last_merge_source_rev
        version._last_merge_target_rev = pull_request._last_merge_target_rev
        version.last_merge_status = pull_request.last_merge_status
        version.shadow_merge_ref = pull_request.shadow_merge_ref
        version.merge_rev = pull_request.merge_rev
        version.reviewer_data = pull_request.reviewer_data

        version.revisions = pull_request.revisions
        version.pull_request = pull_request
        Session().add(version)
        Session().flush()

        return version

    def _generate_update_diffs(self, pull_request, pull_request_version):

        diff_context = (
            self.DIFF_CONTEXT +
            CommentsModel.needed_extra_diff_context())
        hide_whitespace_changes = False
        source_repo = pull_request_version.source_repo
        source_ref_id = pull_request_version.source_ref_parts.commit_id
        target_ref_id = pull_request_version.target_ref_parts.commit_id
        old_diff = self._get_diff_from_pr_or_version(
            source_repo, source_ref_id, target_ref_id,
            hide_whitespace_changes=hide_whitespace_changes, diff_context=diff_context)

        source_repo = pull_request.source_repo
        source_ref_id = pull_request.source_ref_parts.commit_id
        target_ref_id = pull_request.target_ref_parts.commit_id

        new_diff = self._get_diff_from_pr_or_version(
            source_repo, source_ref_id, target_ref_id,
            hide_whitespace_changes=hide_whitespace_changes, diff_context=diff_context)

        old_diff_data = diffs.DiffProcessor(old_diff)
        old_diff_data.prepare()
        new_diff_data = diffs.DiffProcessor(new_diff)
        new_diff_data.prepare()

        return old_diff_data, new_diff_data

    def _link_comments_to_version(self, pull_request_version):
        """
        Link all unlinked comments of this pull request to the given version.

        :param pull_request_version: The `PullRequestVersion` to which
            the comments shall be linked.

        """
        pull_request = pull_request_version.pull_request
        comments = ChangesetComment.query()\
            .filter(
                # TODO: johbo: Should we query for the repo at all here?
                # Pending decision on how comments of PRs are to be related
                # to either the source repo, the target repo or no repo at all.
                ChangesetComment.repo_id == pull_request.target_repo.repo_id,
                ChangesetComment.pull_request == pull_request,
                ChangesetComment.pull_request_version == None)\
            .order_by(ChangesetComment.comment_id.asc())

        # TODO: johbo: Find out why this breaks if it is done in a bulk
        # operation.
        for comment in comments:
            comment.pull_request_version_id = (
                pull_request_version.pull_request_version_id)
            Session().add(comment)

    def _calculate_commit_id_changes(self, old_ids, new_ids):
        added = [x for x in new_ids if x not in old_ids]
        common = [x for x in new_ids if x in old_ids]
        removed = [x for x in old_ids if x not in new_ids]
        total = new_ids
        return ChangeTuple(added, common, removed, total)

    def _calculate_file_changes(self, old_diff_data, new_diff_data):

        old_files = OrderedDict()
        for diff_data in old_diff_data.parsed_diff:
            old_files[diff_data['filename']] = md5_safe(diff_data['raw_diff'])

        added_files = []
        modified_files = []
        removed_files = []
        for diff_data in new_diff_data.parsed_diff:
            new_filename = diff_data['filename']
            new_hash = md5_safe(diff_data['raw_diff'])

            old_hash = old_files.get(new_filename)
            if not old_hash:
                # file is not present in old diff, means it's added
                added_files.append(new_filename)
            else:
                if new_hash != old_hash:
                    modified_files.append(new_filename)
                # now remove a file from old, since we have seen it already
                del old_files[new_filename]

        # removed files is when there are present in old, but not in NEW,
        # since we remove old files that are present in new diff, left-overs
        # if any should be the removed files
        removed_files.extend(old_files.keys())

        return FileChangeTuple(added_files, modified_files, removed_files)

    def _render_update_message(self, changes, file_changes):
        """
        render the message using DEFAULT_COMMENTS_RENDERER (RST renderer),
        so it's always looking the same disregarding on which default
        renderer system is using.

        :param changes: changes named tuple
        :param file_changes: file changes named tuple

        """
        new_status = ChangesetStatus.get_status_lbl(
            ChangesetStatus.STATUS_UNDER_REVIEW)

        changed_files = (
            file_changes.added + file_changes.modified + file_changes.removed)

        params = {
            'under_review_label': new_status,
            'added_commits': changes.added,
            'removed_commits': changes.removed,
            'changed_files': changed_files,
            'added_files': file_changes.added,
            'modified_files': file_changes.modified,
            'removed_files': file_changes.removed,
        }
        renderer = RstTemplateRenderer()
        return renderer.render('pull_request_update.mako', **params)

    def edit(self, pull_request, title, description, description_renderer, user):
        pull_request = self.__get_pull_request(pull_request)
        old_data = pull_request.get_api_data(with_merge_state=False)
        if pull_request.is_closed():
            raise ValueError('This pull request is closed')
        if title:
            pull_request.title = title
        pull_request.description = description
        pull_request.updated_on = datetime.datetime.now()
        pull_request.description_renderer = description_renderer
        Session().add(pull_request)
        self._log_audit_action(
            'repo.pull_request.edit', {'old_data': old_data},
            user, pull_request)

    def update_reviewers(self, pull_request, reviewer_data, user):
        """
        Update the reviewers in the pull request

        :param pull_request: the pr to update
        :param reviewer_data: list of tuples
            [(user, ['reason1', 'reason2'], mandatory_flag, [rules])]
        """
        pull_request = self.__get_pull_request(pull_request)
        if pull_request.is_closed():
            raise ValueError('This pull request is closed')

        reviewers = {}
        for user_id, reasons, mandatory, rules in reviewer_data:
            if isinstance(user_id, (int, compat.string_types)):
                user_id = self._get_user(user_id).user_id
            reviewers[user_id] = {
                'reasons': reasons, 'mandatory': mandatory}

        reviewers_ids = set(reviewers.keys())
        current_reviewers = PullRequestReviewers.query()\
            .filter(PullRequestReviewers.pull_request ==
                    pull_request).all()
        current_reviewers_ids = set([x.user.user_id for x in current_reviewers])

        ids_to_add = reviewers_ids.difference(current_reviewers_ids)
        ids_to_remove = current_reviewers_ids.difference(reviewers_ids)

        log.debug("Adding %s reviewers", ids_to_add)
        log.debug("Removing %s reviewers", ids_to_remove)
        changed = False
        added_audit_reviewers = []
        removed_audit_reviewers = []

        for uid in ids_to_add:
            changed = True
            _usr = self._get_user(uid)
            reviewer = PullRequestReviewers()
            reviewer.user = _usr
            reviewer.pull_request = pull_request
            reviewer.reasons = reviewers[uid]['reasons']
            # NOTE(marcink): mandatory shouldn't be changed now
            # reviewer.mandatory = reviewers[uid]['reasons']
            Session().add(reviewer)
            added_audit_reviewers.append(reviewer.get_dict())

        for uid in ids_to_remove:
            changed = True
            # NOTE(marcink): we fetch "ALL" reviewers using .all(). This is an edge case
            # that prevents and fixes cases that we added the same reviewer twice.
            # this CAN happen due to the lack of DB checks
            reviewers = PullRequestReviewers.query()\
                .filter(PullRequestReviewers.user_id == uid,
                        PullRequestReviewers.pull_request == pull_request)\
                .all()

            for obj in reviewers:
                added_audit_reviewers.append(obj.get_dict())
                Session().delete(obj)

        if changed:
            Session().expire_all()
            pull_request.updated_on = datetime.datetime.now()
            Session().add(pull_request)

        # finally store audit logs
        for user_data in added_audit_reviewers:
            self._log_audit_action(
                'repo.pull_request.reviewer.add', {'data': user_data},
                user, pull_request)
        for user_data in removed_audit_reviewers:
            self._log_audit_action(
                'repo.pull_request.reviewer.delete', {'old_data': user_data},
                user, pull_request)

        self.notify_reviewers(pull_request, ids_to_add)
        return ids_to_add, ids_to_remove

    def get_url(self, pull_request, request=None, permalink=False):
        if not request:
            request = get_current_request()

        if permalink:
            return request.route_url(
                'pull_requests_global',
                pull_request_id=pull_request.pull_request_id,)
        else:
            return request.route_url('pullrequest_show',
                repo_name=safe_str(pull_request.target_repo.repo_name),
                pull_request_id=pull_request.pull_request_id,)

    def get_shadow_clone_url(self, pull_request, request=None):
        """
        Returns qualified url pointing to the shadow repository. If this pull
        request is closed there is no shadow repository and ``None`` will be
        returned.
        """
        if pull_request.is_closed():
            return None
        else:
            pr_url = urllib.unquote(self.get_url(pull_request, request=request))
            return safe_unicode('{pr_url}/repository'.format(pr_url=pr_url))

    def notify_reviewers(self, pull_request, reviewers_ids):
        # notification to reviewers
        if not reviewers_ids:
            return

        pull_request_obj = pull_request
        # get the current participants of this pull request
        recipients = reviewers_ids
        notification_type = EmailNotificationModel.TYPE_PULL_REQUEST

        pr_source_repo = pull_request_obj.source_repo
        pr_target_repo = pull_request_obj.target_repo

        pr_url = h.route_url('pullrequest_show',
            repo_name=pr_target_repo.repo_name,
            pull_request_id=pull_request_obj.pull_request_id,)

        # set some variables for email notification
        pr_target_repo_url = h.route_url(
            'repo_summary', repo_name=pr_target_repo.repo_name)

        pr_source_repo_url = h.route_url(
            'repo_summary', repo_name=pr_source_repo.repo_name)

        # pull request specifics
        pull_request_commits = [
            (x.raw_id, x.message)
            for x in map(pr_source_repo.get_commit, pull_request.revisions)]

        kwargs = {
            'user': pull_request.author,
            'pull_request': pull_request_obj,
            'pull_request_commits': pull_request_commits,

            'pull_request_target_repo': pr_target_repo,
            'pull_request_target_repo_url': pr_target_repo_url,

            'pull_request_source_repo': pr_source_repo,
            'pull_request_source_repo_url': pr_source_repo_url,

            'pull_request_url': pr_url,
        }

        # pre-generate the subject for notification itself
        (subject,
         _h, _e,  # we don't care about those
         body_plaintext) = EmailNotificationModel().render_email(
            notification_type, **kwargs)

        # create notification objects, and emails
        NotificationModel().create(
            created_by=pull_request.author,
            notification_subject=subject,
            notification_body=body_plaintext,
            notification_type=notification_type,
            recipients=recipients,
            email_kwargs=kwargs,
        )

    def delete(self, pull_request, user):
        pull_request = self.__get_pull_request(pull_request)
        old_data = pull_request.get_api_data(with_merge_state=False)
        self._cleanup_merge_workspace(pull_request)
        self._log_audit_action(
            'repo.pull_request.delete', {'old_data': old_data},
            user, pull_request)
        Session().delete(pull_request)

    def close_pull_request(self, pull_request, user):
        pull_request = self.__get_pull_request(pull_request)
        self._cleanup_merge_workspace(pull_request)
        pull_request.status = PullRequest.STATUS_CLOSED
        pull_request.updated_on = datetime.datetime.now()
        Session().add(pull_request)
        self.trigger_pull_request_hook(
            pull_request, pull_request.author, 'close')

        pr_data = pull_request.get_api_data(with_merge_state=False)
        self._log_audit_action(
            'repo.pull_request.close', {'data': pr_data}, user, pull_request)

    def close_pull_request_with_comment(
            self, pull_request, user, repo, message=None, auth_user=None):

        pull_request_review_status = pull_request.calculated_review_status()

        if pull_request_review_status == ChangesetStatus.STATUS_APPROVED:
            # approved only if we have voting consent
            status = ChangesetStatus.STATUS_APPROVED
        else:
            status = ChangesetStatus.STATUS_REJECTED
        status_lbl = ChangesetStatus.get_status_lbl(status)

        default_message = (
            'Closing with status change {transition_icon} {status}.'
        ).format(transition_icon='>', status=status_lbl)
        text = message or default_message

        # create a comment, and link it to new status
        comment = CommentsModel().create(
            text=text,
            repo=repo.repo_id,
            user=user.user_id,
            pull_request=pull_request.pull_request_id,
            status_change=status_lbl,
            status_change_type=status,
            closing_pr=True,
            auth_user=auth_user,
        )

        # calculate old status before we change it
        old_calculated_status = pull_request.calculated_review_status()
        ChangesetStatusModel().set_status(
            repo.repo_id,
            status,
            user.user_id,
            comment=comment,
            pull_request=pull_request.pull_request_id
        )

        Session().flush()
        events.trigger(events.PullRequestCommentEvent(pull_request, comment))
        # we now calculate the status of pull request again, and based on that
        # calculation trigger status change. This might happen in cases
        # that non-reviewer admin closes a pr, which means his vote doesn't
        # change the status, while if he's a reviewer this might change it.
        calculated_status = pull_request.calculated_review_status()
        if old_calculated_status != calculated_status:
            self.trigger_pull_request_hook(
                pull_request, user, 'review_status_change',
                data={'status': calculated_status})

        # finally close the PR
        PullRequestModel().close_pull_request(
            pull_request.pull_request_id, user)

        return comment, status

    def merge_status(self, pull_request, translator=None,
                     force_shadow_repo_refresh=False):
        _ = translator or get_current_request().translate

        if not self._is_merge_enabled(pull_request):
            return False, _('Server-side pull request merging is disabled.')
        if pull_request.is_closed():
            return False, _('This pull request is closed.')
        merge_possible, msg = self._check_repo_requirements(
            target=pull_request.target_repo, source=pull_request.source_repo,
            translator=_)
        if not merge_possible:
            return merge_possible, msg

        try:
            resp = self._try_merge(
                pull_request,
                force_shadow_repo_refresh=force_shadow_repo_refresh)
            log.debug("Merge response: %s", resp)
            status = resp.possible, resp.merge_status_message
        except NotImplementedError:
            status = False, _('Pull request merging is not supported.')

        return status

    def _check_repo_requirements(self, target, source, translator):
        """
        Check if `target` and `source` have compatible requirements.

        Currently this is just checking for largefiles.
        """
        _ = translator
        target_has_largefiles = self._has_largefiles(target)
        source_has_largefiles = self._has_largefiles(source)
        merge_possible = True
        message = u''

        if target_has_largefiles != source_has_largefiles:
            merge_possible = False
            if source_has_largefiles:
                message = _(
                    'Target repository large files support is disabled.')
            else:
                message = _(
                    'Source repository large files support is disabled.')

        return merge_possible, message

    def _has_largefiles(self, repo):
        largefiles_ui = VcsSettingsModel(repo=repo).get_ui_settings(
            'extensions', 'largefiles')
        return largefiles_ui and largefiles_ui[0].active

    def _try_merge(self, pull_request, force_shadow_repo_refresh=False):
        """
        Try to merge the pull request and return the merge status.
        """
        log.debug(
            "Trying out if the pull request %s can be merged. Force_refresh=%s",
            pull_request.pull_request_id, force_shadow_repo_refresh)
        target_vcs = pull_request.target_repo.scm_instance()
        # Refresh the target reference.
        try:
            target_ref = self._refresh_reference(
                pull_request.target_ref_parts, target_vcs)
        except CommitDoesNotExistError:
            merge_state = MergeResponse(
                False, False, None, MergeFailureReason.MISSING_TARGET_REF,
                metadata={'target_ref': pull_request.target_ref_parts})
            return merge_state

        target_locked = pull_request.target_repo.locked
        if target_locked and target_locked[0]:
            locked_by = 'user:{}'.format(target_locked[0])
            log.debug("The target repository is locked by %s.", locked_by)
            merge_state = MergeResponse(
                False, False, None, MergeFailureReason.TARGET_IS_LOCKED,
                metadata={'locked_by': locked_by})
        elif force_shadow_repo_refresh or self._needs_merge_state_refresh(
                pull_request, target_ref):
            log.debug("Refreshing the merge status of the repository.")
            merge_state = self._refresh_merge_state(
                pull_request, target_vcs, target_ref)
        else:
            possible = pull_request.last_merge_status == MergeFailureReason.NONE
            metadata = {
                'target_ref': pull_request.target_ref_parts,
                'source_ref': pull_request.source_ref_parts,
            }
            if not possible and target_ref.type == 'branch':
                # NOTE(marcink): case for mercurial multiple heads on branch
                heads = target_vcs._heads(target_ref.name)
                if len(heads) != 1:
                    heads = '\n,'.join(target_vcs._heads(target_ref.name))
                    metadata.update({
                        'heads': heads
                    })
            merge_state = MergeResponse(
                possible, False, None, pull_request.last_merge_status, metadata=metadata)

        return merge_state

    def _refresh_reference(self, reference, vcs_repository):
        if reference.type in self.UPDATABLE_REF_TYPES:
            name_or_id = reference.name
        else:
            name_or_id = reference.commit_id

        refreshed_commit = vcs_repository.get_commit(name_or_id)
        refreshed_reference = Reference(
            reference.type, reference.name, refreshed_commit.raw_id)
        return refreshed_reference

    def _needs_merge_state_refresh(self, pull_request, target_reference):
        return not(
            pull_request.revisions and
            pull_request.revisions[0] == pull_request._last_merge_source_rev and
            target_reference.commit_id == pull_request._last_merge_target_rev)

    def _refresh_merge_state(self, pull_request, target_vcs, target_reference):
        workspace_id = self._workspace_id(pull_request)
        source_vcs = pull_request.source_repo.scm_instance()
        repo_id = pull_request.target_repo.repo_id
        use_rebase = self._use_rebase_for_merging(pull_request)
        close_branch = self._close_branch_before_merging(pull_request)
        merge_state = target_vcs.merge(
            repo_id, workspace_id,
            target_reference, source_vcs, pull_request.source_ref_parts,
            dry_run=True, use_rebase=use_rebase,
            close_branch=close_branch)

        # Do not store the response if there was an unknown error.
        if merge_state.failure_reason != MergeFailureReason.UNKNOWN:
            pull_request._last_merge_source_rev = \
                pull_request.source_ref_parts.commit_id
            pull_request._last_merge_target_rev = target_reference.commit_id
            pull_request.last_merge_status = merge_state.failure_reason
            pull_request.shadow_merge_ref = merge_state.merge_ref
            Session().add(pull_request)
            Session().commit()

        return merge_state

    def _workspace_id(self, pull_request):
        workspace_id = 'pr-%s' % pull_request.pull_request_id
        return workspace_id

    def generate_repo_data(self, repo, commit_id=None, branch=None,
                           bookmark=None, translator=None):
        from rhodecode.model.repo import RepoModel

        all_refs, selected_ref = \
            self._get_repo_pullrequest_sources(
                repo.scm_instance(), commit_id=commit_id,
                branch=branch, bookmark=bookmark, translator=translator)

        refs_select2 = []
        for element in all_refs:
            children = [{'id': x[0], 'text': x[1]} for x in element[0]]
            refs_select2.append({'text': element[1], 'children': children})

        return {
            'user': {
                'user_id': repo.user.user_id,
                'username': repo.user.username,
                'firstname': repo.user.first_name,
                'lastname': repo.user.last_name,
                'gravatar_link': h.gravatar_url(repo.user.email, 14),
            },
            'name': repo.repo_name,
            'link': RepoModel().get_url(repo),
            'description': h.chop_at_smart(repo.description_safe, '\n'),
            'refs': {
                'all_refs': all_refs,
                'selected_ref': selected_ref,
                'select2_refs': refs_select2
            }
        }

    def generate_pullrequest_title(self, source, source_ref, target):
        return u'{source}#{at_ref} to {target}'.format(
            source=source,
            at_ref=source_ref,
            target=target,
        )

    def _cleanup_merge_workspace(self, pull_request):
        # Merging related cleanup
        repo_id = pull_request.target_repo.repo_id
        target_scm = pull_request.target_repo.scm_instance()
        workspace_id = self._workspace_id(pull_request)

        try:
            target_scm.cleanup_merge_workspace(repo_id, workspace_id)
        except NotImplementedError:
            pass

    def _get_repo_pullrequest_sources(
            self, repo, commit_id=None, branch=None, bookmark=None,
            translator=None):
        """
        Return a structure with repo's interesting commits, suitable for
        the selectors in pullrequest controller

        :param commit_id: a commit that must be in the list somehow
            and selected by default
        :param branch: a branch that must be in the list and selected
            by default - even if closed
        :param bookmark: a bookmark that must be in the list and selected
        """
        _ = translator or get_current_request().translate

        commit_id = safe_str(commit_id) if commit_id else None
        branch = safe_unicode(branch) if branch else None
        bookmark = safe_unicode(bookmark) if bookmark else None

        selected = None

        # order matters: first source that has commit_id in it will be selected
        sources = []
        sources.append(('book', repo.bookmarks.items(), _('Bookmarks'), bookmark))
        sources.append(('branch', repo.branches.items(), _('Branches'), branch))

        if commit_id:
            ref_commit = (h.short_id(commit_id), commit_id)
            sources.append(('rev', [ref_commit], _('Commit IDs'), commit_id))

        sources.append(
            ('branch', repo.branches_closed.items(), _('Closed Branches'), branch),
        )

        groups = []

        for group_key, ref_list, group_name, match in sources:
            group_refs = []
            for ref_name, ref_id in ref_list:
                ref_key = u'{}:{}:{}'.format(group_key, ref_name, ref_id)
                group_refs.append((ref_key, ref_name))

                if not selected:
                    if set([commit_id, match]) & set([ref_id, ref_name]):
                        selected = ref_key

            if group_refs:
                groups.append((group_refs, group_name))

        if not selected:
            ref = commit_id or branch or bookmark
            if ref:
                raise CommitDoesNotExistError(
                    u'No commit refs could be found matching: {}'.format(ref))
            elif repo.DEFAULT_BRANCH_NAME in repo.branches:
                selected = u'branch:{}:{}'.format(
                    safe_unicode(repo.DEFAULT_BRANCH_NAME),
                    safe_unicode(repo.branches[repo.DEFAULT_BRANCH_NAME])
                )
            elif repo.commit_ids:
                # make the user select in this case
                selected = None
            else:
                raise EmptyRepositoryError()
        return groups, selected

    def get_diff(self, source_repo, source_ref_id, target_ref_id,
                 hide_whitespace_changes, diff_context):

        return self._get_diff_from_pr_or_version(
            source_repo, source_ref_id, target_ref_id,
            hide_whitespace_changes=hide_whitespace_changes, diff_context=diff_context)

    def _get_diff_from_pr_or_version(
            self, source_repo, source_ref_id, target_ref_id,
            hide_whitespace_changes, diff_context):

        target_commit = source_repo.get_commit(
            commit_id=safe_str(target_ref_id))
        source_commit = source_repo.get_commit(
            commit_id=safe_str(source_ref_id))
        if isinstance(source_repo, Repository):
            vcs_repo = source_repo.scm_instance()
        else:
            vcs_repo = source_repo

        # TODO: johbo: In the context of an update, we cannot reach
        # the old commit anymore with our normal mechanisms. It needs
        # some sort of special support in the vcs layer to avoid this
        # workaround.
        if (source_commit.raw_id == vcs_repo.EMPTY_COMMIT_ID and
                vcs_repo.alias == 'git'):
            source_commit.raw_id = safe_str(source_ref_id)

        log.debug('calculating diff between '
                  'source_ref:%s and target_ref:%s for repo `%s`',
                  target_ref_id, source_ref_id,
                  safe_unicode(vcs_repo.path))

        vcs_diff = vcs_repo.get_diff(
            commit1=target_commit, commit2=source_commit,
            ignore_whitespace=hide_whitespace_changes, context=diff_context)
        return vcs_diff

    def _is_merge_enabled(self, pull_request):
        return self._get_general_setting(
            pull_request, 'rhodecode_pr_merge_enabled')

    def _use_rebase_for_merging(self, pull_request):
        repo_type = pull_request.target_repo.repo_type
        if repo_type == 'hg':
            return self._get_general_setting(
                pull_request, 'rhodecode_hg_use_rebase_for_merging')
        elif repo_type == 'git':
            return self._get_general_setting(
                pull_request, 'rhodecode_git_use_rebase_for_merging')

        return False

    def _close_branch_before_merging(self, pull_request):
        repo_type = pull_request.target_repo.repo_type
        if repo_type == 'hg':
            return self._get_general_setting(
                pull_request, 'rhodecode_hg_close_branch_before_merging')
        elif repo_type == 'git':
            return self._get_general_setting(
                pull_request, 'rhodecode_git_close_branch_before_merging')

        return False

    def _get_general_setting(self, pull_request, settings_key, default=False):
        settings_model = VcsSettingsModel(repo=pull_request.target_repo)
        settings = settings_model.get_general_settings()
        return settings.get(settings_key, default)

    def _log_audit_action(self, action, action_data, user, pull_request):
        audit_logger.store(
            action=action,
            action_data=action_data,
            user=user,
            repo=pull_request.target_repo)

    def get_reviewer_functions(self):
        """
        Fetches functions for validation and fetching default reviewers.
        If available we use the EE package, else we fallback to CE
        package functions
        """
        try:
            from rc_reviewers.utils import get_default_reviewers_data
            from rc_reviewers.utils import validate_default_reviewers
        except ImportError:
            from rhodecode.apps.repository.utils import get_default_reviewers_data
            from rhodecode.apps.repository.utils import validate_default_reviewers

        return get_default_reviewers_data, validate_default_reviewers


class MergeCheck(object):
    """
    Perform Merge Checks and returns a check object which stores information
    about merge errors, and merge conditions
    """
    TODO_CHECK = 'todo'
    PERM_CHECK = 'perm'
    REVIEW_CHECK = 'review'
    MERGE_CHECK = 'merge'

    def __init__(self):
        self.review_status = None
        self.merge_possible = None
        self.merge_msg = ''
        self.failed = None
        self.errors = []
        self.error_details = OrderedDict()

    def push_error(self, error_type, message, error_key, details):
        self.failed = True
        self.errors.append([error_type, message])
        self.error_details[error_key] = dict(
            details=details,
            error_type=error_type,
            message=message
        )

    @classmethod
    def validate(cls, pull_request, auth_user, translator, fail_early=False,
                 force_shadow_repo_refresh=False):
        _ = translator
        merge_check = cls()

        # permissions to merge
        user_allowed_to_merge = PullRequestModel().check_user_merge(
            pull_request, auth_user)
        if not user_allowed_to_merge:
            log.debug("MergeCheck: cannot merge, approval is pending.")

            msg = _('User `{}` not allowed to perform merge.').format(auth_user.username)
            merge_check.push_error('error', msg, cls.PERM_CHECK, auth_user.username)
            if fail_early:
                return merge_check

        # permission to merge into the target branch
        target_commit_id = pull_request.target_ref_parts.commit_id
        if pull_request.target_ref_parts.type == 'branch':
            branch_name = pull_request.target_ref_parts.name
        else:
            # for mercurial we can always figure out the branch from the commit
            # in case of bookmark
            target_commit = pull_request.target_repo.get_commit(target_commit_id)
            branch_name = target_commit.branch

        rule, branch_perm = auth_user.get_rule_and_branch_permission(
            pull_request.target_repo.repo_name, branch_name)
        if branch_perm and branch_perm == 'branch.none':
            msg = _('Target branch `{}` changes rejected by rule {}.').format(
                branch_name, rule)
            merge_check.push_error('error', msg, cls.PERM_CHECK, auth_user.username)
            if fail_early:
                return merge_check

        # review status, must be always present
        review_status = pull_request.calculated_review_status()
        merge_check.review_status = review_status

        status_approved = review_status == ChangesetStatus.STATUS_APPROVED
        if not status_approved:
            log.debug("MergeCheck: cannot merge, approval is pending.")

            msg = _('Pull request reviewer approval is pending.')

            merge_check.push_error('warning', msg, cls.REVIEW_CHECK, review_status)

            if fail_early:
                return merge_check

        # left over TODOs
        todos = CommentsModel().get_pull_request_unresolved_todos(pull_request)
        if todos:
            log.debug("MergeCheck: cannot merge, {} "
                      "unresolved TODOs left.".format(len(todos)))

            if len(todos) == 1:
                msg = _('Cannot merge, {} TODO still not resolved.').format(
                    len(todos))
            else:
                msg = _('Cannot merge, {} TODOs still not resolved.').format(
                    len(todos))

            merge_check.push_error('warning', msg, cls.TODO_CHECK, todos)

            if fail_early:
                return merge_check

        # merge possible, here is the filesystem simulation + shadow repo
        merge_status, msg = PullRequestModel().merge_status(
            pull_request, translator=translator,
            force_shadow_repo_refresh=force_shadow_repo_refresh)
        merge_check.merge_possible = merge_status
        merge_check.merge_msg = msg
        if not merge_status:
            log.debug("MergeCheck: cannot merge, pull request merge not possible.")
            merge_check.push_error('warning', msg, cls.MERGE_CHECK, None)

            if fail_early:
                return merge_check

        log.debug('MergeCheck: is failed: %s', merge_check.failed)
        return merge_check

    @classmethod
    def get_merge_conditions(cls, pull_request, translator):
        _ = translator
        merge_details = {}

        model = PullRequestModel()
        use_rebase = model._use_rebase_for_merging(pull_request)

        if use_rebase:
            merge_details['merge_strategy'] = dict(
                details={},
                message=_('Merge strategy: rebase')
            )
        else:
            merge_details['merge_strategy'] = dict(
                details={},
                message=_('Merge strategy: explicit merge commit')
            )

        close_branch = model._close_branch_before_merging(pull_request)
        if close_branch:
            repo_type = pull_request.target_repo.repo_type
            close_msg = ''
            if repo_type == 'hg':
                close_msg = _('Source branch will be closed after merge.')
            elif repo_type == 'git':
                close_msg = _('Source branch will be deleted after merge.')

            merge_details['close_branch'] = dict(
                details={},
                message=close_msg
            )

        return merge_details


ChangeTuple = collections.namedtuple(
    'ChangeTuple', ['added', 'common', 'removed', 'total'])

FileChangeTuple = collections.namedtuple(
    'FileChangeTuple', ['added', 'modified', 'removed'])
