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

"""
Repository model for rhodecode
"""

import logging
import os
import re
import shutil
import time
import traceback
from datetime import datetime, timedelta

from pyramid.threadlocal import get_current_request
from zope.cachedescriptors.property import Lazy as LazyProperty

from rhodecode import events
from rhodecode.lib import helpers as h
from rhodecode.lib.auth import HasUserGroupPermissionAny
from rhodecode.lib.caching_query import FromCache
from rhodecode.lib.exceptions import AttachedForksError
from rhodecode.lib.hooks_base import log_delete_repository
from rhodecode.lib.utils import make_db_config
from rhodecode.lib.utils2 import (
    safe_str, safe_unicode, remove_prefix, obfuscate_url_pw,
    get_current_rhodecode_user, safe_int, datetime_to_time, action_logger_generic)
from rhodecode.lib.vcs.backends import get_backend
from rhodecode.model import BaseModel
from rhodecode.model.db import (_hash_key,
    Repository, UserRepoToPerm, UserGroupRepoToPerm, UserRepoGroupToPerm,
    UserGroupRepoGroupToPerm, User, Permission, Statistics, UserGroup,
    RepoGroup, RepositoryField)

from rhodecode.model.settings import VcsSettingsModel


log = logging.getLogger(__name__)


class RepoModel(BaseModel):

    cls = Repository

    def _get_user_group(self, users_group):
        return self._get_instance(UserGroup, users_group,
                                  callback=UserGroup.get_by_group_name)

    def _get_repo_group(self, repo_group):
        return self._get_instance(RepoGroup, repo_group,
                                  callback=RepoGroup.get_by_group_name)

    def _create_default_perms(self, repository, private):
        # create default permission
        default = 'repository.read'
        def_user = User.get_default_user()
        for p in def_user.user_perms:
            if p.permission.permission_name.startswith('repository.'):
                default = p.permission.permission_name
                break

        default_perm = 'repository.none' if private else default

        repo_to_perm = UserRepoToPerm()
        repo_to_perm.permission = Permission.get_by_key(default_perm)

        repo_to_perm.repository = repository
        repo_to_perm.user_id = def_user.user_id

        return repo_to_perm

    @LazyProperty
    def repos_path(self):
        """
        Gets the repositories root path from database
        """
        settings_model = VcsSettingsModel(sa=self.sa)
        return settings_model.get_repos_location()

    def get(self, repo_id, cache=False):
        repo = self.sa.query(Repository) \
            .filter(Repository.repo_id == repo_id)

        if cache:
            repo = repo.options(
                FromCache("sql_cache_short", "get_repo_%s" % repo_id))
        return repo.scalar()

    def get_repo(self, repository):
        return self._get_repo(repository)

    def get_by_repo_name(self, repo_name, cache=False):
        repo = self.sa.query(Repository) \
            .filter(Repository.repo_name == repo_name)

        if cache:
            name_key = _hash_key(repo_name)
            repo = repo.options(
                FromCache("sql_cache_short", "get_repo_%s" % name_key))
        return repo.scalar()

    def _extract_id_from_repo_name(self, repo_name):
        if repo_name.startswith('/'):
            repo_name = repo_name.lstrip('/')
        by_id_match = re.match(r'^_(\d{1,})', repo_name)
        if by_id_match:
            return by_id_match.groups()[0]

    def get_repo_by_id(self, repo_name):
        """
        Extracts repo_name by id from special urls.
        Example url is _11/repo_name

        :param repo_name:
        :return: repo object if matched else None
        """

        try:
            _repo_id = self._extract_id_from_repo_name(repo_name)
            if _repo_id:
                return self.get(_repo_id)
        except Exception:
            log.exception('Failed to extract repo_name from URL')

        return None

    def get_repos_for_root(self, root, traverse=False):
        if traverse:
            like_expression = u'{}%'.format(safe_unicode(root))
            repos = Repository.query().filter(
                Repository.repo_name.like(like_expression)).all()
        else:
            if root and not isinstance(root, RepoGroup):
                raise ValueError(
                    'Root must be an instance '
                    'of RepoGroup, got:{} instead'.format(type(root)))
            repos = Repository.query().filter(Repository.group == root).all()
        return repos

    def get_url(self, repo, request=None):
        if not request:
            request = get_current_request()
        return request.route_url('repo_summary', repo_name=safe_str(repo.repo_name))

    @classmethod
    def update_repoinfo(cls, repositories=None):
        if not repositories:
            repositories = Repository.getAll()
        for repo in repositories:
            repo.update_commit_cache()

    def get_repos_as_dict(self, repo_list=None, admin=False,
                          super_user_actions=False):

        from rhodecode.lib.utils import PartialRenderer
        _render = PartialRenderer('data_table/_dt_elements.mako')
        c = _render.c

        def quick_menu(repo_name):
            return _render('quick_menu', repo_name)

        def repo_lnk(name, rtype, rstate, private, fork_of):
            return _render('repo_name', name, rtype, rstate, private, fork_of,
                           short_name=not admin, admin=False)

        def last_change(last_change):
            if admin and isinstance(last_change, datetime) and not last_change.tzinfo:
                last_change = last_change + timedelta(seconds=
                    (datetime.now() - datetime.utcnow()).seconds)
            return _render("last_change", last_change)

        def rss_lnk(repo_name):
            return _render("rss", repo_name)

        def atom_lnk(repo_name):
            return _render("atom", repo_name)

        def last_rev(repo_name, cs_cache):
            return _render('revision', repo_name, cs_cache.get('revision'),
                           cs_cache.get('raw_id'), cs_cache.get('author'),
                           cs_cache.get('message'))

        def desc(desc):
            if c.visual.stylify_metatags:
                desc = h.urlify_text(h.escaped_stylize(desc))
            else:
                desc = h.urlify_text(h.html_escape(desc))

            return _render('repo_desc', desc)

        def state(repo_state):
            return _render("repo_state", repo_state)

        def repo_actions(repo_name):
            return _render('repo_actions', repo_name, super_user_actions)

        def user_profile(username):
            return _render('user_profile', username)

        repos_data = []
        for repo in repo_list:
            cs_cache = repo.changeset_cache
            row = {
                "menu": quick_menu(repo.repo_name),

                "name": repo_lnk(repo.repo_name, repo.repo_type,
                                 repo.repo_state, repo.private, repo.fork),
                "name_raw": repo.repo_name.lower(),

                "last_change": last_change(repo.last_db_change),
                "last_change_raw": datetime_to_time(repo.last_db_change),

                "last_changeset": last_rev(repo.repo_name, cs_cache),
                "last_changeset_raw": cs_cache.get('revision'),

                "desc": desc(repo.description),
                "owner": user_profile(repo.user.username),

                "state": state(repo.repo_state),
                "rss": rss_lnk(repo.repo_name),

                "atom": atom_lnk(repo.repo_name),
            }
            if admin:
                row.update({
                    "action": repo_actions(repo.repo_name),
                })
            repos_data.append(row)

        return repos_data

    def _get_defaults(self, repo_name):
        """
        Gets information about repository, and returns a dict for
        usage in forms

        :param repo_name:
        """

        repo_info = Repository.get_by_repo_name(repo_name)

        if repo_info is None:
            return None

        defaults = repo_info.get_dict()
        defaults['repo_name'] = repo_info.just_name

        groups = repo_info.groups_with_parents
        parent_group = groups[-1] if groups else None

        # we use -1 as this is how in HTML, we mark an empty group
        defaults['repo_group'] = getattr(parent_group, 'group_id', -1)

        keys_to_process = (
            {'k': 'repo_type', 'strip': False},
            {'k': 'repo_enable_downloads', 'strip': True},
            {'k': 'repo_description', 'strip': True},
            {'k': 'repo_enable_locking', 'strip': True},
            {'k': 'repo_landing_rev', 'strip': True},
            {'k': 'clone_uri', 'strip': False},
            {'k': 'repo_private', 'strip': True},
            {'k': 'repo_enable_statistics', 'strip': True}
        )

        for item in keys_to_process:
            attr = item['k']
            if item['strip']:
                attr = remove_prefix(item['k'], 'repo_')

            val = defaults[attr]
            if item['k'] == 'repo_landing_rev':
                val = ':'.join(defaults[attr])
            defaults[item['k']] = val
            if item['k'] == 'clone_uri':
                defaults['clone_uri_hidden'] = repo_info.clone_uri_hidden

        # fill owner
        if repo_info.user:
            defaults.update({'user': repo_info.user.username})
        else:
            replacement_user = User.get_first_super_admin().username
            defaults.update({'user': replacement_user})

        return defaults

    def update(self, repo, **kwargs):
        try:
            cur_repo = self._get_repo(repo)
            source_repo_name = cur_repo.repo_name
            if 'user' in kwargs:
                cur_repo.user = User.get_by_username(kwargs['user'])

            if 'repo_group' in kwargs:
                cur_repo.group = RepoGroup.get(kwargs['repo_group'])
            log.debug('Updating repo %s with params:%s', cur_repo, kwargs)

            update_keys = [
                (1, 'repo_description'),
                (1, 'repo_landing_rev'),
                (1, 'repo_private'),
                (1, 'repo_enable_downloads'),
                (1, 'repo_enable_locking'),
                (1, 'repo_enable_statistics'),
                (0, 'clone_uri'),
                (0, 'fork_id')
            ]
            for strip, k in update_keys:
                if k in kwargs:
                    val = kwargs[k]
                    if strip:
                        k = remove_prefix(k, 'repo_')

                    setattr(cur_repo, k, val)

            new_name = cur_repo.get_new_name(kwargs['repo_name'])
            cur_repo.repo_name = new_name

            # if private flag is set, reset default permission to NONE
            if kwargs.get('repo_private'):
                EMPTY_PERM = 'repository.none'
                RepoModel().grant_user_permission(
                    repo=cur_repo, user=User.DEFAULT_USER, perm=EMPTY_PERM
                )

            # handle extra fields
            for field in filter(lambda k: k.startswith(RepositoryField.PREFIX),
                                kwargs):
                k = RepositoryField.un_prefix_key(field)
                ex_field = RepositoryField.get_by_key_name(
                    key=k, repo=cur_repo)
                if ex_field:
                    ex_field.field_value = kwargs[field]
                    self.sa.add(ex_field)
            self.sa.add(cur_repo)

            if source_repo_name != new_name:
                # rename repository
                self._rename_filesystem_repo(
                    old=source_repo_name, new=new_name)

            return cur_repo
        except Exception:
            log.error(traceback.format_exc())
            raise

    def _create_repo(self, repo_name, repo_type, description, owner,
                     private=False, clone_uri=None, repo_group=None,
                     landing_rev='rev:tip', fork_of=None,
                     copy_fork_permissions=False, enable_statistics=False,
                     enable_locking=False, enable_downloads=False,
                     copy_group_permissions=False,
                     state=Repository.STATE_PENDING):
        """
        Create repository inside database with PENDING state, this should be
        only executed by create() repo. With exception of importing existing
        repos
        """
        from rhodecode.model.scm import ScmModel

        owner = self._get_user(owner)
        fork_of = self._get_repo(fork_of)
        repo_group = self._get_repo_group(safe_int(repo_group))

        try:
            repo_name = safe_unicode(repo_name)
            description = safe_unicode(description)
            # repo name is just a name of repository
            # while repo_name_full is a full qualified name that is combined
            # with name and path of group
            repo_name_full = repo_name
            repo_name = repo_name.split(Repository.NAME_SEP)[-1]

            new_repo = Repository()
            new_repo.repo_state = state
            new_repo.enable_statistics = False
            new_repo.repo_name = repo_name_full
            new_repo.repo_type = repo_type
            new_repo.user = owner
            new_repo.group = repo_group
            new_repo.description = description or repo_name
            new_repo.private = private
            new_repo.clone_uri = clone_uri
            new_repo.landing_rev = landing_rev

            new_repo.enable_statistics = enable_statistics
            new_repo.enable_locking = enable_locking
            new_repo.enable_downloads = enable_downloads

            if repo_group:
                new_repo.enable_locking = repo_group.enable_locking

            if fork_of:
                parent_repo = fork_of
                new_repo.fork = parent_repo

            events.trigger(events.RepoPreCreateEvent(new_repo))

            self.sa.add(new_repo)

            EMPTY_PERM = 'repository.none'
            if fork_of and copy_fork_permissions:
                repo = fork_of
                user_perms = UserRepoToPerm.query() \
                    .filter(UserRepoToPerm.repository == repo).all()
                group_perms = UserGroupRepoToPerm.query() \
                    .filter(UserGroupRepoToPerm.repository == repo).all()

                for perm in user_perms:
                    UserRepoToPerm.create(
                        perm.user, new_repo, perm.permission)

                for perm in group_perms:
                    UserGroupRepoToPerm.create(
                        perm.users_group, new_repo, perm.permission)
                # in case we copy permissions and also set this repo to private
                # override the default user permission to make it a private
                # repo
                if private:
                    RepoModel(self.sa).grant_user_permission(
                        repo=new_repo, user=User.DEFAULT_USER, perm=EMPTY_PERM)

            elif repo_group and copy_group_permissions:
                user_perms = UserRepoGroupToPerm.query() \
                    .filter(UserRepoGroupToPerm.group == repo_group).all()

                group_perms = UserGroupRepoGroupToPerm.query() \
                    .filter(UserGroupRepoGroupToPerm.group == repo_group).all()

                for perm in user_perms:
                    perm_name = perm.permission.permission_name.replace(
                        'group.', 'repository.')
                    perm_obj = Permission.get_by_key(perm_name)
                    UserRepoToPerm.create(perm.user, new_repo, perm_obj)

                for perm in group_perms:
                    perm_name = perm.permission.permission_name.replace(
                        'group.', 'repository.')
                    perm_obj = Permission.get_by_key(perm_name)
                    UserGroupRepoToPerm.create(
                        perm.users_group, new_repo, perm_obj)

                if private:
                    RepoModel(self.sa).grant_user_permission(
                        repo=new_repo, user=User.DEFAULT_USER, perm=EMPTY_PERM)

            else:
                perm_obj = self._create_default_perms(new_repo, private)
                self.sa.add(perm_obj)

            # now automatically start following this repository as owner
            ScmModel(self.sa).toggle_following_repo(new_repo.repo_id,
                                                    owner.user_id)

            # we need to flush here, in order to check if database won't
            # throw any exceptions, create filesystem dirs at the very end
            self.sa.flush()
            events.trigger(events.RepoCreateEvent(new_repo))
            return new_repo

        except Exception:
            log.error(traceback.format_exc())
            raise

    def create(self, form_data, cur_user):
        """
        Create repository using celery tasks

        :param form_data:
        :param cur_user:
        """
        from rhodecode.lib.celerylib import tasks, run_task
        return run_task(tasks.create_repo, form_data, cur_user)

    def update_permissions(self, repo, perm_additions=None, perm_updates=None,
                           perm_deletions=None, check_perms=True,
                           cur_user=None):
        if not perm_additions:
            perm_additions = []
        if not perm_updates:
            perm_updates = []
        if not perm_deletions:
            perm_deletions = []

        req_perms = ('usergroup.read', 'usergroup.write', 'usergroup.admin')

        changes = {
            'added': [],
            'updated': [],
            'deleted': []
        }
        # update permissions
        for member_id, perm, member_type in perm_updates:
            member_id = int(member_id)
            if member_type == 'user':
                member_name = User.get(member_id).username
                # this updates also current one if found
                self.grant_user_permission(
                    repo=repo, user=member_id, perm=perm)
            else:  # set for user group
                # check if we have permissions to alter this usergroup
                member_name = UserGroup.get(member_id).users_group_name
                if not check_perms or HasUserGroupPermissionAny(
                        *req_perms)(member_name, user=cur_user):
                    self.grant_user_group_permission(
                        repo=repo, group_name=member_id, perm=perm)

            changes['updated'].append({'type': member_type, 'id': member_id,
                                       'name': member_name, 'new_perm': perm})

        # set new permissions
        for member_id, perm, member_type in perm_additions:
            member_id = int(member_id)
            if member_type == 'user':
                member_name = User.get(member_id).username
                self.grant_user_permission(
                    repo=repo, user=member_id, perm=perm)
            else:  # set for user group
                # check if we have permissions to alter this usergroup
                member_name = UserGroup.get(member_id).users_group_name
                if not check_perms or HasUserGroupPermissionAny(
                        *req_perms)(member_name, user=cur_user):
                    self.grant_user_group_permission(
                        repo=repo, group_name=member_id, perm=perm)
            changes['added'].append({'type': member_type, 'id': member_id,
                                     'name': member_name, 'new_perm': perm})
        # delete permissions
        for member_id, perm, member_type in perm_deletions:
            member_id = int(member_id)
            if member_type == 'user':
                member_name = User.get(member_id).username
                self.revoke_user_permission(repo=repo, user=member_id)
            else:  # set for user group
                # check if we have permissions to alter this usergroup
                member_name = UserGroup.get(member_id).users_group_name
                if not check_perms or HasUserGroupPermissionAny(
                        *req_perms)(member_name, user=cur_user):
                    self.revoke_user_group_permission(
                        repo=repo, group_name=member_id)

            changes['deleted'].append({'type': member_type, 'id': member_id,
                                       'name': member_name, 'new_perm': perm})
        return changes

    def create_fork(self, form_data, cur_user):
        """
        Simple wrapper into executing celery task for fork creation

        :param form_data:
        :param cur_user:
        """
        from rhodecode.lib.celerylib import tasks, run_task
        return run_task(tasks.create_repo_fork, form_data, cur_user)

    def delete(self, repo, forks=None, fs_remove=True, cur_user=None):
        """
        Delete given repository, forks parameter defines what do do with
        attached forks. Throws AttachedForksError if deleted repo has attached
        forks

        :param repo:
        :param forks: str 'delete' or 'detach'
        :param fs_remove: remove(archive) repo from filesystem
        """
        if not cur_user:
            cur_user = getattr(get_current_rhodecode_user(), 'username', None)
        repo = self._get_repo(repo)
        if repo:
            if forks == 'detach':
                for r in repo.forks:
                    r.fork = None
                    self.sa.add(r)
            elif forks == 'delete':
                for r in repo.forks:
                    self.delete(r, forks='delete')
            elif [f for f in repo.forks]:
                raise AttachedForksError()

            old_repo_dict = repo.get_dict()
            events.trigger(events.RepoPreDeleteEvent(repo))
            try:
                self.sa.delete(repo)
                if fs_remove:
                    self._delete_filesystem_repo(repo)
                else:
                    log.debug('skipping removal from filesystem')
                old_repo_dict.update({
                    'deleted_by': cur_user,
                    'deleted_on': time.time(),
                })
                log_delete_repository(**old_repo_dict)
                events.trigger(events.RepoDeleteEvent(repo))
            except Exception:
                log.error(traceback.format_exc())
                raise

    def grant_user_permission(self, repo, user, perm):
        """
        Grant permission for user on given repository, or update existing one
        if found

        :param repo: Instance of Repository, repository_id, or repository name
        :param user: Instance of User, user_id or username
        :param perm: Instance of Permission, or permission_name
        """
        user = self._get_user(user)
        repo = self._get_repo(repo)
        permission = self._get_perm(perm)

        # check if we have that permission already
        obj = self.sa.query(UserRepoToPerm) \
            .filter(UserRepoToPerm.user == user) \
            .filter(UserRepoToPerm.repository == repo) \
            .scalar()
        if obj is None:
            # create new !
            obj = UserRepoToPerm()
        obj.repository = repo
        obj.user = user
        obj.permission = permission
        self.sa.add(obj)
        log.debug('Granted perm %s to %s on %s', perm, user, repo)
        action_logger_generic(
            'granted permission: {} to user: {} on repo: {}'.format(
                perm, user, repo), namespace='security.repo')
        return obj

    def revoke_user_permission(self, repo, user):
        """
        Revoke permission for user on given repository

        :param repo: Instance of Repository, repository_id, or repository name
        :param user: Instance of User, user_id or username
        """

        user = self._get_user(user)
        repo = self._get_repo(repo)

        obj = self.sa.query(UserRepoToPerm) \
            .filter(UserRepoToPerm.repository == repo) \
            .filter(UserRepoToPerm.user == user) \
            .scalar()
        if obj:
            self.sa.delete(obj)
            log.debug('Revoked perm on %s on %s', repo, user)
            action_logger_generic(
                'revoked permission from user: {} on repo: {}'.format(
                    user, repo), namespace='security.repo')

    def grant_user_group_permission(self, repo, group_name, perm):
        """
        Grant permission for user group on given repository, or update
        existing one if found

        :param repo: Instance of Repository, repository_id, or repository name
        :param group_name: Instance of UserGroup, users_group_id,
            or user group name
        :param perm: Instance of Permission, or permission_name
        """
        repo = self._get_repo(repo)
        group_name = self._get_user_group(group_name)
        permission = self._get_perm(perm)

        # check if we have that permission already
        obj = self.sa.query(UserGroupRepoToPerm) \
            .filter(UserGroupRepoToPerm.users_group == group_name) \
            .filter(UserGroupRepoToPerm.repository == repo) \
            .scalar()

        if obj is None:
            # create new
            obj = UserGroupRepoToPerm()

        obj.repository = repo
        obj.users_group = group_name
        obj.permission = permission
        self.sa.add(obj)
        log.debug('Granted perm %s to %s on %s', perm, group_name, repo)
        action_logger_generic(
            'granted permission: {} to usergroup: {} on repo: {}'.format(
                perm, group_name, repo), namespace='security.repo')

        return obj

    def revoke_user_group_permission(self, repo, group_name):
        """
        Revoke permission for user group on given repository

        :param repo: Instance of Repository, repository_id, or repository name
        :param group_name: Instance of UserGroup, users_group_id,
            or user group name
        """
        repo = self._get_repo(repo)
        group_name = self._get_user_group(group_name)

        obj = self.sa.query(UserGroupRepoToPerm) \
            .filter(UserGroupRepoToPerm.repository == repo) \
            .filter(UserGroupRepoToPerm.users_group == group_name) \
            .scalar()
        if obj:
            self.sa.delete(obj)
            log.debug('Revoked perm to %s on %s', repo, group_name)
            action_logger_generic(
                'revoked permission from usergroup: {} on repo: {}'.format(
                    group_name, repo), namespace='security.repo')

    def delete_stats(self, repo_name):
        """
        removes stats for given repo

        :param repo_name:
        """
        repo = self._get_repo(repo_name)
        try:
            obj = self.sa.query(Statistics) \
                .filter(Statistics.repository == repo).scalar()
            if obj:
                self.sa.delete(obj)
        except Exception:
            log.error(traceback.format_exc())
            raise

    def add_repo_field(self, repo_name, field_key, field_label, field_value='',
                       field_type='str', field_desc=''):

        repo = self._get_repo(repo_name)

        new_field = RepositoryField()
        new_field.repository = repo
        new_field.field_key = field_key
        new_field.field_type = field_type  # python type
        new_field.field_value = field_value
        new_field.field_desc = field_desc
        new_field.field_label = field_label
        self.sa.add(new_field)
        return new_field

    def delete_repo_field(self, repo_name, field_key):
        repo = self._get_repo(repo_name)
        field = RepositoryField.get_by_key_name(field_key, repo)
        if field:
            self.sa.delete(field)

    def _create_filesystem_repo(self, repo_name, repo_type, repo_group,
                                clone_uri=None, repo_store_location=None,
                                use_global_config=False):
        """
        makes repository on filesystem. It's group aware means it'll create
        a repository within a group, and alter the paths accordingly of
        group location

        :param repo_name:
        :param alias:
        :param parent:
        :param clone_uri:
        :param repo_store_location:
        """
        from rhodecode.lib.utils import is_valid_repo, is_valid_repo_group
        from rhodecode.model.scm import ScmModel

        if Repository.NAME_SEP in repo_name:
            raise ValueError(
                'repo_name must not contain groups got `%s`' % repo_name)

        if isinstance(repo_group, RepoGroup):
            new_parent_path = os.sep.join(repo_group.full_path_splitted)
        else:
            new_parent_path = repo_group or ''

        if repo_store_location:
            _paths = [repo_store_location]
        else:
            _paths = [self.repos_path, new_parent_path, repo_name]
            # we need to make it str for mercurial
        repo_path = os.path.join(*map(lambda x: safe_str(x), _paths))

        # check if this path is not a repository
        if is_valid_repo(repo_path, self.repos_path):
            raise Exception('This path %s is a valid repository' % repo_path)

        # check if this path is a group
        if is_valid_repo_group(repo_path, self.repos_path):
            raise Exception('This path %s is a valid group' % repo_path)

        log.info('creating repo %s in %s from url: `%s`',
                 repo_name, safe_unicode(repo_path),
                 obfuscate_url_pw(clone_uri))

        backend = get_backend(repo_type)

        config_repo = None if use_global_config else repo_name
        if config_repo and new_parent_path:
            config_repo = Repository.NAME_SEP.join(
                (new_parent_path, config_repo))
        config = make_db_config(clear_session=False, repo=config_repo)
        config.set('extensions', 'largefiles', '')

        # patch and reset hooks section of UI config to not run any
        # hooks on creating remote repo
        config.clear_section('hooks')

        # TODO: johbo: Unify this, hardcoded "bare=True" does not look nice
        if repo_type == 'git':
            repo = backend(
                repo_path, config=config, create=True, src_url=clone_uri,
                bare=True)
        else:
            repo = backend(
                repo_path, config=config, create=True, src_url=clone_uri)

        ScmModel().install_hooks(repo, repo_type=repo_type)

        log.debug('Created repo %s with %s backend',
                  safe_unicode(repo_name), safe_unicode(repo_type))
        return repo

    def _rename_filesystem_repo(self, old, new):
        """
        renames repository on filesystem

        :param old: old name
        :param new: new name
        """
        log.info('renaming repo from %s to %s', old, new)

        old_path = os.path.join(self.repos_path, old)
        new_path = os.path.join(self.repos_path, new)
        if os.path.isdir(new_path):
            raise Exception(
                'Was trying to rename to already existing dir %s' % new_path
            )
        shutil.move(old_path, new_path)

    def _delete_filesystem_repo(self, repo):
        """
        removes repo from filesystem, the removal is acctually made by
        added rm__ prefix into dir, and rename internat .hg/.git dirs so this
        repository is no longer valid for rhodecode, can be undeleted later on
        by reverting the renames on this repository

        :param repo: repo object
        """
        rm_path = os.path.join(self.repos_path, repo.repo_name)
        repo_group = repo.group
        log.info("Removing repository %s", rm_path)
        # disable hg/git internal that it doesn't get detected as repo
        alias = repo.repo_type

        config = make_db_config(clear_session=False)
        config.set('extensions', 'largefiles', '')
        bare = getattr(repo.scm_instance(config=config), 'bare', False)

        # skip this for bare git repos
        if not bare:
            # disable VCS repo
            vcs_path = os.path.join(rm_path, '.%s' % alias)
            if os.path.exists(vcs_path):
                shutil.move(vcs_path, os.path.join(rm_path, 'rm__.%s' % alias))

        _now = datetime.now()
        _ms = str(_now.microsecond).rjust(6, '0')
        _d = 'rm__%s__%s' % (_now.strftime('%Y%m%d_%H%M%S_' + _ms),
                             repo.just_name)
        if repo_group:
            # if repository is in group, prefix the removal path with the group
            args = repo_group.full_path_splitted + [_d]
            _d = os.path.join(*args)

        if os.path.isdir(rm_path):
            shutil.move(rm_path, os.path.join(self.repos_path, _d))


