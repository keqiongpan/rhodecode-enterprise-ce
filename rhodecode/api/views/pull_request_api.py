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

from rhodecode.api import jsonrpc_method, JSONRPCError, JSONRPCValidationError
from rhodecode.api.utils import (
    has_superadmin_permission, Optional, OAttr, get_repo_or_error,
    get_pull_request_or_error, get_commit_or_error, get_user_or_error,
    validate_repo_permissions, resolve_ref_or_error, validate_set_owner_permissions)
from rhodecode.lib.auth import (HasRepoPermissionAnyApi)
from rhodecode.lib.exceptions import CommentVersionMismatch
from rhodecode.lib.base import vcs_operation_context
from rhodecode.lib.utils2 import str2bool
from rhodecode.model.changeset_status import ChangesetStatusModel
from rhodecode.model.comment import CommentsModel
from rhodecode.model.db import Session, ChangesetStatus, ChangesetComment, PullRequest
from rhodecode.model.pull_request import PullRequestModel, MergeCheck
from rhodecode.model.settings import SettingsModel
from rhodecode.model.validation_schema import Invalid
from rhodecode.model.validation_schema.schemas.reviewer_schema import(
    ReviewerListSchema)

log = logging.getLogger(__name__)


@jsonrpc_method()
def get_pull_request(request, apiuser, pullrequestid, repoid=Optional(None),
                     merge_state=Optional(False)):
    """
    Get a pull request based on the given ID.

    :param apiuser: This is filled automatically from the |authtoken|.
    :type apiuser: AuthUser
    :param repoid: Optional, repository name or repository ID from where
        the pull request was opened.
    :type repoid: str or int
    :param pullrequestid: ID of the requested pull request.
    :type pullrequestid: int
    :param merge_state: Optional calculate merge state for each repository.
        This could result in longer time to fetch the data
    :type merge_state: bool

    Example output:

    .. code-block:: bash

      "id": <id_given_in_input>,
      "result":
        {
            "pull_request_id":   "<pull_request_id>",
            "url":               "<url>",
            "title":             "<title>",
            "description":       "<description>",
            "status" :           "<status>",
            "created_on":        "<date_time_created>",
            "updated_on":        "<date_time_updated>",
            "versions":          "<number_or_versions_of_pr>",
            "commit_ids":        [
                                     ...
                                     "<commit_id>",
                                     "<commit_id>",
                                     ...
                                 ],
            "review_status":    "<review_status>",
            "mergeable":         {
                                     "status":  "<bool>",
                                     "message": "<message>",
                                 },
            "source":            {
                                     "clone_url":     "<clone_url>",
                                     "repository":    "<repository_name>",
                                     "reference":
                                     {
                                         "name":      "<name>",
                                         "type":      "<type>",
                                         "commit_id": "<commit_id>",
                                     }
                                 },
            "target":            {
                                     "clone_url":   "<clone_url>",
                                     "repository":    "<repository_name>",
                                     "reference":
                                     {
                                         "name":      "<name>",
                                         "type":      "<type>",
                                         "commit_id": "<commit_id>",
                                     }
                                 },
            "merge":             {
                                     "clone_url":   "<clone_url>",
                                     "reference":
                                     {
                                         "name":      "<name>",
                                         "type":      "<type>",
                                         "commit_id": "<commit_id>",
                                     }
                                 },
           "author":             <user_obj>,
           "reviewers":          [
                                     ...
                                     {
                                        "user":          "<user_obj>",
                                        "review_status": "<review_status>",
                                     }
                                     ...
                                 ]
        },
       "error": null
    """

    pull_request = get_pull_request_or_error(pullrequestid)
    if Optional.extract(repoid):
        repo = get_repo_or_error(repoid)
    else:
        repo = pull_request.target_repo

    if not PullRequestModel().check_user_read(pull_request, apiuser, api=True):
        raise JSONRPCError('repository `%s` or pull request `%s` '
                           'does not exist' % (repoid, pullrequestid))

    # NOTE(marcink): only calculate and return merge state if the pr state is 'created'
    # otherwise we can lock the repo on calculation of merge state while update/merge
    # is happening.
    pr_created = pull_request.pull_request_state == pull_request.STATE_CREATED
    merge_state = Optional.extract(merge_state, binary=True) and pr_created
    data = pull_request.get_api_data(with_merge_state=merge_state)
    return data


