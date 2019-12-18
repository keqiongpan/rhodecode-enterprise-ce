# -*- coding: utf-8 -*-

# Copyright (C) 2010-2019 RhodeCode GmbH
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
Scm model for RhodeCode
"""

import os.path
import traceback
import logging
import cStringIO

from sqlalchemy import func
from zope.cachedescriptors.property import Lazy as LazyProperty

import rhodecode
from rhodecode.lib.vcs import get_backend
from rhodecode.lib.vcs.exceptions import RepositoryError, NodeNotChangedError
from rhodecode.lib.vcs.nodes import FileNode
from rhodecode.lib.vcs.backends.base import EmptyCommit
from rhodecode.lib import helpers as h, rc_cache
from rhodecode.lib.auth import (
    HasRepoPermissionAny, HasRepoGroupPermissionAny,
    HasUserGroupPermissionAny)
from rhodecode.lib.exceptions import NonRelativePathError, IMCCommitError
from rhodecode.lib import hooks_utils
from rhodecode.lib.utils import (
    get_filesystem_repos, make_db_config)
from rhodecode.lib.utils2 import (safe_str, safe_unicode)
from rhodecode.lib.system_info import get_system_info
from rhodecode.model import BaseModel
from rhodecode.model.db import (
    or_, false,
    Repository, CacheKey, UserFollowing, UserLog, User, RepoGroup,
    PullRequest, FileStore)
from rhodecode.model.settings import VcsSettingsModel
from rhodecode.model.validation_schema.validators import url_validator, InvalidCloneUrl

log = logging.getLogger(__name__)


class UserTemp(object):
    def __init__(self, user_id):
        self.user_id = user_id

    def __repr__(self):
        return "<%s('id:%s')>" % (self.__class__.__name__, self.user_id)


class RepoTemp(object):
    def __init__(self, repo_id):
        self.repo_id = repo_id

    def __repr__(self):
        return "<%s('id:%s')>" % (self.__class__.__name__, self.repo_id)


class SimpleCachedRepoList(object):
    """
    Lighter version of of iteration of repos without the scm initialisation,
    and with cache usage
    """
    def __init__(self, db_repo_list, repos_path, order_by=None, perm_set=None):
        self.db_repo_list = db_repo_list
        self.repos_path = repos_path
        self.order_by = order_by
        self.reversed = (order_by or '').startswith('-')
        if not perm_set:
            perm_set = ['repository.read', 'repository.write',
                        'repository.admin']
        self.perm_set = perm_set

    def __len__(self):
        return len(self.db_repo_list)

    def __repr__(self):
        return '<%s (%s)>' % (self.__class__.__name__, self.__len__())

    def __iter__(self):
        for dbr in self.db_repo_list:
            # check permission at this level
            has_perm = HasRepoPermissionAny(*self.perm_set)(
                dbr.repo_name, 'SimpleCachedRepoList check')
            if not has_perm:
                continue

            tmp_d = {
                'name': dbr.repo_name,
                'dbrepo': dbr.get_dict(),
                'dbrepo_fork': dbr.fork.get_dict() if dbr.fork else {}
            }
            yield tmp_d


class _PermCheckIterator(object):

    def __init__(
            self, obj_list, obj_attr, perm_set, perm_checker,
            extra_kwargs=None):
        """
        Creates iterator from given list of objects, additionally
        checking permission for them from perm_set var

        :param obj_list: list of db objects
        :param obj_attr: attribute of object to pass into perm_checker
        :param perm_set: list of permissions to check
        :param perm_checker: callable to check permissions against
        """
        self.obj_list = obj_list
        self.obj_attr = obj_attr
        self.perm_set = perm_set
        self.perm_checker = perm_checker(*self.perm_set)
        self.extra_kwargs = extra_kwargs or {}

    def __len__(self):
        return len(self.obj_list)

    def __repr__(self):
        return '<%s (%s)>' % (self.__class__.__name__, self.__len__())

    def __iter__(self):
        for db_obj in self.obj_list:
            # check permission at this level
            name = getattr(db_obj, self.obj_attr, None)
            if not self.perm_checker(name, self.__class__.__name__, **self.extra_kwargs):
                continue

            yield db_obj


class RepoList(_PermCheckIterator):

    def __init__(self, db_repo_list, perm_set=None, extra_kwargs=None):
        if not perm_set:
            perm_set = [
                'repository.read', 'repository.write', 'repository.admin']

        super(RepoList, self).__init__(
            obj_list=db_repo_list,
            obj_attr='repo_name', perm_set=perm_set,
            perm_checker=HasRepoPermissionAny,
            extra_kwargs=extra_kwargs)


class RepoGroupList(_PermCheckIterator):

    def __init__(self, db_repo_group_list, perm_set=None, extra_kwargs=None):
        if not perm_set:
            perm_set = ['group.read', 'group.write', 'group.admin']

        super(RepoGroupList, self).__init__(
            obj_list=db_repo_group_list,
            obj_attr='group_name', perm_set=perm_set,
            perm_checker=HasRepoGroupPermissionAny,
            extra_kwargs=extra_kwargs)


class UserGroupList(_PermCheckIterator):

    def __init__(self, db_user_group_list, perm_set=None, extra_kwargs=None):
        if not perm_set:
            perm_set = ['usergroup.read', 'usergroup.write', 'usergroup.admin']

        super(UserGroupList, self).__init__(
            obj_list=db_user_group_list,
            obj_attr='users_group_name', perm_set=perm_set,
            perm_checker=HasUserGroupPermissionAny,
            extra_kwargs=extra_kwargs)


class ScmModel(BaseModel):
    """
    Generic Scm Model
    """

    @LazyProperty
    def repos_path(self):
        """
        Gets the repositories root path from database
        """

        settings_model = VcsSettingsModel(sa=self.sa)
        return settings_model.get_repos_location()

    def repo_scan(self, repos_path=None):
        """
        Listing of repositories in given path. This path should not be a
        repository itself. Return a dictionary of repository objects

        :param repos_path: path to directory containing repositories
        """

        if repos_path is None:
            repos_path = self.repos_path

        log.info('scanning for repositories in %s', repos_path)

        config = make_db_config()
        config.set('extensions', 'largefiles', '')
        repos = {}

        for name, path in get_filesystem_repos(repos_path, recursive=True):
            # name need to be decomposed and put back together using the /
            # since this is internal storage separator for rhodecode
            name = Repository.normalize_repo_name(name)

            try:
                if name in repos:
                    raise RepositoryError('Duplicate repository name %s '
                                          'found in %s' % (name, path))
                elif path[0] in rhodecode.BACKENDS:
                    backend = get_backend(path[0])
                    repos[name] = backend(path[1], config=config,
                                          with_wire={"cache": False})
            except OSError:
                continue
        log.debug('found %s paths with repositories', len(repos))
        return repos

    def get_repos(self, all_repos=None, sort_key=None):
        """
        Get all repositories from db and for each repo create it's
        backend instance and fill that backed with information from database

        :param all_repos: list of repository names as strings
            give specific repositories list, good for filtering

        :param sort_key: initial sorting of repositories
        """
        if all_repos is None:
            all_repos = self.sa.query(Repository)\
                .filter(Repository.group_id == None)\
                .order_by(func.lower(Repository.repo_name)).all()
        repo_iter = SimpleCachedRepoList(
            all_repos, repos_path=self.repos_path, order_by=sort_key)
        return repo_iter

    def get_repo_groups(self, all_groups=None):
        if all_groups is None:
            all_groups = RepoGroup.query()\
                .filter(RepoGroup.group_parent_id == None).all()
        return [x for x in RepoGroupList(all_groups)]

    def mark_for_invalidation(self, repo_name, delete=False):
        """
        Mark caches of this repo invalid in the database. `delete` flag
        removes the cache entries

        :param repo_name: the repo_name for which caches should be marked
            invalid, or deleted
        :param delete: delete the entry keys instead of setting bool
            flag on them, and also purge caches used by the dogpile
        """
        repo = Repository.get_by_repo_name(repo_name)

        if repo:
            invalidation_namespace = CacheKey.REPO_INVALIDATION_NAMESPACE.format(
                repo_id=repo.repo_id)
            CacheKey.set_invalidate(invalidation_namespace, delete=delete)

            repo_id = repo.repo_id
            config = repo._config
            config.set('extensions', 'largefiles', '')
            repo.update_commit_cache(config=config, cs_cache=None)
            if delete:
                cache_namespace_uid = 'cache_repo.{}'.format(repo_id)
                rc_cache.clear_cache_namespace('cache_repo', cache_namespace_uid)

    def toggle_following_repo(self, follow_repo_id, user_id):

        f = self.sa.query(UserFollowing)\
            .filter(UserFollowing.follows_repo_id == follow_repo_id)\
            .filter(UserFollowing.user_id == user_id).scalar()

        if f is not None:
            try:
                self.sa.delete(f)
                return
            except Exception:
                log.error(traceback.format_exc())
                raise

        try:
            f = UserFollowing()
            f.user_id = user_id
            f.follows_repo_id = follow_repo_id
            self.sa.add(f)
        except Exception:
            log.error(traceback.format_exc())
            raise

    def toggle_following_user(self, follow_user_id, user_id):
        f = self.sa.query(UserFollowing)\
            .filter(UserFollowing.follows_user_id == follow_user_id)\
            .filter(UserFollowing.user_id == user_id).scalar()

        if f is not None:
            try:
                self.sa.delete(f)
                return
            except Exception:
                log.error(traceback.format_exc())
                raise

        try:
            f = UserFollowing()
            f.user_id = user_id
            f.follows_user_id = follow_user_id
            self.sa.add(f)
        except Exception:
            log.error(traceback.format_exc())
            raise

    def is_following_repo(self, repo_name, user_id, cache=False):
        r = self.sa.query(Repository)\
            .filter(Repository.repo_name == repo_name).scalar()

        f = self.sa.query(UserFollowing)\
            .filter(UserFollowing.follows_repository == r)\
            .filter(UserFollowing.user_id == user_id).scalar()

        return f is not None

    def is_following_user(self, username, user_id, cache=False):
        u = User.get_by_username(username)

        f = self.sa.query(UserFollowing)\
            .filter(UserFollowing.follows_user == u)\
            .filter(UserFollowing.user_id == user_id).scalar()

        return f is not None

    def get_followers(self, repo):
        repo = self._get_repo(repo)

        return self.sa.query(UserFollowing)\
            .filter(UserFollowing.follows_repository == repo).count()

    def get_forks(self, repo):
        repo = self._get_repo(repo)
        return self.sa.query(Repository)\
            .filter(Repository.fork == repo).count()

    def get_pull_requests(self, repo):
        repo = self._get_repo(repo)
        return self.sa.query(PullRequest)\
            .filter(PullRequest.target_repo == repo)\
            .filter(PullRequest.status != PullRequest.STATUS_CLOSED).count()

    def get_artifacts(self, repo):
        repo = self._get_repo(repo)
        return self.sa.query(FileStore)\
            .filter(FileStore.repo == repo)\
            .filter(or_(FileStore.hidden == None, FileStore.hidden == false())).count()

    def mark_as_fork(self, repo, fork, user):
        repo = self._get_repo(repo)
        fork = self._get_repo(fork)
        if fork and repo.repo_id == fork.repo_id:
            raise Exception("Cannot set repository as fork of itself")

        if fork and repo.repo_type != fork.repo_type:
            raise RepositoryError(
                "Cannot set repository as fork of repository with other type")

        repo.fork = fork
        self.sa.add(repo)
        return repo

    def pull_changes(self, repo, username, remote_uri=None, validate_uri=True):
        dbrepo = self._get_repo(repo)
        remote_uri = remote_uri or dbrepo.clone_uri
        if not remote_uri:
            raise Exception("This repository doesn't have a clone uri")

        repo = dbrepo.scm_instance(cache=False)
        repo.config.clear_section('hooks')

        try:
            # NOTE(marcink): add extra validation so we skip invalid urls
            # this is due this tasks can be executed via scheduler without
            # proper validation of remote_uri
            if validate_uri:
                config = make_db_config(clear_session=False)
                url_validator(remote_uri, dbrepo.repo_type, config)
        except InvalidCloneUrl:
            raise

        repo_name = dbrepo.repo_name
        try:
            # TODO: we need to make sure those operations call proper hooks !
            repo.fetch(remote_uri)

            self.mark_for_invalidation(repo_name)
        except Exception:
            log.error(traceback.format_exc())
            raise

    def push_changes(self, repo, username, remote_uri=None, validate_uri=True):
        dbrepo = self._get_repo(repo)
        remote_uri = remote_uri or dbrepo.push_uri
        if not remote_uri:
            raise Exception("This repository doesn't have a clone uri")

        repo = dbrepo.scm_instance(cache=False)
        repo.config.clear_section('hooks')

        try:
            # NOTE(marcink): add extra validation so we skip invalid urls
            # this is due this tasks can be executed via scheduler without
            # proper validation of remote_uri
            if validate_uri:
                config = make_db_config(clear_session=False)
                url_validator(remote_uri, dbrepo.repo_type, config)
        except InvalidCloneUrl:
            raise

        try:
            repo.push(remote_uri)
        except Exception:
            log.error(traceback.format_exc())
            raise

    def commit_change(self, repo, repo_name, commit, user, author, message,
                      content, f_path):
        """
        Commits changes

        :param repo: SCM instance

        """
        user = self._get_user(user)

        # decoding here will force that we have proper encoded values
        # in any other case this will throw exceptions and deny commit
        content = safe_str(content)
        path = safe_str(f_path)
        # message and author needs to be unicode
        # proper backend should then translate that into required type
        message = safe_unicode(message)
        author = safe_unicode(author)
        imc = repo.in_memory_commit
        imc.change(FileNode(path, content, mode=commit.get_file_mode(f_path)))
        try:
            # TODO: handle pre-push action !
            tip = imc.commit(
                message=message, author=author, parents=[commit],
                branch=commit.branch)
        except Exception as e:
            log.error(traceback.format_exc())
            raise IMCCommitError(str(e))
        finally:
            # always clear caches, if commit fails we want fresh object also
            self.mark_for_invalidation(repo_name)

        # We trigger the post-push action
        hooks_utils.trigger_post_push_hook(
            username=user.username, action='push_local', hook_type='post_push',
            repo_name=repo_name, repo_alias=repo.alias, commit_ids=[tip.raw_id])
        return tip

    def _sanitize_path(self, f_path):
        if f_path.startswith('/') or f_path.startswith('./') or '../' in f_path:
            raise NonRelativePathError('%s is not an relative path' % f_path)
        if f_path:
            f_path = os.path.normpath(f_path)
        return f_path

    def get_dirnode_metadata(self, request, commit, dir_node):
        if not dir_node.is_dir():
            return []

        data = []
        for node in dir_node:
            if not node.is_file():
                # we skip file-nodes
                continue

            last_commit = node.last_commit
            last_commit_date = last_commit.date
            data.append({
                'name': node.name,
                'size': h.format_byte_size_binary(node.size),
                'modified_at': h.format_date(last_commit_date),
                'modified_ts': last_commit_date.isoformat(),
                'revision': last_commit.revision,
                'short_id': last_commit.short_id,
                'message': h.escape(last_commit.message),
                'author': h.escape(last_commit.author),
                'user_profile': h.gravatar_with_user(
                    request, last_commit.author),
            })

        return data

    def get_nodes(self, repo_name, commit_id, root_path='/', flat=True,
                  extended_info=False, content=False, max_file_bytes=None):
        """
        recursive walk in root dir and return a set of all path in that dir
        based on repository walk function

        :param repo_name: name of repository
        :param commit_id: commit id for which to list nodes
        :param root_path: root path to list
        :param flat: return as a list, if False returns a dict with description
        :param extended_info: show additional info such as md5, binary, size etc
        :param content: add nodes content to the return data
        :param max_file_bytes: will not return file contents over this limit

        """
        _files = list()
        _dirs = list()
        try:
            _repo = self._get_repo(repo_name)
            commit = _repo.scm_instance().get_commit(commit_id=commit_id)
            root_path = root_path.lstrip('/')
            for __, dirs, files in commit.walk(root_path):

                for f in files:
                    _content = None
                    _data = f_name = f.unicode_path

                    if not flat:
                        _data = {
                            "name": h.escape(f_name),
                            "type": "file",
                            }
                        if extended_info:
                            _data.update({
                                "md5": f.md5,
                                "binary": f.is_binary,
                                "size": f.size,
                                "extension": f.extension,
                                "mimetype": f.mimetype,
                                "lines": f.lines()[0]
                            })

                        if content:
                            over_size_limit = (max_file_bytes is not None
                                               and f.size > max_file_bytes)
                            full_content = None
                            if not f.is_binary and not over_size_limit:
                                full_content = safe_str(f.content)

                            _data.update({
                                "content": full_content,
                            })
                    _files.append(_data)

                for d in dirs:
                    _data = d_name = d.unicode_path
                    if not flat:
                        _data = {
                            "name": h.escape(d_name),
                            "type": "dir",
                            }
                    if extended_info:
                        _data.update({
                            "md5": None,
                            "binary": None,
                            "size": None,
                            "extension": None,
                        })
                    if content:
                        _data.update({
                            "content": None
                        })
                    _dirs.append(_data)
        except RepositoryError:
            log.exception("Exception in get_nodes")
            raise

        return _dirs, _files

    def get_quick_filter_nodes(self, repo_name, commit_id, root_path='/'):
        """
        Generate files for quick filter in files view
        """

        _files = list()
        _dirs = list()
        try:
            _repo = self._get_repo(repo_name)
            commit = _repo.scm_instance().get_commit(commit_id=commit_id)
            root_path = root_path.lstrip('/')
            for __, dirs, files in commit.walk(root_path):

                for f in files:

                    _data = {
                        "name": h.escape(f.unicode_path),
                        "type": "file",
                        }

                    _files.append(_data)

                for d in dirs:

                    _data = {
                        "name": h.escape(d.unicode_path),
                        "type": "dir",
                        }

                    _dirs.append(_data)
        except RepositoryError:
            log.exception("Exception in get_quick_filter_nodes")
            raise

        return _dirs, _files

    def get_node(self, repo_name, commit_id, file_path,
                 extended_info=False, content=False, max_file_bytes=None, cache=True):
        """
        retrieve single node from commit
        """
        try:

            _repo = self._get_repo(repo_name)
            commit = _repo.scm_instance().get_commit(commit_id=commit_id)

            file_node = commit.get_node(file_path)
            if file_node.is_dir():
                raise RepositoryError('The given path is a directory')

            _content = None
            f_name = file_node.unicode_path

            file_data = {
                "name": h.escape(f_name),
                "type": "file",
            }

            if extended_info:
                file_data.update({
                    "extension": file_node.extension,
                    "mimetype": file_node.mimetype,
                })

                if cache:
                    md5 = file_node.md5
                    is_binary = file_node.is_binary
                    size = file_node.size
                else:
                    is_binary, md5, size, _content = file_node.metadata_uncached()

                file_data.update({
                    "md5": md5,
                    "binary": is_binary,
                    "size": size,
                })

            if content and cache:
                # get content + cache
                size = file_node.size
                over_size_limit = (max_file_bytes is not None and size > max_file_bytes)
                full_content = None
                all_lines = 0
                if not file_node.is_binary and not over_size_limit:
                    full_content = safe_unicode(file_node.content)
                    all_lines, empty_lines = file_node.count_lines(full_content)

                file_data.update({
                    "content": full_content,
                    "lines": all_lines
                })
            elif content:
                # get content *without* cache
                if _content is None:
                    is_binary, md5, size, _content = file_node.metadata_uncached()

                over_size_limit = (max_file_bytes is not None and size > max_file_bytes)
                full_content = None
                all_lines = 0
                if not is_binary and not over_size_limit:
                    full_content = safe_unicode(_content)
                    all_lines, empty_lines = file_node.count_lines(full_content)

                file_data.update({
                    "content": full_content,
                    "lines": all_lines
                })

        except RepositoryError:
            log.exception("Exception in get_node")
            raise

        return file_data

    def get_fts_data(self, repo_name, commit_id, root_path='/'):
        """
        Fetch node tree for usage in full text search
        """

        tree_info = list()

        try:
            _repo = self._get_repo(repo_name)
            commit = _repo.scm_instance().get_commit(commit_id=commit_id)
            root_path = root_path.lstrip('/')
            for __, dirs, files in commit.walk(root_path):

                for f in files:
                    is_binary, md5, size, _content = f.metadata_uncached()
                    _data = {
                        "name": f.unicode_path,
                        "md5": md5,
                        "extension": f.extension,
                        "binary": is_binary,
                        "size": size
                    }

                    tree_info.append(_data)

        except RepositoryError:
            log.exception("Exception in get_nodes")
            raise

        return tree_info

    def create_nodes(self, user, repo, message, nodes, parent_commit=None,
                     author=None, trigger_push_hook=True):
        """
        Commits given multiple nodes into repo

        :param user: RhodeCode User object or user_id, the commiter
        :param repo: RhodeCode Repository object
        :param message: commit message
        :param nodes: mapping {filename:{'content':content},...}
        :param parent_commit: parent commit, can be empty than it's
           initial commit
        :param author: author of commit, cna be different that commiter
           only for git
        :param trigger_push_hook: trigger push hooks

        :returns: new commited commit
        """

        user = self._get_user(user)
        scm_instance = repo.scm_instance(cache=False)

        processed_nodes = []
        for f_path in nodes:
            f_path = self._sanitize_path(f_path)
            content = nodes[f_path]['content']
            f_path = safe_str(f_path)
            # decoding here will force that we have proper encoded values
            # in any other case this will throw exceptions and deny commit
            if isinstance(content, (basestring,)):
                content = safe_str(content)
            elif isinstance(content, (file, cStringIO.OutputType,)):
                content = content.read()
            else:
                raise Exception('Content is of unrecognized type %s' % (
                    type(content)
                ))
            processed_nodes.append((f_path, content))

        message = safe_unicode(message)
        commiter = user.full_contact
        author = safe_unicode(author) if author else commiter

        imc = scm_instance.in_memory_commit

        if not parent_commit:
            parent_commit = EmptyCommit(alias=scm_instance.alias)

        if isinstance(parent_commit, EmptyCommit):
            # EmptyCommit means we we're editing empty repository
            parents = None
        else:
            parents = [parent_commit]
        # add multiple nodes
        for path, content in processed_nodes:
            imc.add(FileNode(path, content=content))
        # TODO: handle pre push scenario
        tip = imc.commit(message=message,
                         author=author,
                         parents=parents,
                         branch=parent_commit.branch)

        self.mark_for_invalidation(repo.repo_name)
        if trigger_push_hook:
            hooks_utils.trigger_post_push_hook(
                username=user.username, action='push_local',
                repo_name=repo.repo_name, repo_alias=scm_instance.alias,
                hook_type='post_push',
                commit_ids=[tip.raw_id])
        return tip

    def update_nodes(self, user, repo, message, nodes, parent_commit=None,
                     author=None, trigger_push_hook=True):
        user = self._get_user(user)
        scm_instance = repo.scm_instance(cache=False)

        message = safe_unicode(message)
        commiter = user.full_contact
        author = safe_unicode(author) if author else commiter

        imc = scm_instance.in_memory_commit

        if not parent_commit:
            parent_commit = EmptyCommit(alias=scm_instance.alias)

        if isinstance(parent_commit, EmptyCommit):
            # EmptyCommit means we we're editing empty repository
            parents = None
        else:
            parents = [parent_commit]

        # add multiple nodes
        for _filename, data in nodes.items():
            # new filename, can be renamed from the old one, also sanitaze
            # the path for any hack around relative paths like ../../ etc.
            filename = self._sanitize_path(data['filename'])
            old_filename = self._sanitize_path(_filename)
            content = data['content']
            file_mode = data.get('mode')
            filenode = FileNode(old_filename, content=content, mode=file_mode)
            op = data['op']
            if op == 'add':
                imc.add(filenode)
            elif op == 'del':
                imc.remove(filenode)
            elif op == 'mod':
                if filename != old_filename:
                    # TODO: handle renames more efficient, needs vcs lib changes
                    imc.remove(filenode)
                    imc.add(FileNode(filename, content=content, mode=file_mode))
                else:
                    imc.change(filenode)

        try:
            # TODO: handle pre push scenario commit changes
            tip = imc.commit(message=message,
                             author=author,
                             parents=parents,
                             branch=parent_commit.branch)
        except NodeNotChangedError:
            raise
        except Exception as e:
            log.exception("Unexpected exception during call to imc.commit")
            raise IMCCommitError(str(e))
        finally:
            # always clear caches, if commit fails we want fresh object also
            self.mark_for_invalidation(repo.repo_name)

        if trigger_push_hook:
            hooks_utils.trigger_post_push_hook(
                username=user.username, action='push_local', hook_type='post_push',
                repo_name=repo.repo_name, repo_alias=scm_instance.alias,
                commit_ids=[tip.raw_id])

        return tip

    def delete_nodes(self, user, repo, message, nodes, parent_commit=None,
                     author=None, trigger_push_hook=True):
        """
        Deletes given multiple nodes into `repo`

        :param user: RhodeCode User object or user_id, the committer
        :param repo: RhodeCode Repository object
        :param message: commit message
        :param nodes: mapping {filename:{'content':content},...}
        :param parent_commit: parent commit, can be empty than it's initial
           commit
        :param author: author of commit, cna be different that commiter only
           for git
        :param trigger_push_hook: trigger push hooks

        :returns: new commit after deletion
        """

        user = self._get_user(user)
        scm_instance = repo.scm_instance(cache=False)

        processed_nodes = []
        for f_path in nodes:
            f_path = self._sanitize_path(f_path)
            # content can be empty but for compatabilty it allows same dicts
            # structure as add_nodes
            content = nodes[f_path].get('content')
            processed_nodes.append((f_path, content))

        message = safe_unicode(message)
        commiter = user.full_contact
        author = safe_unicode(author) if author else commiter

        imc = scm_instance.in_memory_commit

        if not parent_commit:
            parent_commit = EmptyCommit(alias=scm_instance.alias)

        if isinstance(parent_commit, EmptyCommit):
            # EmptyCommit means we we're editing empty repository
            parents = None
        else:
            parents = [parent_commit]
        # add multiple nodes
        for path, content in processed_nodes:
            imc.remove(FileNode(path, content=content))

        # TODO: handle pre push scenario
        tip = imc.commit(message=message,
                         author=author,
                         parents=parents,
                         branch=parent_commit.branch)

        self.mark_for_invalidation(repo.repo_name)
        if trigger_push_hook:
            hooks_utils.trigger_post_push_hook(
                username=user.username, action='push_local', hook_type='post_push',
                repo_name=repo.repo_name, repo_alias=scm_instance.alias,
                commit_ids=[tip.raw_id])
        return tip

    def strip(self, repo, commit_id, branch):
        scm_instance = repo.scm_instance(cache=False)
        scm_instance.config.clear_section('hooks')
        scm_instance.strip(commit_id, branch)
        self.mark_for_invalidation(repo.repo_name)

    def get_unread_journal(self):
        return self.sa.query(UserLog).count()

    @classmethod
    def backend_landing_ref(cls, repo_type):
        """
        Return a default landing ref based on a repository type.
        """

        landing_ref = {
            'hg': ('branch:default', 'default'),
            'git': ('branch:master', 'master'),
            'svn': ('rev:tip', 'latest tip'),
            'default': ('rev:tip', 'latest tip'),
        }

        return landing_ref.get(repo_type) or landing_ref['default']

    def get_repo_landing_revs(self, translator, repo=None):
        """
        Generates select option with tags branches and bookmarks (for hg only)
        grouped by type

        :param repo:
        """
        _ = translator
        repo = self._get_repo(repo)

        if repo:
            repo_type = repo.repo_type
        else:
            repo_type = 'default'

        default_landing_ref, landing_ref_lbl = self.backend_landing_ref(repo_type)

        default_ref_options = [
            [default_landing_ref, landing_ref_lbl]
        ]
        default_choices = [
            default_landing_ref
        ]

        if not repo:
            return default_choices, default_ref_options

        repo = repo.scm_instance()

        ref_options = [('rev:tip', 'latest tip')]
        choices = ['rev:tip']

        # branches
        branch_group = [(u'branch:%s' % safe_unicode(b), safe_unicode(b)) for b in repo.branches]
        if not branch_group:
            # new repo, or without maybe a branch?
            branch_group = default_ref_options

        branches_group = (branch_group, _("Branches"))
        ref_options.append(branches_group)
        choices.extend([x[0] for x in branches_group[0]])

        # bookmarks for HG
        if repo.alias == 'hg':
            bookmarks_group = (
                [(u'book:%s' % safe_unicode(b), safe_unicode(b))
                    for b in repo.bookmarks],
                _("Bookmarks"))
            ref_options.append(bookmarks_group)
            choices.extend([x[0] for x in bookmarks_group[0]])

        # tags
        tags_group = (
            [(u'tag:%s' % safe_unicode(t), safe_unicode(t))
                for t in repo.tags],
            _("Tags"))
        ref_options.append(tags_group)
        choices.extend([x[0] for x in tags_group[0]])

        return choices, ref_options

    def get_server_info(self, environ=None):
        server_info = get_system_info(environ)
        return server_info
