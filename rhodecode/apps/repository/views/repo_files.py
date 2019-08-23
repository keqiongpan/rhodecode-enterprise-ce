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

import itertools
import logging
import os
import shutil
import tempfile
import collections
import urllib
import pathlib2

from pyramid.httpexceptions import HTTPNotFound, HTTPBadRequest, HTTPFound
from pyramid.view import view_config
from pyramid.renderers import render
from pyramid.response import Response

import rhodecode
from rhodecode.apps._base import RepoAppView


from rhodecode.lib import diffs, helpers as h, rc_cache
from rhodecode.lib import audit_logger
from rhodecode.lib.view_utils import parse_path_ref
from rhodecode.lib.exceptions import NonRelativePathError
from rhodecode.lib.codeblocks import (
    filenode_as_lines_tokens, filenode_as_annotated_lines_tokens)
from rhodecode.lib.utils2 import (
    convert_line_endings, detect_mode, safe_str, str2bool, safe_int, sha1, safe_unicode)
from rhodecode.lib.auth import (
    LoginRequired, HasRepoPermissionAnyDecorator, CSRFRequired)
from rhodecode.lib.vcs import path as vcspath
from rhodecode.lib.vcs.backends.base import EmptyCommit
from rhodecode.lib.vcs.conf import settings
from rhodecode.lib.vcs.nodes import FileNode
from rhodecode.lib.vcs.exceptions import (
    RepositoryError, CommitDoesNotExistError, EmptyRepositoryError,
    ImproperArchiveTypeError, VCSError, NodeAlreadyExistsError,
    NodeDoesNotExistError, CommitError, NodeError)

from rhodecode.model.scm import ScmModel
from rhodecode.model.db import Repository

log = logging.getLogger(__name__)