@jsonrpc_method()
def get_pull_requests(request, apiuser, repoid, status=Optional('new'),
                      merge_state=Optional(False)):
    """
    Get all pull requests from the repository specified in `repoid`.

    :param apiuser: This is filled automatically from the |authtoken|.
    :type apiuser: AuthUser
    :param repoid: Optional repository name or repository ID.
    :type repoid: str or int
    :param status: Only return pull requests with the specified status.
        Valid options are.
        * ``new`` (default)
        * ``open``
        * ``closed``
    :type status: str
    :param merge_state: Optional calculate merge state for each repository.
        This could result in longer time to fetch the data
    :type merge_state: bool

    Example output:

    .. code-block:: bash

      "id": <id_given_in_input>,
      "result":
        [
            ...
            {
                "pull_request_id":   "<pull_request_id>",
                "url":               "<url>",
                "title" :            "<title>",
                "description":       "<description>",
                "status":            "<status>",
                "created_on":        "<date_time_created>",
                "updated_on":        "<date_time_updated>",
                "commit_ids":        [
                                         ...
                                         "<commit_id>",
                                         "<commit_id>",
                                         ...
                                     ],
                "review_status":    "<review_status>",
                "mergeable":         {
                                        "status":      "<bool>",
                                        "message:      "<message>",
                                     },
                "source":            {
                                         "clone_url":     "<clone_url>",
                                         "reference":
                                         {
                                             "name":      "<name>",
                                             "type":      "<type>",
                                             "commit_id": "<commit_id>",
                                         }
                                     },
                "target":            {
                                         "clone_url":   "<clone_url>",
                                         "reference":
                                         {
                                             "name":      "<name>",
                                             "type":      "<type>",
                                             "commit_id": "<commit_id>",
                                         }
                                     },
                "merge":             {
                                         "clone_url":   "<clone_url>",
                                         "reference":
                                         {
                                             "name":      "<name>",
                                             "type":      "<type>",
                                             "commit_id": "<commit_id>",
                                         }
                                     },
               "author":             <user_obj>,
               "reviewers":          [
                                         ...
                                         {
                                            "user":          "<user_obj>",
                                            "review_status": "<review_status>",
                                         }
                                         ...
                                     ]
            }
            ...
        ],
      "error": null

    """
    repo = get_repo_or_error(repoid)
    if not has_superadmin_permission(apiuser):
        _perms = (
            'repository.admin', 'repository.write', 'repository.read',)
        validate_repo_permissions(apiuser, repoid, repo, _perms)

    status = Optional.extract(status)
    merge_state = Optional.extract(merge_state, binary=True)
    pull_requests = PullRequestModel().get_all(repo, statuses=[status],
                                               order_by='id', order_dir='desc')
    data = [pr.get_api_data(with_merge_state=merge_state) for pr in pull_requests]
    return data