class ReadmeFinder:
    """
    Utility which knows how to find a readme for a specific commit.

    The main idea is that this is a configurable algorithm. When creating an
    instance you can define parameters, currently only the `default_renderer`.
    Based on this configuration the method :meth:`search` behaves slightly
    different.
    """

    readme_re = re.compile(r'^readme(\.[^\.]+)?$', re.IGNORECASE)
    path_re = re.compile(r'^docs?', re.IGNORECASE)

    default_priorities = {
        None: 0,
        '.text': 2,
        '.txt': 3,
        '.rst': 1,
        '.rest': 2,
        '.md': 1,
        '.mkdn': 2,
        '.mdown': 3,
        '.markdown': 4,
    }

    path_priority = {
        'doc': 0,
        'docs': 1,
    }

    FALLBACK_PRIORITY = 99

    RENDERER_TO_EXTENSION = {
        'rst': ['.rst', '.rest'],
        'markdown': ['.md', 'mkdn', '.mdown', '.markdown'],
    }

    def __init__(self, default_renderer=None):
        self._default_renderer = default_renderer
        self._renderer_extensions = self.RENDERER_TO_EXTENSION.get(
            default_renderer, [])

    def search(self, commit, path='/'):
        """
        Find a readme in the given `commit`.
        """
        nodes = commit.get_nodes(path)
        matches = self._match_readmes(nodes)
        matches = self._sort_according_to_priority(matches)
        if matches:
            return matches[0].node

        paths = self._match_paths(nodes)
        paths = self._sort_paths_according_to_priority(paths)
        for path in paths:
            match = self.search(commit, path=path)
            if match:
                return match

        return None

    def _match_readmes(self, nodes):
        for node in nodes:
            if not node.is_file():
                continue
            path = node.path.rsplit('/', 1)[-1]
            match = self.readme_re.match(path)
            if match:
                extension = match.group(1)
                yield ReadmeMatch(node, match, self._priority(extension))

    def _match_paths(self, nodes):
        for node in nodes:
            if not node.is_dir():
                continue
            match = self.path_re.match(node.path)
            if match:
                yield node.path

    def _priority(self, extension):
        renderer_priority = (
            0 if extension in self._renderer_extensions else 1)
        extension_priority = self.default_priorities.get(
            extension, self.FALLBACK_PRIORITY)
        return (renderer_priority, extension_priority)

    def _sort_according_to_priority(self, matches):

        def priority_and_path(match):
            return (match.priority, match.path)

        return sorted(matches, key=priority_and_path)

    def _sort_paths_according_to_priority(self, paths):

        def priority_and_path(path):
            return (self.path_priority.get(path, self.FALLBACK_PRIORITY), path)

        return sorted(paths, key=priority_and_path)


class ReadmeMatch:

    def __init__(self, node, match, priority):
        self.node = node
        self._match = match
        self.priority = priority

    @property
    def path(self):
        return self.node.path

    def __repr__(self):
        return '<ReadmeMatch {} priority={}'.format(self.path, self.priority)
