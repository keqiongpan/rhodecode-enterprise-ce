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


import logging
import collections

from pyramid.httpexceptions import HTTPNotFound, HTTPBadRequest, HTTPFound
from pyramid.view import view_config
from pyramid.renderers import render
from pyramid.response import Response

from rhodecode.apps._base import RepoAppView

from rhodecode.lib import diffs, codeblocks
from rhodecode.lib.auth import (
    LoginRequired, HasRepoPermissionAnyDecorator, NotAnonymous, CSRFRequired)

from rhodecode.lib.compat import OrderedDict
from rhodecode.lib.exceptions import StatusChangeOnClosedPullRequestError
import rhodecode.lib.helpers as h
from rhodecode.lib.utils2 import safe_unicode
from rhodecode.lib.vcs.backends.base import EmptyCommit
from rhodecode.lib.vcs.exceptions import (
    RepositoryError, CommitDoesNotExistError, NodeDoesNotExistError)
from rhodecode.model.db import ChangesetComment, ChangesetStatus
from rhodecode.model.changeset_status import ChangesetStatusModel
from rhodecode.model.comment import CommentsModel
from rhodecode.model.meta import Session


log = logging.getLogger(__name__)


def _update_with_GET(params, request):
    for k in ['diff1', 'diff2', 'diff']:
        params[k] += request.GET.getall(k)


def get_ignore_ws(fid, request):
    ig_ws_global = request.GET.get('ignorews')
    ig_ws = filter(lambda k: k.startswith('WS'), request.GET.getall(fid))
    if ig_ws:
        try:
            return int(ig_ws[0].split(':')[-1])
        except Exception:
            pass
    return ig_ws_global


def _ignorews_url(request, fileid=None):
    _ = request.translate
    fileid = str(fileid) if fileid else None
    params = collections.defaultdict(list)
    _update_with_GET(params, request)
    label = _('Show whitespace')
    tooltiplbl = _('Show whitespace for all diffs')
    ig_ws = get_ignore_ws(fileid, request)
    ln_ctx = get_line_ctx(fileid, request)

    if ig_ws is None:
        params['ignorews'] += [1]
        label = _('Ignore whitespace')
        tooltiplbl = _('Ignore whitespace for all diffs')
    ctx_key = 'context'
    ctx_val = ln_ctx

    # if we have passed in ln_ctx pass it along to our params
    if ln_ctx:
        params[ctx_key] += [ctx_val]

    if fileid:
        params['anchor'] = 'a_' + fileid
    return h.link_to(label, request.current_route_path(_query=params),
                     title=tooltiplbl, class_='tooltip')


def get_line_ctx(fid, request):
    ln_ctx_global = request.GET.get('context')
    if fid:
        ln_ctx = filter(lambda k: k.startswith('C'), request.GET.getall(fid))
    else:
        _ln_ctx = filter(lambda k: k.startswith('C'), request.GET)
        ln_ctx = request.GET.get(_ln_ctx[0]) if _ln_ctx else ln_ctx_global
        if ln_ctx:
            ln_ctx = [ln_ctx]

    if ln_ctx:
        retval = ln_ctx[0].split(':')[-1]
    else:
        retval = ln_ctx_global

    try:
        return int(retval)
    except Exception:
        return 3


def _context_url(request, fileid=None):
    """
    Generates a url for context lines.

    :param fileid:
    """

    _ = request.translate
    fileid = str(fileid) if fileid else None
    ig_ws = get_ignore_ws(fileid, request)
    ln_ctx = (get_line_ctx(fileid, request) or 3) * 2

    params = collections.defaultdict(list)
    _update_with_GET(params, request)

    if ln_ctx > 0:
        params['context'] += [ln_ctx]

    if ig_ws:
        ig_ws_key = 'ignorews'
        ig_ws_val = 1
        params[ig_ws_key] += [ig_ws_val]

    lbl = _('Increase context')
    tooltiplbl = _('Increase context for all diffs')

    if fileid:
        params['anchor'] = 'a_' + fileid
    return h.link_to(lbl, request.current_route_path(_query=params),
                     title=tooltiplbl, class_='tooltip')