@jsonrpc_method()
def merge_pull_request(
        request, apiuser, pullrequestid, repoid=Optional(None),
        userid=Optional(OAttr('apiuser'))):
    """
    Merge the pull request specified by `pullrequestid` into its target
    repository.

    :param apiuser: This is filled automatically from the |authtoken|.
    :type apiuser: AuthUser
    :param repoid: Optional, repository name or repository ID of the
        target repository to which the |pr| is to be merged.
    :type repoid: str or int
    :param pullrequestid: ID of the pull request which shall be merged.
    :type pullrequestid: int
    :param userid: Merge the pull request as this user.
    :type userid: Optional(str or int)

    Example output:

    .. code-block:: bash

        "id": <id_given_in_input>,
        "result": {
            "executed":               "<bool>",
            "failure_reason":         "<int>",
            "merge_status_message":   "<str>",
            "merge_commit_id":        "<merge_commit_id>",
            "possible":               "<bool>",
            "merge_ref":        {
                                    "commit_id": "<commit_id>",
                                    "type":      "<type>",
                                    "name":      "<name>"
                                }
        },
        "error": null
    """
    pull_request = get_pull_request_or_error(pullrequestid)
    if Optional.extract(repoid):
        repo = get_repo_or_error(repoid)
    else:
        repo = pull_request.target_repo
    auth_user = apiuser

    if not isinstance(userid, Optional):
        is_repo_admin = HasRepoPermissionAnyApi('repository.admin')(
            user=apiuser, repo_name=repo.repo_name)
        if has_superadmin_permission(apiuser) or is_repo_admin:
            apiuser = get_user_or_error(userid)
            auth_user = apiuser.AuthUser()
        else:
            raise JSONRPCError('userid is not the same as your user')

    if pull_request.pull_request_state != PullRequest.STATE_CREATED:
        raise JSONRPCError(
            'Operation forbidden because pull request is in state {}, '
            'only state {} is allowed.'.format(
                pull_request.pull_request_state, PullRequest.STATE_CREATED))

    with pull_request.set_state(PullRequest.STATE_UPDATING):
        check = MergeCheck.validate(pull_request, auth_user=auth_user,
                                    translator=request.translate)
    merge_possible = not check.failed

    if not merge_possible:
        error_messages = []
        for err_type, error_msg in check.errors:
            error_msg = request.translate(error_msg)
            error_messages.append(error_msg)

        reasons = ','.join(error_messages)
        raise JSONRPCError(
            'merge not possible for following reasons: {}'.format(reasons))

    target_repo = pull_request.target_repo
    extras = vcs_operation_context(
        request.environ, repo_name=target_repo.repo_name,
        username=auth_user.username, action='push',
        scm=target_repo.repo_type)
    with pull_request.set_state(PullRequest.STATE_UPDATING):
        merge_response = PullRequestModel().merge_repo(
            pull_request, apiuser, extras=extras)
    if merge_response.executed:
        PullRequestModel().close_pull_request(pull_request.pull_request_id, auth_user)

        Session().commit()

    # In previous versions the merge response directly contained the merge
    # commit id. It is now contained in the merge reference object. To be
    # backwards compatible we have to extract it again.
    merge_response = merge_response.asdict()
    merge_response['merge_commit_id'] = merge_response['merge_ref'].commit_id

    return merge_response


@jsonrpc_method()
def get_pull_request_comments(
        request, apiuser, pullrequestid, repoid=Optional(None)):
    """
    Get all comments of pull request specified with the `pullrequestid`

    :param apiuser: This is filled automatically from the |authtoken|.
    :type apiuser: AuthUser
    :param repoid: Optional repository name or repository ID.
    :type repoid: str or int
    :param pullrequestid: The pull request ID.
    :type pullrequestid: int

    Example output:

    .. code-block:: bash

        id : <id_given_in_input>
        result : [
            {
              "comment_author": {
                "active": true,
                "full_name_or_username": "Tom Gore",
                "username": "admin"
              },
              "comment_created_on": "2017-01-02T18:43:45.533",
              "comment_f_path": null,
              "comment_id": 25,
              "comment_lineno": null,
              "comment_status": {
                "status": "under_review",
                "status_lbl": "Under Review"
              },
              "comment_text": "Example text",
              "comment_type": null,
              "pull_request_version": null,
              "comment_commit_id": None,
              "comment_pull_request_id": <pull_request_id>
            }
        ],
        error :  null
    """

    pull_request = get_pull_request_or_error(pullrequestid)
    if Optional.extract(repoid):
        repo = get_repo_or_error(repoid)
    else:
        repo = pull_request.target_repo

    if not PullRequestModel().check_user_read(
            pull_request, apiuser, api=True):
        raise JSONRPCError('repository `%s` or pull request `%s` '
                           'does not exist' % (repoid, pullrequestid))

    (pull_request_latest,
     pull_request_at_ver,
     pull_request_display_obj,
     at_version) = PullRequestModel().get_pr_version(
        pull_request.pull_request_id, version=None)

    versions = pull_request_display_obj.versions()
    ver_map = {
        ver.pull_request_version_id: cnt
        for cnt, ver in enumerate(versions, 1)
    }

    # GENERAL COMMENTS with versions #
    q = CommentsModel()._all_general_comments_of_pull_request(pull_request)
    q = q.order_by(ChangesetComment.comment_id.asc())
    general_comments = q.all()

    # INLINE COMMENTS with versions  #
    q = CommentsModel()._all_inline_comments_of_pull_request(pull_request)
    q = q.order_by(ChangesetComment.comment_id.asc())
    inline_comments = q.all()

    data = []
    for comment in inline_comments + general_comments:
        full_data = comment.get_api_data()
        pr_version_id = None
        if comment.pull_request_version_id:
            pr_version_id = 'v{}'.format(
                ver_map[comment.pull_request_version_id])

        # sanitize some entries

        full_data['pull_request_version'] = pr_version_id
        full_data['comment_author'] = {
            'username': full_data['comment_author'].username,
            'full_name_or_username': full_data['comment_author'].full_name_or_username,
            'active': full_data['comment_author'].active,
        }

        if full_data['comment_status']:
            full_data['comment_status'] = {
                'status': full_data['comment_status'][0].status,
                'status_lbl': full_data['comment_status'][0].status_lbl,
            }
        else:
            full_data['comment_status'] = {}

        data.append(full_data)
    return data


