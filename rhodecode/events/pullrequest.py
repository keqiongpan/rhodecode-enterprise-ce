# Copyright (C) 2016-2020 RhodeCode GmbH
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

from rhodecode.translation import lazy_ugettext
from rhodecode.events.repo import (RepoEvent, _commits_as_dict, _issues_as_dict)

log = logging.getLogger(__name__)


class PullRequestEvent(RepoEvent):
    """
    Base class for pull request events.

    :param pullrequest: a :class:`PullRequest` instance
    """

    def __init__(self, pullrequest):
        super(PullRequestEvent, self).__init__(pullrequest.target_repo)
        self.pullrequest = pullrequest

    def as_dict(self):
        from rhodecode.lib.utils2 import md5_safe
        from rhodecode.model.pull_request import PullRequestModel
        data = super(PullRequestEvent, self).as_dict()

        commits = _commits_as_dict(
            self,
            commit_ids=self.pullrequest.revisions,
            repos=[self.pullrequest.source_repo]
        )
        issues = _issues_as_dict(commits)
        # calculate hashes of all commits for unique identifier of commits
        # inside that pull request
        commits_hash = md5_safe(':'.join(x.get('raw_id', '') for x in commits))

        data.update({
            'pullrequest': {
                'title': self.pullrequest.title,
                'issues': issues,
                'pull_request_id': self.pullrequest.pull_request_id,
                'url': PullRequestModel().get_url(
                    self.pullrequest, request=self.request),
                'permalink_url': PullRequestModel().get_url(
                    self.pullrequest, request=self.request, permalink=True),
                'shadow_url': PullRequestModel().get_shadow_clone_url(
                    self.pullrequest, request=self.request),
                'status': self.pullrequest.calculated_review_status(),
                'commits_uid': commits_hash,
                'commits': commits,
            }
        })
        return data


class PullRequestCreateEvent(PullRequestEvent):
    """
    An instance of this class is emitted as an :term:`event` after a pull
    request is created.
    """
    name = 'pullrequest-create'
    display_name = lazy_ugettext('pullrequest created')
    description = lazy_ugettext('Event triggered after pull request was created')


class PullRequestCloseEvent(PullRequestEvent):
    """
    An instance of this class is emitted as an :term:`event` after a pull
    request is closed.
    """
    name = 'pullrequest-close'
    display_name = lazy_ugettext('pullrequest closed')
    description = lazy_ugettext('Event triggered after pull request was closed')


class PullRequestUpdateEvent(PullRequestEvent):
    """
    An instance of this class is emitted as an :term:`event` after a pull
    request's commits have been updated.
    """
    name = 'pullrequest-update'
    display_name = lazy_ugettext('pullrequest commits updated')
    description = lazy_ugettext('Event triggered after pull requests was updated')


class PullRequestReviewEvent(PullRequestEvent):
    """
    An instance of this class is emitted as an :term:`event` after a pull
    request review has changed. A status defines new status of review.
    """
    name = 'pullrequest-review'
    display_name = lazy_ugettext('pullrequest review changed')
    description = lazy_ugettext('Event triggered after a review status of a '
                                'pull requests has changed to other.')

    def __init__(self, pullrequest, status):
        super(PullRequestReviewEvent, self).__init__(pullrequest)
        self.status = status


class PullRequestMergeEvent(PullRequestEvent):
    """
    An instance of this class is emitted as an :term:`event` after a pull
    request is merged.
    """
    name = 'pullrequest-merge'
    display_name = lazy_ugettext('pullrequest merged')
    description = lazy_ugettext('Event triggered after a successful merge operation '
                                'was executed on a pull request')


class PullRequestCommentEvent(PullRequestEvent):
    """
    An instance of this class is emitted as an :term:`event` after a pull
    request comment is created.
    """
    name = 'pullrequest-comment'
    display_name = lazy_ugettext('pullrequest commented')
    description = lazy_ugettext('Event triggered after a comment was made on a code '
                                'in the pull request')

    def __init__(self, pullrequest, comment):
        super(PullRequestCommentEvent, self).__init__(pullrequest)
        self.comment = comment

    def as_dict(self):
        from rhodecode.model.comment import CommentsModel
        data = super(PullRequestCommentEvent, self).as_dict()

        status = None
        if self.comment.status_change:
            status = self.comment.review_status

        data.update({
            'comment': {
                'status': status,
                'text': self.comment.text,
                'type': self.comment.comment_type,
                'file': self.comment.f_path,
                'line': self.comment.line_no,
                'version': self.comment.last_version,
                'url': CommentsModel().get_url(
                    self.comment, request=self.request),
                'permalink_url': CommentsModel().get_url(
                    self.comment, request=self.request, permalink=True),
            }
        })
        return data


class PullRequestCommentEditEvent(PullRequestEvent):
    """
    An instance of this class is emitted as an :term:`event` after a pull
    request comment is edited.
    """
    name = 'pullrequest-comment-edit'
    display_name = lazy_ugettext('pullrequest comment edited')
    description = lazy_ugettext('Event triggered after a comment was edited on a code '
                                'in the pull request')

    def __init__(self, pullrequest, comment):
        super(PullRequestCommentEditEvent, self).__init__(pullrequest)
        self.comment = comment

    def as_dict(self):
        from rhodecode.model.comment import CommentsModel
        data = super(PullRequestCommentEditEvent, self).as_dict()

        status = None
        if self.comment.status_change:
            status = self.comment.review_status

        data.update({
            'comment': {
                'status': status,
                'text': self.comment.text,
                'type': self.comment.comment_type,
                'file': self.comment.f_path,
                'line': self.comment.line_no,
                'version': self.comment.last_version,
                'url': CommentsModel().get_url(
                    self.comment, request=self.request),
                'permalink_url': CommentsModel().get_url(
                    self.comment, request=self.request, permalink=True),
            }
        })
        return data
