# -*- coding: utf-8 -*-

# Copyright (C) 2010-2018 RhodeCode GmbH
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
authentication and permission libraries
"""

import os
import time
import inspect
import collections
import fnmatch
import hashlib
import itertools
import logging
import random
import traceback
from functools import wraps

import ipaddress

from pyramid.httpexceptions import HTTPForbidden, HTTPFound, HTTPNotFound
from sqlalchemy.orm.exc import ObjectDeletedError
from sqlalchemy.orm import joinedload
from zope.cachedescriptors.property import Lazy as LazyProperty

import rhodecode
from rhodecode.model import meta
from rhodecode.model.meta import Session
from rhodecode.model.user import UserModel
from rhodecode.model.db import (
    User, Repository, Permission, UserToPerm, UserGroupToPerm, UserGroupMember,
    UserIpMap, UserApiKeys, RepoGroup, UserGroup)
from rhodecode.lib import rc_cache
from rhodecode.lib.utils2 import safe_unicode, aslist, safe_str, md5, safe_int, sha1
from rhodecode.lib.utils import (
    get_repo_slug, get_repo_group_slug, get_user_group_slug)
from rhodecode.lib.caching_query import FromCache


if rhodecode.is_unix:
    import bcrypt

log = logging.getLogger(__name__)

csrf_token_key = "csrf_token"


class PasswordGenerator(object):
    """
    This is a simple class for generating password from different sets of
    characters
    usage::

        passwd_gen = PasswordGenerator()
        #print 8-letter password containing only big and small letters
            of alphabet
        passwd_gen.gen_password(8, passwd_gen.ALPHABETS_BIG_SMALL)
    """
    ALPHABETS_NUM = r'''1234567890'''
    ALPHABETS_SMALL = r'''qwertyuiopasdfghjklzxcvbnm'''
    ALPHABETS_BIG = r'''QWERTYUIOPASDFGHJKLZXCVBNM'''
    ALPHABETS_SPECIAL = r'''`-=[]\;',./~!@#$%^&*()_+{}|:"<>?'''
    ALPHABETS_FULL = ALPHABETS_BIG + ALPHABETS_SMALL \
        + ALPHABETS_NUM + ALPHABETS_SPECIAL
    ALPHABETS_ALPHANUM = ALPHABETS_BIG + ALPHABETS_SMALL + ALPHABETS_NUM
    ALPHABETS_BIG_SMALL = ALPHABETS_BIG + ALPHABETS_SMALL
    ALPHABETS_ALPHANUM_BIG = ALPHABETS_BIG + ALPHABETS_NUM
    ALPHABETS_ALPHANUM_SMALL = ALPHABETS_SMALL + ALPHABETS_NUM

    def __init__(self, passwd=''):
        self.passwd = passwd

    def gen_password(self, length, type_=None):
        if type_ is None:
            type_ = self.ALPHABETS_FULL
        self.passwd = ''.join([random.choice(type_) for _ in range(length)])
        return self.passwd


class _RhodeCodeCryptoBase(object):
    ENC_PREF = None

    def hash_create(self, str_):
        """
        hash the string using

        :param str_: password to hash
        """
        raise NotImplementedError

    def hash_check_with_upgrade(self, password, hashed):
        """
        Returns tuple in which first element is boolean that states that
        given password matches it's hashed version, and the second is new hash
        of the password, in case this password should be migrated to new
        cipher.
        """
        checked_hash = self.hash_check(password, hashed)
        return checked_hash, None

    def hash_check(self, password, hashed):
        """
        Checks matching password with it's hashed value.

        :param password: password
        :param hashed: password in hashed form
        """
        raise NotImplementedError

    def _assert_bytes(self, value):
        """
        Passing in an `unicode` object can lead to hard to detect issues
        if passwords contain non-ascii characters.  Doing a type check
        during runtime, so that such mistakes are detected early on.
        """
        if not isinstance(value, str):
            raise TypeError(
                "Bytestring required as input, got %r." % (value, ))


class _RhodeCodeCryptoBCrypt(_RhodeCodeCryptoBase):
    ENC_PREF = ('$2a$10', '$2b$10')

    def hash_create(self, str_):
        self._assert_bytes(str_)
        return bcrypt.hashpw(str_, bcrypt.gensalt(10))

    def hash_check_with_upgrade(self, password, hashed):
        """
        Returns tuple in which first element is boolean that states that
        given password matches it's hashed version, and the second is new hash
        of the password, in case this password should be migrated to new
        cipher.

        This implements special upgrade logic which works like that:
         - check if the given password == bcrypted hash, if yes then we
           properly used password and it was already in bcrypt. Proceed
           without any changes
         - if bcrypt hash check is not working try with sha256. If hash compare
           is ok, it means we using correct but old hashed password. indicate
           hash change and proceed
        """

        new_hash = None

        # regular pw check
        password_match_bcrypt = self.hash_check(password, hashed)

        # now we want to know if the password was maybe from sha256
        # basically calling _RhodeCodeCryptoSha256().hash_check()
        if not password_match_bcrypt:
            if _RhodeCodeCryptoSha256().hash_check(password, hashed):
                new_hash = self.hash_create(password)  # make new bcrypt hash
                password_match_bcrypt = True

        return password_match_bcrypt, new_hash

    def hash_check(self, password, hashed):
        """
        Checks matching password with it's hashed value.

        :param password: password
        :param hashed: password in hashed form
        """
        self._assert_bytes(password)
        try:
            return bcrypt.hashpw(password, hashed) == hashed
        except ValueError as e:
            # we're having a invalid salt here probably, we should not crash
            # just return with False as it would be a wrong password.
            log.debug('Failed to check password hash using bcrypt %s',
                      safe_str(e))

        return False


class _RhodeCodeCryptoSha256(_RhodeCodeCryptoBase):
    ENC_PREF = '_'

    def hash_create(self, str_):
        self._assert_bytes(str_)
        return hashlib.sha256(str_).hexdigest()

    def hash_check(self, password, hashed):
        """
        Checks matching password with it's hashed value.

        :param password: password
        :param hashed: password in hashed form
        """
        self._assert_bytes(password)
        return hashlib.sha256(password).hexdigest() == hashed


class _RhodeCodeCryptoTest(_RhodeCodeCryptoBase):
    ENC_PREF = '_'

    def hash_create(self, str_):
        self._assert_bytes(str_)
        return sha1(str_)

    def hash_check(self, password, hashed):
        """
        Checks matching password with it's hashed value.

        :param password: password
        :param hashed: password in hashed form
        """
        self._assert_bytes(password)
        return sha1(password) == hashed


def crypto_backend():
    """
    Return the matching crypto backend.

    Selection is based on if we run tests or not, we pick sha1-test backend to run
    tests faster since BCRYPT is expensive to calculate
    """
    if rhodecode.is_test:
        RhodeCodeCrypto = _RhodeCodeCryptoTest()
    else:
        RhodeCodeCrypto = _RhodeCodeCryptoBCrypt()

    return RhodeCodeCrypto


def get_crypt_password(password):
    """
    Create the hash of `password` with the active crypto backend.

    :param password: The cleartext password.
    :type password: unicode
    """
    password = safe_str(password)
    return crypto_backend().hash_create(password)


def check_password(password, hashed):
    """
    Check if the value in `password` matches the hash in `hashed`.

    :param password: The cleartext password.
    :type password: unicode

    :param hashed: The expected hashed version of the password.
    :type hashed: The hash has to be passed in in text representation.
    """
    password = safe_str(password)
    return crypto_backend().hash_check(password, hashed)


def generate_auth_token(data, salt=None):
    """
    Generates API KEY from given string
    """

    if salt is None:
        salt = os.urandom(16)
    return hashlib.sha1(safe_str(data) + salt).hexdigest()


def get_came_from(request):
    """
    get query_string+path from request sanitized after removing auth_token
    """
    _req = request

    path = _req.path
    if 'auth_token' in _req.GET:
        # sanitize the request and remove auth_token for redirection
        _req.GET.pop('auth_token')
    qs = _req.query_string
    if qs:
        path += '?' + qs

    return path


class CookieStoreWrapper(object):

    def __init__(self, cookie_store):
        self.cookie_store = cookie_store

    def __repr__(self):
        return 'CookieStore<%s>' % (self.cookie_store)

    def get(self, key, other=None):
        if isinstance(self.cookie_store, dict):
            return self.cookie_store.get(key, other)
        elif isinstance(self.cookie_store, AuthUser):
            return self.cookie_store.__dict__.get(key, other)


def _cached_perms_data(user_id, scope, user_is_admin,
                       user_inherit_default_permissions, explicit, algo,
                       calculate_super_admin):

    permissions = PermissionCalculator(
        user_id, scope, user_is_admin, user_inherit_default_permissions,
        explicit, algo, calculate_super_admin)
    return permissions.calculate()


class PermOrigin(object):
    SUPER_ADMIN = 'superadmin'

    REPO_USER = 'user:%s'
    REPO_USERGROUP = 'usergroup:%s'
    REPO_OWNER = 'repo.owner'
    REPO_DEFAULT = 'repo.default'
    REPO_DEFAULT_NO_INHERIT = 'repo.default.no.inherit'
    REPO_PRIVATE = 'repo.private'

    REPOGROUP_USER = 'user:%s'
    REPOGROUP_USERGROUP = 'usergroup:%s'
    REPOGROUP_OWNER = 'group.owner'
    REPOGROUP_DEFAULT = 'group.default'
    REPOGROUP_DEFAULT_NO_INHERIT = 'group.default.no.inherit'

    USERGROUP_USER = 'user:%s'
    USERGROUP_USERGROUP = 'usergroup:%s'
    USERGROUP_OWNER = 'usergroup.owner'
    USERGROUP_DEFAULT = 'usergroup.default'
    USERGROUP_DEFAULT_NO_INHERIT = 'usergroup.default.no.inherit'


class PermOriginDict(dict):
    """
    A special dict used for tracking permissions along with their origins.

    `__setitem__` has been overridden to expect a tuple(perm, origin)
    `__getitem__` will return only the perm
    `.perm_origin_stack` will return the stack of (perm, origin) set per key

    >>> perms = PermOriginDict()
    >>> perms['resource'] = 'read', 'default'
    >>> perms['resource']
    'read'
    >>> perms['resource'] = 'write', 'admin'
    >>> perms['resource']
    'write'
    >>> perms.perm_origin_stack
    {'resource': [('read', 'default'), ('write', 'admin')]}
    """

    def __init__(self, *args, **kw):
        dict.__init__(self, *args, **kw)
        self.perm_origin_stack = collections.OrderedDict()

    def __setitem__(self, key, (perm, origin)):
        self.perm_origin_stack.setdefault(key, []).append(
            (perm, origin))
        dict.__setitem__(self, key, perm)


class BranchPermOriginDict(PermOriginDict):
    """
    Dedicated branch permissions dict, with tracking of patterns and origins.

    >>> perms = BranchPermOriginDict()
    >>> perms['resource'] = '*pattern', 'read', 'default'
    >>> perms['resource']
    {'*pattern': 'read'}
    >>> perms['resource'] = '*pattern', 'write', 'admin'
    >>> perms['resource']
    {'*pattern': 'write'}
    >>> perms.perm_origin_stack
    {'resource': {'*pattern': [('read', 'default'), ('write', 'admin')]}}
    """
    def __setitem__(self, key, (pattern, perm, origin)):

        self.perm_origin_stack.setdefault(key, {}) \
            .setdefault(pattern, []).append((perm, origin))

        if key in self:
            self[key].__setitem__(pattern, perm)
        else:
            patterns = collections.OrderedDict()
            patterns[pattern] = perm
            dict.__setitem__(self, key, patterns)


class PermissionCalculator(object):

    def __init__(
            self, user_id, scope, user_is_admin,
            user_inherit_default_permissions, explicit, algo,
            calculate_super_admin_as_user=False):

        self.user_id = user_id
        self.user_is_admin = user_is_admin
        self.inherit_default_permissions = user_inherit_default_permissions
        self.explicit = explicit
        self.algo = algo
        self.calculate_super_admin_as_user = calculate_super_admin_as_user

        scope = scope or {}
        self.scope_repo_id = scope.get('repo_id')
        self.scope_repo_group_id = scope.get('repo_group_id')
        self.scope_user_group_id = scope.get('user_group_id')

        self.default_user_id = User.get_default_user(cache=True).user_id

        self.permissions_repositories = PermOriginDict()
        self.permissions_repository_groups = PermOriginDict()
        self.permissions_user_groups = PermOriginDict()
        self.permissions_repository_branches = BranchPermOriginDict()
        self.permissions_global = set()

        self.default_repo_perms = Permission.get_default_repo_perms(
            self.default_user_id, self.scope_repo_id)
        self.default_repo_groups_perms = Permission.get_default_group_perms(
            self.default_user_id, self.scope_repo_group_id)
        self.default_user_group_perms = \
            Permission.get_default_user_group_perms(
                self.default_user_id, self.scope_user_group_id)

        # default branch perms
        self.default_branch_repo_perms = \
            Permission.get_default_repo_branch_perms(
                self.default_user_id, self.scope_repo_id)

    def calculate(self):
        if self.user_is_admin and not self.calculate_super_admin_as_user:
            return self._calculate_admin_permissions()

        self._calculate_global_default_permissions()
        self._calculate_global_permissions()
        self._calculate_default_permissions()
        self._calculate_repository_permissions()
        self._calculate_repository_branch_permissions()
        self._calculate_repository_group_permissions()
        self._calculate_user_group_permissions()
        return self._permission_structure()

    def _calculate_admin_permissions(self):
        """
        admin user have all default rights for repositories
        and groups set to admin
        """
        self.permissions_global.add('hg.admin')
        self.permissions_global.add('hg.create.write_on_repogroup.true')

        # repositories
        for perm in self.default_repo_perms:
            r_k = perm.UserRepoToPerm.repository.repo_name
            p = 'repository.admin'
            self.permissions_repositories[r_k] = p, PermOrigin.SUPER_ADMIN

        # repository groups
        for perm in self.default_repo_groups_perms:
            rg_k = perm.UserRepoGroupToPerm.group.group_name
            p = 'group.admin'
            self.permissions_repository_groups[rg_k] = p, PermOrigin.SUPER_ADMIN

        # user groups
        for perm in self.default_user_group_perms:
            u_k = perm.UserUserGroupToPerm.user_group.users_group_name
            p = 'usergroup.admin'
            self.permissions_user_groups[u_k] = p, PermOrigin.SUPER_ADMIN

        # branch permissions
        # since super-admin also can have custom rule permissions
        # we *always* need to calculate those inherited from default, and also explicit
        self._calculate_default_permissions_repository_branches(
            user_inherit_object_permissions=False)
        self._calculate_repository_branch_permissions()

        return self._permission_structure()

    def _calculate_global_default_permissions(self):
        """
        global permissions taken from the default user
        """
        default_global_perms = UserToPerm.query()\
            .filter(UserToPerm.user_id == self.default_user_id)\
            .options(joinedload(UserToPerm.permission))

        for perm in default_global_perms:
            self.permissions_global.add(perm.permission.permission_name)

        if self.user_is_admin:
            self.permissions_global.add('hg.admin')
            self.permissions_global.add('hg.create.write_on_repogroup.true')

    def _calculate_global_permissions(self):
        """
        Set global system permissions with user permissions or permissions
        taken from the user groups of the current user.

        The permissions include repo creating, repo group creating, forking
        etc.
        """

        # now we read the defined permissions and overwrite what we have set
        # before those can be configured from groups or users explicitly.

        # In case we want to extend this list we should make sure
        # this is in sync with User.DEFAULT_USER_PERMISSIONS definitions
        _configurable = frozenset([
            'hg.fork.none', 'hg.fork.repository',
            'hg.create.none', 'hg.create.repository',
            'hg.usergroup.create.false', 'hg.usergroup.create.true',
            'hg.repogroup.create.false', 'hg.repogroup.create.true',
            'hg.create.write_on_repogroup.false', 'hg.create.write_on_repogroup.true',
            'hg.inherit_default_perms.false', 'hg.inherit_default_perms.true'
        ])

        # USER GROUPS comes first user group global permissions
        user_perms_from_users_groups = Session().query(UserGroupToPerm)\
            .options(joinedload(UserGroupToPerm.permission))\
            .join((UserGroupMember, UserGroupToPerm.users_group_id ==
                   UserGroupMember.users_group_id))\
            .filter(UserGroupMember.user_id == self.user_id)\
            .order_by(UserGroupToPerm.users_group_id)\
            .all()

        # need to group here by groups since user can be in more than
        # one group, so we get all groups
        _explicit_grouped_perms = [
            [x, list(y)] for x, y in
            itertools.groupby(user_perms_from_users_groups,
                              lambda _x: _x.users_group)]

        for gr, perms in _explicit_grouped_perms:
            # since user can be in multiple groups iterate over them and
            # select the lowest permissions first (more explicit)
            # TODO(marcink): do this^^

            # group doesn't inherit default permissions so we actually set them
            if not gr.inherit_default_permissions:
                # NEED TO IGNORE all previously set configurable permissions
                # and replace them with explicitly set from this user
                # group permissions
                self.permissions_global = self.permissions_global.difference(
                    _configurable)
                for perm in perms:
                    self.permissions_global.add(perm.permission.permission_name)

        # user explicit global permissions
        user_perms = Session().query(UserToPerm)\
            .options(joinedload(UserToPerm.permission))\
            .filter(UserToPerm.user_id == self.user_id).all()

        if not self.inherit_default_permissions:
            # NEED TO IGNORE all configurable permissions and
            # replace them with explicitly set from this user permissions
            self.permissions_global = self.permissions_global.difference(
                _configurable)
            for perm in user_perms:
                self.permissions_global.add(perm.permission.permission_name)

    def _calculate_default_permissions_repositories(self, user_inherit_object_permissions):
        for perm in self.default_repo_perms:
            r_k = perm.UserRepoToPerm.repository.repo_name
            p = perm.Permission.permission_name
            o = PermOrigin.REPO_DEFAULT
            self.permissions_repositories[r_k] = p, o

            # if we decide this user isn't inheriting permissions from
            # default user we set him to .none so only explicit
            # permissions work
            if not user_inherit_object_permissions:
                p = 'repository.none'
                o = PermOrigin.REPO_DEFAULT_NO_INHERIT
                self.permissions_repositories[r_k] = p, o

            if perm.Repository.private and not (
                    perm.Repository.user_id == self.user_id):
                # disable defaults for private repos,
                p = 'repository.none'
                o = PermOrigin.REPO_PRIVATE
                self.permissions_repositories[r_k] = p, o

            elif perm.Repository.user_id == self.user_id:
                # set admin if owner
                p = 'repository.admin'
                o = PermOrigin.REPO_OWNER
                self.permissions_repositories[r_k] = p, o

            if self.user_is_admin:
                p = 'repository.admin'
                o = PermOrigin.SUPER_ADMIN
                self.permissions_repositories[r_k] = p, o

    def _calculate_default_permissions_repository_branches(self, user_inherit_object_permissions):
        for perm in self.default_branch_repo_perms:

            r_k = perm.UserRepoToPerm.repository.repo_name
            p = perm.Permission.permission_name
            pattern = perm.UserToRepoBranchPermission.branch_pattern
            o = PermOrigin.REPO_USER % perm.UserRepoToPerm.user.username

            if not self.explicit:
                # TODO(marcink): fix this for multiple entries
                cur_perm = self.permissions_repository_branches.get(r_k) or 'branch.none'
                p = self._choose_permission(p, cur_perm)

            # NOTE(marcink): register all pattern/perm instances in this
            # special dict that aggregates entries
            self.permissions_repository_branches[r_k] = pattern, p, o

    def _calculate_default_permissions_repository_groups(self, user_inherit_object_permissions):
        for perm in self.default_repo_groups_perms:
            rg_k = perm.UserRepoGroupToPerm.group.group_name
            p = perm.Permission.permission_name
            o = PermOrigin.REPOGROUP_DEFAULT
            self.permissions_repository_groups[rg_k] = p, o

            # if we decide this user isn't inheriting permissions from default
            # user we set him to .none so only explicit permissions work
            if not user_inherit_object_permissions:
                p = 'group.none'
                o = PermOrigin.REPOGROUP_DEFAULT_NO_INHERIT
                self.permissions_repository_groups[rg_k] = p, o

            if perm.RepoGroup.user_id == self.user_id:
                # set admin if owner
                p = 'group.admin'
                o = PermOrigin.REPOGROUP_OWNER
                self.permissions_repository_groups[rg_k] = p, o

            if self.user_is_admin:
                p = 'group.admin'
                o = PermOrigin.SUPER_ADMIN
                self.permissions_repository_groups[rg_k] = p, o

    def _calculate_default_permissions_user_groups(self, user_inherit_object_permissions):
        for perm in self.default_user_group_perms:
            u_k = perm.UserUserGroupToPerm.user_group.users_group_name
            p = perm.Permission.permission_name
            o = PermOrigin.USERGROUP_DEFAULT
            self.permissions_user_groups[u_k] = p, o

            # if we decide this user isn't inheriting permissions from default
            # user we set him to .none so only explicit permissions work
            if not user_inherit_object_permissions:
                p = 'usergroup.none'
                o = PermOrigin.USERGROUP_DEFAULT_NO_INHERIT
                self.permissions_user_groups[u_k] = p, o

            if perm.UserGroup.user_id == self.user_id:
                # set admin if owner
                p = 'usergroup.admin'
                o = PermOrigin.USERGROUP_OWNER
                self.permissions_user_groups[u_k] = p, o

            if self.user_is_admin:
                p = 'usergroup.admin'
                o = PermOrigin.SUPER_ADMIN
                self.permissions_user_groups[u_k] = p, o

    def _calculate_default_permissions(self):
        """
        Set default user permissions for repositories, repository branches,
        repository groups, user groups taken from the default user.

        Calculate inheritance of object permissions based on what we have now
        in GLOBAL permissions. We check if .false is in GLOBAL since this is
        explicitly set. Inherit is the opposite of .false being there.

        .. note::

           the syntax is little bit odd but what we need to check here is
           the opposite of .false permission being in the list so even for
           inconsistent state when both .true/.false is there
           .false is more important

        """
        user_inherit_object_permissions = not ('hg.inherit_default_perms.false'
                                               in self.permissions_global)

        # default permissions inherited from `default` user permissions
        self._calculate_default_permissions_repositories(
            user_inherit_object_permissions)

        self._calculate_default_permissions_repository_branches(
            user_inherit_object_permissions)

        self._calculate_default_permissions_repository_groups(
            user_inherit_object_permissions)

        self._calculate_default_permissions_user_groups(
            user_inherit_object_permissions)

    def _calculate_repository_permissions(self):
        """
        Repository permissions for the current user.

        Check if the user is part of user groups for this repository and
        fill in the permission from it. `_choose_permission` decides of which
        permission should be selected based on selected method.
        """

        # user group for repositories permissions
        user_repo_perms_from_user_group = Permission\
            .get_default_repo_perms_from_user_group(
                self.user_id, self.scope_repo_id)

        multiple_counter = collections.defaultdict(int)
        for perm in user_repo_perms_from_user_group:
            r_k = perm.UserGroupRepoToPerm.repository.repo_name
            multiple_counter[r_k] += 1
            p = perm.Permission.permission_name
            o = PermOrigin.REPO_USERGROUP % perm.UserGroupRepoToPerm\
                .users_group.users_group_name

            if multiple_counter[r_k] > 1:
                cur_perm = self.permissions_repositories[r_k]
                p = self._choose_permission(p, cur_perm)

            self.permissions_repositories[r_k] = p, o

            if perm.Repository.user_id == self.user_id:
                # set admin if owner
                p = 'repository.admin'
                o = PermOrigin.REPO_OWNER
                self.permissions_repositories[r_k] = p, o

            if self.user_is_admin:
                p = 'repository.admin'
                o = PermOrigin.SUPER_ADMIN
                self.permissions_repositories[r_k] = p, o

        # user explicit permissions for repositories, overrides any specified
        # by the group permission
        user_repo_perms = Permission.get_default_repo_perms(
            self.user_id, self.scope_repo_id)
        for perm in user_repo_perms:
            r_k = perm.UserRepoToPerm.repository.repo_name
            p = perm.Permission.permission_name
            o = PermOrigin.REPO_USER % perm.UserRepoToPerm.user.username

            if not self.explicit:
                cur_perm = self.permissions_repositories.get(
                    r_k, 'repository.none')
                p = self._choose_permission(p, cur_perm)

            self.permissions_repositories[r_k] = p, o

            if perm.Repository.user_id == self.user_id:
                # set admin if owner
                p = 'repository.admin'
                o = PermOrigin.REPO_OWNER
                self.permissions_repositories[r_k] = p, o

            if self.user_is_admin:
                p = 'repository.admin'
                o = PermOrigin.SUPER_ADMIN
                self.permissions_repositories[r_k] = p, o

    def _calculate_repository_branch_permissions(self):
        # user group for repositories permissions
        user_repo_branch_perms_from_user_group = Permission\
            .get_default_repo_branch_perms_from_user_group(
                self.user_id, self.scope_repo_id)

        multiple_counter = collections.defaultdict(int)
        for perm in user_repo_branch_perms_from_user_group:
            r_k = perm.UserGroupRepoToPerm.repository.repo_name
            p = perm.Permission.permission_name
            pattern = perm.UserGroupToRepoBranchPermission.branch_pattern
            o = PermOrigin.REPO_USERGROUP % perm.UserGroupRepoToPerm\
                .users_group.users_group_name

            multiple_counter[r_k] += 1
            if multiple_counter[r_k] > 1:
                # TODO(marcink): fix this for multi branch support, and multiple entries
                cur_perm = self.permissions_repository_branches[r_k]
                p = self._choose_permission(p, cur_perm)

            self.permissions_repository_branches[r_k] = pattern, p, o

        # user explicit branch permissions for repositories, overrides
        # any specified by the group permission
        user_repo_branch_perms = Permission.get_default_repo_branch_perms(
            self.user_id, self.scope_repo_id)

        for perm in user_repo_branch_perms:

            r_k = perm.UserRepoToPerm.repository.repo_name
            p = perm.Permission.permission_name
            pattern = perm.UserToRepoBranchPermission.branch_pattern
            o = PermOrigin.REPO_USER % perm.UserRepoToPerm.user.username

            if not self.explicit:
                # TODO(marcink): fix this for multiple entries
                cur_perm = self.permissions_repository_branches.get(r_k) or 'branch.none'
                p = self._choose_permission(p, cur_perm)

            # NOTE(marcink): register all pattern/perm instances in this
            # special dict that aggregates entries
            self.permissions_repository_branches[r_k] = pattern, p, o

    def _calculate_repository_group_permissions(self):
        """
        Repository group permissions for the current user.

        Check if the user is part of user groups for repository groups and
        fill in the permissions from it. `_choose_permission` decides of which
        permission should be selected based on selected method.
        """
        # user group for repo groups permissions
        user_repo_group_perms_from_user_group = Permission\
            .get_default_group_perms_from_user_group(
                self.user_id, self.scope_repo_group_id)

        multiple_counter = collections.defaultdict(int)
        for perm in user_repo_group_perms_from_user_group:
            rg_k = perm.UserGroupRepoGroupToPerm.group.group_name
            multiple_counter[rg_k] += 1
            o = PermOrigin.REPOGROUP_USERGROUP % perm.UserGroupRepoGroupToPerm\
                .users_group.users_group_name
            p = perm.Permission.permission_name

            if multiple_counter[rg_k] > 1:
                cur_perm = self.permissions_repository_groups[rg_k]
                p = self._choose_permission(p, cur_perm)
            self.permissions_repository_groups[rg_k] = p, o

            if perm.RepoGroup.user_id == self.user_id:
                # set admin if owner, even for member of other user group
                p = 'group.admin'
                o = PermOrigin.REPOGROUP_OWNER
                self.permissions_repository_groups[rg_k] = p, o

            if self.user_is_admin:
                p = 'group.admin'
                o = PermOrigin.SUPER_ADMIN
                self.permissions_repository_groups[rg_k] = p, o

        # user explicit permissions for repository groups
        user_repo_groups_perms = Permission.get_default_group_perms(
            self.user_id, self.scope_repo_group_id)
        for perm in user_repo_groups_perms:
            rg_k = perm.UserRepoGroupToPerm.group.group_name
            o = PermOrigin.REPOGROUP_USER % perm.UserRepoGroupToPerm\
                .user.username
            p = perm.Permission.permission_name

            if not self.explicit:
                cur_perm = self.permissions_repository_groups.get(
                    rg_k, 'group.none')
                p = self._choose_permission(p, cur_perm)

            self.permissions_repository_groups[rg_k] = p, o

            if perm.RepoGroup.user_id == self.user_id:
                # set admin if owner
                p = 'group.admin'
                o = PermOrigin.REPOGROUP_OWNER
                self.permissions_repository_groups[rg_k] = p, o

            if self.user_is_admin:
                p = 'group.admin'
                o = PermOrigin.SUPER_ADMIN
                self.permissions_repository_groups[rg_k] = p, o

    def _calculate_user_group_permissions(self):
        """
        User group permissions for the current user.
        """
        # user group for user group permissions
        user_group_from_user_group = Permission\
            .get_default_user_group_perms_from_user_group(
                self.user_id, self.scope_user_group_id)

        multiple_counter = collections.defaultdict(int)
        for perm in user_group_from_user_group:
            ug_k = perm.UserGroupUserGroupToPerm\
                .target_user_group.users_group_name
            multiple_counter[ug_k] += 1
            o = PermOrigin.USERGROUP_USERGROUP % perm.UserGroupUserGroupToPerm\
                .user_group.users_group_name
            p = perm.Permission.permission_name

            if multiple_counter[ug_k] > 1:
                cur_perm = self.permissions_user_groups[ug_k]
                p = self._choose_permission(p, cur_perm)

            self.permissions_user_groups[ug_k] = p, o

            if perm.UserGroup.user_id == self.user_id:
                # set admin if owner, even for member of other user group
                p = 'usergroup.admin'
                o = PermOrigin.USERGROUP_OWNER
                self.permissions_user_groups[ug_k] = p, o

            if self.user_is_admin:
                p = 'usergroup.admin'
                o = PermOrigin.SUPER_ADMIN
                self.permissions_user_groups[ug_k] = p, o

        # user explicit permission for user groups
        user_user_groups_perms = Permission.get_default_user_group_perms(
            self.user_id, self.scope_user_group_id)
        for perm in user_user_groups_perms:
            ug_k = perm.UserUserGroupToPerm.user_group.users_group_name
            o = PermOrigin.USERGROUP_USER % perm.UserUserGroupToPerm\
                .user.username
            p = perm.Permission.permission_name

            if not self.explicit:
                cur_perm = self.permissions_user_groups.get(
                    ug_k, 'usergroup.none')
                p = self._choose_permission(p, cur_perm)

            self.permissions_user_groups[ug_k] = p, o

            if perm.UserGroup.user_id == self.user_id:
                # set admin if owner
                p = 'usergroup.admin'
                o = PermOrigin.USERGROUP_OWNER
                self.permissions_user_groups[ug_k] = p, o

            if self.user_is_admin:
                p = 'usergroup.admin'
                o = PermOrigin.SUPER_ADMIN
                self.permissions_user_groups[ug_k] = p, o

    def _choose_permission(self, new_perm, cur_perm):
        new_perm_val = Permission.PERM_WEIGHTS[new_perm]
        cur_perm_val = Permission.PERM_WEIGHTS[cur_perm]
        if self.algo == 'higherwin':
            if new_perm_val > cur_perm_val:
                return new_perm
            return cur_perm
        elif self.algo == 'lowerwin':
            if new_perm_val < cur_perm_val:
                return new_perm
            return cur_perm

    def _permission_structure(self):
        return {
            'global': self.permissions_global,
            'repositories': self.permissions_repositories,
            'repository_branches': self.permissions_repository_branches,
            'repositories_groups': self.permissions_repository_groups,
            'user_groups': self.permissions_user_groups,
        }


def allowed_auth_token_access(view_name, auth_token, whitelist=None):
    """
    Check if given controller_name is in whitelist of auth token access
    """
    if not whitelist:
        from rhodecode import CONFIG
        whitelist = aslist(
            CONFIG.get('api_access_controllers_whitelist'), sep=',')
    # backward compat translation
    compat = {
        # old controller, new VIEW
        'ChangesetController:*': 'RepoCommitsView:*',
        'ChangesetController:changeset_patch': 'RepoCommitsView:repo_commit_patch',
        'ChangesetController:changeset_raw': 'RepoCommitsView:repo_commit_raw',
        'FilesController:raw': 'RepoCommitsView:repo_commit_raw',
        'FilesController:archivefile': 'RepoFilesView:repo_archivefile',
        'GistsController:*': 'GistView:*',
    }

    log.debug(
        'Allowed views for AUTH TOKEN access: %s', whitelist)
    auth_token_access_valid = False

    for entry in whitelist:
        token_match = True
        if entry in compat:
            # translate from old Controllers to Pyramid Views
            entry = compat[entry]

        if '@' in entry:
            # specific AuthToken
            entry, allowed_token = entry.split('@', 1)
            token_match = auth_token == allowed_token

        if fnmatch.fnmatch(view_name, entry) and token_match:
            auth_token_access_valid = True
            break

    if auth_token_access_valid:
        log.debug('view: `%s` matches entry in whitelist: %s',
                  view_name, whitelist)

    else:
        msg = ('view: `%s` does *NOT* match any entry in whitelist: %s'
               % (view_name, whitelist))
        if auth_token:
            # if we use auth token key and don't have access it's a warning
            log.warning(msg)
        else:
            log.debug(msg)

    return auth_token_access_valid


class AuthUser(object):
    """
    A simple object that handles all attributes of user in RhodeCode

    It does lookup based on API key,given user, or user present in session
    Then it fills all required information for such user. It also checks if
    anonymous access is enabled and if so, it returns default user as logged in
    """
    GLOBAL_PERMS = [x[0] for x in Permission.PERMS]

    def __init__(self, user_id=None, api_key=None, username=None, ip_addr=None):

        self.user_id = user_id
        self._api_key = api_key

        self.api_key = None
        self.username = username
        self.ip_addr = ip_addr
        self.name = ''
        self.lastname = ''
        self.first_name = ''
        self.last_name = ''
        self.email = ''
        self.is_authenticated = False
        self.admin = False
        self.inherit_default_permissions = False
        self.password = ''

        self.anonymous_user = None  # propagated on propagate_data
        self.propagate_data()
        self._instance = None
        self._permissions_scoped_cache = {}  # used to bind scoped calculation

    @LazyProperty
    def permissions(self):
        return self.get_perms(user=self, cache=None)

    @LazyProperty
    def permissions_safe(self):
        """
        Filtered permissions excluding not allowed repositories
        """
        perms = self.get_perms(user=self, cache=None)

        perms['repositories'] = {
            k: v for k, v in perms['repositories'].items()
            if v != 'repository.none'}
        perms['repositories_groups'] = {
            k: v for k, v in perms['repositories_groups'].items()
            if v != 'group.none'}
        perms['user_groups'] = {
            k: v for k, v in perms['user_groups'].items()
            if v != 'usergroup.none'}
        perms['repository_branches'] = {
            k: v for k, v in perms['repository_branches'].iteritems()
            if v != 'branch.none'}
        return perms

    @LazyProperty
    def permissions_full_details(self):
        return self.get_perms(
            user=self, cache=None, calculate_super_admin=True)

    def permissions_with_scope(self, scope):
        """
        Call the get_perms function with scoped data. The scope in that function
        narrows the SQL calls to the given ID of objects resulting in fetching
        Just particular permission we want to obtain. If scope is an empty dict
        then it basically narrows the scope to GLOBAL permissions only.

        :param scope: dict
        """
        if 'repo_name' in scope:
            obj = Repository.get_by_repo_name(scope['repo_name'])
            if obj:
                scope['repo_id'] = obj.repo_id
        _scope = collections.OrderedDict()
        _scope['repo_id'] = -1
        _scope['user_group_id'] = -1
        _scope['repo_group_id'] = -1

        for k in sorted(scope.keys()):
            _scope[k] = scope[k]

        # store in cache to mimic how the @LazyProperty works,
        # the difference here is that we use the unique key calculated
        # from params and values
        return self.get_perms(user=self, cache=None, scope=_scope)

    def get_instance(self):
        return User.get(self.user_id)

    def propagate_data(self):
        """
        Fills in user data and propagates values to this instance. Maps fetched
        user attributes to this class instance attributes
        """
        log.debug('AuthUser: starting data propagation for new potential user')
        user_model = UserModel()
        anon_user = self.anonymous_user = User.get_default_user(cache=True)
        is_user_loaded = False

        # lookup by userid
        if self.user_id is not None and self.user_id != anon_user.user_id:
            log.debug('Trying Auth User lookup by USER ID: `%s`', self.user_id)
            is_user_loaded = user_model.fill_data(self, user_id=self.user_id)

        # try go get user by api key
        elif self._api_key and self._api_key != anon_user.api_key:
            log.debug('Trying Auth User lookup by API KEY: `%s`', self._api_key)
            is_user_loaded = user_model.fill_data(self, api_key=self._api_key)

        # lookup by username
        elif self.username:
            log.debug('Trying Auth User lookup by USER NAME: `%s`', self.username)
            is_user_loaded = user_model.fill_data(self, username=self.username)
        else:
            log.debug('No data in %s that could been used to log in', self)

        if not is_user_loaded:
            log.debug(
                'Failed to load user. Fallback to default user %s', anon_user)
            # if we cannot authenticate user try anonymous
            if anon_user.active:
                log.debug('default user is active, using it as a session user')
                user_model.fill_data(self, user_id=anon_user.user_id)
                # then we set this user is logged in
                self.is_authenticated = True
            else:
                log.debug('default user is NOT active')
                # in case of disabled anonymous user we reset some of the
                # parameters so such user is "corrupted", skipping the fill_data
                for attr in ['user_id', 'username', 'admin', 'active']:
                    setattr(self, attr, None)
                self.is_authenticated = False

        if not self.username:
            self.username = 'None'

        log.debug('AuthUser: propagated user is now %s', self)

    def get_perms(self, user, scope=None, explicit=True, algo='higherwin',
                  calculate_super_admin=False, cache=None):
        """
        Fills user permission attribute with permissions taken from database
        works for permissions given for repositories, and for permissions that
        are granted to groups

        :param user: instance of User object from database
        :param explicit: In case there are permissions both for user and a group
            that user is part of, explicit flag will defiine if user will
            explicitly override permissions from group, if it's False it will
            make decision based on the algo
        :param algo: algorithm to decide what permission should be choose if
            it's multiple defined, eg user in two different groups. It also
            decides if explicit flag is turned off how to specify the permission
            for case when user is in a group + have defined separate permission
        :param calculate_super_admin: calculate permissions for super-admin in the
            same way as for regular user without speedups
        :param cache: Use caching for calculation, None = let the cache backend decide
        """
        user_id = user.user_id
        user_is_admin = user.is_admin

        # inheritance of global permissions like create repo/fork repo etc
        user_inherit_default_permissions = user.inherit_default_permissions

        cache_seconds = safe_int(
            rhodecode.CONFIG.get('rc_cache.cache_perms.expiration_time'))

        if cache is None:
            # let the backend cache decide
            cache_on = cache_seconds > 0
        else:
            cache_on = cache

        log.debug(
            'Computing PERMISSION tree for user %s scope `%s` '
            'with caching: %s[TTL: %ss]', user, scope, cache_on, cache_seconds or 0)

        cache_namespace_uid = 'cache_user_auth.{}'.format(user_id)
        region = rc_cache.get_or_create_region('cache_perms', cache_namespace_uid)

        @region.conditional_cache_on_arguments(namespace=cache_namespace_uid,
                                               condition=cache_on)
        def compute_perm_tree(cache_name,
                user_id, scope, user_is_admin,user_inherit_default_permissions,
                explicit, algo, calculate_super_admin):
            return _cached_perms_data(
                user_id, scope, user_is_admin, user_inherit_default_permissions,
                explicit, algo, calculate_super_admin)

        start = time.time()
        result = compute_perm_tree(
            'permissions', user_id, scope, user_is_admin,
             user_inherit_default_permissions, explicit, algo,
             calculate_super_admin)

        result_repr = []
        for k in result:
            result_repr.append((k, len(result[k])))
        total = time.time() - start
        log.debug('PERMISSION tree for user %s computed in %.3fs: %s',
                  user, total, result_repr)

        return result

    @property
    def is_default(self):
        return self.username == User.DEFAULT_USER

    @property
    def is_admin(self):
        return self.admin

    @property
    def is_user_object(self):
        return self.user_id is not None

    @property
    def repositories_admin(self):
        """
        Returns list of repositories you're an admin of
        """
        return [
            x[0] for x in self.permissions['repositories'].items()
            if x[1] == 'repository.admin']

    @property
    def repository_groups_admin(self):
        """
        Returns list of repository groups you're an admin of
        """
        return [
            x[0] for x in self.permissions['repositories_groups'].items()
            if x[1] == 'group.admin']

    @property
    def user_groups_admin(self):
        """
        Returns list of user groups you're an admin of
        """
        return [
            x[0] for x in self.permissions['user_groups'].items()
            if x[1] == 'usergroup.admin']

    def repo_acl_ids(self, perms=None, name_filter=None, cache=False):
        """
        Returns list of repository ids that user have access to based on given
        perms. The cache flag should be only used in cases that are used for
        display purposes, NOT IN ANY CASE for permission checks.
        """
        from rhodecode.model.scm import RepoList
        if not perms:
            perms = [
                'repository.read', 'repository.write', 'repository.admin']

        def _cached_repo_acl(user_id, perm_def, _name_filter):
            qry = Repository.query()
            if _name_filter:
                ilike_expression = u'%{}%'.format(safe_unicode(_name_filter))
                qry = qry.filter(
                    Repository.repo_name.ilike(ilike_expression))

            return [x.repo_id for x in
                    RepoList(qry, perm_set=perm_def)]

        return _cached_repo_acl(self.user_id, perms, name_filter)

    def repo_group_acl_ids(self, perms=None, name_filter=None, cache=False):
        """
        Returns list of repository group ids that user have access to based on given
        perms. The cache flag should be only used in cases that are used for
        display purposes, NOT IN ANY CASE for permission checks.
        """
        from rhodecode.model.scm import RepoGroupList
        if not perms:
            perms = [
                'group.read', 'group.write', 'group.admin']

        def _cached_repo_group_acl(user_id, perm_def, _name_filter):
            qry = RepoGroup.query()
            if _name_filter:
                ilike_expression = u'%{}%'.format(safe_unicode(_name_filter))
                qry = qry.filter(
                    RepoGroup.group_name.ilike(ilike_expression))

            return [x.group_id for x in
                    RepoGroupList(qry, perm_set=perm_def)]

        return _cached_repo_group_acl(self.user_id, perms, name_filter)

    def user_group_acl_ids(self, perms=None, name_filter=None, cache=False):
        """
        Returns list of user group ids that user have access to based on given
        perms. The cache flag should be only used in cases that are used for
        display purposes, NOT IN ANY CASE for permission checks.
        """
        from rhodecode.model.scm import UserGroupList
        if not perms:
            perms = [
                'usergroup.read', 'usergroup.write', 'usergroup.admin']

        def _cached_user_group_acl(user_id, perm_def, name_filter):
            qry = UserGroup.query()
            if name_filter:
                ilike_expression = u'%{}%'.format(safe_unicode(name_filter))
                qry = qry.filter(
                    UserGroup.users_group_name.ilike(ilike_expression))

            return [x.users_group_id for x in
                    UserGroupList(qry, perm_set=perm_def)]

        return _cached_user_group_acl(self.user_id, perms, name_filter)

    @property
    def ip_allowed(self):
        """
        Checks if ip_addr used in constructor is allowed from defined list of
        allowed ip_addresses for user

        :returns: boolean, True if ip is in allowed ip range
        """
        # check IP
        inherit = self.inherit_default_permissions
        return AuthUser.check_ip_allowed(self.user_id, self.ip_addr,
                                         inherit_from_default=inherit)
    @property
    def personal_repo_group(self):
        return RepoGroup.get_user_personal_repo_group(self.user_id)

    @LazyProperty
    def feed_token(self):
        return self.get_instance().feed_token

    @classmethod
    def check_ip_allowed(cls, user_id, ip_addr, inherit_from_default):
        allowed_ips = AuthUser.get_allowed_ips(
            user_id, cache=True, inherit_from_default=inherit_from_default)
        if check_ip_access(source_ip=ip_addr, allowed_ips=allowed_ips):
            log.debug('IP:%s for user %s is in range of %s',
                      ip_addr, user_id, allowed_ips)
            return True
        else:
            log.info('Access for IP:%s forbidden for user %s, '
                     'not in %s', ip_addr, user_id, allowed_ips)
            return False

    def get_branch_permissions(self, repo_name, perms=None):
        perms = perms or self.permissions_with_scope({'repo_name': repo_name})
        branch_perms = perms.get('repository_branches', {})
        if not branch_perms:
            return {}
        repo_branch_perms = branch_perms.get(repo_name)
        return repo_branch_perms or {}

    def get_rule_and_branch_permission(self, repo_name, branch_name):
        """
        Check if this AuthUser has defined any permissions for branches. If any of
        the rules match in order, we return the matching permissions
        """

        rule = default_perm = ''

        repo_branch_perms = self.get_branch_permissions(repo_name=repo_name)
        if not repo_branch_perms:
            return rule, default_perm

        # now calculate the permissions
        for pattern, branch_perm in repo_branch_perms.items():
            if fnmatch.fnmatch(branch_name, pattern):
                rule = '`{}`=>{}'.format(pattern, branch_perm)
                return rule, branch_perm

        return rule, default_perm

    def __repr__(self):
        return "<AuthUser('id:%s[%s] ip:%s auth:%s')>"\
            % (self.user_id, self.username, self.ip_addr, self.is_authenticated)

    def set_authenticated(self, authenticated=True):
        if self.user_id != self.anonymous_user.user_id:
            self.is_authenticated = authenticated

    def get_cookie_store(self):
        return {
            'username': self.username,
            'password': md5(self.password or ''),
            'user_id': self.user_id,
            'is_authenticated': self.is_authenticated
        }

    @classmethod
    def from_cookie_store(cls, cookie_store):
        """
        Creates AuthUser from a cookie store

        :param cls:
        :param cookie_store:
        """
        user_id = cookie_store.get('user_id')
        username = cookie_store.get('username')
        api_key = cookie_store.get('api_key')
        return AuthUser(user_id, api_key, username)

    @classmethod
    def get_allowed_ips(cls, user_id, cache=False, inherit_from_default=False):
        _set = set()

        if inherit_from_default:
            def_user_id = User.get_default_user(cache=True).user_id
            default_ips = UserIpMap.query().filter(UserIpMap.user_id == def_user_id)
            if cache:
                default_ips = default_ips.options(
                    FromCache("sql_cache_short", "get_user_ips_default"))

            # populate from default user
            for ip in default_ips:
                try:
                    _set.add(ip.ip_addr)
                except ObjectDeletedError:
                    # since we use heavy caching sometimes it happens that
                    # we get deleted objects here, we just skip them
                    pass

        # NOTE:(marcink) we don't want to load any rules for empty
        # user_id which is the case of access of non logged users when anonymous
        # access is disabled
        user_ips = []
        if user_id:
            user_ips = UserIpMap.query().filter(UserIpMap.user_id == user_id)
            if cache:
                user_ips = user_ips.options(
                    FromCache("sql_cache_short", "get_user_ips_%s" % user_id))

        for ip in user_ips:
            try:
                _set.add(ip.ip_addr)
            except ObjectDeletedError:
                # since we use heavy caching sometimes it happens that we get
                # deleted objects here, we just skip them
                pass
        return _set or {ip for ip in ['0.0.0.0/0', '::/0']}


def set_available_permissions(settings):
    """
    This function will propagate pyramid settings with all available defined
    permission given in db. We don't want to check each time from db for new
    permissions since adding a new permission also requires application restart
    ie. to decorate new views with the newly created permission

    :param settings: current pyramid registry.settings

    """
    log.debug('auth: getting information about all available permissions')
    try:
        sa = meta.Session
        all_perms = sa.query(Permission).all()
        settings.setdefault('available_permissions',
                            [x.permission_name for x in all_perms])
        log.debug('auth: set available permissions')
    except Exception:
        log.exception('Failed to fetch permissions from the database.')
        raise


def get_csrf_token(session, force_new=False, save_if_missing=True):
    """
    Return the current authentication token, creating one if one doesn't
    already exist and the save_if_missing flag is present.

    :param session: pass in the pyramid session, else we use the global ones
    :param force_new: force to re-generate the token and store it in session
    :param save_if_missing: save the newly generated token if it's missing in
        session
    """
    # NOTE(marcink): probably should be replaced with below one from pyramid 1.9
    # from pyramid.csrf import get_csrf_token

    if (csrf_token_key not in session and save_if_missing) or force_new:
        token = hashlib.sha1(str(random.getrandbits(128))).hexdigest()
        session[csrf_token_key] = token
        if hasattr(session, 'save'):
            session.save()
    return session.get(csrf_token_key)


def get_request(perm_class_instance):
    from pyramid.threadlocal import get_current_request
    pyramid_request = get_current_request()
    return pyramid_request


# CHECK DECORATORS
class CSRFRequired(object):
    """
    Decorator for authenticating a form

    This decorator uses an authorization token stored in the client's
    session for prevention of certain Cross-site request forgery (CSRF)
    attacks (See
    http://en.wikipedia.org/wiki/Cross-site_request_forgery for more
    information).

    For use with the ``webhelpers.secure_form`` helper functions.

    """
    def __init__(self, token=csrf_token_key, header='X-CSRF-Token',
        except_methods=None):
        self.token = token
        self.header = header
        self.except_methods = except_methods or []

    def __call__(self, func):
        return get_cython_compat_decorator(self.__wrapper, func)

    def _get_csrf(self, _request):
        return _request.POST.get(self.token, _request.headers.get(self.header))

    def check_csrf(self, _request, cur_token):
        supplied_token = self._get_csrf(_request)
        return supplied_token and supplied_token == cur_token

    def _get_request(self):
        return get_request(self)

    def __wrapper(self, func, *fargs, **fkwargs):
        request = self._get_request()

        if request.method in self.except_methods:
            return func(*fargs, **fkwargs)

        cur_token = get_csrf_token(request.session, save_if_missing=False)
        if self.check_csrf(request, cur_token):
            if request.POST.get(self.token):
                del request.POST[self.token]
            return func(*fargs, **fkwargs)
        else:
            reason = 'token-missing'
            supplied_token = self._get_csrf(request)
            if supplied_token and cur_token != supplied_token:
                reason = 'token-mismatch [%s:%s]' % (
                    cur_token or ''[:6], supplied_token or ''[:6])

            csrf_message = \
                ("Cross-site request forgery detected, request denied. See "
                 "http://en.wikipedia.org/wiki/Cross-site_request_forgery for "
                 "more information.")
        log.warn('Cross-site request forgery detected, request %r DENIED: %s '
                 'REMOTE_ADDR:%s, HEADERS:%s' % (
                     request, reason, request.remote_addr, request.headers))

        raise HTTPForbidden(explanation=csrf_message)


class LoginRequired(object):
    """
    Must be logged in to execute this function else
    redirect to login page

    :param api_access: if enabled this checks only for valid auth token
        and grants access based on valid token
    """
    def __init__(self, auth_token_access=None):
        self.auth_token_access = auth_token_access

    def __call__(self, func):
        return get_cython_compat_decorator(self.__wrapper, func)

    def _get_request(self):
        return get_request(self)

    def __wrapper(self, func, *fargs, **fkwargs):
        from rhodecode.lib import helpers as h
        cls = fargs[0]
        user = cls._rhodecode_user
        request = self._get_request()
        _ = request.translate

        loc = "%s:%s" % (cls.__class__.__name__, func.__name__)
        log.debug('Starting login restriction checks for user: %s', user)
        # check if our IP is allowed
        ip_access_valid = True
        if not user.ip_allowed:
            h.flash(h.literal(_('IP %s not allowed' % (user.ip_addr,))),
                    category='warning')
            ip_access_valid = False

        # check if we used an APIKEY and it's a valid one
        # defined white-list of controllers which API access will be enabled
        _auth_token = request.GET.get(
            'auth_token', '') or request.GET.get('api_key', '')
        auth_token_access_valid = allowed_auth_token_access(
            loc, auth_token=_auth_token)

        # explicit controller is enabled or API is in our whitelist
        if self.auth_token_access or auth_token_access_valid:
            log.debug('Checking AUTH TOKEN access for %s', cls)
            db_user = user.get_instance()

            if db_user:
                if self.auth_token_access:
                    roles = self.auth_token_access
                else:
                    roles = [UserApiKeys.ROLE_HTTP]
                token_match = db_user.authenticate_by_token(
                    _auth_token, roles=roles)
            else:
                log.debug('Unable to fetch db instance for auth user: %s', user)
                token_match = False

            if _auth_token and token_match:
                auth_token_access_valid = True
                log.debug('AUTH TOKEN ****%s is VALID', _auth_token[-4:])
            else:
                auth_token_access_valid = False
                if not _auth_token:
                    log.debug("AUTH TOKEN *NOT* present in request")
                else:
                    log.warning("AUTH TOKEN ****%s *NOT* valid", _auth_token[-4:])

        log.debug('Checking if %s is authenticated @ %s', user.username, loc)
        reason = 'RHODECODE_AUTH' if user.is_authenticated \
            else 'AUTH_TOKEN_AUTH'

        if ip_access_valid and (
                user.is_authenticated or auth_token_access_valid):
            log.info('user %s authenticating with:%s IS authenticated on func %s',
                     user, reason, loc)

            return func(*fargs, **fkwargs)
        else:
            log.warning(
                'user %s authenticating with:%s NOT authenticated on '
                'func: %s: IP_ACCESS:%s AUTH_TOKEN_ACCESS:%s',
                user, reason, loc, ip_access_valid, auth_token_access_valid)
            # we preserve the get PARAM
            came_from = get_came_from(request)

            log.debug('redirecting to login page with %s', came_from)
            raise HTTPFound(
                h.route_path('login', _query={'came_from': came_from}))


class NotAnonymous(object):
    """
    Must be logged in to execute this function else
    redirect to login page
    """

    def __call__(self, func):
        return get_cython_compat_decorator(self.__wrapper, func)

    def _get_request(self):
        return get_request(self)

    def __wrapper(self, func, *fargs, **fkwargs):
        import rhodecode.lib.helpers as h
        cls = fargs[0]
        self.user = cls._rhodecode_user
        request = self._get_request()
        _ = request.translate
        log.debug('Checking if user is not anonymous @%s', cls)

        anonymous = self.user.username == User.DEFAULT_USER

        if anonymous:
            came_from = get_came_from(request)
            h.flash(_('You need to be a registered user to '
                      'perform this action'),
                    category='warning')
            raise HTTPFound(
                h.route_path('login', _query={'came_from': came_from}))
        else:
            return func(*fargs, **fkwargs)


class PermsDecorator(object):
    """
    Base class for controller decorators, we extract the current user from
    the class itself, which has it stored in base controllers
    """

    def __init__(self, *required_perms):
        self.required_perms = set(required_perms)

    def __call__(self, func):
        return get_cython_compat_decorator(self.__wrapper, func)

    def _get_request(self):
        return get_request(self)

    def __wrapper(self, func, *fargs, **fkwargs):
        import rhodecode.lib.helpers as h
        cls = fargs[0]
        _user = cls._rhodecode_user
        request = self._get_request()
        _ = request.translate

        log.debug('checking %s permissions %s for %s %s',
                  self.__class__.__name__, self.required_perms, cls, _user)

        if self.check_permissions(_user):
            log.debug('Permission granted for %s %s', cls, _user)
            return func(*fargs, **fkwargs)

        else:
            log.debug('Permission denied for %s %s', cls, _user)
            anonymous = _user.username == User.DEFAULT_USER

            if anonymous:
                came_from = get_came_from(self._get_request())
                h.flash(_('You need to be signed in to view this page'),
                        category='warning')
                raise HTTPFound(
                    h.route_path('login', _query={'came_from': came_from}))

            else:
                # redirect with 404 to prevent resource discovery
                raise HTTPNotFound()

    def check_permissions(self, user):
        """Dummy function for overriding"""
        raise NotImplementedError(
            'You have to write this function in child class')


class HasPermissionAllDecorator(PermsDecorator):
    """
    Checks for access permission for all given predicates. All of them
    have to be meet in order to fulfill the request
    """

    def check_permissions(self, user):
        perms = user.permissions_with_scope({})
        if self.required_perms.issubset(perms['global']):
            return True
        return False


class HasPermissionAnyDecorator(PermsDecorator):
    """
    Checks for access permission for any of given predicates. In order to
    fulfill the request any of predicates must be meet
    """

    def check_permissions(self, user):
        perms = user.permissions_with_scope({})
        if self.required_perms.intersection(perms['global']):
            return True
        return False


class HasRepoPermissionAllDecorator(PermsDecorator):
    """
    Checks for access permission for all given predicates for specific
    repository. All of them have to be meet in order to fulfill the request
    """
    def _get_repo_name(self):
        _request = self._get_request()
        return get_repo_slug(_request)

    def check_permissions(self, user):
        perms = user.permissions
        repo_name = self._get_repo_name()

        try:
            user_perms = {perms['repositories'][repo_name]}
        except KeyError:
            log.debug('cannot locate repo with name: `%s` in permissions defs',
                      repo_name)
            return False

        log.debug('checking `%s` permissions for repo `%s`',
                  user_perms, repo_name)
        if self.required_perms.issubset(user_perms):
            return True
        return False


class HasRepoPermissionAnyDecorator(PermsDecorator):
    """
    Checks for access permission for any of given predicates for specific
    repository. In order to fulfill the request any of predicates must be meet
    """
    def _get_repo_name(self):
        _request = self._get_request()
        return get_repo_slug(_request)

    def check_permissions(self, user):
        perms = user.permissions
        repo_name = self._get_repo_name()

        try:
            user_perms = {perms['repositories'][repo_name]}
        except KeyError:
            log.debug(
                'cannot locate repo with name: `%s` in permissions defs',
                repo_name)
            return False

        log.debug('checking `%s` permissions for repo `%s`',
                  user_perms, repo_name)
        if self.required_perms.intersection(user_perms):
            return True
        return False


class HasRepoGroupPermissionAllDecorator(PermsDecorator):
    """
    Checks for access permission for all given predicates for specific
    repository group. All of them have to be meet in order to
    fulfill the request
    """
    def _get_repo_group_name(self):
        _request = self._get_request()
        return get_repo_group_slug(_request)

    def check_permissions(self, user):
        perms = user.permissions
        group_name = self._get_repo_group_name()
        try:
            user_perms = {perms['repositories_groups'][group_name]}
        except KeyError:
            log.debug(
                'cannot locate repo group with name: `%s` in permissions defs',
                group_name)
            return False

        log.debug('checking `%s` permissions for repo group `%s`',
                  user_perms, group_name)
        if self.required_perms.issubset(user_perms):
            return True
        return False


class HasRepoGroupPermissionAnyDecorator(PermsDecorator):
    """
    Checks for access permission for any of given predicates for specific
    repository group. In order to fulfill the request any
    of predicates must be met
    """
    def _get_repo_group_name(self):
        _request = self._get_request()
        return get_repo_group_slug(_request)

    def check_permissions(self, user):
        perms = user.permissions
        group_name = self._get_repo_group_name()

        try:
            user_perms = {perms['repositories_groups'][group_name]}
        except KeyError:
            log.debug(
                'cannot locate repo group with name: `%s` in permissions defs',
                group_name)
            return False

        log.debug('checking `%s` permissions for repo group `%s`',
                  user_perms, group_name)
        if self.required_perms.intersection(user_perms):
            return True
        return False


class HasUserGroupPermissionAllDecorator(PermsDecorator):
    """
    Checks for access permission for all given predicates for specific
    user group. All of them have to be meet in order to fulfill the request
    """
    def _get_user_group_name(self):
        _request = self._get_request()
        return get_user_group_slug(_request)

    def check_permissions(self, user):
        perms = user.permissions
        group_name = self._get_user_group_name()
        try:
            user_perms = {perms['user_groups'][group_name]}
        except KeyError:
            return False

        if self.required_perms.issubset(user_perms):
            return True
        return False


class HasUserGroupPermissionAnyDecorator(PermsDecorator):
    """
    Checks for access permission for any of given predicates for specific
    user group. In order to fulfill the request any of predicates must be meet
    """
    def _get_user_group_name(self):
        _request = self._get_request()
        return get_user_group_slug(_request)

    def check_permissions(self, user):
        perms = user.permissions
        group_name = self._get_user_group_name()
        try:
            user_perms = {perms['user_groups'][group_name]}
        except KeyError:
            return False

        if self.required_perms.intersection(user_perms):
            return True
        return False


# CHECK FUNCTIONS
class PermsFunction(object):
    """Base function for other check functions"""

    def __init__(self, *perms):
        self.required_perms = set(perms)
        self.repo_name = None
        self.repo_group_name = None
        self.user_group_name = None

    def __bool__(self):
        frame = inspect.currentframe()
        stack_trace = traceback.format_stack(frame)
        log.error('Checking bool value on a class instance of perm '
                  'function is not allowed: %s', ''.join(stack_trace))
        # rather than throwing errors, here we always return False so if by
        # accident someone checks truth for just an instance it will always end
        # up in returning False
        return False
    __nonzero__ = __bool__

    def __call__(self, check_location='', user=None):
        if not user:
            log.debug('Using user attribute from global request')
            request = self._get_request()
            user = request.user

        # init auth user if not already given
        if not isinstance(user, AuthUser):
            log.debug('Wrapping user %s into AuthUser', user)
            user = AuthUser(user.user_id)

        cls_name = self.__class__.__name__
        check_scope = self._get_check_scope(cls_name)
        check_location = check_location or 'unspecified location'

        log.debug('checking cls:%s %s usr:%s %s @ %s', cls_name,
                  self.required_perms, user, check_scope, check_location)
        if not user:
            log.warning('Empty user given for permission check')
            return False

        if self.check_permissions(user):
            log.debug('Permission to repo:`%s` GRANTED for user:`%s` @ %s',
                      check_scope, user, check_location)
            return True

        else:
            log.debug('Permission to repo:`%s` DENIED for user:`%s` @ %s',
                      check_scope, user, check_location)
            return False

    def _get_request(self):
        return get_request(self)

    def _get_check_scope(self, cls_name):
        return {
            'HasPermissionAll':          'GLOBAL',
            'HasPermissionAny':          'GLOBAL',
            'HasRepoPermissionAll':      'repo:%s' % self.repo_name,
            'HasRepoPermissionAny':      'repo:%s' % self.repo_name,
            'HasRepoGroupPermissionAll': 'repo_group:%s' % self.repo_group_name,
            'HasRepoGroupPermissionAny': 'repo_group:%s' % self.repo_group_name,
            'HasUserGroupPermissionAll': 'user_group:%s' % self.user_group_name,
            'HasUserGroupPermissionAny': 'user_group:%s' % self.user_group_name,
        }.get(cls_name, '?:%s' % cls_name)

    def check_permissions(self, user):
        """Dummy function for overriding"""
        raise Exception('You have to write this function in child class')


class HasPermissionAll(PermsFunction):
    def check_permissions(self, user):
        perms = user.permissions_with_scope({})
        if self.required_perms.issubset(perms.get('global')):
            return True
        return False


class HasPermissionAny(PermsFunction):
    def check_permissions(self, user):
        perms = user.permissions_with_scope({})
        if self.required_perms.intersection(perms.get('global')):
            return True
        return False


class HasRepoPermissionAll(PermsFunction):
    def __call__(self, repo_name=None, check_location='', user=None):
        self.repo_name = repo_name
        return super(HasRepoPermissionAll, self).__call__(check_location, user)

    def _get_repo_name(self):
        if not self.repo_name:
            _request = self._get_request()
            self.repo_name = get_repo_slug(_request)
        return self.repo_name

    def check_permissions(self, user):
        self.repo_name = self._get_repo_name()
        perms = user.permissions
        try:
            user_perms = {perms['repositories'][self.repo_name]}
        except KeyError:
            return False
        if self.required_perms.issubset(user_perms):
            return True
        return False


class HasRepoPermissionAny(PermsFunction):
    def __call__(self, repo_name=None, check_location='', user=None):
        self.repo_name = repo_name
        return super(HasRepoPermissionAny, self).__call__(check_location, user)

    def _get_repo_name(self):
        if not self.repo_name:
            _request = self._get_request()
            self.repo_name = get_repo_slug(_request)
        return self.repo_name

    def check_permissions(self, user):
        self.repo_name = self._get_repo_name()
        perms = user.permissions
        try:
            user_perms = {perms['repositories'][self.repo_name]}
        except KeyError:
            return False
        if self.required_perms.intersection(user_perms):
            return True
        return False


class HasRepoGroupPermissionAny(PermsFunction):
    def __call__(self, group_name=None, check_location='', user=None):
        self.repo_group_name = group_name
        return super(HasRepoGroupPermissionAny, self).__call__(
            check_location, user)

    def check_permissions(self, user):
        perms = user.permissions
        try:
            user_perms = {perms['repositories_groups'][self.repo_group_name]}
        except KeyError:
            return False
        if self.required_perms.intersection(user_perms):
            return True
        return False


class HasRepoGroupPermissionAll(PermsFunction):
    def __call__(self, group_name=None, check_location='', user=None):
        self.repo_group_name = group_name
        return super(HasRepoGroupPermissionAll, self).__call__(
            check_location, user)

    def check_permissions(self, user):
        perms = user.permissions
        try:
            user_perms = {perms['repositories_groups'][self.repo_group_name]}
        except KeyError:
            return False
        if self.required_perms.issubset(user_perms):
            return True
        return False


class HasUserGroupPermissionAny(PermsFunction):
    def __call__(self, user_group_name=None, check_location='', user=None):
        self.user_group_name = user_group_name
        return super(HasUserGroupPermissionAny, self).__call__(
            check_location, user)

    def check_permissions(self, user):
        perms = user.permissions
        try:
            user_perms = {perms['user_groups'][self.user_group_name]}
        except KeyError:
            return False
        if self.required_perms.intersection(user_perms):
            return True
        return False


class HasUserGroupPermissionAll(PermsFunction):
    def __call__(self, user_group_name=None, check_location='', user=None):
        self.user_group_name = user_group_name
        return super(HasUserGroupPermissionAll, self).__call__(
            check_location, user)

    def check_permissions(self, user):
        perms = user.permissions
        try:
            user_perms = {perms['user_groups'][self.user_group_name]}
        except KeyError:
            return False
        if self.required_perms.issubset(user_perms):
            return True
        return False


# SPECIAL VERSION TO HANDLE MIDDLEWARE AUTH
class HasPermissionAnyMiddleware(object):
    def __init__(self, *perms):
        self.required_perms = set(perms)

    def __call__(self, auth_user, repo_name):
        # repo_name MUST be unicode, since we handle keys in permission
        # dict by unicode
        repo_name = safe_unicode(repo_name)
        log.debug(
            'Checking VCS protocol permissions %s for user:%s repo:`%s`',
            self.required_perms, auth_user, repo_name)

        if self.check_permissions(auth_user, repo_name):
            log.debug('Permission to repo:`%s` GRANTED for user:%s @ %s',
                      repo_name, auth_user, 'PermissionMiddleware')
            return True

        else:
            log.debug('Permission to repo:`%s` DENIED for user:%s @ %s',
                      repo_name, auth_user, 'PermissionMiddleware')
            return False

    def check_permissions(self, user, repo_name):
        perms = user.permissions_with_scope({'repo_name': repo_name})

        try:
            user_perms = {perms['repositories'][repo_name]}
        except Exception:
            log.exception('Error while accessing user permissions')
            return False

        if self.required_perms.intersection(user_perms):
            return True
        return False


# SPECIAL VERSION TO HANDLE API AUTH
class _BaseApiPerm(object):
    def __init__(self, *perms):
        self.required_perms = set(perms)

    def __call__(self, check_location=None, user=None, repo_name=None,
                 group_name=None, user_group_name=None):
        cls_name = self.__class__.__name__
        check_scope = 'global:%s' % (self.required_perms,)
        if repo_name:
            check_scope += ', repo_name:%s' % (repo_name,)

        if group_name:
            check_scope += ', repo_group_name:%s' % (group_name,)

        if user_group_name:
            check_scope += ', user_group_name:%s' % (user_group_name,)

        log.debug('checking cls:%s %s %s @ %s',
                  cls_name, self.required_perms, check_scope, check_location)
        if not user:
            log.debug('Empty User passed into arguments')
            return False

        # process user
        if not isinstance(user, AuthUser):
            user = AuthUser(user.user_id)
        if not check_location:
            check_location = 'unspecified'
        if self.check_permissions(user.permissions, repo_name, group_name,
                                  user_group_name):
            log.debug('Permission to repo:`%s` GRANTED for user:`%s` @ %s',
                      check_scope, user, check_location)
            return True

        else:
            log.debug('Permission to repo:`%s` DENIED for user:`%s` @ %s',
                      check_scope, user, check_location)
            return False

    def check_permissions(self, perm_defs, repo_name=None, group_name=None,
                          user_group_name=None):
        """
        implement in child class should return True if permissions are ok,
        False otherwise

        :param perm_defs: dict with permission definitions
        :param repo_name: repo name
        """
        raise NotImplementedError()


class HasPermissionAllApi(_BaseApiPerm):
    def check_permissions(self, perm_defs, repo_name=None, group_name=None,
                          user_group_name=None):
        if self.required_perms.issubset(perm_defs.get('global')):
            return True
        return False


class HasPermissionAnyApi(_BaseApiPerm):
    def check_permissions(self, perm_defs, repo_name=None, group_name=None,
                          user_group_name=None):
        if self.required_perms.intersection(perm_defs.get('global')):
            return True
        return False


class HasRepoPermissionAllApi(_BaseApiPerm):
    def check_permissions(self, perm_defs, repo_name=None, group_name=None,
                          user_group_name=None):
        try:
            _user_perms = {perm_defs['repositories'][repo_name]}
        except KeyError:
            log.warning(traceback.format_exc())
            return False
        if self.required_perms.issubset(_user_perms):
            return True
        return False


class HasRepoPermissionAnyApi(_BaseApiPerm):
    def check_permissions(self, perm_defs, repo_name=None, group_name=None,
                          user_group_name=None):
        try:
            _user_perms = {perm_defs['repositories'][repo_name]}
        except KeyError:
            log.warning(traceback.format_exc())
            return False
        if self.required_perms.intersection(_user_perms):
            return True
        return False


class HasRepoGroupPermissionAnyApi(_BaseApiPerm):
    def check_permissions(self, perm_defs, repo_name=None, group_name=None,
                          user_group_name=None):
        try:
            _user_perms = {perm_defs['repositories_groups'][group_name]}
        except KeyError:
            log.warning(traceback.format_exc())
            return False
        if self.required_perms.intersection(_user_perms):
            return True
        return False


class HasRepoGroupPermissionAllApi(_BaseApiPerm):
    def check_permissions(self, perm_defs, repo_name=None, group_name=None,
                          user_group_name=None):
        try:
            _user_perms = {perm_defs['repositories_groups'][group_name]}
        except KeyError:
            log.warning(traceback.format_exc())
            return False
        if self.required_perms.issubset(_user_perms):
            return True
        return False


class HasUserGroupPermissionAnyApi(_BaseApiPerm):
    def check_permissions(self, perm_defs, repo_name=None, group_name=None,
                          user_group_name=None):
        try:
            _user_perms = {perm_defs['user_groups'][user_group_name]}
        except KeyError:
            log.warning(traceback.format_exc())
            return False
        if self.required_perms.intersection(_user_perms):
            return True
        return False


def check_ip_access(source_ip, allowed_ips=None):
    """
    Checks if source_ip is a subnet of any of allowed_ips.

    :param source_ip:
    :param allowed_ips: list of allowed ips together with mask
    """
    log.debug('checking if ip:%s is subnet of %s', source_ip, allowed_ips)
    source_ip_address = ipaddress.ip_address(safe_unicode(source_ip))
    if isinstance(allowed_ips, (tuple, list, set)):
        for ip in allowed_ips:
            ip = safe_unicode(ip)
            try:
                network_address = ipaddress.ip_network(ip, strict=False)
                if source_ip_address in network_address:
                    log.debug('IP %s is network %s', source_ip_address, network_address)
                    return True
                # for any case we cannot determine the IP, don't crash just
                # skip it and log as error, we want to say forbidden still when
                # sending bad IP
            except Exception:
                log.error(traceback.format_exc())
                continue
    return False


def get_cython_compat_decorator(wrapper, func):
    """
    Creates a cython compatible decorator. The previously used
    decorator.decorator() function seems to be incompatible with cython.

    :param wrapper: __wrapper method of the decorator class
    :param func: decorated function
    """
    @wraps(func)
    def local_wrapper(*args, **kwds):
        return wrapper(func, *args, **kwds)
    local_wrapper.__wrapped__ = func
    return local_wrapper