@jsonrpc_method()
def comment_pull_request(
        request, apiuser, pullrequestid, repoid=Optional(None),
        message=Optional(None), commit_id=Optional(None), status=Optional(None),
        comment_type=Optional(ChangesetComment.COMMENT_TYPE_NOTE),
        resolves_comment_id=Optional(None), extra_recipients=Optional([]),
        userid=Optional(OAttr('apiuser')), send_email=Optional(True)):
    """
    Comment on the pull request specified with the `pullrequestid`,
    in the |repo| specified by the `repoid`, and optionally change the
    review status.

    :param apiuser: This is filled automatically from the |authtoken|.
    :type apiuser: AuthUser
    :param repoid: Optional repository name or repository ID.
    :type repoid: str or int
    :param pullrequestid: The pull request ID.
    :type pullrequestid: int
    :param commit_id: Specify the commit_id for which to set a comment. If
        given commit_id is different than latest in the PR status
        change won't be performed.
    :type commit_id: str
    :param message: The text content of the comment.
    :type message: str
    :param status: (**Optional**) Set the approval status of the pull
        request. One of: 'not_reviewed', 'approved', 'rejected',
        'under_review'
    :type status: str
    :param comment_type: Comment type, one of: 'note', 'todo'
    :type comment_type: Optional(str), default: 'note'
    :param resolves_comment_id: id of comment which this one will resolve
    :type resolves_comment_id: Optional(int)
    :param extra_recipients: list of user ids or usernames to add
        notifications for this comment. Acts like a CC for notification
    :type extra_recipients: Optional(list)
    :param userid: Comment on the pull request as this user
    :type userid: Optional(str or int)
    :param send_email: Define if this comment should also send email notification
    :type send_email: Optional(bool)

    Example output:

    .. code-block:: bash

        id : <id_given_in_input>
        result : {
            "pull_request_id":  "<Integer>",
            "comment_id":       "<Integer>",
            "status": {"given": <given_status>,
                       "was_changed": <bool status_was_actually_changed> },
        },
        error :  null
    """
    pull_request = get_pull_request_or_error(pullrequestid)
    if Optional.extract(repoid):
        repo = get_repo_or_error(repoid)
    else:
        repo = pull_request.target_repo

    auth_user = apiuser
    if not isinstance(userid, Optional):
        is_repo_admin = HasRepoPermissionAnyApi('repository.admin')(
            user=apiuser, repo_name=repo.repo_name)
        if has_superadmin_permission(apiuser) or is_repo_admin:
            apiuser = get_user_or_error(userid)
            auth_user = apiuser.AuthUser()
        else:
            raise JSONRPCError('userid is not the same as your user')

    if pull_request.is_closed():
        raise JSONRPCError(
            'pull request `%s` comment failed, pull request is closed' % (
                pullrequestid,))

    if not PullRequestModel().check_user_read(
            pull_request, apiuser, api=True):
        raise JSONRPCError('repository `%s` does not exist' % (repoid,))
    message = Optional.extract(message)
    status = Optional.extract(status)
    commit_id = Optional.extract(commit_id)
    comment_type = Optional.extract(comment_type)
    resolves_comment_id = Optional.extract(resolves_comment_id)
    extra_recipients = Optional.extract(extra_recipients)
    send_email = Optional.extract(send_email, binary=True)

    if not message and not status:
        raise JSONRPCError(
            'Both message and status parameters are missing. '
            'At least one is required.')

    if (status not in (st[0] for st in ChangesetStatus.STATUSES) and
            status is not None):
        raise JSONRPCError('Unknown comment status: `%s`' % status)

    if commit_id and commit_id not in pull_request.revisions:
        raise JSONRPCError(
            'Invalid commit_id `%s` for this pull request.' % commit_id)

    allowed_to_change_status = PullRequestModel().check_user_change_status(
        pull_request, apiuser)

    # if commit_id is passed re-validated if user is allowed to change status
    # based on latest commit_id from the PR
    if commit_id:
        commit_idx = pull_request.revisions.index(commit_id)
        if commit_idx != 0:
            allowed_to_change_status = False

    if resolves_comment_id:
        comment = ChangesetComment.get(resolves_comment_id)
        if not comment:
            raise JSONRPCError(
                'Invalid resolves_comment_id `%s` for this pull request.'
                % resolves_comment_id)
        if comment.comment_type != ChangesetComment.COMMENT_TYPE_TODO:
            raise JSONRPCError(
                'Comment `%s` is wrong type for setting status to resolved.'
                % resolves_comment_id)

    text = message
    status_label = ChangesetStatus.get_status_lbl(status)
    if status and allowed_to_change_status:
        st_message = ('Status change %(transition_icon)s %(status)s'
                      % {'transition_icon': '>', 'status': status_label})
        text = message or st_message

    rc_config = SettingsModel().get_all_settings()
    renderer = rc_config.get('rhodecode_markup_renderer', 'rst')

    status_change = status and allowed_to_change_status
    comment = CommentsModel().create(
        text=text,
        repo=pull_request.target_repo.repo_id,
        user=apiuser.user_id,
        pull_request=pull_request.pull_request_id,
        f_path=None,
        line_no=None,
        status_change=(status_label if status_change else None),
        status_change_type=(status if status_change else None),
        closing_pr=False,
        renderer=renderer,
        comment_type=comment_type,
        resolves_comment_id=resolves_comment_id,
        auth_user=auth_user,
        extra_recipients=extra_recipients,
        send_email=send_email
    )

    if allowed_to_change_status and status:
        old_calculated_status = pull_request.calculated_review_status()
        ChangesetStatusModel().set_status(
            pull_request.target_repo.repo_id,
            status,
            apiuser.user_id,
            comment,
            pull_request=pull_request.pull_request_id
        )
        Session().flush()

    Session().commit()

    PullRequestModel().trigger_pull_request_hook(
        pull_request, apiuser, 'comment',
        data={'comment': comment})

    if allowed_to_change_status and status:
        # we now calculate the status of pull request, and based on that
        # calculation we set the commits status
        calculated_status = pull_request.calculated_review_status()
        if old_calculated_status != calculated_status:
            PullRequestModel().trigger_pull_request_hook(
                pull_request, apiuser, 'review_status_change',
                data={'status': calculated_status})

    data = {
        'pull_request_id': pull_request.pull_request_id,
        'comment_id': comment.comment_id if comment else None,
        'status': {'given': status, 'was_changed': status_change},
    }
    return data