class RepoFilesView(RepoAppView):

    @staticmethod
    def adjust_file_path_for_svn(f_path, repo):
        """
        Computes the relative path of `f_path`.

        This is mainly based on prefix matching of the recognized tags and
        branches in the underlying repository.
        """
        tags_and_branches = itertools.chain(
            repo.branches.iterkeys(),
            repo.tags.iterkeys())
        tags_and_branches = sorted(tags_and_branches, key=len, reverse=True)

        for name in tags_and_branches:
            if f_path.startswith('{}/'.format(name)):
                f_path = vcspath.relpath(f_path, name)
                break
        return f_path

    def load_default_context(self):
        c = self._get_local_tmpl_context(include_app_defaults=True)
        c.rhodecode_repo = self.rhodecode_vcs_repo
        c.enable_downloads = self.db_repo.enable_downloads
        return c

    def _ensure_not_locked(self, commit_id='tip'):
        _ = self.request.translate

        repo = self.db_repo
        if repo.enable_locking and repo.locked[0]:
            h.flash(_('This repository has been locked by %s on %s')
                    % (h.person_by_id(repo.locked[0]),
                    h.format_date(h.time_to_datetime(repo.locked[1]))),
                    'warning')
            files_url = h.route_path(
                'repo_files:default_path',
                repo_name=self.db_repo_name, commit_id=commit_id)
            raise HTTPFound(files_url)

    def forbid_non_head(self, is_head, f_path, commit_id='tip', json_mode=False):
        _ = self.request.translate

        if not is_head:
            message = _('Cannot modify file. '
                        'Given commit `{}` is not head of a branch.').format(commit_id)
            h.flash(message, category='warning')

            if json_mode:
                return message

            files_url = h.route_path(
                'repo_files', repo_name=self.db_repo_name, commit_id=commit_id,
                f_path=f_path)
            raise HTTPFound(files_url)

    def check_branch_permission(self, branch_name, commit_id='tip', json_mode=False):
        _ = self.request.translate

        rule, branch_perm = self._rhodecode_user.get_rule_and_branch_permission(
            self.db_repo_name, branch_name)
        if branch_perm and branch_perm not in ['branch.push', 'branch.push_force']:
            message = _('Branch `{}` changes forbidden by rule {}.').format(
                branch_name, rule)
            h.flash(message, 'warning')

            if json_mode:
                return message

            files_url = h.route_path(
                'repo_files:default_path', repo_name=self.db_repo_name, commit_id=commit_id)

            raise HTTPFound(files_url)

    def _get_commit_and_path(self):
        default_commit_id = self.db_repo.landing_rev[1]
        default_f_path = '/'

        commit_id = self.request.matchdict.get(
            'commit_id', default_commit_id)
        f_path = self._get_f_path(self.request.matchdict, default_f_path)
        return commit_id, f_path

    def _get_default_encoding(self, c):
        enc_list = getattr(c, 'default_encodings', [])
        return enc_list[0] if enc_list else 'UTF-8'

    def _get_commit_or_redirect(self, commit_id, redirect_after=True):
        """
        This is a safe way to get commit. If an error occurs it redirects to
        tip with proper message

        :param commit_id: id of commit to fetch
        :param redirect_after: toggle redirection
        """
        _ = self.request.translate

        try:
            return self.rhodecode_vcs_repo.get_commit(commit_id)
        except EmptyRepositoryError:
            if not redirect_after:
                return None

            _url = h.route_path(
                'repo_files_add_file',
                repo_name=self.db_repo_name, commit_id=0, f_path='')

            if h.HasRepoPermissionAny(
                    'repository.write', 'repository.admin')(self.db_repo_name):
                add_new = h.link_to(
                    _('Click here to add a new file.'), _url, class_="alert-link")
            else:
                add_new = ""

            h.flash(h.literal(
                _('There are no files yet. %s') % add_new), category='warning')
            raise HTTPFound(
                h.route_path('repo_summary', repo_name=self.db_repo_name))

        except (CommitDoesNotExistError, LookupError):
            msg = _('No such commit exists for this repository')
            h.flash(msg, category='error')
            raise HTTPNotFound()
        except RepositoryError as e:
            h.flash(safe_str(h.escape(e)), category='error')
            raise HTTPNotFound()

    def _get_filenode_or_redirect(self, commit_obj, path):
        """
        Returns file_node, if error occurs or given path is directory,
        it'll redirect to top level path
        """
        _ = self.request.translate

        try:
            file_node = commit_obj.get_node(path)
            if file_node.is_dir():
                raise RepositoryError('The given path is a directory')
        except CommitDoesNotExistError:
            log.exception('No such commit exists for this repository')
            h.flash(_('No such commit exists for this repository'), category='error')
            raise HTTPNotFound()
        except RepositoryError as e:
            log.warning('Repository error while fetching filenode `%s`. Err:%s', path, e)
            h.flash(safe_str(h.escape(e)), category='error')
            raise HTTPNotFound()

        return file_node

    def _is_valid_head(self, commit_id, repo):
        branch_name = sha_commit_id = ''
        is_head = False
        log.debug('Checking if commit_id `%s` is a head for %s.', commit_id, repo)

        for _branch_name, branch_commit_id in repo.branches.items():
            # simple case we pass in branch name, it's a HEAD
            if commit_id == _branch_name:
                is_head = True
                branch_name = _branch_name
                sha_commit_id = branch_commit_id
                break
            # case when we pass in full sha commit_id, which is a head
            elif commit_id == branch_commit_id:
                is_head = True
                branch_name = _branch_name
                sha_commit_id = branch_commit_id
                break

        if h.is_svn(repo) and not repo.is_empty():
            # Note: Subversion only has one head.
            if commit_id == repo.get_commit(commit_idx=-1).raw_id:
                is_head = True
                return branch_name, sha_commit_id, is_head

        # checked branches, means we only need to try to get the branch/commit_sha
        if not repo.is_empty():
            commit = repo.get_commit(commit_id=commit_id)
            if commit:
                branch_name = commit.branch
                sha_commit_id = commit.raw_id

        return branch_name, sha_commit_id, is_head

    def _get_tree_at_commit(self, c, commit_id, f_path, full_load=False):

        repo_id = self.db_repo.repo_id
        force_recache = self.get_recache_flag()

        cache_seconds = safe_int(
            rhodecode.CONFIG.get('rc_cache.cache_repo.expiration_time'))
        cache_on = not force_recache and cache_seconds > 0
        log.debug(
            'Computing FILE TREE for repo_id %s commit_id `%s` and path `%s`'
            'with caching: %s[TTL: %ss]' % (
                repo_id, commit_id, f_path, cache_on, cache_seconds or 0))

        cache_namespace_uid = 'cache_repo.{}'.format(repo_id)
        region = rc_cache.get_or_create_region('cache_repo', cache_namespace_uid)

        @region.conditional_cache_on_arguments(namespace=cache_namespace_uid,
                                               condition=cache_on)
        def compute_file_tree(ver, repo_id, commit_id, f_path, full_load):
            log.debug('Generating cached file tree at ver:%s for repo_id: %s, %s, %s',
                      ver, repo_id, commit_id, f_path)

            c.full_load = full_load
            return render(
                'rhodecode:templates/files/files_browser_tree.mako',
                self._get_template_context(c), self.request)

        return compute_file_tree('v1', self.db_repo.repo_id, commit_id, f_path, full_load)

    def _get_archive_spec(self, fname):
        log.debug('Detecting archive spec for: `%s`', fname)

        fileformat = None
        ext = None
        content_type = None
        for a_type, content_type, extension in settings.ARCHIVE_SPECS:

            if fname.endswith(extension):
                fileformat = a_type
                log.debug('archive is of type: %s', fileformat)
                ext = extension
                break

        if not fileformat:
            raise ValueError()

        # left over part of whole fname is the commit
        commit_id = fname[:-len(ext)]

        return commit_id, ext, fileformat, content_type

    def create_pure_path(self, *parts):
        # Split paths and sanitize them, removing any ../ etc
        sanitized_path = [
            x for x in pathlib2.PurePath(*parts).parts
            if x not in ['.', '..']]

        pure_path = pathlib2.PurePath(*sanitized_path)
        return pure_path

    def _is_lf_enabled(self, target_repo):
        lf_enabled = False

        lf_key_for_vcs_map = {
            'hg': 'extensions_largefiles',
            'git': 'vcs_git_lfs_enabled'
        }

        lf_key_for_vcs = lf_key_for_vcs_map.get(target_repo.repo_type)

        if lf_key_for_vcs:
            lf_enabled = self._get_repo_setting(target_repo, lf_key_for_vcs)

        return lf_enabled

    @LoginRequired()
    @HasRepoPermissionAnyDecorator(
        'repository.read', 'repository.write', 'repository.admin')
    @view_config(
        route_name='repo_archivefile', request_method='GET',
        renderer=None)
    def repo_archivefile(self):
        # archive cache config
        from rhodecode import CONFIG
        _ = self.request.translate
        self.load_default_context()
        default_at_path = '/'
        fname = self.request.matchdict['fname']
        subrepos = self.request.GET.get('subrepos') == 'true'
        at_path = self.request.GET.get('at_path') or default_at_path

        if not self.db_repo.enable_downloads:
            return Response(_('Downloads disabled'))

        try:
            commit_id, ext, fileformat, content_type = \
                self._get_archive_spec(fname)
        except ValueError:
            return Response(_('Unknown archive type for: `{}`').format(
                h.escape(fname)))

        try:
            commit = self.rhodecode_vcs_repo.get_commit(commit_id)
        except CommitDoesNotExistError:
            return Response(_('Unknown commit_id {}').format(
                h.escape(commit_id)))
        except EmptyRepositoryError:
            return Response(_('Empty repository'))

        try:
            at_path = commit.get_node(at_path).path or default_at_path
        except Exception:
            return Response(_('No node at path {} for this repository').format(at_path))

        path_sha = sha1(at_path)[:8]

        # original backward compat name of archive
        clean_name = safe_str(self.db_repo_name.replace('/', '_'))
        short_sha = safe_str(commit.short_id)

        if at_path == default_at_path:
            archive_name = '{}-{}{}{}'.format(
                clean_name,
                '-sub' if subrepos else '',
                short_sha,
                ext)
        # custom path and new name
        else:
            archive_name = '{}-{}{}-{}{}'.format(
                clean_name,
                '-sub' if subrepos else '',
                short_sha,
                path_sha,
                ext)

        use_cached_archive = False
        archive_cache_enabled = CONFIG.get(
            'archive_cache_dir') and not self.request.GET.get('no_cache')
        cached_archive_path = None

        if archive_cache_enabled:
            # check if we it's ok to write
            if not os.path.isdir(CONFIG['archive_cache_dir']):
                os.makedirs(CONFIG['archive_cache_dir'])
            cached_archive_path = os.path.join(
                CONFIG['archive_cache_dir'], archive_name)
            if os.path.isfile(cached_archive_path):
                log.debug('Found cached archive in %s', cached_archive_path)
                fd, archive = None, cached_archive_path
                use_cached_archive = True
            else:
                log.debug('Archive %s is not yet cached', archive_name)

        if not use_cached_archive:
            # generate new archive
            fd, archive = tempfile.mkstemp()
            log.debug('Creating new temp archive in %s', archive)
            try:
                commit.archive_repo(archive, kind=fileformat, subrepos=subrepos,
                                    archive_at_path=at_path)
            except ImproperArchiveTypeError:
                return _('Unknown archive type')
            if archive_cache_enabled:
                # if we generated the archive and we have cache enabled
                # let's use this for future
                log.debug('Storing new archive in %s', cached_archive_path)
                shutil.move(archive, cached_archive_path)
                archive = cached_archive_path

        # store download action
        audit_logger.store_web(
            'repo.archive.download', action_data={
                'user_agent': self.request.user_agent,
                'archive_name': archive_name,
                'archive_spec': fname,
                'archive_cached': use_cached_archive},
            user=self._rhodecode_user,
            repo=self.db_repo,
            commit=True
        )

        def get_chunked_archive(archive_path):
            with open(archive_path, 'rb') as stream:
                while True:
                    data = stream.read(16 * 1024)
                    if not data:
                        if fd:  # fd means we used temporary file
                            os.close(fd)
                        if not archive_cache_enabled:
                            log.debug('Destroying temp archive %s', archive_path)
                            os.remove(archive_path)
                        break
                    yield data

        response = Response(app_iter=get_chunked_archive(archive))
        response.content_disposition = str(
            'attachment; filename=%s' % archive_name)
        response.content_type = str(content_type)

        return response

    def _get_file_node(self, commit_id, f_path):
        if commit_id not in ['', None, 'None', '0' * 12, '0' * 40]:
            commit = self.rhodecode_vcs_repo.get_commit(commit_id=commit_id)
            try:
                node = commit.get_node(f_path)
                if node.is_dir():
                    raise NodeError('%s path is a %s not a file'
                                    % (node, type(node)))
            except NodeDoesNotExistError:
                commit = EmptyCommit(
                    commit_id=commit_id,
                    idx=commit.idx,
                    repo=commit.repository,
                    alias=commit.repository.alias,
                    message=commit.message,
                    author=commit.author,
                    date=commit.date)
                node = FileNode(f_path, '', commit=commit)
        else:
            commit = EmptyCommit(
                repo=self.rhodecode_vcs_repo,
                alias=self.rhodecode_vcs_repo.alias)
            node = FileNode(f_path, '', commit=commit)
        return node

    @LoginRequired()
    @HasRepoPermissionAnyDecorator(
        'repository.read', 'repository.write', 'repository.admin')
    @view_config(
        route_name='repo_files_diff', request_method='GET',
        renderer=None)
    def repo_files_diff(self):
        c = self.load_default_context()
        f_path = self._get_f_path(self.request.matchdict)
        diff1 = self.request.GET.get('diff1', '')
        diff2 = self.request.GET.get('diff2', '')

        path1, diff1 = parse_path_ref(diff1, default_path=f_path)

        ignore_whitespace = str2bool(self.request.GET.get('ignorews'))
        line_context = self.request.GET.get('context', 3)

        if not any((diff1, diff2)):
            h.flash(
                'Need query parameter "diff1" or "diff2" to generate a diff.',
                category='error')
            raise HTTPBadRequest()

        c.action = self.request.GET.get('diff')
        if c.action not in ['download', 'raw']:
            compare_url = h.route_path(
                'repo_compare',
                repo_name=self.db_repo_name,
                source_ref_type='rev',
                source_ref=diff1,
                target_repo=self.db_repo_name,
                target_ref_type='rev',
                target_ref=diff2,
                _query=dict(f_path=f_path))
            # redirect to new view if we render diff
            raise HTTPFound(compare_url)

        try:
            node1 = self._get_file_node(diff1, path1)
            node2 = self._get_file_node(diff2, f_path)
        except (RepositoryError, NodeError):
            log.exception("Exception while trying to get node from repository")
            raise HTTPFound(
                h.route_path('repo_files', repo_name=self.db_repo_name,
                             commit_id='tip', f_path=f_path))

        if all(isinstance(node.commit, EmptyCommit)
               for node in (node1, node2)):
            raise HTTPNotFound()

        c.commit_1 = node1.commit
        c.commit_2 = node2.commit

        if c.action == 'download':
            _diff = diffs.get_gitdiff(node1, node2,
                                      ignore_whitespace=ignore_whitespace,
                                      context=line_context)
            diff = diffs.DiffProcessor(_diff, format='gitdiff')

            response = Response(self.path_filter.get_raw_patch(diff))
            response.content_type = 'text/plain'
            response.content_disposition = (
                'attachment; filename=%s_%s_vs_%s.diff' % (f_path, diff1, diff2)
            )
            charset = self._get_default_encoding(c)
            if charset:
                response.charset = charset
            return response

        elif c.action == 'raw':
            _diff = diffs.get_gitdiff(node1, node2,
                                      ignore_whitespace=ignore_whitespace,
                                      context=line_context)
            diff = diffs.DiffProcessor(_diff, format='gitdiff')

            response = Response(self.path_filter.get_raw_patch(diff))
            response.content_type = 'text/plain'
            charset = self._get_default_encoding(c)
            if charset:
                response.charset = charset
            return response

        # in case we ever end up here
        raise HTTPNotFound()

    @LoginRequired()
    @HasRepoPermissionAnyDecorator(
        'repository.read', 'repository.write', 'repository.admin')
    @view_config(
        route_name='repo_files_diff_2way_redirect', request_method='GET',
        renderer=None)
    def repo_files_diff_2way_redirect(self):
        """
        Kept only to make OLD links work
        """
        f_path = self._get_f_path_unchecked(self.request.matchdict)
        diff1 = self.request.GET.get('diff1', '')
        diff2 = self.request.GET.get('diff2', '')

        if not any((diff1, diff2)):
            h.flash(
                'Need query parameter "diff1" or "diff2" to generate a diff.',
                category='error')
            raise HTTPBadRequest()

        compare_url = h.route_path(
            'repo_compare',
            repo_name=self.db_repo_name,
            source_ref_type='rev',
            source_ref=diff1,
            target_ref_type='rev',
            target_ref=diff2,
            _query=dict(f_path=f_path, diffmode='sideside',
                        target_repo=self.db_repo_name,))
        raise HTTPFound(compare_url)

    @LoginRequired()
    @HasRepoPermissionAnyDecorator(
        'repository.read', 'repository.write', 'repository.admin')
    @view_config(
        route_name='repo_files', request_method='GET',
        renderer=None)
    @view_config(
        route_name='repo_files:default_path', request_method='GET',
        renderer=None)
    @view_config(
        route_name='repo_files:default_commit', request_method='GET',
        renderer=None)
    @view_config(
        route_name='repo_files:rendered', request_method='GET',
        renderer=None)
    @view_config(
        route_name='repo_files:annotated', request_method='GET',
        renderer=None)
    def repo_files(self):
        c = self.load_default_context()

        view_name = getattr(self.request.matched_route, 'name', None)

        c.annotate = view_name == 'repo_files:annotated'
        # default is false, but .rst/.md files later are auto rendered, we can
        # overwrite auto rendering by setting this GET flag
        c.renderer = view_name == 'repo_files:rendered' or \
                        not self.request.GET.get('no-render', False)

        # redirect to given commit_id from form if given
        get_commit_id = self.request.GET.get('at_rev', None)
        if get_commit_id:
            self._get_commit_or_redirect(get_commit_id)

        commit_id, f_path = self._get_commit_and_path()
        c.commit = self._get_commit_or_redirect(commit_id)
        c.branch = self.request.GET.get('branch', None)
        c.f_path = f_path

        # prev link
        try:
            prev_commit = c.commit.prev(c.branch)
            c.prev_commit = prev_commit
            c.url_prev = h.route_path(
                'repo_files', repo_name=self.db_repo_name,
                commit_id=prev_commit.raw_id, f_path=f_path)
            if c.branch:
                c.url_prev += '?branch=%s' % c.branch
        except (CommitDoesNotExistError, VCSError):
            c.url_prev = '#'
            c.prev_commit = EmptyCommit()

        # next link
        try:
            next_commit = c.commit.next(c.branch)
            c.next_commit = next_commit
            c.url_next = h.route_path(
                'repo_files', repo_name=self.db_repo_name,
                commit_id=next_commit.raw_id, f_path=f_path)
            if c.branch:
                c.url_next += '?branch=%s' % c.branch
        except (CommitDoesNotExistError, VCSError):
            c.url_next = '#'
            c.next_commit = EmptyCommit()

        # files or dirs
        try:
            c.file = c.commit.get_node(f_path)
            c.file_author = True
            c.file_tree = ''

            # load file content
            if c.file.is_file():
                c.lf_node = {}

                has_lf_enabled = self._is_lf_enabled(self.db_repo)
                if has_lf_enabled:
                    c.lf_node = c.file.get_largefile_node()

                c.file_source_page = 'true'
                c.file_last_commit = c.file.last_commit

                c.file_size_too_big = c.file.size > c.visual.cut_off_limit_file

                if not (c.file_size_too_big or c.file.is_binary):
                    if c.annotate:  # annotation has precedence over renderer
                        c.annotated_lines = filenode_as_annotated_lines_tokens(
                            c.file
                        )
                    else:
                        c.renderer = (
                            c.renderer and h.renderer_from_filename(c.file.path)
                        )
                        if not c.renderer:
                            c.lines = filenode_as_lines_tokens(c.file)

                _branch_name, _sha_commit_id, is_head = self._is_valid_head(
                    commit_id, self.rhodecode_vcs_repo)
                c.on_branch_head = is_head

                branch = c.commit.branch if (
                    c.commit.branch and '/' not in c.commit.branch) else None
                c.branch_or_raw_id = branch or c.commit.raw_id
                c.branch_name = c.commit.branch or h.short_id(c.commit.raw_id)

                author = c.file_last_commit.author
                c.authors = [[
                    h.email(author),
                    h.person(author, 'username_or_name_or_email'),
                    1
                ]]

            else:  # load tree content at path
                c.file_source_page = 'false'
                c.authors = []
                # this loads a simple tree without metadata to speed things up
                # later via ajax we call repo_nodetree_full and fetch whole
                c.file_tree = self._get_tree_at_commit(c, c.commit.raw_id, f_path)

        except RepositoryError as e:
            h.flash(safe_str(h.escape(e)), category='error')
            raise HTTPNotFound()

        if self.request.environ.get('HTTP_X_PJAX'):
            html = render('rhodecode:templates/files/files_pjax.mako',
                          self._get_template_context(c), self.request)
        else:
            html = render('rhodecode:templates/files/files.mako',
                          self._get_template_context(c), self.request)
        return Response(html)

    @HasRepoPermissionAnyDecorator(
        'repository.read', 'repository.write', 'repository.admin')
    @view_config(
        route_name='repo_files:annotated_previous', request_method='GET',
        renderer=None)
    def repo_files_annotated_previous(self):
        self.load_default_context()

        commit_id, f_path = self._get_commit_and_path()
        commit = self._get_commit_or_redirect(commit_id)
        prev_commit_id = commit.raw_id
        line_anchor = self.request.GET.get('line_anchor')
        is_file = False
        try:
            _file = commit.get_node(f_path)
            is_file = _file.is_file()
        except (NodeDoesNotExistError, CommitDoesNotExistError, VCSError):
            pass

        if is_file:
            history = commit.get_path_history(f_path)
            prev_commit_id = history[1].raw_id \
                if len(history) > 1 else prev_commit_id
        prev_url = h.route_path(
            'repo_files:annotated', repo_name=self.db_repo_name,
            commit_id=prev_commit_id, f_path=f_path,
            _anchor='L{}'.format(line_anchor))

        raise HTTPFound(prev_url)

    @LoginRequired()
    @HasRepoPermissionAnyDecorator(
        'repository.read', 'repository.write', 'repository.admin')
    @view_config(
        route_name='repo_nodetree_full', request_method='GET',
        renderer=None, xhr=True)
    @view_config(
        route_name='repo_nodetree_full:default_path', request_method='GET',
        renderer=None, xhr=True)
    def repo_nodetree_full(self):
        """
        Returns rendered html of file tree that contains commit date,
        author, commit_id for the specified combination of
        repo, commit_id and file path
        """
        c = self.load_default_context()

        commit_id, f_path = self._get_commit_and_path()
        commit = self._get_commit_or_redirect(commit_id)
        try:
            dir_node = commit.get_node(f_path)
        except RepositoryError as e:
            return Response('error: {}'.format(h.escape(safe_str(e))))

        if dir_node.is_file():
            return Response('')

        c.file = dir_node
        c.commit = commit

        html = self._get_tree_at_commit(
            c, commit.raw_id, dir_node.path, full_load=True)

        return Response(html)

    def _get_attachement_headers(self, f_path):
        f_name = safe_str(f_path.split(Repository.NAME_SEP)[-1])
        safe_path = f_name.replace('"', '\\"')
        encoded_path = urllib.quote(f_name)

        return "attachment; " \
               "filename=\"{}\"; " \
               "filename*=UTF-8\'\'{}".format(safe_path, encoded_path)

    @LoginRequired()
    @HasRepoPermissionAnyDecorator(
        'repository.read', 'repository.write', 'repository.admin')
    @view_config(
        route_name='repo_file_raw', request_method='GET',
        renderer=None)
    def repo_file_raw(self):
        """
        Action for show as raw, some mimetypes are "rendered",
        those include images, icons.
        """
        c = self.load_default_context()

        commit_id, f_path = self._get_commit_and_path()
        commit = self._get_commit_or_redirect(commit_id)
        file_node = self._get_filenode_or_redirect(commit, f_path)

        raw_mimetype_mapping = {
            # map original mimetype to a mimetype used for "show as raw"
            # you can also provide a content-disposition to override the
            # default "attachment" disposition.
            # orig_type: (new_type, new_dispo)

            # show images inline:
            # Do not re-add SVG: it is unsafe and permits XSS attacks. One can
            # for example render an SVG with javascript inside or even render
            # HTML.
            'image/x-icon': ('image/x-icon', 'inline'),
            'image/png': ('image/png', 'inline'),
            'image/gif': ('image/gif', 'inline'),
            'image/jpeg': ('image/jpeg', 'inline'),
            'application/pdf': ('application/pdf', 'inline'),
        }

        mimetype = file_node.mimetype
        try:
            mimetype, disposition = raw_mimetype_mapping[mimetype]
        except KeyError:
            # we don't know anything special about this, handle it safely
            if file_node.is_binary:
                # do same as download raw for binary files
                mimetype, disposition = 'application/octet-stream', 'attachment'
            else:
                # do not just use the original mimetype, but force text/plain,
                # otherwise it would serve text/html and that might be unsafe.
                # Note: underlying vcs library fakes text/plain mimetype if the
                # mimetype can not be determined and it thinks it is not
                # binary.This might lead to erroneous text display in some
                # cases, but helps in other cases, like with text files
                # without extension.
                mimetype, disposition = 'text/plain', 'inline'

        if disposition == 'attachment':
            disposition = self._get_attachement_headers(f_path)

        stream_content = file_node.stream_bytes()

        response = Response(app_iter=stream_content)
        response.content_disposition = disposition
        response.content_type = mimetype

        charset = self._get_default_encoding(c)
        if charset:
            response.charset = charset

        return response

    @LoginRequired()
    @HasRepoPermissionAnyDecorator(
        'repository.read', 'repository.write', 'repository.admin')
    @view_config(
        route_name='repo_file_download', request_method='GET',
        renderer=None)
    @view_config(
        route_name='repo_file_download:legacy', request_method='GET',
        renderer=None)
    def repo_file_download(self):
        c = self.load_default_context()

        commit_id, f_path = self._get_commit_and_path()
        commit = self._get_commit_or_redirect(commit_id)
        file_node = self._get_filenode_or_redirect(commit, f_path)

        if self.request.GET.get('lf'):
            # only if lf get flag is passed, we download this file
            # as LFS/Largefile
            lf_node = file_node.get_largefile_node()
            if lf_node:
                # overwrite our pointer with the REAL large-file
                file_node = lf_node

        disposition = self._get_attachement_headers(f_path)

        stream_content = file_node.stream_bytes()

        response = Response(app_iter=stream_content)
        response.content_disposition = disposition
        response.content_type = file_node.mimetype

        charset = self._get_default_encoding(c)
        if charset:
            response.charset = charset

        return response

    def _get_nodelist_at_commit(self, repo_name, repo_id, commit_id, f_path):

        cache_seconds = safe_int(
            rhodecode.CONFIG.get('rc_cache.cache_repo.expiration_time'))
        cache_on = cache_seconds > 0
        log.debug(
            'Computing FILE SEARCH for repo_id %s commit_id `%s` and path `%s`'
            'with caching: %s[TTL: %ss]' % (
                repo_id, commit_id, f_path, cache_on, cache_seconds or 0))

        cache_namespace_uid = 'cache_repo.{}'.format(repo_id)
        region = rc_cache.get_or_create_region('cache_repo', cache_namespace_uid)

        @region.conditional_cache_on_arguments(namespace=cache_namespace_uid,
                                               condition=cache_on)
        def compute_file_search(repo_id, commit_id, f_path):
            log.debug('Generating cached nodelist for repo_id:%s, %s, %s',
                      repo_id, commit_id, f_path)
            try:
                _d, _f = ScmModel().get_nodes(
                    repo_name, commit_id, f_path, flat=False)
            except (RepositoryError, CommitDoesNotExistError, Exception) as e:
                log.exception(safe_str(e))
                h.flash(safe_str(h.escape(e)), category='error')
                raise HTTPFound(h.route_path(
                    'repo_files', repo_name=self.db_repo_name,
                    commit_id='tip', f_path='/'))

            return _d + _f

        result = compute_file_search(self.db_repo.repo_id, commit_id, f_path)
        return filter(lambda n: self.path_filter.path_access_allowed(n['name']), result)

    @LoginRequired()
    @HasRepoPermissionAnyDecorator(
        'repository.read', 'repository.write', 'repository.admin')
    @view_config(
        route_name='repo_files_nodelist', request_method='GET',
        renderer='json_ext', xhr=True)
    def repo_nodelist(self):
        self.load_default_context()

        commit_id, f_path = self._get_commit_and_path()
        commit = self._get_commit_or_redirect(commit_id)

        metadata = self._get_nodelist_at_commit(
            self.db_repo_name, self.db_repo.repo_id, commit.raw_id, f_path)
        return {'nodes': metadata}

    def _create_references(self, branches_or_tags, symbolic_reference, f_path, ref_type):
        items = []
        for name, commit_id in branches_or_tags.items():
            sym_ref = symbolic_reference(commit_id, name, f_path, ref_type)
            items.append((sym_ref, name, ref_type))
        return items

    def _symbolic_reference(self, commit_id, name, f_path, ref_type):
        return commit_id

    def _symbolic_reference_svn(self, commit_id, name, f_path, ref_type):
        new_f_path = vcspath.join(name, f_path)
        return u'%s@%s' % (new_f_path, commit_id)

    def _get_node_history(self, commit_obj, f_path, commits=None):
        """
        get commit history for given node

        :param commit_obj: commit to calculate history
        :param f_path: path for node to calculate history for
        :param commits: if passed don't calculate history and take
            commits defined in this list
        """
        _ = self.request.translate

        # calculate history based on tip
        tip = self.rhodecode_vcs_repo.get_commit()
        if commits is None:
            pre_load = ["author", "branch"]
            try:
                commits = tip.get_path_history(f_path, pre_load=pre_load)
            except (NodeDoesNotExistError, CommitError):
                # this node is not present at tip!
                commits = commit_obj.get_path_history(f_path, pre_load=pre_load)

        history = []
        commits_group = ([], _("Changesets"))
        for commit in commits:
            branch = ' (%s)' % commit.branch if commit.branch else ''
            n_desc = 'r%s:%s%s' % (commit.idx, commit.short_id, branch)
            commits_group[0].append((commit.raw_id, n_desc, 'sha'))
        history.append(commits_group)

        symbolic_reference = self._symbolic_reference

        if self.rhodecode_vcs_repo.alias == 'svn':
            adjusted_f_path = RepoFilesView.adjust_file_path_for_svn(
                f_path, self.rhodecode_vcs_repo)
            if adjusted_f_path != f_path:
                log.debug(
                    'Recognized svn tag or branch in file "%s", using svn '
                    'specific symbolic references', f_path)
                f_path = adjusted_f_path
                symbolic_reference = self._symbolic_reference_svn

        branches = self._create_references(
            self.rhodecode_vcs_repo.branches, symbolic_reference, f_path, 'branch')
        branches_group = (branches, _("Branches"))

        tags = self._create_references(
            self.rhodecode_vcs_repo.tags, symbolic_reference, f_path, 'tag')
        tags_group = (tags, _("Tags"))

        history.append(branches_group)
        history.append(tags_group)

        return history, commits

    @LoginRequired()
    @HasRepoPermissionAnyDecorator(
        'repository.read', 'repository.write', 'repository.admin')
    @view_config(
        route_name='repo_file_history', request_method='GET',
        renderer='json_ext')
    def repo_file_history(self):
        self.load_default_context()

        commit_id, f_path = self._get_commit_and_path()
        commit = self._get_commit_or_redirect(commit_id)
        file_node = self._get_filenode_or_redirect(commit, f_path)

        if file_node.is_file():
            file_history, _hist = self._get_node_history(commit, f_path)

            res = []
            for obj in file_history:
                res.append({
                    'text': obj[1],
                    'children': [{'id': o[0], 'text': o[1], 'type': o[2]} for o in obj[0]]
                })

            data = {
                'more': False,
                'results': res
            }
            return data

        log.warning('Cannot fetch history for directory')
        raise HTTPBadRequest()

    @LoginRequired()
    @HasRepoPermissionAnyDecorator(
        'repository.read', 'repository.write', 'repository.admin')
    @view_config(
        route_name='repo_file_authors', request_method='GET',
        renderer='rhodecode:templates/files/file_authors_box.mako')
    def repo_file_authors(self):
        c = self.load_default_context()

        commit_id, f_path = self._get_commit_and_path()
        commit = self._get_commit_or_redirect(commit_id)
        file_node = self._get_filenode_or_redirect(commit, f_path)

        if not file_node.is_file():
            raise HTTPBadRequest()

        c.file_last_commit = file_node.last_commit
        if self.request.GET.get('annotate') == '1':
            # use _hist from annotation if annotation mode is on
            commit_ids = set(x[1] for x in file_node.annotate)
            _hist = (
                self.rhodecode_vcs_repo.get_commit(commit_id)
                for commit_id in commit_ids)
        else:
            _f_history, _hist = self._get_node_history(commit, f_path)
        c.file_author = False

        unique = collections.OrderedDict()
        for commit in _hist:
            author = commit.author
            if author not in unique:
                unique[commit.author] = [
                    h.email(author),
                    h.person(author, 'username_or_name_or_email'),
                    1  # counter
                ]

            else:
                # increase counter
                unique[commit.author][2] += 1

        c.authors = [val for val in unique.values()]

        return self._get_template_context(c)

    @LoginRequired()
    @HasRepoPermissionAnyDecorator('repository.write', 'repository.admin')
    @view_config(
        route_name='repo_files_remove_file', request_method='GET',
        renderer='rhodecode:templates/files/files_delete.mako')
    def repo_files_remove_file(self):
        _ = self.request.translate
        c = self.load_default_context()
        commit_id, f_path = self._get_commit_and_path()

        self._ensure_not_locked()
        _branch_name, _sha_commit_id, is_head = \
            self._is_valid_head(commit_id, self.rhodecode_vcs_repo)

        self.forbid_non_head(is_head, f_path)
        self.check_branch_permission(_branch_name)

        c.commit = self._get_commit_or_redirect(commit_id)
        c.file = self._get_filenode_or_redirect(c.commit, f_path)

        c.default_message = _(
            'Deleted file {} via RhodeCode Enterprise').format(f_path)
        c.f_path = f_path

        return self._get_template_context(c)

    @LoginRequired()
    @HasRepoPermissionAnyDecorator('repository.write', 'repository.admin')
    @CSRFRequired()
    @view_config(
        route_name='repo_files_delete_file', request_method='POST',
        renderer=None)
    def repo_files_delete_file(self):
        _ = self.request.translate

        c = self.load_default_context()
        commit_id, f_path = self._get_commit_and_path()

        self._ensure_not_locked()
        _branch_name, _sha_commit_id, is_head = \
            self._is_valid_head(commit_id, self.rhodecode_vcs_repo)

        self.forbid_non_head(is_head, f_path)
        self.check_branch_permission(_branch_name)

        c.commit = self._get_commit_or_redirect(commit_id)
        c.file = self._get_filenode_or_redirect(c.commit, f_path)

        c.default_message = _(
            'Deleted file {} via RhodeCode Enterprise').format(f_path)
        c.f_path = f_path
        node_path = f_path
        author = self._rhodecode_db_user.full_contact
        message = self.request.POST.get('message') or c.default_message
        try:
            nodes = {
                node_path: {
                    'content': ''
                }
            }
            ScmModel().delete_nodes(
                user=self._rhodecode_db_user.user_id, repo=self.db_repo,
                message=message,
                nodes=nodes,
                parent_commit=c.commit,
                author=author,
            )

            h.flash(
                _('Successfully deleted file `{}`').format(
                    h.escape(f_path)), category='success')
        except Exception:
            log.exception('Error during commit operation')
            h.flash(_('Error occurred during commit'), category='error')
        raise HTTPFound(
            h.route_path('repo_commit', repo_name=self.db_repo_name,
                         commit_id='tip'))

    @LoginRequired()
    @HasRepoPermissionAnyDecorator('repository.write', 'repository.admin')
    @view_config(
        route_name='repo_files_edit_file', request_method='GET',
        renderer='rhodecode:templates/files/files_edit.mako')
    def repo_files_edit_file(self):
        _ = self.request.translate
        c = self.load_default_context()
        commit_id, f_path = self._get_commit_and_path()

        self._ensure_not_locked()
        _branch_name, _sha_commit_id, is_head = \
            self._is_valid_head(commit_id, self.rhodecode_vcs_repo)

        self.forbid_non_head(is_head, f_path, commit_id=commit_id)
        self.check_branch_permission(_branch_name, commit_id=commit_id)

        c.commit = self._get_commit_or_redirect(commit_id)
        c.file = self._get_filenode_or_redirect(c.commit, f_path)

        if c.file.is_binary:
            files_url = h.route_path(
                'repo_files',
                repo_name=self.db_repo_name,
                commit_id=c.commit.raw_id, f_path=f_path)
            raise HTTPFound(files_url)

        c.default_message = _('Edited file {} via RhodeCode Enterprise').format(f_path)
        c.f_path = f_path

        return self._get_template_context(c)

    @LoginRequired()
    @HasRepoPermissionAnyDecorator('repository.write', 'repository.admin')
    @CSRFRequired()
    @view_config(
        route_name='repo_files_update_file', request_method='POST',
        renderer=None)
    def repo_files_update_file(self):
        _ = self.request.translate
        c = self.load_default_context()
        commit_id, f_path = self._get_commit_and_path()

        self._ensure_not_locked()

        c.commit = self._get_commit_or_redirect(commit_id)
        c.file = self._get_filenode_or_redirect(c.commit, f_path)

        if c.file.is_binary:
            raise HTTPFound(h.route_path('repo_files', repo_name=self.db_repo_name,
                                         commit_id=c.commit.raw_id, f_path=f_path))

        _branch_name, _sha_commit_id, is_head = \
            self._is_valid_head(commit_id, self.rhodecode_vcs_repo)

        self.forbid_non_head(is_head, f_path, commit_id=commit_id)
        self.check_branch_permission(_branch_name, commit_id=commit_id)

        c.default_message = _('Edited file {} via RhodeCode Enterprise').format(f_path)
        c.f_path = f_path

        old_content = c.file.content
        sl = old_content.splitlines(1)
        first_line = sl[0] if sl else ''

        r_post = self.request.POST
        # line endings:  0 - Unix, 1 - Mac, 2 - DOS
        line_ending_mode = detect_mode(first_line, 0)
        content = convert_line_endings(r_post.get('content', ''), line_ending_mode)

        message = r_post.get('message') or c.default_message
        org_node_path = c.file.unicode_path
        filename = r_post['filename']

        root_path = c.file.dir_path
        pure_path = self.create_pure_path(root_path, filename)
        node_path = safe_unicode(bytes(pure_path))

        default_redirect_url = h.route_path('repo_commit', repo_name=self.db_repo_name,
                                            commit_id=commit_id)
        if content == old_content and node_path == org_node_path:
            h.flash(_('No changes detected on {}').format(org_node_path),
                    category='warning')
            raise HTTPFound(default_redirect_url)

        try:
            mapping = {
                org_node_path: {
                    'org_filename': org_node_path,
                    'filename': node_path,
                    'content': content,
                    'lexer': '',
                    'op': 'mod',
                    'mode': c.file.mode
                }
            }

            commit = ScmModel().update_nodes(
                user=self._rhodecode_db_user.user_id,
                repo=self.db_repo,
                message=message,
                nodes=mapping,
                parent_commit=c.commit,
            )

            h.flash(_('Successfully committed changes to file `{}`').format(
                    h.escape(f_path)), category='success')
            default_redirect_url = h.route_path(
                'repo_commit', repo_name=self.db_repo_name, commit_id=commit.raw_id)

        except Exception:
            log.exception('Error occurred during commit')
            h.flash(_('Error occurred during commit'), category='error')

        raise HTTPFound(default_redirect_url)

    @LoginRequired()
    @HasRepoPermissionAnyDecorator('repository.write', 'repository.admin')
    @view_config(
        route_name='repo_files_add_file', request_method='GET',
        renderer='rhodecode:templates/files/files_add.mako')
    @view_config(
        route_name='repo_files_upload_file', request_method='GET',
        renderer='rhodecode:templates/files/files_upload.mako')
    def repo_files_add_file(self):
        _ = self.request.translate
        c = self.load_default_context()
        commit_id, f_path = self._get_commit_and_path()

        self._ensure_not_locked()

        c.commit = self._get_commit_or_redirect(commit_id, redirect_after=False)
        if c.commit is None:
            c.commit = EmptyCommit(alias=self.rhodecode_vcs_repo.alias)

        if self.rhodecode_vcs_repo.is_empty():
            # for empty repository we cannot check for current branch, we rely on
            # c.commit.branch instead
            _branch_name, _sha_commit_id, is_head = c.commit.branch, '', True
        else:
            _branch_name, _sha_commit_id, is_head = \
                self._is_valid_head(commit_id, self.rhodecode_vcs_repo)

        self.forbid_non_head(is_head, f_path, commit_id=commit_id)
        self.check_branch_permission(_branch_name, commit_id=commit_id)

        c.default_message = (_('Added file via RhodeCode Enterprise'))
        c.f_path = f_path.lstrip('/')  # ensure not relative path

        return self._get_template_context(c)

    @LoginRequired()
    @HasRepoPermissionAnyDecorator('repository.write', 'repository.admin')
    @CSRFRequired()
    @view_config(
        route_name='repo_files_create_file', request_method='POST',
        renderer=None)
    def repo_files_create_file(self):
        _ = self.request.translate
        c = self.load_default_context()
        commit_id, f_path = self._get_commit_and_path()

        self._ensure_not_locked()

        c.commit = self._get_commit_or_redirect(commit_id, redirect_after=False)
        if c.commit is None:
            c.commit = EmptyCommit(alias=self.rhodecode_vcs_repo.alias)

        # calculate redirect URL
        if self.rhodecode_vcs_repo.is_empty():
            default_redirect_url = h.route_path(
                'repo_summary', repo_name=self.db_repo_name)
        else:
            default_redirect_url = h.route_path(
                'repo_commit', repo_name=self.db_repo_name, commit_id='tip')

        if self.rhodecode_vcs_repo.is_empty():
            # for empty repository we cannot check for current branch, we rely on
            # c.commit.branch instead
            _branch_name, _sha_commit_id, is_head = c.commit.branch, '', True
        else:
            _branch_name, _sha_commit_id, is_head = \
                self._is_valid_head(commit_id, self.rhodecode_vcs_repo)

        self.forbid_non_head(is_head, f_path, commit_id=commit_id)
        self.check_branch_permission(_branch_name, commit_id=commit_id)

        c.default_message = (_('Added file via RhodeCode Enterprise'))
        c.f_path = f_path

        r_post = self.request.POST
        message = r_post.get('message') or c.default_message
        filename = r_post.get('filename')
        unix_mode = 0
        content = convert_line_endings(r_post.get('content', ''), unix_mode)

        if not filename:
            # If there's no commit, redirect to repo summary
            if type(c.commit) is EmptyCommit:
                redirect_url = h.route_path(
                    'repo_summary', repo_name=self.db_repo_name)
            else:
                redirect_url = default_redirect_url
            h.flash(_('No filename specified'), category='warning')
            raise HTTPFound(redirect_url)

        root_path = f_path
        pure_path = self.create_pure_path(root_path, filename)
        node_path = safe_unicode(bytes(pure_path).lstrip('/'))

        author = self._rhodecode_db_user.full_contact
        nodes = {
            node_path: {
                'content': content
            }
        }

        try:

            commit = ScmModel().create_nodes(
                user=self._rhodecode_db_user.user_id,
                repo=self.db_repo,
                message=message,
                nodes=nodes,
                parent_commit=c.commit,
                author=author,
            )

            h.flash(_('Successfully committed new file `{}`').format(
                    h.escape(node_path)), category='success')

            default_redirect_url = h.route_path(
                'repo_commit', repo_name=self.db_repo_name, commit_id=commit.raw_id)

        except NonRelativePathError:
            log.exception('Non Relative path found')
            h.flash(_('The location specified must be a relative path and must not '
                      'contain .. in the path'), category='warning')
            raise HTTPFound(default_redirect_url)
        except (NodeError, NodeAlreadyExistsError) as e:
            h.flash(_(h.escape(e)), category='error')
        except Exception:
            log.exception('Error occurred during commit')
            h.flash(_('Error occurred during commit'), category='error')

        raise HTTPFound(default_redirect_url)

    @LoginRequired()
    @HasRepoPermissionAnyDecorator('repository.write', 'repository.admin')
    @CSRFRequired()
    @view_config(
        route_name='repo_files_upload_file', request_method='POST',
        renderer='json_ext')
    def repo_files_upload_file(self):
        _ = self.request.translate
        c = self.load_default_context()
        commit_id, f_path = self._get_commit_and_path()

        self._ensure_not_locked()

        c.commit = self._get_commit_or_redirect(commit_id, redirect_after=False)
        if c.commit is None:
            c.commit = EmptyCommit(alias=self.rhodecode_vcs_repo.alias)

        # calculate redirect URL
        if self.rhodecode_vcs_repo.is_empty():
            default_redirect_url = h.route_path(
                'repo_summary', repo_name=self.db_repo_name)
        else:
            default_redirect_url = h.route_path(
                'repo_commit', repo_name=self.db_repo_name, commit_id='tip')

        if self.rhodecode_vcs_repo.is_empty():
            # for empty repository we cannot check for current branch, we rely on
            # c.commit.branch instead
            _branch_name, _sha_commit_id, is_head = c.commit.branch, '', True
        else:
            _branch_name, _sha_commit_id, is_head = \
                self._is_valid_head(commit_id, self.rhodecode_vcs_repo)

        error = self.forbid_non_head(is_head, f_path, json_mode=True)
        if error:
            return {
                'error': error,
                'redirect_url': default_redirect_url
            }
        error = self.check_branch_permission(_branch_name, json_mode=True)
        if error:
            return {
                'error': error,
                'redirect_url': default_redirect_url
            }

        c.default_message = (_('Uploaded file via RhodeCode Enterprise'))
        c.f_path = f_path

        r_post = self.request.POST

        message = c.default_message
        user_message = r_post.getall('message')
        if isinstance(user_message, list) and user_message:
            # we take the first from duplicated results if it's not empty
            message = user_message[0] if user_message[0] else message

        nodes = {}

        for file_obj in r_post.getall('files_upload') or []:
            content = file_obj.file
            filename = file_obj.filename

            root_path = f_path
            pure_path = self.create_pure_path(root_path, filename)
            node_path = safe_unicode(bytes(pure_path).lstrip('/'))

            nodes[node_path] = {
                'content': content
            }

        if not nodes:
            error = 'missing files'
            return {
                'error': error,
                'redirect_url': default_redirect_url
            }

        author = self._rhodecode_db_user.full_contact

        try:
            commit = ScmModel().create_nodes(
                user=self._rhodecode_db_user.user_id,
                repo=self.db_repo,
                message=message,
                nodes=nodes,
                parent_commit=c.commit,
                author=author,
            )
            if len(nodes) == 1:
                flash_message = _('Successfully committed {} new files').format(len(nodes))
            else:
                flash_message = _('Successfully committed 1 new file')

            h.flash(flash_message, category='success')

            default_redirect_url = h.route_path(
                'repo_commit', repo_name=self.db_repo_name, commit_id=commit.raw_id)

        except NonRelativePathError:
            log.exception('Non Relative path found')
            error = _('The location specified must be a relative path and must not '
                      'contain .. in the path')
            h.flash(error, category='warning')

            return {
                'error': error,
                'redirect_url': default_redirect_url
            }
        except (NodeError, NodeAlreadyExistsError) as e:
            error = h.escape(e)
            h.flash(error, category='error')

            return {
                'error': error,
                'redirect_url': default_redirect_url
            }
        except Exception:
            log.exception('Error occurred during commit')
            error = _('Error occurred during commit')
            h.flash(error, category='error')
            return {
                'error': error,
                'redirect_url': default_redirect_url
            }

        return {
            'error': None,
            'redirect_url': default_redirect_url
        }
