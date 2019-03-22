# -*- coding: utf-8 -*-

# Copyright (C) 2011-2019 RhodeCode GmbH
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
comments model for RhodeCode
"""

import logging
import traceback
import collections

from pyramid.threadlocal import get_current_registry, get_current_request
from sqlalchemy.sql.expression import null
from sqlalchemy.sql.functions import coalesce

from rhodecode.lib import helpers as h, diffs, channelstream
from rhodecode.lib import audit_logger
from rhodecode.lib.utils2 import extract_mentioned_users, safe_str
from rhodecode.model import BaseModel
from rhodecode.model.db import (
    ChangesetComment, User, Notification, PullRequest, AttributeDict)
from rhodecode.model.notification import NotificationModel
from rhodecode.model.meta import Session
from rhodecode.model.settings import VcsSettingsModel
from rhodecode.model.notification import EmailNotificationModel
from rhodecode.model.validation_schema.schemas import comment_schema


log = logging.getLogger(__name__)


class CommentsModel(BaseModel):

    cls = ChangesetComment

    DIFF_CONTEXT_BEFORE = 3
    DIFF_CONTEXT_AFTER = 3

    def __get_commit_comment(self, changeset_comment):
        return self._get_instance(ChangesetComment, changeset_comment)

    def __get_pull_request(self, pull_request):
        return self._get_instance(PullRequest, pull_request)

    def _extract_mentions(self, s):
        user_objects = []
        for username in extract_mentioned_users(s):
            user_obj = User.get_by_username(username, case_insensitive=True)
            if user_obj:
                user_objects.append(user_obj)
        return user_objects

    def _get_renderer(self, global_renderer='rst', request=None):
        request = request or get_current_request()

        try:
            global_renderer = request.call_context.visual.default_renderer
        except AttributeError:
            log.debug("Renderer not set, falling back "
                      "to default renderer '%s'", global_renderer)
        except Exception:
            log.error(traceback.format_exc())
        return global_renderer

    def aggregate_comments(self, comments, versions, show_version, inline=False):
        # group by versions, and count until, and display objects

        comment_groups = collections.defaultdict(list)
        [comment_groups[
             _co.pull_request_version_id].append(_co) for _co in comments]

        def yield_comments(pos):
            for co in comment_groups[pos]:
                yield co

        comment_versions = collections.defaultdict(
            lambda: collections.defaultdict(list))
        prev_prvid = -1
        # fake last entry with None, to aggregate on "latest" version which
        # doesn't have an pull_request_version_id
        for ver in versions + [AttributeDict({'pull_request_version_id': None})]:
            prvid = ver.pull_request_version_id
            if prev_prvid == -1:
                prev_prvid = prvid

            for co in yield_comments(prvid):
                comment_versions[prvid]['at'].append(co)

            # save until
            current = comment_versions[prvid]['at']
            prev_until = comment_versions[prev_prvid]['until']
            cur_until = prev_until + current
            comment_versions[prvid]['until'].extend(cur_until)

            # save outdated
            if inline:
                outdated = [x for x in cur_until
                            if x.outdated_at_version(show_version)]
            else:
                outdated = [x for x in cur_until
                            if x.older_than_version(show_version)]
            display = [x for x in cur_until if x not in outdated]

            comment_versions[prvid]['outdated'] = outdated
            comment_versions[prvid]['display'] = display

            prev_prvid = prvid

        return comment_versions

    def get_repository_comments(self, repo, comment_type=None, user=None, commit_id=None):
        qry = Session().query(ChangesetComment) \
            .filter(ChangesetComment.repo == repo)

        if comment_type and comment_type in ChangesetComment.COMMENT_TYPES:
            qry = qry.filter(ChangesetComment.comment_type == comment_type)

        if user:
            user = self._get_user(user)
            if user:
                qry = qry.filter(ChangesetComment.user_id == user.user_id)

        if commit_id:
            qry = qry.filter(ChangesetComment.revision == commit_id)

        qry = qry.order_by(ChangesetComment.created_on)
        return qry.all()

    def get_repository_unresolved_todos(self, repo):
        todos = Session().query(ChangesetComment) \
            .filter(ChangesetComment.repo == repo) \
            .filter(ChangesetComment.resolved_by == None) \
            .filter(ChangesetComment.comment_type
                    == ChangesetComment.COMMENT_TYPE_TODO)
        todos = todos.all()

        return todos

    def get_pull_request_unresolved_todos(self, pull_request, show_outdated=True):

        todos = Session().query(ChangesetComment) \
            .filter(ChangesetComment.pull_request == pull_request) \
            .filter(ChangesetComment.resolved_by == None) \
            .filter(ChangesetComment.comment_type
                    == ChangesetComment.COMMENT_TYPE_TODO)

        if not show_outdated:
            todos = todos.filter(
                coalesce(ChangesetComment.display_state, '') !=
                ChangesetComment.COMMENT_OUTDATED)

        todos = todos.all()

        return todos

    def get_commit_unresolved_todos(self, commit_id, show_outdated=True):

        todos = Session().query(ChangesetComment) \
            .filter(ChangesetComment.revision == commit_id) \
            .filter(ChangesetComment.resolved_by == None) \
            .filter(ChangesetComment.comment_type
                    == ChangesetComment.COMMENT_TYPE_TODO)

        if not show_outdated:
            todos = todos.filter(
                coalesce(ChangesetComment.display_state, '') !=
                ChangesetComment.COMMENT_OUTDATED)

        todos = todos.all()

        return todos

    def _log_audit_action(self, action, action_data, auth_user, comment):
        audit_logger.store(
            action=action,
            action_data=action_data,
            user=auth_user,
            repo=comment.repo)

    def create(self, text, repo, user, commit_id=None, pull_request=None,
               f_path=None, line_no=None, status_change=None,
               status_change_type=None, comment_type=None,
               resolves_comment_id=None, closing_pr=False, send_email=True,
               renderer=None, auth_user=None):
        """
        Creates new comment for commit or pull request.
        IF status_change is not none this comment is associated with a
        status change of commit or commit associated with pull request

        :param text:
        :param repo:
        :param user:
        :param commit_id:
        :param pull_request:
        :param f_path:
        :param line_no:
        :param status_change: Label for status change
        :param comment_type: Type of comment
        :param status_change_type: type of status change
        :param closing_pr:
        :param send_email:
        :param renderer: pick renderer for this comment
        """

        if not text:
            log.warning('Missing text for comment, skipping...')
            return
        request = get_current_request()
        _ = request.translate

        if not renderer:
            renderer = self._get_renderer(request=request)

        repo = self._get_repo(repo)
        user = self._get_user(user)
        auth_user = auth_user or user

        schema = comment_schema.CommentSchema()
        validated_kwargs = schema.deserialize(dict(
            comment_body=text,
            comment_type=comment_type,
            comment_file=f_path,
            comment_line=line_no,
            renderer_type=renderer,
            status_change=status_change_type,
            resolves_comment_id=resolves_comment_id,
            repo=repo.repo_id,
            user=user.user_id,
        ))

        comment = ChangesetComment()
        comment.renderer = validated_kwargs['renderer_type']
        comment.text = validated_kwargs['comment_body']
        comment.f_path = validated_kwargs['comment_file']
        comment.line_no = validated_kwargs['comment_line']
        comment.comment_type = validated_kwargs['comment_type']

        comment.repo = repo
        comment.author = user
        resolved_comment = self.__get_commit_comment(
            validated_kwargs['resolves_comment_id'])
        # check if the comment actually belongs to this PR
        if resolved_comment and resolved_comment.pull_request and \
                resolved_comment.pull_request != pull_request:
            log.warning('Comment tried to resolved unrelated todo comment: %s',
                        resolved_comment)
            # comment not bound to this pull request, forbid
            resolved_comment = None

        elif resolved_comment and resolved_comment.repo and \
                resolved_comment.repo != repo:
            log.warning('Comment tried to resolved unrelated todo comment: %s',
                        resolved_comment)
            # comment not bound to this repo, forbid
            resolved_comment = None

        comment.resolved_comment = resolved_comment

        pull_request_id = pull_request

        commit_obj = None
        pull_request_obj = None

        if commit_id:
            notification_type = EmailNotificationModel.TYPE_COMMIT_COMMENT
            # do a lookup, so we don't pass something bad here
            commit_obj = repo.scm_instance().get_commit(commit_id=commit_id)
            comment.revision = commit_obj.raw_id

        elif pull_request_id:
            notification_type = EmailNotificationModel.TYPE_PULL_REQUEST_COMMENT
            pull_request_obj = self.__get_pull_request(pull_request_id)
            comment.pull_request = pull_request_obj
        else:
            raise Exception('Please specify commit or pull_request_id')

        Session().add(comment)
        Session().flush()
        kwargs = {
            'user': user,
            'renderer_type': renderer,
            'repo_name': repo.repo_name,
            'status_change': status_change,
            'status_change_type': status_change_type,
            'comment_body': text,
            'comment_file': f_path,
            'comment_line': line_no,
            'comment_type': comment_type or 'note'
        }

        if commit_obj:
            recipients = ChangesetComment.get_users(
                revision=commit_obj.raw_id)
            # add commit author if it's in RhodeCode system
            cs_author = User.get_from_cs_author(commit_obj.author)
            if not cs_author:
                # use repo owner if we cannot extract the author correctly
                cs_author = repo.user
            recipients += [cs_author]

            commit_comment_url = self.get_url(comment, request=request)

            target_repo_url = h.link_to(
                repo.repo_name,
                h.route_url('repo_summary', repo_name=repo.repo_name))

            # commit specifics
            kwargs.update({
                'commit': commit_obj,
                'commit_message': commit_obj.message,
                'commit_target_repo': target_repo_url,
                'commit_comment_url': commit_comment_url,
            })

        elif pull_request_obj:
            # get the current participants of this pull request
            recipients = ChangesetComment.get_users(
                pull_request_id=pull_request_obj.pull_request_id)
            # add pull request author
            recipients += [pull_request_obj.author]

            # add the reviewers to notification
            recipients += [x.user for x in pull_request_obj.reviewers]

            pr_target_repo = pull_request_obj.target_repo
            pr_source_repo = pull_request_obj.source_repo

            pr_comment_url = h.route_url(
                'pullrequest_show',
                repo_name=pr_target_repo.repo_name,
                pull_request_id=pull_request_obj.pull_request_id,
                _anchor='comment-%s' % comment.comment_id)

            # set some variables for email notification
            pr_target_repo_url = h.route_url(
                'repo_summary', repo_name=pr_target_repo.repo_name)

            pr_source_repo_url = h.route_url(
                'repo_summary', repo_name=pr_source_repo.repo_name)

            # pull request specifics
            kwargs.update({
                'pull_request': pull_request_obj,
                'pr_id': pull_request_obj.pull_request_id,
                'pr_target_repo': pr_target_repo,
                'pr_target_repo_url': pr_target_repo_url,
                'pr_source_repo': pr_source_repo,
                'pr_source_repo_url': pr_source_repo_url,
                'pr_comment_url': pr_comment_url,
                'pr_closing': closing_pr,
            })
        if send_email:
            # pre-generate the subject for notification itself
            (subject,
             _h, _e,  # we don't care about those
             body_plaintext) = EmailNotificationModel().render_email(
                notification_type, **kwargs)

            mention_recipients = set(
                self._extract_mentions(text)).difference(recipients)

            # create notification objects, and emails
            NotificationModel().create(
                created_by=user,
                notification_subject=subject,
                notification_body=body_plaintext,
                notification_type=notification_type,
                recipients=recipients,
                mention_recipients=mention_recipients,
                email_kwargs=kwargs,
            )

        Session().flush()
        if comment.pull_request:
            action = 'repo.pull_request.comment.create'
        else:
            action = 'repo.commit.comment.create'

        comment_data = comment.get_api_data()
        self._log_audit_action(
            action, {'data': comment_data}, auth_user, comment)

        msg_url = ''
        channel = None
        if commit_obj:
            msg_url = commit_comment_url
            repo_name = repo.repo_name
            channel = u'/repo${}$/commit/{}'.format(
                repo_name,
                commit_obj.raw_id
            )
        elif pull_request_obj:
            msg_url = pr_comment_url
            repo_name = pr_target_repo.repo_name
            channel = u'/repo${}$/pr/{}'.format(
                repo_name,
                pull_request_id
            )

        message = '<strong>{}</strong> {} - ' \
                  '<a onclick="window.location=\'{}\';' \
                  'window.location.reload()">' \
                  '<strong>{}</strong></a>'
        message = message.format(
            user.username, _('made a comment'), msg_url,
            _('Show it now'))

        channelstream.post_message(
            channel, message, user.username,
            registry=get_current_registry())

        return comment

    def delete(self, comment, auth_user):
        """
        Deletes given comment
        """
        comment = self.__get_commit_comment(comment)
        old_data = comment.get_api_data()
        Session().delete(comment)

        if comment.pull_request:
            action = 'repo.pull_request.comment.delete'
        else:
            action = 'repo.commit.comment.delete'

        self._log_audit_action(
            action, {'old_data': old_data}, auth_user, comment)

        return comment

    def get_all_comments(self, repo_id, revision=None, pull_request=None):
        q = ChangesetComment.query()\
                .filter(ChangesetComment.repo_id == repo_id)
        if revision:
            q = q.filter(ChangesetComment.revision == revision)
        elif pull_request:
            pull_request = self.__get_pull_request(pull_request)
            q = q.filter(ChangesetComment.pull_request == pull_request)
        else:
            raise Exception('Please specify commit or pull_request')
        q = q.order_by(ChangesetComment.created_on)
        return q.all()

    def get_url(self, comment, request=None, permalink=False):
        if not request:
            request = get_current_request()

        comment = self.__get_commit_comment(comment)
        if comment.pull_request:
            pull_request = comment.pull_request
            if permalink:
                return request.route_url(
                    'pull_requests_global',
                    pull_request_id=pull_request.pull_request_id,
                    _anchor='comment-%s' % comment.comment_id)
            else:
                return request.route_url(
                    'pullrequest_show',
                    repo_name=safe_str(pull_request.target_repo.repo_name),
                    pull_request_id=pull_request.pull_request_id,
                    _anchor='comment-%s' % comment.comment_id)

        else:
            repo = comment.repo
            commit_id = comment.revision

            if permalink:
                return request.route_url(
                    'repo_commit', repo_name=safe_str(repo.repo_id),
                    commit_id=commit_id,
                    _anchor='comment-%s' % comment.comment_id)

            else:
                return request.route_url(
                    'repo_commit', repo_name=safe_str(repo.repo_name),
                    commit_id=commit_id,
                    _anchor='comment-%s' % comment.comment_id)

    def get_comments(self, repo_id, revision=None, pull_request=None):
        """
        Gets main comments based on revision or pull_request_id

        :param repo_id:
        :param revision:
        :param pull_request:
        """

        q = ChangesetComment.query()\
                .filter(ChangesetComment.repo_id == repo_id)\
                .filter(ChangesetComment.line_no == None)\
                .filter(ChangesetComment.f_path == None)
        if revision:
            q = q.filter(ChangesetComment.revision == revision)
        elif pull_request:
            pull_request = self.__get_pull_request(pull_request)
            q = q.filter(ChangesetComment.pull_request == pull_request)
        else:
            raise Exception('Please specify commit or pull_request')
        q = q.order_by(ChangesetComment.created_on)
        return q.all()

    def get_inline_comments(self, repo_id, revision=None, pull_request=None):
        q = self._get_inline_comments_query(repo_id, revision, pull_request)
        return self._group_comments_by_path_and_line_number(q)

    def get_inline_comments_count(self, inline_comments, skip_outdated=True,
                                  version=None):
        inline_cnt = 0
        for fname, per_line_comments in inline_comments.iteritems():
            for lno, comments in per_line_comments.iteritems():
                for comm in comments:
                    if not comm.outdated_at_version(version) and skip_outdated:
                        inline_cnt += 1

        return inline_cnt

    def get_outdated_comments(self, repo_id, pull_request):
        # TODO: johbo: Remove `repo_id`, it is not needed to find the comments
        # of a pull request.
        q = self._all_inline_comments_of_pull_request(pull_request)
        q = q.filter(
            ChangesetComment.display_state ==
            ChangesetComment.COMMENT_OUTDATED
        ).order_by(ChangesetComment.comment_id.asc())

        return self._group_comments_by_path_and_line_number(q)

    def _get_inline_comments_query(self, repo_id, revision, pull_request):
        # TODO: johbo: Split this into two methods: One for PR and one for
        # commit.
        if revision:
            q = Session().query(ChangesetComment).filter(
                ChangesetComment.repo_id == repo_id,
                ChangesetComment.line_no != null(),
                ChangesetComment.f_path != null(),
                ChangesetComment.revision == revision)

        elif pull_request:
            pull_request = self.__get_pull_request(pull_request)
            if not CommentsModel.use_outdated_comments(pull_request):
                q = self._visible_inline_comments_of_pull_request(pull_request)
            else:
                q = self._all_inline_comments_of_pull_request(pull_request)

        else:
            raise Exception('Please specify commit or pull_request_id')
        q = q.order_by(ChangesetComment.comment_id.asc())
        return q

    def _group_comments_by_path_and_line_number(self, q):
        comments = q.all()
        paths = collections.defaultdict(lambda: collections.defaultdict(list))
        for co in comments:
            paths[co.f_path][co.line_no].append(co)
        return paths

    @classmethod
    def needed_extra_diff_context(cls):
        return max(cls.DIFF_CONTEXT_BEFORE, cls.DIFF_CONTEXT_AFTER)

    def outdate_comments(self, pull_request, old_diff_data, new_diff_data):
        if not CommentsModel.use_outdated_comments(pull_request):
            return

        comments = self._visible_inline_comments_of_pull_request(pull_request)
        comments_to_outdate = comments.all()

        for comment in comments_to_outdate:
            self._outdate_one_comment(comment, old_diff_data, new_diff_data)

    def _outdate_one_comment(self, comment, old_diff_proc, new_diff_proc):
        diff_line = _parse_comment_line_number(comment.line_no)

        try:
            old_context = old_diff_proc.get_context_of_line(
                path=comment.f_path, diff_line=diff_line)
            new_context = new_diff_proc.get_context_of_line(
                path=comment.f_path, diff_line=diff_line)
        except (diffs.LineNotInDiffException,
                diffs.FileNotInDiffException):
            comment.display_state = ChangesetComment.COMMENT_OUTDATED
            return

        if old_context == new_context:
            return

        if self._should_relocate_diff_line(diff_line):
            new_diff_lines = new_diff_proc.find_context(
                path=comment.f_path, context=old_context,
                offset=self.DIFF_CONTEXT_BEFORE)
            if not new_diff_lines:
                comment.display_state = ChangesetComment.COMMENT_OUTDATED
            else:
                new_diff_line = self._choose_closest_diff_line(
                    diff_line, new_diff_lines)
                comment.line_no = _diff_to_comment_line_number(new_diff_line)
        else:
            comment.display_state = ChangesetComment.COMMENT_OUTDATED

    def _should_relocate_diff_line(self, diff_line):
        """
        Checks if relocation shall be tried for the given `diff_line`.

        If a comment points into the first lines, then we can have a situation
        that after an update another line has been added on top. In this case
        we would find the context still and move the comment around. This
        would be wrong.
        """
        should_relocate = (
            (diff_line.new and diff_line.new > self.DIFF_CONTEXT_BEFORE) or
            (diff_line.old and diff_line.old > self.DIFF_CONTEXT_BEFORE))
        return should_relocate

    def _choose_closest_diff_line(self, diff_line, new_diff_lines):
        candidate = new_diff_lines[0]
        best_delta = _diff_line_delta(diff_line, candidate)
        for new_diff_line in new_diff_lines[1:]:
            delta = _diff_line_delta(diff_line, new_diff_line)
            if delta < best_delta:
                candidate = new_diff_line
                best_delta = delta
        return candidate

    def _visible_inline_comments_of_pull_request(self, pull_request):
        comments = self._all_inline_comments_of_pull_request(pull_request)
        comments = comments.filter(
            coalesce(ChangesetComment.display_state, '') !=
            ChangesetComment.COMMENT_OUTDATED)
        return comments

    def _all_inline_comments_of_pull_request(self, pull_request):
        comments = Session().query(ChangesetComment)\
            .filter(ChangesetComment.line_no != None)\
            .filter(ChangesetComment.f_path != None)\
            .filter(ChangesetComment.pull_request == pull_request)
        return comments

    def _all_general_comments_of_pull_request(self, pull_request):
        comments = Session().query(ChangesetComment)\
            .filter(ChangesetComment.line_no == None)\
            .filter(ChangesetComment.f_path == None)\
            .filter(ChangesetComment.pull_request == pull_request)
        return comments

    @staticmethod
    def use_outdated_comments(pull_request):
        settings_model = VcsSettingsModel(repo=pull_request.target_repo)
        settings = settings_model.get_general_settings()
        return settings.get('rhodecode_use_outdated_comments', False)


def _parse_comment_line_number(line_no):
    """
    Parses line numbers of the form "(o|n)\d+" and returns them in a tuple.
    """
    old_line = None
    new_line = None
    if line_no.startswith('o'):
        old_line = int(line_no[1:])
    elif line_no.startswith('n'):
        new_line = int(line_no[1:])
    else:
        raise ValueError("Comment lines have to start with either 'o' or 'n'.")
    return diffs.DiffLineNumber(old_line, new_line)


def _diff_to_comment_line_number(diff_line):
    if diff_line.new is not None:
        return u'n{}'.format(diff_line.new)
    elif diff_line.old is not None:
        return u'o{}'.format(diff_line.old)
    return u''


def _diff_line_delta(a, b):
    if None not in (a.new, b.new):
        return abs(a.new - b.new)
    elif None not in (a.old, b.old):
        return abs(a.old - b.old)
    else:
        raise ValueError(
            "Cannot compute delta between {} and {}".format(a, b))