@jsonrpc_method()
def edit_comment(
        request, apiuser, message, comment_id, version,
        userid=Optional(OAttr('apiuser')),
):
    """
    Edit comment on the pull request or commit,
    specified by the `comment_id` and version. Initially version should be 0

    :param apiuser: This is filled automatically from the |authtoken|.
    :type apiuser: AuthUser
    :param comment_id: Specify the comment_id for editing
    :type comment_id: int
    :param version: version of the comment that will be created, starts from 0
    :type version: int
    :param message: The text content of the comment.
    :type message: str
    :param userid: Comment on the pull request as this user
    :type userid: Optional(str or int)

    Example output:

    .. code-block:: bash

        id : <id_given_in_input>
        result : {
            "comment_history_id":  "<Integer>",
            "version":       "<Integer>",
        },
        error :  null
    """

    auth_user = apiuser
    comment = ChangesetComment.get(comment_id)

    is_super_admin = has_superadmin_permission(apiuser)
    is_repo_admin = HasRepoPermissionAnyApi('repository.admin') \
        (user=apiuser, repo_name=comment.repo.repo_name)

    if not isinstance(userid, Optional):
        if is_super_admin or is_repo_admin:
            apiuser = get_user_or_error(userid)
            auth_user = apiuser.AuthUser()
        else:
            raise JSONRPCError('userid is not the same as your user')

    comment_author = comment.author.user_id == auth_user.user_id
    if not (comment.immutable is False and (is_super_admin or is_repo_admin) or comment_author):
        raise JSONRPCError("you don't have access to edit this comment")

    try:
        comment_history = CommentsModel().edit(
            comment_id=comment_id,
            text=message,
            auth_user=auth_user,
            version=version,
        )
        Session().commit()
    except CommentVersionMismatch:
        raise JSONRPCError(
            'comment ({}) version ({}) mismatch'.format(comment_id, version)
        )
    if not comment_history and not message:
        raise JSONRPCError(
            "comment ({}) can't be changed with empty string".format(comment_id)
        )
    data = {
        'comment_history_id': comment_history.comment_history_id if comment_history else None,
        'version': comment_history.version if comment_history else None,
    }
    return data


