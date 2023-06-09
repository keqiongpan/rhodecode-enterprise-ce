# -*- coding: utf-8 -*-

# Copyright (C) 2014-2020 RhodeCode GmbH
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
GIT repository module
"""

import logging
import os
import re

from zope.cachedescriptors.property import Lazy as LazyProperty

from rhodecode.lib.compat import OrderedDict
from rhodecode.lib.datelib import (
    utcdate_fromtimestamp, makedate, date_astimestamp)
from rhodecode.lib.utils import safe_unicode, safe_str
from rhodecode.lib.utils2 import CachedProperty
from rhodecode.lib.vcs import connection, path as vcspath
from rhodecode.lib.vcs.backends.base import (
    BaseRepository, CollectionGenerator, Config, MergeResponse,
    MergeFailureReason, Reference)
from rhodecode.lib.vcs.backends.git.commit import GitCommit
from rhodecode.lib.vcs.backends.git.diff import GitDiff
from rhodecode.lib.vcs.backends.git.inmemory import GitInMemoryCommit
from rhodecode.lib.vcs.exceptions import (
    CommitDoesNotExistError, EmptyRepositoryError,
    RepositoryError, TagAlreadyExistError, TagDoesNotExistError, VCSError, UnresolvedFilesInRepo)


SHA_PATTERN = re.compile(r'^[[0-9a-fA-F]{12}|[0-9a-fA-F]{40}]$')

log = logging.getLogger(__name__)


class GitRepository(BaseRepository):
    """
    Git repository backend.
    """
    DEFAULT_BRANCH_NAME = os.environ.get('GIT_DEFAULT_BRANCH_NAME') or 'master'

    contact = BaseRepository.DEFAULT_CONTACT

    def __init__(self, repo_path, config=None, create=False, src_url=None,
                 do_workspace_checkout=False, with_wire=None, bare=False):

        self.path = safe_str(os.path.abspath(repo_path))
        self.config = config if config else self.get_default_config()
        self.with_wire = with_wire or {"cache": False}  # default should not use cache

        self._init_repo(create, src_url, do_workspace_checkout, bare)

        # caches
        self._commit_ids = {}

    @LazyProperty
    def _remote(self):
        repo_id = self.path
        return connection.Git(self.path, repo_id, self.config, with_wire=self.with_wire)

    @LazyProperty
    def bare(self):
        return self._remote.bare()

    @LazyProperty
    def head(self):
        return self._remote.head()

    @CachedProperty
    def commit_ids(self):
        """
        Returns list of commit ids, in ascending order.  Being lazy
        attribute allows external tools to inject commit ids from cache.
        """
        commit_ids = self._get_all_commit_ids()
        self._rebuild_cache(commit_ids)
        return commit_ids

    def _rebuild_cache(self, commit_ids):
        self._commit_ids = dict((commit_id, index)
                                for index, commit_id in enumerate(commit_ids))

    def run_git_command(self, cmd, **opts):
        """
        Runs given ``cmd`` as git command and returns tuple
        (stdout, stderr).

        :param cmd: git command to be executed
        :param opts: env options to pass into Subprocess command
        """
        if not isinstance(cmd, list):
            raise ValueError('cmd must be a list, got %s instead' % type(cmd))

        skip_stderr_log = opts.pop('skip_stderr_log', False)
        out, err = self._remote.run_git_command(cmd, **opts)
        if err and not skip_stderr_log:
            log.debug('Stderr output of git command "%s":\n%s', cmd, err)
        return out, err

    @staticmethod
    def check_url(url, config):
        """
        Function will check given url and try to verify if it's a valid
        link. Sometimes it may happened that git will issue basic
        auth request that can cause whole API to hang when used from python
        or other external calls.

        On failures it'll raise urllib2.HTTPError, exception is also thrown
        when the return code is non 200
        """
        # check first if it's not an url
        if os.path.isdir(url) or url.startswith('file:'):
            return True

        if '+' in url.split('://', 1)[0]:
            url = url.split('+', 1)[1]

        # Request the _remote to verify the url
        return connection.Git.check_url(url, config.serialize())

    @staticmethod
    def is_valid_repository(path):
        if os.path.isdir(os.path.join(path, '.git')):
            return True
        # check case of bare repository
        try:
            GitRepository(path)
            return True
        except VCSError:
            pass
        return False

    def _init_repo(self, create, src_url=None, do_workspace_checkout=False,
                   bare=False):
        if create and os.path.exists(self.path):
            raise RepositoryError(
                "Cannot create repository at %s, location already exist"
                % self.path)

        if bare and do_workspace_checkout:
            raise RepositoryError("Cannot update a bare repository")
        try:

            if src_url:
                # check URL before any actions
                GitRepository.check_url(src_url, self.config)

            if create:
                os.makedirs(self.path, mode=0o755)

                if bare:
                    self._remote.init_bare()
                else:
                    self._remote.init()

                if src_url and bare:
                    # bare repository only allows a fetch and checkout is not allowed
                    self.fetch(src_url, commit_ids=None)
                elif src_url:
                    self.pull(src_url, commit_ids=None,
                              update_after=do_workspace_checkout)

            else:
                if not self._remote.assert_correct_path():
                    raise RepositoryError(
                        'Path "%s" does not contain a Git repository' %
                        (self.path,))

        # TODO: johbo: check if we have to translate the OSError here
        except OSError as err:
            raise RepositoryError(err)

    def _get_all_commit_ids(self):
        return self._remote.get_all_commit_ids()

    def _get_commit_ids(self, filters=None):
        # we must check if this repo is not empty, since later command
        # fails if it is. And it's cheaper to ask than throw the subprocess
        # errors

        head = self._remote.head(show_exc=False)

        if not head:
            return []

        rev_filter = ['--branches', '--tags']
        extra_filter = []

        if filters:
            if filters.get('since'):
                extra_filter.append('--since=%s' % (filters['since']))
            if filters.get('until'):
                extra_filter.append('--until=%s' % (filters['until']))
            if filters.get('branch_name'):
                rev_filter = []
                extra_filter.append(filters['branch_name'])
        rev_filter.extend(extra_filter)

            # if filters.get('start') or filters.get('end'):
            #     # skip is offset, max-count is limit
            #     if filters.get('start'):
            #         extra_filter += ' --skip=%s' % filters['start']
            #     if filters.get('end'):
            #         extra_filter += ' --max-count=%s' % (filters['end'] - (filters['start'] or 0))

        cmd = ['rev-list', '--reverse', '--date-order'] + rev_filter
        try:
            output, __ = self.run_git_command(cmd)
        except RepositoryError:
            # Can be raised for empty repositories
            return []
        return output.splitlines()

    def _lookup_commit(self, commit_id_or_idx, translate_tag=True, maybe_unreachable=False, reference_obj=None):

        def is_null(value):
            return len(value) == commit_id_or_idx.count('0')

        if commit_id_or_idx in (None, '', 'tip', 'HEAD', 'head', -1):
            return self.commit_ids[-1]

        commit_missing_err = "Commit {} does not exist for `{}`".format(
            *map(safe_str, [commit_id_or_idx, self.name]))

        is_bstr = isinstance(commit_id_or_idx, (str, unicode))
        is_branch = reference_obj and reference_obj.branch

        lookup_ok = False
        if is_bstr:
            # Need to call remote to translate id for tagging scenarios,
            # or branch that are numeric
            try:
                remote_data = self._remote.get_object(commit_id_or_idx,
                                                      maybe_unreachable=maybe_unreachable)
                commit_id_or_idx = remote_data["commit_id"]
                lookup_ok = True
            except (CommitDoesNotExistError,):
                lookup_ok = False

        if lookup_ok is False:
            is_numeric_idx = \
                (is_bstr and commit_id_or_idx.isdigit() and len(commit_id_or_idx) < 12) \
                or isinstance(commit_id_or_idx, int)
            if not is_branch and (is_numeric_idx or is_null(commit_id_or_idx)):
                try:
                    commit_id_or_idx = self.commit_ids[int(commit_id_or_idx)]
                    lookup_ok = True
                except Exception:
                    raise CommitDoesNotExistError(commit_missing_err)

        # we failed regular lookup, and by integer number lookup
        if lookup_ok is False:
            raise CommitDoesNotExistError(commit_missing_err)

        # Ensure we return full id
        if not SHA_PATTERN.match(str(commit_id_or_idx)):
            raise CommitDoesNotExistError(
                "Given commit id %s not recognized" % commit_id_or_idx)
        return commit_id_or_idx

    def get_hook_location(self):
        """
        returns absolute path to location where hooks are stored
        """
        loc = os.path.join(self.path, 'hooks')
        if not self.bare:
            loc = os.path.join(self.path, '.git', 'hooks')
        return loc

    @LazyProperty
    def last_change(self):
        """
        Returns last change made on this repository as
        `datetime.datetime` object.
        """
        try:
            return self.get_commit().date
        except RepositoryError:
            tzoffset = makedate()[1]
            return utcdate_fromtimestamp(self._get_fs_mtime(), tzoffset)

    def _get_fs_mtime(self):
        idx_loc = '' if self.bare else '.git'
        # fallback to filesystem
        in_path = os.path.join(self.path, idx_loc, "index")
        he_path = os.path.join(self.path, idx_loc, "HEAD")
        if os.path.exists(in_path):
            return os.stat(in_path).st_mtime
        else:
            return os.stat(he_path).st_mtime

    @LazyProperty
    def description(self):
        description = self._remote.get_description()
        return safe_unicode(description or self.DEFAULT_DESCRIPTION)

    def _get_refs_entries(self, prefix='', reverse=False, strip_prefix=True):
        if self.is_empty():
            return OrderedDict()

        result = []
        for ref, sha in self._refs.iteritems():
            if ref.startswith(prefix):
                ref_name = ref
                if strip_prefix:
                    ref_name = ref[len(prefix):]
                result.append((safe_unicode(ref_name), sha))

        def get_name(entry):
            return entry[0]

        return OrderedDict(sorted(result, key=get_name, reverse=reverse))

    def _get_branches(self):
        return self._get_refs_entries(prefix='refs/heads/', strip_prefix=True)

    @CachedProperty
    def branches(self):
        return self._get_branches()

    @CachedProperty
    def branches_closed(self):
        return {}

    @CachedProperty
    def bookmarks(self):
        return {}

    @CachedProperty
    def branches_all(self):
        all_branches = {}
        all_branches.update(self.branches)
        all_branches.update(self.branches_closed)
        return all_branches

    @CachedProperty
    def tags(self):
        return self._get_tags()

    def _get_tags(self):
        return self._get_refs_entries(prefix='refs/tags/', strip_prefix=True, reverse=True)

    def tag(self, name, user, commit_id=None, message=None, date=None,
            **kwargs):
        # TODO: fix this method to apply annotated tags correct with message
        """
        Creates and returns a tag for the given ``commit_id``.

        :param name: name for new tag
        :param user: full username, i.e.: "Joe Doe <joe.doe@example.com>"
        :param commit_id: commit id for which new tag would be created
        :param message: message of the tag's commit
        :param date: date of tag's commit

        :raises TagAlreadyExistError: if tag with same name already exists
        """
        if name in self.tags:
            raise TagAlreadyExistError("Tag %s already exists" % name)
        commit = self.get_commit(commit_id=commit_id)
        message = message or "Added tag %s for commit %s" % (name, commit.raw_id)

        self._remote.set_refs('refs/tags/%s' % name, commit.raw_id)

        self._invalidate_prop_cache('tags')
        self._invalidate_prop_cache('_refs')

        return commit

    def remove_tag(self, name, user, message=None, date=None):
        """
        Removes tag with the given ``name``.

        :param name: name of the tag to be removed
        :param user: full username, i.e.: "Joe Doe <joe.doe@example.com>"
        :param message: message of the tag's removal commit
        :param date: date of tag's removal commit

        :raises TagDoesNotExistError: if tag with given name does not exists
        """
        if name not in self.tags:
            raise TagDoesNotExistError("Tag %s does not exist" % name)

        self._remote.tag_remove(name)
        self._invalidate_prop_cache('tags')
        self._invalidate_prop_cache('_refs')

    def _get_refs(self):
        return self._remote.get_refs()

    @CachedProperty
    def _refs(self):
        return self._get_refs()

    @property
    def _ref_tree(self):
        node = tree = {}
        for ref, sha in self._refs.iteritems():
            path = ref.split('/')
            for bit in path[:-1]:
                node = node.setdefault(bit, {})
            node[path[-1]] = sha
            node = tree
        return tree

    def get_remote_ref(self, ref_name):
        ref_key = 'refs/remotes/origin/{}'.format(safe_str(ref_name))
        try:
            return self._refs[ref_key]
        except Exception:
            return

    def get_commit(self, commit_id=None, commit_idx=None, pre_load=None,
                   translate_tag=True, maybe_unreachable=False, reference_obj=None):
        """
        Returns `GitCommit` object representing commit from git repository
        at the given `commit_id` or head (most recent commit) if None given.
        """

        if self.is_empty():
            raise EmptyRepositoryError("There are no commits yet")

        if commit_id is not None:
            self._validate_commit_id(commit_id)
            try:
                # we have cached idx, use it without contacting the remote
                idx = self._commit_ids[commit_id]
                return GitCommit(self, commit_id, idx, pre_load=pre_load)
            except KeyError:
                pass

        elif commit_idx is not None:
            self._validate_commit_idx(commit_idx)
            try:
                _commit_id = self.commit_ids[commit_idx]
                if commit_idx < 0:
                    commit_idx = self.commit_ids.index(_commit_id)
                return GitCommit(self, _commit_id, commit_idx, pre_load=pre_load)
            except IndexError:
                commit_id = commit_idx
        else:
            commit_id = "tip"

        if translate_tag:
            commit_id = self._lookup_commit(
                commit_id, maybe_unreachable=maybe_unreachable,
                reference_obj=reference_obj)

        try:
            idx = self._commit_ids[commit_id]
        except KeyError:
            idx = -1

        return GitCommit(self, commit_id, idx, pre_load=pre_load)

    def get_commits(
            self, start_id=None, end_id=None, start_date=None, end_date=None,
            branch_name=None, show_hidden=False, pre_load=None, translate_tags=True):
        """
        Returns generator of `GitCommit` objects from start to end (both
        are inclusive), in ascending date order.

        :param start_id: None, str(commit_id)
        :param end_id: None, str(commit_id)
        :param start_date: if specified, commits with commit date less than
          ``start_date`` would be filtered out from returned set
        :param end_date: if specified, commits with commit date greater than
          ``end_date`` would be filtered out from returned set
        :param branch_name: if specified, commits not reachable from given
          branch would be filtered out from returned set
        :param show_hidden: Show hidden commits such as obsolete or hidden from
            Mercurial evolve
        :raise BranchDoesNotExistError: If given `branch_name` does not
            exist.
        :raise CommitDoesNotExistError: If commits for given `start` or
          `end` could not be found.

        """
        if self.is_empty():
            raise EmptyRepositoryError("There are no commits yet")

        self._validate_branch_name(branch_name)

        if start_id is not None:
            self._validate_commit_id(start_id)
        if end_id is not None:
            self._validate_commit_id(end_id)

        start_raw_id = self._lookup_commit(start_id)
        start_pos = self._commit_ids[start_raw_id] if start_id else None
        end_raw_id = self._lookup_commit(end_id)
        end_pos = max(0, self._commit_ids[end_raw_id]) if end_id else None

        if None not in [start_id, end_id] and start_pos > end_pos:
            raise RepositoryError(
                "Start commit '%s' cannot be after end commit '%s'" %
                (start_id, end_id))

        if end_pos is not None:
            end_pos += 1

        filter_ = []
        if branch_name:
            filter_.append({'branch_name': branch_name})
        if start_date and not end_date:
            filter_.append({'since': start_date})
        if end_date and not start_date:
            filter_.append({'until': end_date})
        if start_date and end_date:
            filter_.append({'since': start_date})
            filter_.append({'until': end_date})

        # if start_pos or end_pos:
        #     filter_.append({'start': start_pos})
        #     filter_.append({'end': end_pos})

        if filter_:
            revfilters = {
                'branch_name': branch_name,
                'since': start_date.strftime('%m/%d/%y %H:%M:%S') if start_date else None,
                'until': end_date.strftime('%m/%d/%y %H:%M:%S') if end_date else None,
                'start': start_pos,
                'end': end_pos,
            }
            commit_ids = self._get_commit_ids(filters=revfilters)

        else:
            commit_ids = self.commit_ids

        if start_pos or end_pos:
            commit_ids = commit_ids[start_pos: end_pos]

        return CollectionGenerator(self, commit_ids, pre_load=pre_load,
                                   translate_tag=translate_tags)

    def get_diff(
            self, commit1, commit2, path='', ignore_whitespace=False,
            context=3, path1=None):
        """
        Returns (git like) *diff*, as plain text. Shows changes introduced by
        ``commit2`` since ``commit1``.

        :param commit1: Entry point from which diff is shown. Can be
          ``self.EMPTY_COMMIT`` - in this case, patch showing all
          the changes since empty state of the repository until ``commit2``
        :param commit2: Until which commits changes should be shown.
        :param ignore_whitespace: If set to ``True``, would not show whitespace
          changes. Defaults to ``False``.
        :param context: How many lines before/after changed lines should be
          shown. Defaults to ``3``.
        """
        self._validate_diff_commits(commit1, commit2)
        if path1 is not None and path1 != path:
            raise ValueError("Diff of two different paths not supported.")

        if path:
            file_filter = path
        else:
            file_filter = None

        diff = self._remote.diff(
            commit1.raw_id, commit2.raw_id, file_filter=file_filter,
            opt_ignorews=ignore_whitespace,
            context=context)
        return GitDiff(diff)

    def strip(self, commit_id, branch_name):
        commit = self.get_commit(commit_id=commit_id)
        if commit.merge:
            raise Exception('Cannot reset to merge commit')

        # parent is going to be the new head now
        commit = commit.parents[0]
        self._remote.set_refs('refs/heads/%s' % branch_name, commit.raw_id)

        # clear cached properties
        self._invalidate_prop_cache('commit_ids')
        self._invalidate_prop_cache('_refs')
        self._invalidate_prop_cache('branches')

        return len(self.commit_ids)

    def get_common_ancestor(self, commit_id1, commit_id2, repo2):
        log.debug('Calculating common ancestor between %sc1:%s and %sc2:%s',
                  self, commit_id1, repo2, commit_id2)

        if commit_id1 == commit_id2:
            return commit_id1

        if self != repo2:
            commits = self._remote.get_missing_revs(
                commit_id1, commit_id2, repo2.path)
            if commits:
                commit = repo2.get_commit(commits[-1])
                if commit.parents:
                    ancestor_id = commit.parents[0].raw_id
                else:
                    ancestor_id = None
            else:
                # no commits from other repo, ancestor_id is the commit_id2
                ancestor_id = commit_id2
        else:
            output, __ = self.run_git_command(
                ['merge-base', commit_id1, commit_id2])
            ancestor_id = self.COMMIT_ID_PAT.findall(output)[0]

        log.debug('Found common ancestor with sha: %s', ancestor_id)

        return ancestor_id

    def compare(self, commit_id1, commit_id2, repo2, merge, pre_load=None):
        repo1 = self
        ancestor_id = None

        if commit_id1 == commit_id2:
            commits = []
        elif repo1 != repo2:
            missing_ids = self._remote.get_missing_revs(commit_id1, commit_id2,
                                                        repo2.path)
            commits = [
                repo2.get_commit(commit_id=commit_id, pre_load=pre_load)
                for commit_id in reversed(missing_ids)]
        else:
            output, __ = repo1.run_git_command(
                ['log', '--reverse', '--pretty=format: %H', '-s',
                 '%s..%s' % (commit_id1, commit_id2)])
            commits = [
                repo1.get_commit(commit_id=commit_id, pre_load=pre_load)
                for commit_id in self.COMMIT_ID_PAT.findall(output)]

        return commits

    @LazyProperty
    def in_memory_commit(self):
        """
        Returns ``GitInMemoryCommit`` object for this repository.
        """
        return GitInMemoryCommit(self)

    def pull(self, url, commit_ids=None, update_after=False):
        """
        Pull changes from external location. Pull is different in GIT
        that fetch since it's doing a checkout

        :param commit_ids: Optional. Can be set to a list of commit ids
           which shall be pulled from the other repository.
        """
        refs = None
        if commit_ids is not None:
            remote_refs = self._remote.get_remote_refs(url)
            refs = [ref for ref in remote_refs if remote_refs[ref] in commit_ids]
        self._remote.pull(url, refs=refs, update_after=update_after)
        self._remote.invalidate_vcs_cache()

    def fetch(self, url, commit_ids=None):
        """
        Fetch all git objects from external location.
        """
        self._remote.sync_fetch(url, refs=commit_ids)
        self._remote.invalidate_vcs_cache()

    def push(self, url):
        refs = None
        self._remote.sync_push(url, refs=refs)

    def set_refs(self, ref_name, commit_id):
        self._remote.set_refs(ref_name, commit_id)
        self._invalidate_prop_cache('_refs')

    def remove_ref(self, ref_name):
        self._remote.remove_ref(ref_name)
        self._invalidate_prop_cache('_refs')

    def run_gc(self, prune=True):
        cmd = ['gc', '--aggressive']
        if prune:
            cmd += ['--prune=now']
        _stdout, stderr = self.run_git_command(cmd, fail_on_stderr=False)
        return stderr

    def _update_server_info(self):
        """
        runs gits update-server-info command in this repo instance
        """
        self._remote.update_server_info()

    def _current_branch(self):
        """
        Return the name of the current branch.

        It only works for non bare repositories (i.e. repositories with a
        working copy)
        """
        if self.bare:
            raise RepositoryError('Bare git repos do not have active branches')

        if self.is_empty():
            return None

        stdout, _ = self.run_git_command(['rev-parse', '--abbrev-ref', 'HEAD'])
        return stdout.strip()

    def _checkout(self, branch_name, create=False, force=False):
        """
        Checkout a branch in the working directory.

        It tries to create the branch if create is True, failing if the branch
        already exists.

        It only works for non bare repositories (i.e. repositories with a
        working copy)
        """
        if self.bare:
            raise RepositoryError('Cannot checkout branches in a bare git repo')

        cmd = ['checkout']
        if force:
            cmd.append('-f')
        if create:
            cmd.append('-b')
        cmd.append(branch_name)
        self.run_git_command(cmd, fail_on_stderr=False)

    def _create_branch(self, branch_name, commit_id):
        """
        creates a branch in a GIT repo
        """
        self._remote.create_branch(branch_name, commit_id)

    def _identify(self):
        """
        Return the current state of the working directory.
        """
        if self.bare:
            raise RepositoryError('Bare git repos do not have active branches')

        if self.is_empty():
            return None

        stdout, _ = self.run_git_command(['rev-parse', 'HEAD'])
        return stdout.strip()

    def _local_clone(self, clone_path, branch_name, source_branch=None):
        """
        Create a local clone of the current repo.
        """
        # N.B.(skreft): the --branch option is required as otherwise the shallow
        # clone will only fetch the active branch.
        cmd = ['clone', '--branch', branch_name,
               self.path, os.path.abspath(clone_path)]

        self.run_git_command(cmd, fail_on_stderr=False)

        # if we get the different source branch, make sure we also fetch it for
        # merge conditions
        if source_branch and source_branch != branch_name:
            # check if the ref exists.
            shadow_repo = GitRepository(os.path.abspath(clone_path))
            if shadow_repo.get_remote_ref(source_branch):
                cmd = ['fetch', self.path, source_branch]
                self.run_git_command(cmd, fail_on_stderr=False)

    def _local_fetch(self, repository_path, branch_name, use_origin=False):
        """
        Fetch a branch from a local repository.
        """
        repository_path = os.path.abspath(repository_path)
        if repository_path == self.path:
            raise ValueError('Cannot fetch from the same repository')

        if use_origin:
            branch_name = '+{branch}:refs/heads/{branch}'.format(
                branch=branch_name)

        cmd = ['fetch', '--no-tags', '--update-head-ok',
               repository_path, branch_name]
        self.run_git_command(cmd, fail_on_stderr=False)

    def _local_reset(self, branch_name):
        branch_name = '{}'.format(branch_name)
        cmd = ['reset', '--hard', branch_name, '--']
        self.run_git_command(cmd, fail_on_stderr=False)

    def _last_fetch_heads(self):
        """
        Return the last fetched heads that need merging.

        The algorithm is defined at
        https://github.com/git/git/blob/v2.1.3/git-pull.sh#L283
        """
        if not self.bare:
            fetch_heads_path = os.path.join(self.path, '.git', 'FETCH_HEAD')
        else:
            fetch_heads_path = os.path.join(self.path, 'FETCH_HEAD')

        heads = []
        with open(fetch_heads_path) as f:
            for line in f:
                if '    not-for-merge   ' in line:
                    continue
                line = re.sub('\t.*', '', line, flags=re.DOTALL)
                heads.append(line)

        return heads

    def get_shadow_instance(self, shadow_repository_path, enable_hooks=False, cache=False):
        return GitRepository(shadow_repository_path, with_wire={"cache": cache})

    def _local_pull(self, repository_path, branch_name, ff_only=True):
        """
        Pull a branch from a local repository.
        """
        if self.bare:
            raise RepositoryError('Cannot pull into a bare git repository')
        # N.B.(skreft): The --ff-only option is to make sure this is a
        # fast-forward (i.e., we are only pulling new changes and there are no
        # conflicts with our current branch)
        # Additionally, that option needs to go before --no-tags, otherwise git
        # pull complains about it being an unknown flag.
        cmd = ['pull']
        if ff_only:
            cmd.append('--ff-only')
        cmd.extend(['--no-tags', repository_path, branch_name])
        self.run_git_command(cmd, fail_on_stderr=False)

    def _local_merge(self, merge_message, user_name, user_email, heads):
        """
        Merge the given head into the checked out branch.

        It will force a merge commit.

        Currently it raises an error if the repo is empty, as it is not possible
        to create a merge commit in an empty repo.

        :param merge_message: The message to use for the merge commit.
        :param heads: the heads to merge.
        """
        if self.bare:
            raise RepositoryError('Cannot merge into a bare git repository')

        if not heads:
            return

        if self.is_empty():
            # TODO(skreft): do something more robust in this case.
            raise RepositoryError('Do not know how to merge into empty repositories yet')
        unresolved = None

        # N.B.(skreft): the --no-ff option is used to enforce the creation of a
        # commit message. We also specify the user who is doing the merge.
        cmd = ['-c', 'user.name="%s"' % safe_str(user_name),
               '-c', 'user.email=%s' % safe_str(user_email),
               'merge', '--no-ff', '-m', safe_str(merge_message)]

        merge_cmd = cmd + heads

        try:
            self.run_git_command(merge_cmd, fail_on_stderr=False)
        except RepositoryError:
            files = self.run_git_command(['diff', '--name-only', '--diff-filter', 'U'],
                                         fail_on_stderr=False)[0].splitlines()
            # NOTE(marcink): we add U notation for consistent with HG backend output
            unresolved = ['U {}'.format(f) for f in files]

            # Cleanup any merge leftovers
            self._remote.invalidate_vcs_cache()
            self.run_git_command(['merge', '--abort'], fail_on_stderr=False)

            if unresolved:
                raise UnresolvedFilesInRepo(unresolved)
            else:
                raise

    def _local_push(
            self, source_branch, repository_path, target_branch,
            enable_hooks=False, rc_scm_data=None):
        """
        Push the source_branch to the given repository and target_branch.

        Currently it if the target_branch is not master and the target repo is
        empty, the push will work, but then GitRepository won't be able to find
        the pushed branch or the commits. As the HEAD will be corrupted (i.e.,
        pointing to master, which does not exist).

        It does not run the hooks in the target repo.
        """
        # TODO(skreft): deal with the case in which the target repo is empty,
        # and the target_branch is not master.
        target_repo = GitRepository(repository_path)
        if (not target_repo.bare and
                target_repo._current_branch() == target_branch):
            # Git prevents pushing to the checked out branch, so simulate it by
            # pulling into the target repository.
            target_repo._local_pull(self.path, source_branch)
        else:
            cmd = ['push', os.path.abspath(repository_path),
                   '%s:%s' % (source_branch, target_branch)]
            gitenv = {}
            if rc_scm_data:
                gitenv.update({'RC_SCM_DATA': rc_scm_data})

            if not enable_hooks:
                gitenv['RC_SKIP_HOOKS'] = '1'
            self.run_git_command(cmd, fail_on_stderr=False, extra_env=gitenv)

    def _get_new_pr_branch(self, source_branch, target_branch):
        prefix = 'pr_%s-%s_' % (source_branch, target_branch)
        pr_branches = []
        for branch in self.branches:
            if branch.startswith(prefix):
                pr_branches.append(int(branch[len(prefix):]))

        if not pr_branches:
            branch_id = 0
        else:
            branch_id = max(pr_branches) + 1

        return '%s%d' % (prefix, branch_id)

    def _maybe_prepare_merge_workspace(
            self, repo_id, workspace_id, target_ref, source_ref):
        shadow_repository_path = self._get_shadow_repository_path(
            self.path, repo_id, workspace_id)
        if not os.path.exists(shadow_repository_path):
            self._local_clone(
                shadow_repository_path, target_ref.name, source_ref.name)
            log.debug('Prepared %s shadow repository in %s',
                      self.alias, shadow_repository_path)

        return shadow_repository_path

    def _merge_repo(self, repo_id, workspace_id, target_ref,
                    source_repo, source_ref, merge_message,
                    merger_name, merger_email, dry_run=False,
                    use_rebase=False, close_branch=False):

        log.debug('Executing merge_repo with %s strategy, dry_run mode:%s',
                  'rebase' if use_rebase else 'merge', dry_run)
        if target_ref.commit_id != self.branches[target_ref.name]:
            log.warning('Target ref %s commit mismatch %s vs %s', target_ref,
                        target_ref.commit_id, self.branches[target_ref.name])
            return MergeResponse(
                False, False, None, MergeFailureReason.TARGET_IS_NOT_HEAD,
                metadata={'target_ref': target_ref})

        shadow_repository_path = self._maybe_prepare_merge_workspace(
            repo_id, workspace_id, target_ref, source_ref)
        shadow_repo = self.get_shadow_instance(shadow_repository_path)

        # checkout source, if it's different. Otherwise we could not
        # fetch proper commits for merge testing
        if source_ref.name != target_ref.name:
            if shadow_repo.get_remote_ref(source_ref.name):
                shadow_repo._checkout(source_ref.name, force=True)

        # checkout target, and fetch changes
        shadow_repo._checkout(target_ref.name, force=True)

        # fetch/reset pull the target, in case it is changed
        # this handles even force changes
        shadow_repo._local_fetch(self.path, target_ref.name, use_origin=True)
        shadow_repo._local_reset(target_ref.name)

        # Need to reload repo to invalidate the cache, or otherwise we cannot
        # retrieve the last target commit.
        shadow_repo = self.get_shadow_instance(shadow_repository_path)
        if target_ref.commit_id != shadow_repo.branches[target_ref.name]:
            log.warning('Shadow Target ref %s commit mismatch %s vs %s',
                        target_ref, target_ref.commit_id,
                        shadow_repo.branches[target_ref.name])
            return MergeResponse(
                False, False, None, MergeFailureReason.TARGET_IS_NOT_HEAD,
                metadata={'target_ref': target_ref})

        # calculate new branch
        pr_branch = shadow_repo._get_new_pr_branch(
            source_ref.name, target_ref.name)
        log.debug('using pull-request merge branch: `%s`', pr_branch)
        # checkout to temp branch, and fetch changes
        shadow_repo._checkout(pr_branch, create=True)
        try:
            shadow_repo._local_fetch(source_repo.path, source_ref.name)
        except RepositoryError:
            log.exception('Failure when doing local fetch on '
                          'shadow repo: %s', shadow_repo)
            return MergeResponse(
                False, False, None, MergeFailureReason.MISSING_SOURCE_REF,
                metadata={'source_ref': source_ref})

        merge_ref = None
        merge_failure_reason = MergeFailureReason.NONE
        metadata = {}
        try:
            shadow_repo._local_merge(merge_message, merger_name, merger_email,
                                     [source_ref.commit_id])
            merge_possible = True

            # Need to invalidate the cache, or otherwise we
            # cannot retrieve the merge commit.
            shadow_repo = shadow_repo.get_shadow_instance(shadow_repository_path)
            merge_commit_id = shadow_repo.branches[pr_branch]

            # Set a reference pointing to the merge commit. This reference may
            # be used to easily identify the last successful merge commit in
            # the shadow repository.
            shadow_repo.set_refs('refs/heads/pr-merge', merge_commit_id)
            merge_ref = Reference('branch', 'pr-merge', merge_commit_id)
        except RepositoryError as e:
            log.exception('Failure when doing local merge on git shadow repo')
            if isinstance(e, UnresolvedFilesInRepo):
                metadata['unresolved_files'] = '\n* conflict: ' + ('\n * conflict: '.join(e.args[0]))

            merge_possible = False
            merge_failure_reason = MergeFailureReason.MERGE_FAILED

        if merge_possible and not dry_run:
            try:
                shadow_repo._local_push(
                    pr_branch, self.path, target_ref.name, enable_hooks=True,
                    rc_scm_data=self.config.get('rhodecode', 'RC_SCM_DATA'))
                merge_succeeded = True
            except RepositoryError:
                log.exception(
                    'Failure when doing local push from the shadow '
                    'repository to the target repository at %s.', self.path)
                merge_succeeded = False
                merge_failure_reason = MergeFailureReason.PUSH_FAILED
                metadata['target'] = 'git shadow repo'
                metadata['merge_commit'] = pr_branch
        else:
            merge_succeeded = False

        return MergeResponse(
            merge_possible, merge_succeeded, merge_ref, merge_failure_reason,
            metadata=metadata)