class RepoCommitsView(RepoAppView):
    def load_default_context(self):
        c = self._get_local_tmpl_context(include_app_defaults=True)
        c.rhodecode_repo = self.rhodecode_vcs_repo

        self._register_global_c(c)
        return c

    def _commit(self, commit_id_range, method):
        _ = self.request.translate
        c = self.load_default_context()
        c.ignorews_url = _ignorews_url
        c.context_url = _context_url
        c.fulldiff = self.request.GET.get('fulldiff')

        # fetch global flags of ignore ws or context lines
        context_lcl = get_line_ctx('', self.request)
        ign_whitespace_lcl = get_ignore_ws('', self.request)

        # diff_limit will cut off the whole diff if the limit is applied
        # otherwise it will just hide the big files from the front-end
        diff_limit = c.visual.cut_off_limit_diff
        file_limit = c.visual.cut_off_limit_file

        # get ranges of commit ids if preset
        commit_range = commit_id_range.split('...')[:2]

        try:
            pre_load = ['affected_files', 'author', 'branch', 'date',
                        'message', 'parents']

            if len(commit_range) == 2:
                commits = self.rhodecode_vcs_repo.get_commits(
                    start_id=commit_range[0], end_id=commit_range[1],
                    pre_load=pre_load)
                commits = list(commits)
            else:
                commits = [self.rhodecode_vcs_repo.get_commit(
                    commit_id=commit_id_range, pre_load=pre_load)]

            c.commit_ranges = commits
            if not c.commit_ranges:
                raise RepositoryError(
                    'The commit range returned an empty result')
        except CommitDoesNotExistError:
            msg = _('No such commit exists for this repository')
            h.flash(msg, category='error')
            raise HTTPNotFound()
        except Exception:
            log.exception("General failure")
            raise HTTPNotFound()

        c.changes = OrderedDict()
        c.lines_added = 0
        c.lines_deleted = 0

        # auto collapse if we have more than limit
        collapse_limit = diffs.DiffProcessor._collapse_commits_over
        c.collapse_all_commits = len(c.commit_ranges) > collapse_limit

        c.commit_statuses = ChangesetStatus.STATUSES
        c.inline_comments = []
        c.files = []

        c.statuses = []
        c.comments = []
        c.unresolved_comments = []
        if len(c.commit_ranges) == 1:
            commit = c.commit_ranges[0]
            c.comments = CommentsModel().get_comments(
                self.db_repo.repo_id,
                revision=commit.raw_id)
            c.statuses.append(ChangesetStatusModel().get_status(
                self.db_repo.repo_id, commit.raw_id))
            # comments from PR
            statuses = ChangesetStatusModel().get_statuses(
                self.db_repo.repo_id, commit.raw_id,
                with_revisions=True)
            prs = set(st.pull_request for st in statuses
                      if st.pull_request is not None)
            # from associated statuses, check the pull requests, and
            # show comments from them
            for pr in prs:
                c.comments.extend(pr.comments)

            c.unresolved_comments = CommentsModel()\
                .get_commit_unresolved_todos(commit.raw_id)

        diff = None
        # Iterate over ranges (default commit view is always one commit)
        for commit in c.commit_ranges:
            c.changes[commit.raw_id] = []

            commit2 = commit
            commit1 = commit.parents[0] if commit.parents else EmptyCommit()

            _diff = self.rhodecode_vcs_repo.get_diff(
                commit1, commit2,
                ignore_whitespace=ign_whitespace_lcl, context=context_lcl)
            diff_processor = diffs.DiffProcessor(
                _diff, format='newdiff', diff_limit=diff_limit,
                file_limit=file_limit, show_full_diff=c.fulldiff)

            commit_changes = OrderedDict()
            if method == 'show':
                _parsed = diff_processor.prepare()
                c.limited_diff = isinstance(_parsed, diffs.LimitedDiffContainer)

                _parsed = diff_processor.prepare()

                def _node_getter(commit):
                    def get_node(fname):
                        try:
                            return commit.get_node(fname)
                        except NodeDoesNotExistError:
                            return None
                    return get_node

                inline_comments = CommentsModel().get_inline_comments(
                    self.db_repo.repo_id, revision=commit.raw_id)
                c.inline_cnt = CommentsModel().get_inline_comments_count(
                    inline_comments)

                diffset = codeblocks.DiffSet(
                    repo_name=self.db_repo_name,
                    source_node_getter=_node_getter(commit1),
                    target_node_getter=_node_getter(commit2),
                    comments=inline_comments)
                diffset = diffset.render_patchset(
                    _parsed, commit1.raw_id, commit2.raw_id)

                c.changes[commit.raw_id] = diffset
            else:
                # downloads/raw we only need RAW diff nothing else
                diff = diff_processor.as_raw()
                c.changes[commit.raw_id] = [None, None, None, None, diff, None, None]

        # sort comments by how they were generated
        c.comments = sorted(c.comments, key=lambda x: x.comment_id)

        if len(c.commit_ranges) == 1:
            c.commit = c.commit_ranges[0]
            c.parent_tmpl = ''.join(
                '# Parent  %s\n' % x.raw_id for x in c.commit.parents)

        if method == 'download':
            response = Response(diff)
            response.content_type = 'text/plain'
            response.content_disposition = (
                'attachment; filename=%s.diff' % commit_id_range[:12])
            return response
        elif method == 'patch':
            c.diff = safe_unicode(diff)
            patch = render(
                'rhodecode:templates/changeset/patch_changeset.mako',
                self._get_template_context(c), self.request)
            response = Response(patch)
            response.content_type = 'text/plain'
            return response
        elif method == 'raw':
            response = Response(diff)
            response.content_type = 'text/plain'
            return response
        elif method == 'show':
            if len(c.commit_ranges) == 1:
                html = render(
                    'rhodecode:templates/changeset/changeset.mako',
                    self._get_template_context(c), self.request)
                return Response(html)
            else:
                c.ancestor = None
                c.target_repo = self.db_repo
                html = render(
                    'rhodecode:templates/changeset/changeset_range.mako',
                    self._get_template_context(c), self.request)
                return Response(html)

        raise HTTPBadRequest()

    @LoginRequired()
    @HasRepoPermissionAnyDecorator(
        'repository.read', 'repository.write', 'repository.admin')
    @view_config(
        route_name='repo_commit', request_method='GET',
        renderer=None)
    def repo_commit_show(self):
        commit_id = self.request.matchdict['commit_id']
        return self._commit(commit_id, method='show')

    @LoginRequired()
    @HasRepoPermissionAnyDecorator(
        'repository.read', 'repository.write', 'repository.admin')
    @view_config(
        route_name='repo_commit_raw', request_method='GET',
        renderer=None)
    @view_config(
        route_name='repo_commit_raw_deprecated', request_method='GET',
        renderer=None)
    def repo_commit_raw(self):
        commit_id = self.request.matchdict['commit_id']
        return self._commit(commit_id, method='raw')

    @LoginRequired()
    @HasRepoPermissionAnyDecorator(
        'repository.read', 'repository.write', 'repository.admin')
    @view_config(
        route_name='repo_commit_patch', request_method='GET',
        renderer=None)
    def repo_commit_patch(self):
        commit_id = self.request.matchdict['commit_id']
        return self._commit(commit_id, method='patch')

    @LoginRequired()
    @HasRepoPermissionAnyDecorator(
        'repository.read', 'repository.write', 'repository.admin')
    @view_config(
        route_name='repo_commit_download', request_method='GET',
        renderer=None)
    def repo_commit_download(self):
        commit_id = self.request.matchdict['commit_id']
        return self._commit(commit_id, method='download')

    @LoginRequired()
    @NotAnonymous()
    @HasRepoPermissionAnyDecorator(
        'repository.read', 'repository.write', 'repository.admin')
    @CSRFRequired()
    @view_config(
        route_name='repo_commit_comment_create', request_method='POST',
        renderer='json_ext')
    def repo_commit_comment_create(self):
        _ = self.request.translate
        commit_id = self.request.matchdict['commit_id']

        c = self.load_default_context()
        status = self.request.POST.get('changeset_status', None)
        text = self.request.POST.get('text')
        comment_type = self.request.POST.get('comment_type')
        resolves_comment_id = self.request.POST.get('resolves_comment_id', None)

        if status:
            text = text or (_('Status change %(transition_icon)s %(status)s')
                            % {'transition_icon': '>',
                               'status': ChangesetStatus.get_status_lbl(status)})

        multi_commit_ids = []
        for _commit_id in self.request.POST.get('commit_ids', '').split(','):
            if _commit_id not in ['', None, EmptyCommit.raw_id]:
                if _commit_id not in multi_commit_ids:
                    multi_commit_ids.append(_commit_id)

        commit_ids = multi_commit_ids or [commit_id]

        comment = None
        for current_id in filter(None, commit_ids):
            comment = CommentsModel().create(
                text=text,
                repo=self.db_repo.repo_id,
                user=self._rhodecode_db_user.user_id,
                commit_id=current_id,
                f_path=self.request.POST.get('f_path'),
                line_no=self.request.POST.get('line'),
                status_change=(ChangesetStatus.get_status_lbl(status)
                               if status else None),
                status_change_type=status,
                comment_type=comment_type,
                resolves_comment_id=resolves_comment_id
            )

            # get status if set !
            if status:
                # if latest status was from pull request and it's closed
                # disallow changing status !
                # dont_allow_on_closed_pull_request = True !

                try:
                    ChangesetStatusModel().set_status(
                        self.db_repo.repo_id,
                        status,
                        self._rhodecode_db_user.user_id,
                        comment,
                        revision=current_id,
                        dont_allow_on_closed_pull_request=True
                    )
                except StatusChangeOnClosedPullRequestError:
                    msg = _('Changing the status of a commit associated with '
                            'a closed pull request is not allowed')
                    log.exception(msg)
                    h.flash(msg, category='warning')
                    raise HTTPFound(h.route_path(
                        'repo_commit', repo_name=self.db_repo_name,
                        commit_id=current_id))

        # finalize, commit and redirect
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
        route_name='repo_commit_comment_preview', request_method='POST',
        renderer='string', xhr=True)
    def repo_commit_comment_preview(self):
        # Technically a CSRF token is not needed as no state changes with this
        # call. However, as this is a POST is better to have it, so automated
        # tools don't flag it as potential CSRF.
        # Post is required because the payload could be bigger than the maximum
        # allowed by GET.

        text = self.request.POST.get('text')
        renderer = self.request.POST.get('renderer') or 'rst'
        if text:
            return h.render(text, renderer=renderer, mentions=True)
        return ''

    @LoginRequired()
    @NotAnonymous()
    @HasRepoPermissionAnyDecorator(
        'repository.read', 'repository.write', 'repository.admin')
    @CSRFRequired()
    @view_config(
        route_name='repo_commit_comment_delete', request_method='POST',
        renderer='json_ext')
    def repo_commit_comment_delete(self):
        commit_id = self.request.matchdict['commit_id']
        comment_id = self.request.matchdict['comment_id']

        comment = ChangesetComment.get_or_404(comment_id)
        if not comment:
            log.debug('Comment with id:%s not found, skipping', comment_id)
            # comment already deleted in another call probably
            return True

        is_repo_admin = h.HasRepoPermissionAny('repository.admin')(self.db_repo_name)
        super_admin = h.HasPermissionAny('hg.admin')()
        comment_owner = (comment.author.user_id == self._rhodecode_db_user.user_id)
        is_repo_comment = comment.repo.repo_name == self.db_repo_name
        comment_repo_admin = is_repo_admin and is_repo_comment

        if super_admin or comment_owner or comment_repo_admin:
            CommentsModel().delete(comment=comment, user=self._rhodecode_db_user)
            Session().commit()
            return True
        else:
            log.warning('No permissions for user %s to delete comment_id: %s',
                        self._rhodecode_db_user, comment_id)
            raise HTTPNotFound()

    @LoginRequired()
    @HasRepoPermissionAnyDecorator(
        'repository.read', 'repository.write', 'repository.admin')
    @view_config(
        route_name='repo_commit_data', request_method='GET',
        renderer='json_ext', xhr=True)
    def repo_commit_data(self):
        commit_id = self.request.matchdict['commit_id']
        self.load_default_context()

        try:
            return self.rhodecode_vcs_repo.get_commit(commit_id=commit_id)
        except CommitDoesNotExistError as e:
            return EmptyCommit(message=str(e))

    @LoginRequired()
    @HasRepoPermissionAnyDecorator(
        'repository.read', 'repository.write', 'repository.admin')
    @view_config(
        route_name='repo_commit_children', request_method='GET',
        renderer='json_ext', xhr=True)
    def repo_commit_children(self):
        commit_id = self.request.matchdict['commit_id']
        self.load_default_context()

        commit = self.rhodecode_vcs_repo.get_commit(commit_id=commit_id)
        result = {"results": commit.children}
        return result

    @LoginRequired()
    @HasRepoPermissionAnyDecorator(
        'repository.read', 'repository.write', 'repository.admin')
    @view_config(
        route_name='repo_commit_parents', request_method='GET',
        renderer='json_ext')
    def repo_commit_parents(self):
        commit_id = self.request.matchdict['commit_id']
        self.load_default_context()

        commit = self.rhodecode_vcs_repo.get_commit(commit_id=commit_id)
        result = {"results": commit.parents}
        return result