@jsonrpc_method()
def create_pull_request(
        request, apiuser, source_repo, target_repo, source_ref, target_ref,
        owner=Optional(OAttr('apiuser')), title=Optional(''), description=Optional(''),
        description_renderer=Optional(''), reviewers=Optional(None)):
    """
    Creates a new pull request.

    Accepts refs in the following formats:

        * branch:<branch_name>:<sha>
        * branch:<branch_name>
        * bookmark:<bookmark_name>:<sha> (Mercurial only)
        * bookmark:<bookmark_name> (Mercurial only)

    :param apiuser: This is filled automatically from the |authtoken|.
    :type apiuser: AuthUser
    :param source_repo: Set the source repository name.
    :type source_repo: str
    :param target_repo: Set the target repository name.
    :type target_repo: str
    :param source_ref: Set the source ref name.
    :type source_ref: str
    :param target_ref: Set the target ref name.
    :type target_ref: str
    :param owner: user_id or username
    :type owner: Optional(str)
    :param title: Optionally Set the pull request title, it's generated otherwise
    :type title: str
    :param description: Set the pull request description.
    :type description: Optional(str)
    :type description_renderer: Optional(str)
    :param description_renderer: Set pull request renderer for the description.
        It should be 'rst', 'markdown' or 'plain'. If not give default
        system renderer will be used
    :param reviewers: Set the new pull request reviewers list.
        Reviewer defined by review rules will be added automatically to the
        defined list.
    :type reviewers: Optional(list)
        Accepts username strings or objects of the format:

            [{'username': 'nick', 'reasons': ['original author'], 'mandatory': <bool>}]
    """

    source_db_repo = get_repo_or_error(source_repo)
    target_db_repo = get_repo_or_error(target_repo)
    if not has_superadmin_permission(apiuser):
        _perms = ('repository.admin', 'repository.write', 'repository.read',)
        validate_repo_permissions(apiuser, source_repo, source_db_repo, _perms)

    owner = validate_set_owner_permissions(apiuser, owner)

    full_source_ref = resolve_ref_or_error(source_ref, source_db_repo)
    full_target_ref = resolve_ref_or_error(target_ref, target_db_repo)

    source_commit = get_commit_or_error(full_source_ref, source_db_repo)
    target_commit = get_commit_or_error(full_target_ref, target_db_repo)

    reviewer_objects = Optional.extract(reviewers) or []

    # serialize and validate passed in given reviewers
    if reviewer_objects:
        schema = ReviewerListSchema()
        try:
            reviewer_objects = schema.deserialize(reviewer_objects)
        except Invalid as err:
            raise JSONRPCValidationError(colander_exc=err)

        # validate users
        for reviewer_object in reviewer_objects:
            user = get_user_or_error(reviewer_object['username'])
            reviewer_object['user_id'] = user.user_id

    get_default_reviewers_data, validate_default_reviewers = \
        PullRequestModel().get_reviewer_functions()

    # recalculate reviewers logic, to make sure we can validate this
    default_reviewers_data = get_default_reviewers_data(
        owner, source_db_repo,
        source_commit, target_db_repo, target_commit)

    # now MERGE our given with the calculated
    reviewer_objects = default_reviewers_data['reviewers'] + reviewer_objects

    try:
        reviewers = validate_default_reviewers(
            reviewer_objects, default_reviewers_data)
    except ValueError as e:
        raise JSONRPCError('Reviewers Validation: {}'.format(e))

    title = Optional.extract(title)
    if not title:
        title_source_ref = source_ref.split(':', 2)[1]
        title = PullRequestModel().generate_pullrequest_title(
            source=source_repo,
            source_ref=title_source_ref,
            target=target_repo
        )

    diff_info = default_reviewers_data['diff_info']
    common_ancestor_id = diff_info['ancestor']
    commits = diff_info['commits']

    if not common_ancestor_id:
        raise JSONRPCError('no common ancestor found')

    if not commits:
        raise JSONRPCError('no commits found')

    # NOTE(marcink): reversed is consistent with how we open it in the WEB interface
    revisions = [commit.raw_id for commit in reversed(commits)]

    # recalculate target ref based on ancestor
    target_ref_type, target_ref_name, __ = full_target_ref.split(':')
    full_target_ref = ':'.join((target_ref_type, target_ref_name, common_ancestor_id))

    # fetch renderer, if set fallback to plain in case of PR
    rc_config = SettingsModel().get_all_settings()
    default_system_renderer = rc_config.get('rhodecode_markup_renderer', 'plain')
    description = Optional.extract(description)
    description_renderer = Optional.extract(description_renderer) or default_system_renderer

    pull_request = PullRequestModel().create(
        created_by=owner.user_id,
        source_repo=source_repo,
        source_ref=full_source_ref,
        target_repo=target_repo,
        target_ref=full_target_ref,
        common_ancestor_id=common_ancestor_id,
        revisions=revisions,
        reviewers=reviewers,
        title=title,
        description=description,
        description_renderer=description_renderer,
        reviewer_data=default_reviewers_data,
        auth_user=apiuser
    )

    Session().commit()
    data = {
        'msg': 'Created new pull request `{}`'.format(title),
        'pull_request_id': pull_request.pull_request_id,
    }
    return data


