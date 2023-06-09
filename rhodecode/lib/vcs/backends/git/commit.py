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
GIT commit module
"""

import re
import stat
from itertools import chain
from StringIO import StringIO

from zope.cachedescriptors.property import Lazy as LazyProperty

from rhodecode.lib.datelib import utcdate_fromtimestamp
from rhodecode.lib.utils import safe_unicode, safe_str
from rhodecode.lib.utils2 import safe_int
from rhodecode.lib.vcs.conf import settings
from rhodecode.lib.vcs.backends import base
from rhodecode.lib.vcs.exceptions import CommitError, NodeDoesNotExistError
from rhodecode.lib.vcs.nodes import (
    FileNode, DirNode, NodeKind, RootNode, SubModuleNode,
    ChangedFileNodesGenerator, AddedFileNodesGenerator,
    RemovedFileNodesGenerator, LargeFileNode)
from rhodecode.lib.vcs.compat import configparser


class GitCommit(base.BaseCommit):
    """
    Represents state of the repository at single commit id.
    """

    _filter_pre_load = [
        # done through a more complex tree walk on parents
        "affected_files",
        # done through subprocess not remote call
        "children",
        # done through a more complex tree walk on parents
        "status",
        # mercurial specific property not supported here
        "_file_paths",
        # mercurial specific property not supported here
        'obsolete',
        # mercurial specific property not supported here
        'phase',
        # mercurial specific property not supported here
        'hidden'
    ]

    def __init__(self, repository, raw_id, idx, pre_load=None):
        self.repository = repository
        self._remote = repository._remote
        # TODO: johbo: Tweak of raw_id should not be necessary
        self.raw_id = safe_str(raw_id)
        self.idx = idx

        self._set_bulk_properties(pre_load)

        # caches
        self._stat_modes = {}  # stat info for paths
        self._paths = {}  # path processed with parse_tree
        self.nodes = {}
        self._submodules = None

    def _set_bulk_properties(self, pre_load):

        if not pre_load:
            return
        pre_load = [entry for entry in pre_load
                    if entry not in self._filter_pre_load]
        if not pre_load:
            return

        result = self._remote.bulk_request(self.raw_id, pre_load)
        for attr, value in result.items():
            if attr in ["author", "message"]:
                if value:
                    value = safe_unicode(value)
            elif attr == "date":
                value = utcdate_fromtimestamp(*value)
            elif attr == "parents":
                value = self._make_commits(value)
            elif attr == "branch":
                value = self._set_branch(value)
            self.__dict__[attr] = value

    @LazyProperty
    def _commit(self):
        return self._remote[self.raw_id]

    @LazyProperty
    def _tree_id(self):
        return self._remote[self._commit['tree']]['id']

    @LazyProperty
    def id(self):
        return self.raw_id

    @LazyProperty
    def short_id(self):
        return self.raw_id[:12]

    @LazyProperty
    def message(self):
        return safe_unicode(self._remote.message(self.id))

    @LazyProperty
    def committer(self):
        return safe_unicode(self._remote.author(self.id))

    @LazyProperty
    def author(self):
        return safe_unicode(self._remote.author(self.id))

    @LazyProperty
    def date(self):
        unix_ts, tz = self._remote.date(self.raw_id)
        return utcdate_fromtimestamp(unix_ts, tz)

    @LazyProperty
    def status(self):
        """
        Returns modified, added, removed, deleted files for current commit
        """
        return self.changed, self.added, self.removed

    @LazyProperty
    def tags(self):
        tags = [safe_unicode(name) for name,
                commit_id in self.repository.tags.iteritems()
                if commit_id == self.raw_id]
        return tags

    @LazyProperty
    def commit_branches(self):
        branches = []
        for name, commit_id in self.repository.branches.iteritems():
            if commit_id == self.raw_id:
                branches.append(name)
        return branches

    def _set_branch(self, branches):
        if branches:
            # actually commit can have multiple branches in git
            return safe_unicode(branches[0])

    @LazyProperty
    def branch(self):
        branches = self._remote.branch(self.raw_id)
        return self._set_branch(branches)

    def _get_tree_id_for_path(self, path):
        path = safe_str(path)
        if path in self._paths:
            return self._paths[path]

        tree_id = self._tree_id

        path = path.strip('/')
        if path == '':
            data = [tree_id, "tree"]
            self._paths[''] = data
            return data

        tree_id, tree_type, tree_mode = \
            self._remote.tree_and_type_for_path(self.raw_id, path)
        if tree_id is None:
            raise self.no_node_at_path(path)

        self._paths[path] = [tree_id, tree_type]
        self._stat_modes[path] = tree_mode

        if path not in self._paths:
            raise self.no_node_at_path(path)

        return self._paths[path]

    def _get_kind(self, path):
        tree_id, type_ = self._get_tree_id_for_path(path)
        if type_ == 'blob':
            return NodeKind.FILE
        elif type_ == 'tree':
            return NodeKind.DIR
        elif type_ == 'link':
            return NodeKind.SUBMODULE
        return None

    def _get_filectx(self, path):
        path = self._fix_path(path)
        if self._get_kind(path) != NodeKind.FILE:
            raise CommitError(
                "File does not exist for commit %s at  '%s'" % (self.raw_id, path))
        return path

    def _get_file_nodes(self):
        return chain(*(t[2] for t in self.walk()))

    @LazyProperty
    def parents(self):
        """
        Returns list of parent commits.
        """
        parent_ids = self._remote.parents(self.id)
        return self._make_commits(parent_ids)

    @LazyProperty
    def children(self):
        """
        Returns list of child commits.
        """

        children = self._remote.children(self.raw_id)
        return self._make_commits(children)

    def _make_commits(self, commit_ids):
        def commit_maker(_commit_id):
            return self.repository.get_commit(commit_id=commit_id)

        return [commit_maker(commit_id) for commit_id in commit_ids]

    def get_file_mode(self, path):
        """
        Returns stat mode of the file at the given `path`.
        """
        path = safe_str(path)
        # ensure path is traversed
        self._get_tree_id_for_path(path)
        return self._stat_modes[path]

    def is_link(self, path):
        return stat.S_ISLNK(self.get_file_mode(path))

    def is_node_binary(self, path):
        tree_id, _ = self._get_tree_id_for_path(path)
        return self._remote.is_binary(tree_id)

    def get_file_content(self, path):
        """
        Returns content of the file at given `path`.
        """
        tree_id, _ = self._get_tree_id_for_path(path)
        return self._remote.blob_as_pretty_string(tree_id)

    def get_file_content_streamed(self, path):
        tree_id, _ = self._get_tree_id_for_path(path)
        stream_method = getattr(self._remote, 'stream:blob_as_pretty_string')
        return stream_method(tree_id)

    def get_file_size(self, path):
        """
        Returns size of the file at given `path`.
        """
        tree_id, _ = self._get_tree_id_for_path(path)
        return self._remote.blob_raw_length(tree_id)

    def get_path_history(self, path, limit=None, pre_load=None):
        """
        Returns history of file as reversed list of `GitCommit` objects for
        which file at given `path` has been modified.
        """

        path = self._get_filectx(path)
        hist = self._remote.node_history(self.raw_id, path, limit)
        return [
            self.repository.get_commit(commit_id=commit_id, pre_load=pre_load)
            for commit_id in hist]

    def get_file_annotate(self, path, pre_load=None):
        """
        Returns a generator of four element tuples with
            lineno, commit_id, commit lazy loader and line
        """

        result = self._remote.node_annotate(self.raw_id, path)

        for ln_no, commit_id, content in result:
            yield (
                ln_no, commit_id,
                lambda: self.repository.get_commit(commit_id=commit_id, pre_load=pre_load),
                content)

    def get_nodes(self, path):

        if self._get_kind(path) != NodeKind.DIR:
            raise CommitError(
                "Directory does not exist for commit %s at '%s'" % (self.raw_id, path))
        path = self._fix_path(path)

        tree_id, _ = self._get_tree_id_for_path(path)

        dirnodes = []
        filenodes = []

        # extracted tree ID gives us our files...
        bytes_path = safe_str(path)  # libgit operates on bytes
        for name, stat_, id_, type_ in self._remote.tree_items(tree_id):
            if type_ == 'link':
                url = self._get_submodule_url('/'.join((bytes_path, name)))
                dirnodes.append(SubModuleNode(
                    name, url=url, commit=id_, alias=self.repository.alias))
                continue

            if bytes_path != '':
                obj_path = '/'.join((bytes_path, name))
            else:
                obj_path = name
            if obj_path not in self._stat_modes:
                self._stat_modes[obj_path] = stat_

            if type_ == 'tree':
                dirnodes.append(DirNode(obj_path, commit=self))
            elif type_ == 'blob':
                filenodes.append(FileNode(obj_path, commit=self, mode=stat_))
            else:
                raise CommitError(
                    "Requested object should be Tree or Blob, is %s", type_)

        nodes = dirnodes + filenodes
        for node in nodes:
            if node.path not in self.nodes:
                self.nodes[node.path] = node
        nodes.sort()
        return nodes

    def get_node(self, path, pre_load=None):
        if isinstance(path, unicode):
            path = path.encode('utf-8')
        path = self._fix_path(path)
        if path not in self.nodes:
            try:
                tree_id, type_ = self._get_tree_id_for_path(path)
            except CommitError:
                raise NodeDoesNotExistError(
                    "Cannot find one of parents' directories for a given "
                    "path: %s" % path)

            if type_ in ['link', 'commit']:
                url = self._get_submodule_url(path)
                node = SubModuleNode(path, url=url, commit=tree_id,
                                     alias=self.repository.alias)
            elif type_ == 'tree':
                if path == '':
                    node = RootNode(commit=self)
                else:
                    node = DirNode(path, commit=self)
            elif type_ == 'blob':
                node = FileNode(path, commit=self, pre_load=pre_load)
                self._stat_modes[path] = node.mode
            else:
                raise self.no_node_at_path(path)

            # cache node
            self.nodes[path] = node

        return self.nodes[path]

    def get_largefile_node(self, path):
        tree_id, _ = self._get_tree_id_for_path(path)
        pointer_spec = self._remote.is_large_file(tree_id)

        if pointer_spec:
            # content of that file regular FileNode is the hash of largefile
            file_id = pointer_spec.get('oid_hash')
            if self._remote.in_largefiles_store(file_id):
                lf_path = self._remote.store_path(file_id)
                return LargeFileNode(lf_path, commit=self, org_path=path)

    @LazyProperty
    def affected_files(self):
        """
        Gets a fast accessible file changes for given commit
        """
        added, modified, deleted = self._changes_cache
        return list(added.union(modified).union(deleted))

    @LazyProperty
    def _changes_cache(self):
        added = set()
        modified = set()
        deleted = set()
        _r = self._remote

        parents = self.parents
        if not self.parents:
            parents = [base.EmptyCommit()]
        for parent in parents:
            if isinstance(parent, base.EmptyCommit):
                oid = None
            else:
                oid = parent.raw_id
            changes = _r.tree_changes(oid, self.raw_id)
            for (oldpath, newpath), (_, _), (_, _) in changes:
                if newpath and oldpath:
                    modified.add(newpath)
                elif newpath and not oldpath:
                    added.add(newpath)
                elif not newpath and oldpath:
                    deleted.add(oldpath)
        return added, modified, deleted

    def _get_paths_for_status(self, status):
        """
        Returns sorted list of paths for given ``status``.

        :param status: one of: *added*, *modified* or *deleted*
        """
        added, modified, deleted = self._changes_cache
        return sorted({
            'added': list(added),
            'modified': list(modified),
            'deleted': list(deleted)}[status]
        )

    @LazyProperty
    def added(self):
        """
        Returns list of added ``FileNode`` objects.
        """
        if not self.parents:
            return list(self._get_file_nodes())
        return AddedFileNodesGenerator(self.added_paths, self)

    @LazyProperty
    def added_paths(self):
        return [n for n in self._get_paths_for_status('added')]

    @LazyProperty
    def changed(self):
        """
        Returns list of modified ``FileNode`` objects.
        """
        if not self.parents:
            return []
        return ChangedFileNodesGenerator(self.changed_paths, self)

    @LazyProperty
    def changed_paths(self):
        return [n for n in self._get_paths_for_status('modified')]

    @LazyProperty
    def removed(self):
        """
        Returns list of removed ``FileNode`` objects.
        """
        if not self.parents:
            return []
        return RemovedFileNodesGenerator(self.removed_paths, self)

    @LazyProperty
    def removed_paths(self):
        return [n for n in self._get_paths_for_status('deleted')]

    def _get_submodule_url(self, submodule_path):
        git_modules_path = '.gitmodules'

        if self._submodules is None:
            self._submodules = {}

            try:
                submodules_node = self.get_node(git_modules_path)
            except NodeDoesNotExistError:
                return None

            # ConfigParser fails if there are whitespaces, also it needs an iterable
            # file like content
            def iter_content(_content):
                for line in _content.splitlines():
                    yield line

            parser = configparser.RawConfigParser()
            parser.read_file(iter_content(submodules_node.content))

            for section in parser.sections():
                path = parser.get(section, 'path')
                url = parser.get(section, 'url')
                if path and url:
                    self._submodules[path.strip('/')] = url

        return self._submodules.get(submodule_path.strip('/'))