@jsonrpc_method()
def update_pull_request(
        request, apiuser, pullrequestid, repoid=Optional(None),
        title=Optional(''), description=Optional(''), description_renderer=Optional(''),
        reviewers=Optional(None), update_commits=Optional(None)):
    """
    Updates a pull request.

    :param apiuser: This is filled automatically from the |authtoken|.
    :type apiuser: AuthUser
    :param repoid: Optional repository name or repository ID.
    :type repoid: str or int
    :param pullrequestid: The pull request ID.
    :type pullrequestid: int
    :param title: Set the pull request title.
    :type title: str
    :param description: Update pull request description.
    :type description: Optional(str)
    :type description_renderer: Optional(str)
    :param description_renderer: Update pull request renderer for the description.
        It should be 'rst', 'markdown' or 'plain'
    :param reviewers: Update pull request reviewers list with new value.
    :type reviewers: Optional(list)
        Accepts username strings or objects of the format:

            [{'username': 'nick', 'reasons': ['original author'], 'mandatory': <bool>}]

    :param update_commits: Trigger update of commits for this pull request
    :type: update_commits: Optional(bool)

    Example output:

    .. code-block:: bash

        id : <id_given_in_input>
        result : {
            "msg": "Updated pull request `63`",
            "pull_request": <pull_request_object>,
            "updated_reviewers": {
              "added": [
                "username"
              ],
              "removed": []
            },
            "updated_commits": {
              "added": [
                "<sha1_hash>"
              ],
              "common": [
                "<sha1_hash>",
                "<sha1_hash>",
              ],
              "removed": []
            }
        }
        error :  null
    """

    pull_request = get_pull_request_or_error(pullrequestid)
    if Optional.extract(repoid):
        repo = get_repo_or_error(repoid)
    else:
        repo = pull_request.target_repo

    if not PullRequestModel().check_user_update(
            pull_request, apiuser, api=True):
        raise JSONRPCError(
            'pull request `%s` update failed, no permission to update.' % (
                pullrequestid,))
    if pull_request.is_closed():
        raise JSONRPCError(
            'pull request `%s` update failed, pull request is closed' % (
                pullrequestid,))

    reviewer_objects = Optional.extract(reviewers) or []

    if reviewer_objects:
        schema = ReviewerListSchema()
        try:
            reviewer_objects = schema.deserialize(reviewer_objects)
        except Invalid as err:
            raise JSONRPCValidationError(colander_exc=err)

        # validate users
        for reviewer_object in reviewer_objects:
            user = get_user_or_error(reviewer_object['username'])
            reviewer_object['user_id'] = user.user_id

        get_default_reviewers_data, get_validated_reviewers = \
            PullRequestModel().get_reviewer_functions()

        # re-use stored rules
        reviewer_rules = pull_request.reviewer_data
        try:
            reviewers = get_validated_reviewers(
                reviewer_objects, reviewer_rules)
        except ValueError as e:
            raise JSONRPCError('Reviewers Validation: {}'.format(e))
    else:
        reviewers = []

    title = Optional.extract(title)
    description = Optional.extract(description)
    description_renderer = Optional.extract(description_renderer)

    if title or description:
        PullRequestModel().edit(
            pull_request,
            title or pull_request.title,
            description or pull_request.description,
            description_renderer or pull_request.description_renderer,
            apiuser)
        Session().commit()

    commit_changes = {"added": [], "common": [], "removed": []}
    if str2bool(Optional.extract(update_commits)):

        if pull_request.pull_request_state != PullRequest.STATE_CREATED:
            raise JSONRPCError(
                'Operation forbidden because pull request is in state {}, '
                'only state {} is allowed.'.format(
                    pull_request.pull_request_state, PullRequest.STATE_CREATED))

        with pull_request.set_state(PullRequest.STATE_UPDATING):
            if PullRequestModel().has_valid_update_type(pull_request):
                db_user = apiuser.get_instance()
                update_response = PullRequestModel().update_commits(
                    pull_request, db_user)
                commit_changes = update_response.changes or commit_changes
            Session().commit()

    reviewers_changes = {"added": [], "removed": []}
    if reviewers:
        old_calculated_status = pull_request.calculated_review_status()
        added_reviewers, removed_reviewers = \
            PullRequestModel().update_reviewers(pull_request, reviewers, apiuser)

        reviewers_changes['added'] = sorted(
            [get_user_or_error(n).username for n in added_reviewers])
        reviewers_changes['removed'] = sorted(
            [get_user_or_error(n).username for n in removed_reviewers])
        Session().commit()

        # trigger status changed if change in reviewers changes the status
        calculated_status = pull_request.calculated_review_status()
        if old_calculated_status != calculated_status:
            PullRequestModel().trigger_pull_request_hook(
                pull_request, apiuser, 'review_status_change',
                data={'status': calculated_status})

    data = {
        'msg': 'Updated pull request `{}`'.format(
            pull_request.pull_request_id),
        'pull_request': pull_request.get_api_data(),
        'updated_commits': commit_changes,
        'updated_reviewers': reviewers_changes
    }

    return data


@jsonrpc_method()
def close_pull_request(
        request, apiuser, pullrequestid, repoid=Optional(None),
        userid=Optional(OAttr('apiuser')), message=Optional('')):
    """
    Close the pull request specified by `pullrequestid`.

    :param apiuser: This is filled automatically from the |authtoken|.
    :type apiuser: AuthUser
    :param repoid: Repository name or repository ID to which the pull
        request belongs.
    :type repoid: str or int
    :param pullrequestid: ID of the pull request to be closed.
    :type pullrequestid: int
    :param userid: Close the pull request as this user.
    :type userid: Optional(str or int)
    :param message: Optional message to close the Pull Request with. If not
        specified it will be generated automatically.
    :type message: Optional(str)

    Example output:

    .. code-block:: bash

        "id": <id_given_in_input>,
        "result": {
            "pull_request_id":  "<int>",
            "close_status":     "<str:status_lbl>,
            "closed":           "<bool>"
        },
        "error": null

    """
    _ = request.translate

    pull_request = get_pull_request_or_error(pullrequestid)
    if Optional.extract(repoid):
        repo = get_repo_or_error(repoid)
    else:
        repo = pull_request.target_repo

    is_repo_admin = HasRepoPermissionAnyApi('repository.admin')(
                    user=apiuser, repo_name=repo.repo_name)
    if not isinstance(userid, Optional):
        if has_superadmin_permission(apiuser) or is_repo_admin:
            apiuser = get_user_or_error(userid)
        else:
            raise JSONRPCError('userid is not the same as your user')

    if pull_request.is_closed():
        raise JSONRPCError(
            'pull request `%s` is already closed' % (pullrequestid,))

    # only owner or admin or person with write permissions
    allowed_to_close = PullRequestModel().check_user_update(
            pull_request, apiuser, api=True)

    if not allowed_to_close:
        raise JSONRPCError(
            'pull request `%s` close failed, no permission to close.' % (
                pullrequestid,))

    # message we're using to close the PR, else it's automatically generated
    message = Optional.extract(message)

    # finally close the PR, with proper message comment
    comment, status = PullRequestModel().close_pull_request_with_comment(
        pull_request, apiuser, repo, message=message, auth_user=apiuser)
    status_lbl = ChangesetStatus.get_status_lbl(status)

    Session().commit()

    data = {
        'pull_request_id': pull_request.pull_request_id,
        'close_status': status_lbl,
        'closed': True,
    }
    return data
