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
Database Models for RhodeCode Enterprise
"""

import re
import os
import time
import string
import hashlib
import logging
import datetime
import uuid
import warnings
import ipaddress
import functools
import traceback
import collections

from sqlalchemy import (
    or_, and_, not_, func, cast, TypeDecorator, event,
    Index, Sequence, UniqueConstraint, ForeignKey, CheckConstraint, Column,
    Boolean, String, Unicode, UnicodeText, DateTime, Integer, LargeBinary,
    Text, Float, PickleType, BigInteger)
from sqlalchemy.sql.expression import true, false, case
from sqlalchemy.sql.functions import coalesce, count  # pragma: no cover
from sqlalchemy.orm import (
    relationship, joinedload, class_mapper, validates, aliased)
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.exc import IntegrityError  # pragma: no cover
from sqlalchemy.dialects.mysql import LONGTEXT
from zope.cachedescriptors.property import Lazy as LazyProperty
from pyramid import compat
from pyramid.threadlocal import get_current_request
from webhelpers2.text import remove_formatting

from rhodecode.translation import _
from rhodecode.lib.vcs import get_vcs_instance
from rhodecode.lib.vcs.backends.base import EmptyCommit, Reference
from rhodecode.lib.utils2 import (
    str2bool, safe_str, get_commit_safe, safe_unicode, sha1_safe,
    time_to_datetime, aslist, Optional, safe_int, get_clone_url, AttributeDict,
    glob2re, StrictAttributeDict, cleaned_uri, datetime_to_time, OrderedDefaultDict)
from rhodecode.lib.jsonalchemy import MutationObj, MutationList, JsonType, \
    JsonRaw
from rhodecode.lib.ext_json import json
from rhodecode.lib.caching_query import FromCache
from rhodecode.lib.encrypt import AESCipher, validate_and_get_enc_data
from rhodecode.lib.encrypt2 import Encryptor
from rhodecode.lib.exceptions import (
    ArtifactMetadataDuplicate, ArtifactMetadataBadValueType)
from rhodecode.model.meta import Base, Session

URL_SEP = '/'
log = logging.getLogger(__name__)

# =============================================================================
# BASE CLASSES
# =============================================================================

# this is propagated from .ini file rhodecode.encrypted_values.secret or
# beaker.session.secret if first is not set.
# and initialized at environment.py
ENCRYPTION_KEY = None

# used to sort permissions by types, '#' used here is not allowed to be in
# usernames, and it's very early in sorted string.printable table.
PERMISSION_TYPE_SORT = {
    'admin': '####',
    'write': '###',
    'read':  '##',
    'none':  '#',
}


def display_user_sort(obj):
    """
    Sort function used to sort permissions in .permissions() function of
    Repository, RepoGroup, UserGroup. Also it put the default user in front
    of all other resources
    """

    if obj.username == User.DEFAULT_USER:
        return '#####'
    prefix = PERMISSION_TYPE_SORT.get(obj.permission.split('.')[-1], '')
    return prefix + obj.username


def display_user_group_sort(obj):
    """
    Sort function used to sort permissions in .permissions() function of
    Repository, RepoGroup, UserGroup. Also it put the default user in front
    of all other resources
    """

    prefix = PERMISSION_TYPE_SORT.get(obj.permission.split('.')[-1], '')
    return prefix + obj.users_group_name


def _hash_key(k):
    return sha1_safe(k)


def in_filter_generator(qry, items, limit=500):
    """
    Splits IN() into multiple with OR
    e.g.::
    cnt = Repository.query().filter(
        or_(
            *in_filter_generator(Repository.repo_id, range(100000))
        )).count()
    """
    if not items:
        # empty list will cause empty query which might cause security issues
        # this can lead to hidden unpleasant results
        items = [-1]

    parts = []
    for chunk in xrange(0, len(items), limit):
        parts.append(
            qry.in_(items[chunk: chunk + limit])
        )

    return parts


base_table_args = {
    'extend_existing': True,
    'mysql_engine': 'InnoDB',
    'mysql_charset': 'utf8',
    'sqlite_autoincrement': True
}


class EncryptedTextValue(TypeDecorator):
    """
    Special column for encrypted long text data, use like::

        value = Column("encrypted_value", EncryptedValue(), nullable=False)

    This column is intelligent so if value is in unencrypted form it return
    unencrypted form, but on save it always encrypts
    """
    impl = Text

    def process_bind_param(self, value, dialect):
        """
        Setter for storing value
        """
        import rhodecode
        if not value:
            return value

        # protect against double encrypting if values is already encrypted
        if value.startswith('enc$aes$') \
                or value.startswith('enc$aes_hmac$') \
                or value.startswith('enc2$'):
            raise ValueError('value needs to be in unencrypted format, '
                             'ie. not starting with enc$ or enc2$')

        algo = rhodecode.CONFIG.get('rhodecode.encrypted_values.algorithm') or 'aes'
        if algo == 'aes':
            return 'enc$aes_hmac$%s' % AESCipher(ENCRYPTION_KEY, hmac=True).encrypt(value)
        elif algo == 'fernet':
            return Encryptor(ENCRYPTION_KEY).encrypt(value)
        else:
            ValueError('Bad encryption algorithm, should be fernet or aes, got: {}'.format(algo))

    def process_result_value(self, value, dialect):
        """
        Getter for retrieving value
        """

        import rhodecode
        if not value:
            return value

        algo = rhodecode.CONFIG.get('rhodecode.encrypted_values.algorithm') or 'aes'
        enc_strict_mode = str2bool(rhodecode.CONFIG.get('rhodecode.encrypted_values.strict') or True)
        if algo == 'aes':
            decrypted_data = validate_and_get_enc_data(value, ENCRYPTION_KEY, enc_strict_mode)
        elif algo == 'fernet':
            return Encryptor(ENCRYPTION_KEY).decrypt(value)
        else:
            ValueError('Bad encryption algorithm, should be fernet or aes, got: {}'.format(algo))
        return decrypted_data


class BaseModel(object):
    """
    Base Model for all classes
    """

    @classmethod
    def _get_keys(cls):
        """return column names for this model """
        return class_mapper(cls).c.keys()

    def get_dict(self):
        """
        return dict with keys and values corresponding
        to this model data """

        d = {}
        for k in self._get_keys():
            d[k] = getattr(self, k)

        # also use __json__() if present to get additional fields
        _json_attr = getattr(self, '__json__', None)
        if _json_attr:
            # update with attributes from __json__
            if callable(_json_attr):
                _json_attr = _json_attr()
            for k, val in _json_attr.iteritems():
                d[k] = val
        return d

    def get_appstruct(self):
        """return list with keys and values tuples corresponding
        to this model data """

        lst = []
        for k in self._get_keys():
            lst.append((k, getattr(self, k),))
        return lst

    def populate_obj(self, populate_dict):
        """populate model with data from given populate_dict"""

        for k in self._get_keys():
            if k in populate_dict:
                setattr(self, k, populate_dict[k])

    @classmethod
    def query(cls):
        return Session().query(cls)

    @classmethod
    def get(cls, id_):
        if id_:
            return cls.query().get(id_)

    @classmethod
    def get_or_404(cls, id_):
        from pyramid.httpexceptions import HTTPNotFound

        try:
            id_ = int(id_)
        except (TypeError, ValueError):
            raise HTTPNotFound()

        res = cls.query().get(id_)
        if not res:
            raise HTTPNotFound()
        return res

    @classmethod
    def getAll(cls):
        # deprecated and left for backward compatibility
        return cls.get_all()

    @classmethod
    def get_all(cls):
        return cls.query().all()

    @classmethod
    def delete(cls, id_):
        obj = cls.query().get(id_)
        Session().delete(obj)

    @classmethod
    def identity_cache(cls, session, attr_name, value):
        exist_in_session = []
        for (item_cls, pkey), instance in session.identity_map.items():
            if cls == item_cls and getattr(instance, attr_name) == value:
                exist_in_session.append(instance)
        if exist_in_session:
            if len(exist_in_session) == 1:
                return exist_in_session[0]
            log.exception(
                'multiple objects with attr %s and '
                'value %s found with same name: %r',
                attr_name, value, exist_in_session)

    def __repr__(self):
        if hasattr(self, '__unicode__'):
            # python repr needs to return str
            try:
                return safe_str(self.__unicode__())
            except UnicodeDecodeError:
                pass
        return '<DB:%s>' % (self.__class__.__name__)


class RhodeCodeSetting(Base, BaseModel):
    __tablename__ = 'rhodecode_settings'
    __table_args__ = (
        UniqueConstraint('app_settings_name'),
        base_table_args
    )

    SETTINGS_TYPES = {
        'str': safe_str,
        'int': safe_int,
        'unicode': safe_unicode,
        'bool': str2bool,
        'list': functools.partial(aslist, sep=',')
    }
    DEFAULT_UPDATE_URL = 'https://rhodecode.com/api/v1/info/versions'
    GLOBAL_CONF_KEY = 'app_settings'

    app_settings_id = Column("app_settings_id", Integer(), nullable=False, unique=True, default=None, primary_key=True)
    app_settings_name = Column("app_settings_name", String(255), nullable=True, unique=None, default=None)
    _app_settings_value = Column("app_settings_value", String(4096), nullable=True, unique=None, default=None)
    _app_settings_type = Column("app_settings_type", String(255), nullable=True, unique=None, default=None)

    def __init__(self, key='', val='', type='unicode'):
        self.app_settings_name = key
        self.app_settings_type = type
        self.app_settings_value = val

    @validates('_app_settings_value')
    def validate_settings_value(self, key, val):
        assert type(val) == unicode
        return val

    @hybrid_property
    def app_settings_value(self):
        v = self._app_settings_value
        _type = self.app_settings_type
        if _type:
            _type = self.app_settings_type.split('.')[0]
            # decode the encrypted value
            if 'encrypted' in self.app_settings_type:
                cipher = EncryptedTextValue()
                v = safe_unicode(cipher.process_result_value(v, None))

        converter = self.SETTINGS_TYPES.get(_type) or \
            self.SETTINGS_TYPES['unicode']
        return converter(v)

    @app_settings_value.setter
    def app_settings_value(self, val):
        """
        Setter that will always make sure we use unicode in app_settings_value

        :param val:
        """
        val = safe_unicode(val)
        # encode the encrypted value
        if 'encrypted' in self.app_settings_type:
            cipher = EncryptedTextValue()
            val = safe_unicode(cipher.process_bind_param(val, None))
        self._app_settings_value = val

    @hybrid_property
    def app_settings_type(self):
        return self._app_settings_type

    @app_settings_type.setter
    def app_settings_type(self, val):
        if val.split('.')[0] not in self.SETTINGS_TYPES:
            raise Exception('type must be one of %s got %s'
                            % (self.SETTINGS_TYPES.keys(), val))
        self._app_settings_type = val

    @classmethod
    def get_by_prefix(cls, prefix):
        return RhodeCodeSetting.query()\
            .filter(RhodeCodeSetting.app_settings_name.startswith(prefix))\
            .all()

    def __unicode__(self):
        return u"<%s('%s:%s[%s]')>" % (
            self.__class__.__name__,
            self.app_settings_name, self.app_settings_value,
            self.app_settings_type
        )


class RhodeCodeUi(Base, BaseModel):
    __tablename__ = 'rhodecode_ui'
    __table_args__ = (
        UniqueConstraint('ui_key'),
        base_table_args
    )

    HOOK_REPO_SIZE = 'changegroup.repo_size'
    # HG
    HOOK_PRE_PULL = 'preoutgoing.pre_pull'
    HOOK_PULL = 'outgoing.pull_logger'
    HOOK_PRE_PUSH = 'prechangegroup.pre_push'
    HOOK_PRETX_PUSH = 'pretxnchangegroup.pre_push'
    HOOK_PUSH = 'changegroup.push_logger'
    HOOK_PUSH_KEY = 'pushkey.key_push'

    HOOKS_BUILTIN = [
        HOOK_PRE_PULL,
        HOOK_PULL,
        HOOK_PRE_PUSH,
        HOOK_PRETX_PUSH,
        HOOK_PUSH,
        HOOK_PUSH_KEY,
    ]

    # TODO: johbo: Unify way how hooks are configured for git and hg,
    # git part is currently hardcoded.

    # SVN PATTERNS
    SVN_BRANCH_ID = 'vcs_svn_branch'
    SVN_TAG_ID = 'vcs_svn_tag'

    ui_id = Column(
        "ui_id", Integer(), nullable=False, unique=True, default=None,
        primary_key=True)
    ui_section = Column(
        "ui_section", String(255), nullable=True, unique=None, default=None)
    ui_key = Column(
        "ui_key", String(255), nullable=True, unique=None, default=None)
    ui_value = Column(
        "ui_value", String(255), nullable=True, unique=None, default=None)
    ui_active = Column(
        "ui_active", Boolean(), nullable=True, unique=None, default=True)

    def __repr__(self):
        return '<%s[%s]%s=>%s]>' % (self.__class__.__name__, self.ui_section,
                                    self.ui_key, self.ui_value)


class RepoRhodeCodeSetting(Base, BaseModel):
    __tablename__ = 'repo_rhodecode_settings'
    __table_args__ = (
        UniqueConstraint(
            'app_settings_name', 'repository_id',
            name='uq_repo_rhodecode_setting_name_repo_id'),
        base_table_args
    )

    repository_id = Column(
        "repository_id", Integer(), ForeignKey('repositories.repo_id'),
        nullable=False)
    app_settings_id = Column(
        "app_settings_id", Integer(), nullable=False, unique=True,
        default=None, primary_key=True)
    app_settings_name = Column(
        "app_settings_name", String(255), nullable=True, unique=None,
        default=None)
    _app_settings_value = Column(
        "app_settings_value", String(4096), nullable=True, unique=None,
        default=None)
    _app_settings_type = Column(
        "app_settings_type", String(255), nullable=True, unique=None,
        default=None)

    repository = relationship('Repository')

    def __init__(self, repository_id, key='', val='', type='unicode'):
        self.repository_id = repository_id
        self.app_settings_name = key
        self.app_settings_type = type
        self.app_settings_value = val

    @validates('_app_settings_value')
    def validate_settings_value(self, key, val):
        assert type(val) == unicode
        return val

    @hybrid_property
    def app_settings_value(self):
        v = self._app_settings_value
        type_ = self.app_settings_type
        SETTINGS_TYPES = RhodeCodeSetting.SETTINGS_TYPES
        converter = SETTINGS_TYPES.get(type_) or SETTINGS_TYPES['unicode']
        return converter(v)

    @app_settings_value.setter
    def app_settings_value(self, val):
        """
        Setter that will always make sure we use unicode in app_settings_value

        :param val:
        """
        self._app_settings_value = safe_unicode(val)

    @hybrid_property
    def app_settings_type(self):
        return self._app_settings_type

    @app_settings_type.setter
    def app_settings_type(self, val):
        SETTINGS_TYPES = RhodeCodeSetting.SETTINGS_TYPES
        if val not in SETTINGS_TYPES:
            raise Exception('type must be one of %s got %s'
                            % (SETTINGS_TYPES.keys(), val))
        self._app_settings_type = val

    def __unicode__(self):
        return u"<%s('%s:%s:%s[%s]')>" % (
            self.__class__.__name__, self.repository.repo_name,
            self.app_settings_name, self.app_settings_value,
            self.app_settings_type
        )


class RepoRhodeCodeUi(Base, BaseModel):
    __tablename__ = 'repo_rhodecode_ui'
    __table_args__ = (
        UniqueConstraint(
            'repository_id', 'ui_section', 'ui_key',
            name='uq_repo_rhodecode_ui_repository_id_section_key'),
        base_table_args
    )

    repository_id = Column(
        "repository_id", Integer(), ForeignKey('repositories.repo_id'),
        nullable=False)
    ui_id = Column(
        "ui_id", Integer(), nullable=False, unique=True, default=None,
        primary_key=True)
    ui_section = Column(
        "ui_section", String(255), nullable=True, unique=None, default=None)
    ui_key = Column(
        "ui_key", String(255), nullable=True, unique=None, default=None)
    ui_value = Column(
        "ui_value", String(255), nullable=True, unique=None, default=None)
    ui_active = Column(
        "ui_active", Boolean(), nullable=True, unique=None, default=True)

    repository = relationship('Repository')

    def __repr__(self):
        return '<%s[%s:%s]%s=>%s]>' % (
            self.__class__.__name__, self.repository.repo_name,
            self.ui_section, self.ui_key, self.ui_value)


class User(Base, BaseModel):
    __tablename__ = 'users'
    __table_args__ = (
        UniqueConstraint('username'), UniqueConstraint('email'),
        Index('u_username_idx', 'username'),
        Index('u_email_idx', 'email'),
        base_table_args
    )

    DEFAULT_USER = 'default'
    DEFAULT_USER_EMAIL = 'anonymous@rhodecode.org'
    DEFAULT_GRAVATAR_URL = 'https://secure.gravatar.com/avatar/{md5email}?d=identicon&s={size}'

    user_id = Column("user_id", Integer(), nullable=False, unique=True, default=None, primary_key=True)
    username = Column("username", String(255), nullable=True, unique=None, default=None)
    password = Column("password", String(255), nullable=True, unique=None, default=None)
    active = Column("active", Boolean(), nullable=True, unique=None, default=True)
    admin = Column("admin", Boolean(), nullable=True, unique=None, default=False)
    name = Column("firstname", String(255), nullable=True, unique=None, default=None)
    lastname = Column("lastname", String(255), nullable=True, unique=None, default=None)
    _email = Column("email", String(255), nullable=True, unique=None, default=None)
    last_login = Column("last_login", DateTime(timezone=False), nullable=True, unique=None, default=None)
    last_activity = Column('last_activity', DateTime(timezone=False), nullable=True, unique=None, default=None)
    description = Column('description', UnicodeText().with_variant(UnicodeText(1024), 'mysql'))

    extern_type = Column("extern_type", String(255), nullable=True, unique=None, default=None)
    extern_name = Column("extern_name", String(255), nullable=True, unique=None, default=None)
    _api_key = Column("api_key", String(255), nullable=True, unique=None, default=None)
    inherit_default_permissions = Column("inherit_default_permissions", Boolean(), nullable=False, unique=None, default=True)
    created_on = Column('created_on', DateTime(timezone=False), nullable=False, default=datetime.datetime.now)
    _user_data = Column("user_data", LargeBinary(), nullable=True)  # JSON data

    user_log = relationship('UserLog')
    user_perms = relationship('UserToPerm', primaryjoin="User.user_id==UserToPerm.user_id", cascade='all, delete-orphan')

    repositories = relationship('Repository')
    repository_groups = relationship('RepoGroup')
    user_groups = relationship('UserGroup')

    user_followers = relationship('UserFollowing', primaryjoin='UserFollowing.follows_user_id==User.user_id', cascade='all')
    followings = relationship('UserFollowing', primaryjoin='UserFollowing.user_id==User.user_id', cascade='all')

    repo_to_perm = relationship('UserRepoToPerm', primaryjoin='UserRepoToPerm.user_id==User.user_id', cascade='all, delete-orphan')
    repo_group_to_perm = relationship('UserRepoGroupToPerm', primaryjoin='UserRepoGroupToPerm.user_id==User.user_id', cascade='all, delete-orphan')
    user_group_to_perm = relationship('UserUserGroupToPerm', primaryjoin='UserUserGroupToPerm.user_id==User.user_id', cascade='all, delete-orphan')

    group_member = relationship('UserGroupMember', cascade='all')

    notifications = relationship('UserNotification', cascade='all')
    # notifications assigned to this user
    user_created_notifications = relationship('Notification', cascade='all')
    # comments created by this user
    user_comments = relationship('ChangesetComment', cascade='all')
    # user profile extra info
    user_emails = relationship('UserEmailMap', cascade='all')
    user_ip_map = relationship('UserIpMap', cascade='all')
    user_auth_tokens = relationship('UserApiKeys', cascade='all')
    user_ssh_keys = relationship('UserSshKeys', cascade='all')

    # gists
    user_gists = relationship('Gist', cascade='all')
    # user pull requests
    user_pull_requests = relationship('PullRequest', cascade='all')
    # external identities
    external_identities = relationship(
        'ExternalIdentity',
        primaryjoin="User.user_id==ExternalIdentity.local_user_id",
        cascade='all')
    # review rules
    user_review_rules = relationship('RepoReviewRuleUser', cascade='all')

    # artifacts owned
    artifacts = relationship('FileStore', primaryjoin='FileStore.user_id==User.user_id')

    # no cascade, set NULL
    scope_artifacts = relationship('FileStore', primaryjoin='FileStore.scope_user_id==User.user_id')

    def __unicode__(self):
        return u"<%s('id:%s:%s')>" % (self.__class__.__name__,
                                      self.user_id, self.username)

    @hybrid_property
    def email(self):
        return self._email

    @email.setter
    def email(self, val):
        self._email = val.lower() if val else None

    @hybrid_property
    def first_name(self):
        from rhodecode.lib import helpers as h
        if self.name:
            return h.escape(self.name)
        return self.name

    @hybrid_property
    def last_name(self):
        from rhodecode.lib import helpers as h
        if self.lastname:
            return h.escape(self.lastname)
        return self.lastname

    @hybrid_property
    def api_key(self):
        """
        Fetch if exist an auth-token with role ALL connected to this user
        """
        user_auth_token = UserApiKeys.query()\
            .filter(UserApiKeys.user_id == self.user_id)\
            .filter(or_(UserApiKeys.expires == -1,
                            UserApiKeys.expires >= time.time()))\
            .filter(UserApiKeys.role == UserApiKeys.ROLE_ALL).first()
        if user_auth_token:
            user_auth_token = user_auth_token.api_key

        return user_auth_token

    @api_key.setter
    def api_key(self, val):
        # don't allow to set API key this is deprecated for now
        self._api_key = None

    @property
    def reviewer_pull_requests(self):
        return PullRequestReviewers.query() \
            .options(joinedload(PullRequestReviewers.pull_request)) \
            .filter(PullRequestReviewers.user_id == self.user_id) \
            .all()

    @property
    def firstname(self):
        # alias for future
        return self.name

    @property
    def emails(self):
        other = UserEmailMap.query()\
            .filter(UserEmailMap.user == self) \
            .order_by(UserEmailMap.email_id.asc()) \
            .all()
        return [self.email] + [x.email for x in other]

    def emails_cached(self):
        emails = UserEmailMap.query()\
            .filter(UserEmailMap.user == self) \
            .order_by(UserEmailMap.email_id.asc())

        emails = emails.options(
            FromCache("sql_cache_short", "get_user_{}_emails".format(self.user_id))
        )

        return [self.email] + [x.email for x in emails]

    @property
    def auth_tokens(self):
        auth_tokens = self.get_auth_tokens()
        return [x.api_key for x in auth_tokens]

    def get_auth_tokens(self):
        return UserApiKeys.query()\
            .filter(UserApiKeys.user == self)\
            .order_by(UserApiKeys.user_api_key_id.asc())\
            .all()

    @LazyProperty
    def feed_token(self):
        return self.get_feed_token()

    def get_feed_token(self, cache=True):
        feed_tokens = UserApiKeys.query()\
            .filter(UserApiKeys.user == self)\
            .filter(UserApiKeys.role == UserApiKeys.ROLE_FEED)
        if cache:
            feed_tokens = feed_tokens.options(
                FromCache("sql_cache_short", "get_user_feed_token_%s" % self.user_id))

        feed_tokens = feed_tokens.all()
        if feed_tokens:
            return feed_tokens[0].api_key
        return 'NO_FEED_TOKEN_AVAILABLE'

    @LazyProperty
    def artifact_token(self):
        return self.get_artifact_token()

    def get_artifact_token(self, cache=True):
        artifacts_tokens = UserApiKeys.query()\
            .filter(UserApiKeys.user == self)\
            .filter(UserApiKeys.role == UserApiKeys.ROLE_ARTIFACT_DOWNLOAD)
        if cache:
            artifacts_tokens = artifacts_tokens.options(
                FromCache("sql_cache_short", "get_user_artifact_token_%s" % self.user_id))

        artifacts_tokens = artifacts_tokens.all()
        if artifacts_tokens:
            return artifacts_tokens[0].api_key
        return 'NO_ARTIFACT_TOKEN_AVAILABLE'

    @classmethod
    def get(cls, user_id, cache=False):
        if not user_id:
            return

        user = cls.query()
        if cache:
            user = user.options(
                FromCache("sql_cache_short", "get_users_%s" % user_id))
        return user.get(user_id)

    @classmethod
    def extra_valid_auth_tokens(cls, user, role=None):
        tokens = UserApiKeys.query().filter(UserApiKeys.user == user)\
                .filter(or_(UserApiKeys.expires == -1,
                            UserApiKeys.expires >= time.time()))
        if role:
            tokens = tokens.filter(or_(UserApiKeys.role == role,
                                       UserApiKeys.role == UserApiKeys.ROLE_ALL))
        return tokens.all()

    def authenticate_by_token(self, auth_token, roles=None, scope_repo_id=None):
        from rhodecode.lib import auth

        log.debug('Trying to authenticate user: %s via auth-token, '
                  'and roles: %s', self, roles)

        if not auth_token:
            return False

        roles = (roles or []) + [UserApiKeys.ROLE_ALL]
        tokens_q = UserApiKeys.query()\
            .filter(UserApiKeys.user_id == self.user_id)\
            .filter(or_(UserApiKeys.expires == -1,
                        UserApiKeys.expires >= time.time()))

        tokens_q = tokens_q.filter(UserApiKeys.role.in_(roles))

        crypto_backend = auth.crypto_backend()
        enc_token_map = {}
        plain_token_map = {}
        for token in tokens_q:
            if token.api_key.startswith(crypto_backend.ENC_PREF):
                enc_token_map[token.api_key] = token
            else:
                plain_token_map[token.api_key] = token
        log.debug(
            'Found %s plain and %s encrypted tokens to check for authentication for this user',
            len(plain_token_map), len(enc_token_map))

        # plain token match comes first
        match = plain_token_map.get(auth_token)

        # check encrypted tokens now
        if not match:
            for token_hash, token in enc_token_map.items():
                # NOTE(marcink): this is expensive to calculate, but most secure
                if crypto_backend.hash_check(auth_token, token_hash):
                    match = token
                    break

        if match:
            log.debug('Found matching token %s', match)
            if match.repo_id:
                log.debug('Found scope, checking for scope match of token %s', match)
                if match.repo_id == scope_repo_id:
                    return True
                else:
                    log.debug(
                        'AUTH_TOKEN: scope mismatch, token has a set repo scope: %s, '
                        'and calling scope is:%s, skipping further checks',
                         match.repo, scope_repo_id)
                    return False
            else:
                return True

        return False

    @property
    def ip_addresses(self):
        ret = UserIpMap.query().filter(UserIpMap.user == self).all()
        return [x.ip_addr for x in ret]

    @property
    def username_and_name(self):
        return '%s (%s %s)' % (self.username, self.first_name, self.last_name)

    @property
    def username_or_name_or_email(self):
        full_name = self.full_name if self.full_name is not ' ' else None
        return self.username or full_name or self.email

    @property
    def full_name(self):
        return '%s %s' % (self.first_name, self.last_name)

    @property
    def full_name_or_username(self):
        return ('%s %s' % (self.first_name, self.last_name)
                if (self.first_name and self.last_name) else self.username)

    @property
    def full_contact(self):
        return '%s %s <%s>' % (self.first_name, self.last_name, self.email)

    @property
    def short_contact(self):
        return '%s %s' % (self.first_name, self.last_name)

    @property
    def is_admin(self):
        return self.admin

    @property
    def language(self):
        return self.user_data.get('language')

    def AuthUser(self, **kwargs):
        """
        Returns instance of AuthUser for this user
        """
        from rhodecode.lib.auth import AuthUser
        return AuthUser(user_id=self.user_id, username=self.username, **kwargs)

    @hybrid_property
    def user_data(self):
        if not self._user_data:
            return {}

        try:
            return json.loads(self._user_data)
        except TypeError:
            return {}

    @user_data.setter
    def user_data(self, val):
        if not isinstance(val, dict):
            raise Exception('user_data must be dict, got %s' % type(val))
        try:
            self._user_data = json.dumps(val)
        except Exception:
            log.error(traceback.format_exc())

    @classmethod
    def get_by_username(cls, username, case_insensitive=False,
                        cache=False, identity_cache=False):
        session = Session()

        if case_insensitive:
            q = cls.query().filter(
                func.lower(cls.username) == func.lower(username))
        else:
            q = cls.query().filter(cls.username == username)

        if cache:
            if identity_cache:
                val = cls.identity_cache(session, 'username', username)
                if val:
                    return val
            else:
                cache_key = "get_user_by_name_%s" % _hash_key(username)
                q = q.options(
                    FromCache("sql_cache_short", cache_key))

        return q.scalar()

    @classmethod
    def get_by_auth_token(cls, auth_token, cache=False):
        q = UserApiKeys.query()\
            .filter(UserApiKeys.api_key == auth_token)\
            .filter(or_(UserApiKeys.expires == -1,
                        UserApiKeys.expires >= time.time()))
        if cache:
            q = q.options(
                FromCache("sql_cache_short", "get_auth_token_%s" % auth_token))

        match = q.first()
        if match:
            return match.user

    @classmethod
    def get_by_email(cls, email, case_insensitive=False, cache=False):

        if case_insensitive:
            q = cls.query().filter(func.lower(cls.email) == func.lower(email))

        else:
            q = cls.query().filter(cls.email == email)

        email_key = _hash_key(email)
        if cache:
            q = q.options(
                FromCache("sql_cache_short", "get_email_key_%s" % email_key))

        ret = q.scalar()
        if ret is None:
            q = UserEmailMap.query()
            # try fetching in alternate email map
            if case_insensitive:
                q = q.filter(func.lower(UserEmailMap.email) == func.lower(email))
            else:
                q = q.filter(UserEmailMap.email == email)
            q = q.options(joinedload(UserEmailMap.user))
            if cache:
                q = q.options(
                    FromCache("sql_cache_short", "get_email_map_key_%s" % email_key))
            ret = getattr(q.scalar(), 'user', None)

        return ret

    @classmethod
    def get_from_cs_author(cls, author):
        """
        Tries to get User objects out of commit author string

        :param author:
        """
        from rhodecode.lib.helpers import email, author_name
        # Valid email in the attribute passed, see if they're in the system
        _email = email(author)
        if _email:
            user = cls.get_by_email(_email, case_insensitive=True)
            if user:
                return user
        # Maybe we can match by username?
        _author = author_name(author)
        user = cls.get_by_username(_author, case_insensitive=True)
        if user:
            return user

    def update_userdata(self, **kwargs):
        usr = self
        old = usr.user_data
        old.update(**kwargs)
        usr.user_data = old
        Session().add(usr)
        log.debug('updated userdata with %s', kwargs)

    def update_lastlogin(self):
        """Update user lastlogin"""
        self.last_login = datetime.datetime.now()
        Session().add(self)
        log.debug('updated user %s lastlogin', self.username)

    def update_password(self, new_password):
        from rhodecode.lib.auth import get_crypt_password

        self.password = get_crypt_password(new_password)
        Session().add(self)

    @classmethod
    def get_first_super_admin(cls):
        user = User.query()\
            .filter(User.admin == true()) \
            .order_by(User.user_id.asc()) \
            .first()

        if user is None:
            raise Exception('FATAL: Missing administrative account!')
        return user

    @classmethod
    def get_all_super_admins(cls, only_active=False):
        """
        Returns all admin accounts sorted by username
        """
        qry = User.query().filter(User.admin == true()).order_by(User.username.asc())
        if only_active:
            qry = qry.filter(User.active == true())
        return qry.all()

    @classmethod
    def get_default_user(cls, cache=False, refresh=False):
        user = User.get_by_username(User.DEFAULT_USER, cache=cache)
        if user is None:
            raise Exception('FATAL: Missing default account!')
        if refresh:
            # The default user might be based on outdated state which
            # has been loaded from the cache.
            # A call to refresh() ensures that the
            # latest state from the database is used.
            Session().refresh(user)
        return user

    def _get_default_perms(self, user, suffix=''):
        from rhodecode.model.permission import PermissionModel
        return PermissionModel().get_default_perms(user.user_perms, suffix)

    def get_default_perms(self, suffix=''):
        return self._get_default_perms(self, suffix)

    def get_api_data(self, include_secrets=False, details='full'):
        """
        Common function for generating user related data for API

        :param include_secrets: By default secrets in the API data will be replaced
           by a placeholder value to prevent exposing this data by accident. In case
           this data shall be exposed, set this flag to ``True``.

        :param details: details can be 'basic|full' basic gives only a subset of
           the available user information that includes user_id, name and emails.
        """
        user = self
        user_data = self.user_data
        data = {
            'user_id': user.user_id,
            'username': user.username,
            'firstname': user.name,
            'lastname': user.lastname,
            'description': user.description,
            'email': user.email,
            'emails': user.emails,
        }
        if details == 'basic':
            return data

        auth_token_length = 40
        auth_token_replacement = '*' * auth_token_length

        extras = {
            'auth_tokens': [auth_token_replacement],
            'active': user.active,
            'admin': user.admin,
            'extern_type': user.extern_type,
            'extern_name': user.extern_name,
            'last_login': user.last_login,
            'last_activity': user.last_activity,
            'ip_addresses': user.ip_addresses,
            'language': user_data.get('language')
        }
        data.update(extras)

        if include_secrets:
            data['auth_tokens'] = user.auth_tokens
        return data

    def __json__(self):
        data = {
            'full_name': self.full_name,
            'full_name_or_username': self.full_name_or_username,
            'short_contact': self.short_contact,
            'full_contact': self.full_contact,
        }
        data.update(self.get_api_data())
        return data


class UserApiKeys(Base, BaseModel):
    __tablename__ = 'user_api_keys'
    __table_args__ = (
        Index('uak_api_key_idx', 'api_key'),
        Index('uak_api_key_expires_idx', 'api_key', 'expires'),
        base_table_args
    )
    __mapper_args__ = {}

    # ApiKey role
    ROLE_ALL = 'token_role_all'
    ROLE_HTTP = 'token_role_http'
    ROLE_VCS = 'token_role_vcs'
    ROLE_API = 'token_role_api'
    ROLE_FEED = 'token_role_feed'
    ROLE_ARTIFACT_DOWNLOAD = 'role_artifact_download'
    ROLE_PASSWORD_RESET = 'token_password_reset'

    ROLES = [ROLE_ALL, ROLE_HTTP, ROLE_VCS, ROLE_API, ROLE_FEED, ROLE_ARTIFACT_DOWNLOAD]

    user_api_key_id = Column("user_api_key_id", Integer(), nullable=False, unique=True, default=None, primary_key=True)
    user_id = Column("user_id", Integer(), ForeignKey('users.user_id'), nullable=True, unique=None, default=None)
    api_key = Column("api_key", String(255), nullable=False, unique=True)
    description = Column('description', UnicodeText().with_variant(UnicodeText(1024), 'mysql'))
    expires = Column('expires', Float(53), nullable=False)
    role = Column('role', String(255), nullable=True)
    created_on = Column('created_on', DateTime(timezone=False), nullable=False, default=datetime.datetime.now)

    # scope columns
    repo_id = Column(
        'repo_id', Integer(), ForeignKey('repositories.repo_id'),
        nullable=True, unique=None, default=None)
    repo = relationship('Repository', lazy='joined')

    repo_group_id = Column(
        'repo_group_id', Integer(), ForeignKey('groups.group_id'),
        nullable=True, unique=None, default=None)
    repo_group = relationship('RepoGroup', lazy='joined')

    user = relationship('User', lazy='joined')

    def __unicode__(self):
        return u"<%s('%s')>" % (self.__class__.__name__, self.role)

    def __json__(self):
        data = {
            'auth_token': self.api_key,
            'role': self.role,
            'scope': self.scope_humanized,
            'expired': self.expired
        }
        return data

    def get_api_data(self, include_secrets=False):
        data = self.__json__()
        if include_secrets:
            return data
        else:
            data['auth_token'] = self.token_obfuscated
            return data

    @hybrid_property
    def description_safe(self):
        from rhodecode.lib import helpers as h
        return h.escape(self.description)

    @property
    def expired(self):
        if self.expires == -1:
            return False
        return time.time() > self.expires

    @classmethod
    def _get_role_name(cls, role):
        return {
            cls.ROLE_ALL: _('all'),
            cls.ROLE_HTTP: _('http/web interface'),
            cls.ROLE_VCS: _('vcs (git/hg/svn protocol)'),
            cls.ROLE_API: _('api calls'),
            cls.ROLE_FEED: _('feed access'),
            cls.ROLE_ARTIFACT_DOWNLOAD: _('artifacts downloads'),
        }.get(role, role)

    @property
    def role_humanized(self):
        return self._get_role_name(self.role)

    def _get_scope(self):
        if self.repo:
            return 'Repository: {}'.format(self.repo.repo_name)
        if self.repo_group:
            return 'RepositoryGroup: {} (recursive)'.format(self.repo_group.group_name)
        return 'Global'

    @property
    def scope_humanized(self):
        return self._get_scope()

    @property
    def token_obfuscated(self):
        if self.api_key:
            return self.api_key[:4] + "****"


class UserEmailMap(Base, BaseModel):
    __tablename__ = 'user_email_map'
    __table_args__ = (
        Index('uem_email_idx', 'email'),
        UniqueConstraint('email'),
        base_table_args
    )
    __mapper_args__ = {}

    email_id = Column("email_id", Integer(), nullable=False, unique=True, default=None, primary_key=True)
    user_id = Column("user_id", Integer(), ForeignKey('users.user_id'), nullable=True, unique=None, default=None)
    _email = Column("email", String(255), nullable=True, unique=False, default=None)
    user = relationship('User', lazy='joined')

    @validates('_email')
    def validate_email(self, key, email):
        # check if this email is not main one
        main_email = Session().query(User).filter(User.email == email).scalar()
        if main_email is not None:
            raise AttributeError('email %s is present is user table' % email)
        return email

    @hybrid_property
    def email(self):
        return self._email

    @email.setter
    def email(self, val):
        self._email = val.lower() if val else None


class UserIpMap(Base, BaseModel):
    __tablename__ = 'user_ip_map'
    __table_args__ = (
        UniqueConstraint('user_id', 'ip_addr'),
        base_table_args
    )
    __mapper_args__ = {}

    ip_id = Column("ip_id", Integer(), nullable=False, unique=True, default=None, primary_key=True)
    user_id = Column("user_id", Integer(), ForeignKey('users.user_id'), nullable=True, unique=None, default=None)
    ip_addr = Column("ip_addr", String(255), nullable=True, unique=False, default=None)
    active = Column("active", Boolean(), nullable=True, unique=None, default=True)
    description = Column("description", String(10000), nullable=True, unique=None, default=None)
    user = relationship('User', lazy='joined')

    @hybrid_property
    def description_safe(self):
        from rhodecode.lib import helpers as h
        return h.escape(self.description)

    @classmethod
    def _get_ip_range(cls, ip_addr):
        net = ipaddress.ip_network(safe_unicode(ip_addr), strict=False)
        return [str(net.network_address), str(net.broadcast_address)]

    def __json__(self):
        return {
          'ip_addr': self.ip_addr,
          'ip_range': self._get_ip_range(self.ip_addr),
        }

    def __unicode__(self):
        return u"<%s('user_id:%s=>%s')>" % (self.__class__.__name__,
                                            self.user_id, self.ip_addr)


class UserSshKeys(Base, BaseModel):
    __tablename__ = 'user_ssh_keys'
    __table_args__ = (
        Index('usk_ssh_key_fingerprint_idx', 'ssh_key_fingerprint'),

        UniqueConstraint('ssh_key_fingerprint'),

        base_table_args
    )
    __mapper_args__ = {}

    ssh_key_id = Column('ssh_key_id', Integer(), nullable=False, unique=True, default=None, primary_key=True)
    ssh_key_data = Column('ssh_key_data', String(10240), nullable=False, unique=None, default=None)
    ssh_key_fingerprint = Column('ssh_key_fingerprint', String(255), nullable=False, unique=None, default=None)

    description = Column('description', UnicodeText().with_variant(UnicodeText(1024), 'mysql'))

    created_on = Column('created_on', DateTime(timezone=False), nullable=False, default=datetime.datetime.now)
    accessed_on = Column('accessed_on', DateTime(timezone=False), nullable=True, default=None)
    user_id = Column('user_id', Integer(), ForeignKey('users.user_id'), nullable=True, unique=None, default=None)

    user = relationship('User', lazy='joined')

    def __json__(self):
        data = {
            'ssh_fingerprint': self.ssh_key_fingerprint,
            'description': self.description,
            'created_on': self.created_on
        }
        return data

    def get_api_data(self):
        data = self.__json__()
        return data


class UserLog(Base, BaseModel):
    __tablename__ = 'user_logs'
    __table_args__ = (
        base_table_args,
    )

    VERSION_1 = 'v1'
    VERSION_2 = 'v2'
    VERSIONS = [VERSION_1, VERSION_2]

    user_log_id = Column("user_log_id", Integer(), nullable=False, unique=True, default=None, primary_key=True)
    user_id = Column("user_id", Integer(), ForeignKey('users.user_id',ondelete='SET NULL'), nullable=True, unique=None, default=None)
    username = Column("username", String(255), nullable=True, unique=None, default=None)
    repository_id = Column("repository_id", Integer(), ForeignKey('repositories.repo_id', ondelete='SET NULL'), nullable=True, unique=None, default=None)
    repository_name = Column("repository_name", String(255), nullable=True, unique=None, default=None)
    user_ip = Column("user_ip", String(255), nullable=True, unique=None, default=None)
    action = Column("action", Text().with_variant(Text(1200000), 'mysql'), nullable=True, unique=None, default=None)
    action_date = Column("action_date", DateTime(timezone=False), nullable=True, unique=None, default=None)

    version = Column("version", String(255), nullable=True, default=VERSION_1)
    user_data = Column('user_data_json', MutationObj.as_mutable(JsonType(dialect_map=dict(mysql=LONGTEXT()))))
    action_data = Column('action_data_json', MutationObj.as_mutable(JsonType(dialect_map=dict(mysql=LONGTEXT()))))

    def __unicode__(self):
        return u"<%s('id:%s:%s')>" % (
            self.__class__.__name__, self.repository_name, self.action)

    def __json__(self):
        return {
            'user_id': self.user_id,
            'username': self.username,
            'repository_id': self.repository_id,
            'repository_name': self.repository_name,
            'user_ip': self.user_ip,
            'action_date': self.action_date,
            'action': self.action,
        }

    @hybrid_property
    def entry_id(self):
        return self.user_log_id

    @property
    def action_as_day(self):
        return datetime.date(*self.action_date.timetuple()[:3])

    user = relationship('User')
    repository = relationship('Repository', cascade='')


class UserGroup(Base, BaseModel):
    __tablename__ = 'users_groups'
    __table_args__ = (
        base_table_args,
    )

    users_group_id = Column("users_group_id", Integer(), nullable=False, unique=True, default=None, primary_key=True)
    users_group_name = Column("users_group_name", String(255), nullable=False, unique=True, default=None)
    user_group_description = Column("user_group_description", String(10000), nullable=True, unique=None, default=None)
    users_group_active = Column("users_group_active", Boolean(), nullable=True, unique=None, default=None)
    inherit_default_permissions = Column("users_group_inherit_default_permissions", Boolean(), nullable=False, unique=None, default=True)
    user_id = Column("user_id", Integer(), ForeignKey('users.user_id'), nullable=False, unique=False, default=None)
    created_on = Column('created_on', DateTime(timezone=False), nullable=False, default=datetime.datetime.now)
    _group_data = Column("group_data", LargeBinary(), nullable=True)  # JSON data

    members = relationship('UserGroupMember', cascade="all, delete-orphan", lazy="joined")
    users_group_to_perm = relationship('UserGroupToPerm', cascade='all')
    users_group_repo_to_perm = relationship('UserGroupRepoToPerm', cascade='all')
    users_group_repo_group_to_perm = relationship('UserGroupRepoGroupToPerm', cascade='all')
    user_user_group_to_perm = relationship('UserUserGroupToPerm', cascade='all')
    user_group_user_group_to_perm = relationship('UserGroupUserGroupToPerm ', primaryjoin="UserGroupUserGroupToPerm.target_user_group_id==UserGroup.users_group_id", cascade='all')

    user_group_review_rules = relationship('RepoReviewRuleUserGroup', cascade='all')
    user = relationship('User', primaryjoin="User.user_id==UserGroup.user_id")

    @classmethod
    def _load_group_data(cls, column):
        if not column:
            return {}

        try:
            return json.loads(column) or {}
        except TypeError:
            return {}

    @hybrid_property
    def description_safe(self):
        from rhodecode.lib import helpers as h
        return h.escape(self.user_group_description)

    @hybrid_property
    def group_data(self):
        return self._load_group_data(self._group_data)

    @group_data.expression
    def group_data(self, **kwargs):
        return self._group_data

    @group_data.setter
    def group_data(self, val):
        try:
            self._group_data = json.dumps(val)
        except Exception:
            log.error(traceback.format_exc())

    @classmethod
    def _load_sync(cls, group_data):
        if group_data:
            return group_data.get('extern_type')

    @property
    def sync(self):
        return self._load_sync(self.group_data)

    def __unicode__(self):
        return u"<%s('id:%s:%s')>" % (self.__class__.__name__,
                                      self.users_group_id,
                                      self.users_group_name)

    @classmethod
    def get_by_group_name(cls, group_name, cache=False,
                          case_insensitive=False):
        if case_insensitive:
            q = cls.query().filter(func.lower(cls.users_group_name) ==
                                   func.lower(group_name))

        else:
            q = cls.query().filter(cls.users_group_name == group_name)
        if cache:
            q = q.options(
                FromCache("sql_cache_short", "get_group_%s" % _hash_key(group_name)))
        return q.scalar()

    @classmethod
    def get(cls, user_group_id, cache=False):
        if not user_group_id:
            return

        user_group = cls.query()
        if cache:
            user_group = user_group.options(
                FromCache("sql_cache_short", "get_users_group_%s" % user_group_id))
        return user_group.get(user_group_id)

    def permissions(self, with_admins=True, with_owner=True,
                    expand_from_user_groups=False):
        """
        Permissions for user groups
        """
        _admin_perm = 'usergroup.admin'

        owner_row = []
        if with_owner:
            usr = AttributeDict(self.user.get_dict())
            usr.owner_row = True
            usr.permission = _admin_perm
            owner_row.append(usr)

        super_admin_ids = []
        super_admin_rows = []
        if with_admins:
            for usr in User.get_all_super_admins():
                super_admin_ids.append(usr.user_id)
                # if this admin is also owner, don't double the record
                if usr.user_id == owner_row[0].user_id:
                    owner_row[0].admin_row = True
                else:
                    usr = AttributeDict(usr.get_dict())
                    usr.admin_row = True
                    usr.permission = _admin_perm
                    super_admin_rows.append(usr)

        q = UserUserGroupToPerm.query().filter(UserUserGroupToPerm.user_group == self)
        q = q.options(joinedload(UserUserGroupToPerm.user_group),
                      joinedload(UserUserGroupToPerm.user),
                      joinedload(UserUserGroupToPerm.permission),)

        # get owners and admins and permissions. We do a trick of re-writing
        # objects from sqlalchemy to named-tuples due to sqlalchemy session
        # has a global reference and changing one object propagates to all
        # others. This means if admin is also an owner admin_row that change
        # would propagate to both objects
        perm_rows = []
        for _usr in q.all():
            usr = AttributeDict(_usr.user.get_dict())
            # if this user is also owner/admin, mark as duplicate record
            if usr.user_id == owner_row[0].user_id or usr.user_id in super_admin_ids:
                usr.duplicate_perm = True
            usr.permission = _usr.permission.permission_name
            perm_rows.append(usr)

        # filter the perm rows by 'default' first and then sort them by
        # admin,write,read,none permissions sorted again alphabetically in
        # each group
        perm_rows = sorted(perm_rows, key=display_user_sort)

        user_groups_rows = []
        if expand_from_user_groups:
            for ug in self.permission_user_groups(with_members=True):
                for user_data in ug.members:
                    user_groups_rows.append(user_data)

        return super_admin_rows + owner_row + perm_rows + user_groups_rows

    def permission_user_groups(self, with_members=False):
        q = UserGroupUserGroupToPerm.query()\
            .filter(UserGroupUserGroupToPerm.target_user_group == self)
        q = q.options(joinedload(UserGroupUserGroupToPerm.user_group),
                      joinedload(UserGroupUserGroupToPerm.target_user_group),
                      joinedload(UserGroupUserGroupToPerm.permission),)

        perm_rows = []
        for _user_group in q.all():
            entry = AttributeDict(_user_group.user_group.get_dict())
            entry.permission = _user_group.permission.permission_name
            if with_members:
                entry.members = [x.user.get_dict()
                                 for x in _user_group.user_group.members]
            perm_rows.append(entry)

        perm_rows = sorted(perm_rows, key=display_user_group_sort)
        return perm_rows

    def _get_default_perms(self, user_group, suffix=''):
        from rhodecode.model.permission import PermissionModel
        return PermissionModel().get_default_perms(user_group.users_group_to_perm, suffix)

    def get_default_perms(self, suffix=''):
        return self._get_default_perms(self, suffix)

    def get_api_data(self, with_group_members=True, include_secrets=False):
        """
        :param include_secrets: See :meth:`User.get_api_data`, this parameter is
           basically forwarded.

        """
        user_group = self
        data = {
            'users_group_id': user_group.users_group_id,
            'group_name': user_group.users_group_name,
            'group_description': user_group.user_group_description,
            'active': user_group.users_group_active,
            'owner': user_group.user.username,
            'sync': user_group.sync,
            'owner_email': user_group.user.email,
        }

        if with_group_members:
            users = []
            for user in user_group.members:
                user = user.user
                users.append(user.get_api_data(include_secrets=include_secrets))
            data['users'] = users

        return data


class UserGroupMember(Base, BaseModel):
    __tablename__ = 'users_groups_members'
    __table_args__ = (
        base_table_args,
    )

    users_group_member_id = Column("users_group_member_id", Integer(), nullable=False, unique=True, default=None, primary_key=True)
    users_group_id = Column("users_group_id", Integer(), ForeignKey('users_groups.users_group_id'), nullable=False, unique=None, default=None)
    user_id = Column("user_id", Integer(), ForeignKey('users.user_id'), nullable=False, unique=None, default=None)

    user = relationship('User', lazy='joined')
    users_group = relationship('UserGroup')

    def __init__(self, gr_id='', u_id=''):
        self.users_group_id = gr_id
        self.user_id = u_id


class RepositoryField(Base, BaseModel):
    __tablename__ = 'repositories_fields'
    __table_args__ = (
        UniqueConstraint('repository_id', 'field_key'),  # no-multi field
        base_table_args,
    )

    PREFIX = 'ex_'  # prefix used in form to not conflict with already existing fields

    repo_field_id = Column("repo_field_id", Integer(), nullable=False, unique=True, default=None, primary_key=True)
    repository_id = Column("repository_id", Integer(), ForeignKey('repositories.repo_id'), nullable=False, unique=None, default=None)
    field_key = Column("field_key", String(250))
    field_label = Column("field_label", String(1024), nullable=False)
    field_value = Column("field_value", String(10000), nullable=False)
    field_desc = Column("field_desc", String(1024), nullable=False)
    field_type = Column("field_type", String(255), nullable=False, unique=None)
    created_on = Column('created_on', DateTime(timezone=False), nullable=False, default=datetime.datetime.now)

    repository = relationship('Repository')

    @property
    def field_key_prefixed(self):
        return 'ex_%s' % self.field_key

    @classmethod
    def un_prefix_key(cls, key):
        if key.startswith(cls.PREFIX):
            return key[len(cls.PREFIX):]
        return key

    @classmethod
    def get_by_key_name(cls, key, repo):
        row = cls.query()\
                .filter(cls.repository == repo)\
                .filter(cls.field_key == key).scalar()
        return row


class Repository(Base, BaseModel):
    __tablename__ = 'repositories'
    __table_args__ = (
        Index('r_repo_name_idx', 'repo_name', mysql_length=255),
        base_table_args,
    )
    DEFAULT_CLONE_URI = '{scheme}://{user}@{netloc}/{repo}'
    DEFAULT_CLONE_URI_ID = '{scheme}://{user}@{netloc}/_{repoid}'
    DEFAULT_CLONE_URI_SSH = 'ssh://{sys_user}@{hostname}/{repo}'

    STATE_CREATED = 'repo_state_created'
    STATE_PENDING = 'repo_state_pending'
    STATE_ERROR = 'repo_state_error'

    LOCK_AUTOMATIC = 'lock_auto'
    LOCK_API = 'lock_api'
    LOCK_WEB = 'lock_web'
    LOCK_PULL = 'lock_pull'

    NAME_SEP = URL_SEP

    repo_id = Column(
        "repo_id", Integer(), nullable=False, unique=True, default=None,
        primary_key=True)
    _repo_name = Column(
        "repo_name", Text(), nullable=False, default=None)
    _repo_name_hash = Column(
        "repo_name_hash", String(255), nullable=False, unique=True)
    repo_state = Column("repo_state", String(255), nullable=True)

    clone_uri = Column(
        "clone_uri", EncryptedTextValue(), nullable=True, unique=False,
        default=None)
    push_uri = Column(
        "push_uri", EncryptedTextValue(), nullable=True, unique=False,
        default=None)
    repo_type = Column(
        "repo_type", String(255), nullable=False, unique=False, default=None)
    user_id = Column(
        "user_id", Integer(), ForeignKey('users.user_id'), nullable=False,
        unique=False, default=None)
    private = Column(
        "private", Boolean(), nullable=True, unique=None, default=None)
    archived = Column(
        "archived", Boolean(), nullable=True, unique=None, default=None)
    enable_statistics = Column(
        "statistics", Boolean(), nullable=True, unique=None, default=True)
    enable_downloads = Column(
        "downloads", Boolean(), nullable=True, unique=None, default=True)
    description = Column(
        "description", String(10000), nullable=True, unique=None, default=None)
    created_on = Column(
        'created_on', DateTime(timezone=False), nullable=True, unique=None,
        default=datetime.datetime.now)
    updated_on = Column(
        'updated_on', DateTime(timezone=False), nullable=True, unique=None,
        default=datetime.datetime.now)
    _landing_revision = Column(
        "landing_revision", String(255), nullable=False, unique=False,
        default=None)
    enable_locking = Column(
        "enable_locking", Boolean(), nullable=False, unique=None,
        default=False)
    _locked = Column(
        "locked", String(255), nullable=True, unique=False, default=None)
    _changeset_cache = Column(
        "changeset_cache", LargeBinary(), nullable=True)  # JSON data

    fork_id = Column(
        "fork_id", Integer(), ForeignKey('repositories.repo_id'),
        nullable=True, unique=False, default=None)
    group_id = Column(
        "group_id", Integer(), ForeignKey('groups.group_id'), nullable=True,
        unique=False, default=None)

    user = relationship('User', lazy='joined')
    fork = relationship('Repository', remote_side=repo_id, lazy='joined')
    group = relationship('RepoGroup', lazy='joined')
    repo_to_perm = relationship(
        'UserRepoToPerm', cascade='all',
        order_by='UserRepoToPerm.repo_to_perm_id')
    users_group_to_perm = relationship('UserGroupRepoToPerm', cascade='all')
    stats = relationship('Statistics', cascade='all', uselist=False)

    followers = relationship(
        'UserFollowing',
        primaryjoin='UserFollowing.follows_repo_id==Repository.repo_id',
        cascade='all')
    extra_fields = relationship(
        'RepositoryField', cascade="all, delete-orphan")
    logs = relationship('UserLog')
    comments = relationship(
        'ChangesetComment', cascade="all, delete-orphan")
    pull_requests_source = relationship(
        'PullRequest',
        primaryjoin='PullRequest.source_repo_id==Repository.repo_id',
        cascade="all, delete-orphan")
    pull_requests_target = relationship(
        'PullRequest',
        primaryjoin='PullRequest.target_repo_id==Repository.repo_id',
        cascade="all, delete-orphan")
    ui = relationship('RepoRhodeCodeUi', cascade="all")
    settings = relationship('RepoRhodeCodeSetting', cascade="all")
    integrations = relationship('Integration', cascade="all, delete-orphan")

    scoped_tokens = relationship('UserApiKeys', cascade="all")

    # no cascade, set NULL
    artifacts = relationship('FileStore', primaryjoin='FileStore.scope_repo_id==Repository.repo_id')

    def __unicode__(self):
        return u"<%s('%s:%s')>" % (self.__class__.__name__, self.repo_id,
                                   safe_unicode(self.repo_name))

    @hybrid_property
    def description_safe(self):
        from rhodecode.lib import helpers as h
        return h.escape(self.description)

    @hybrid_property
    def landing_rev(self):
        # always should return [rev_type, rev]
        if self._landing_revision:
            _rev_info = self._landing_revision.split(':')
            if len(_rev_info) < 2:
                _rev_info.insert(0, 'rev')
            return [_rev_info[0], _rev_info[1]]
        return [None, None]

    @landing_rev.setter
    def landing_rev(self, val):
        if ':' not in val:
            raise ValueError('value must be delimited with `:` and consist '
                             'of <rev_type>:<rev>, got %s instead' % val)
        self._landing_revision = val

    @hybrid_property
    def locked(self):
        if self._locked:
            user_id, timelocked, reason = self._locked.split(':')
            lock_values = int(user_id), timelocked, reason
        else:
            lock_values = [None, None, None]
        return lock_values

    @locked.setter
    def locked(self, val):
        if val and isinstance(val, (list, tuple)):
            self._locked = ':'.join(map(str, val))
        else:
            self._locked = None

    @hybrid_property
    def changeset_cache(self):
        from rhodecode.lib.vcs.backends.base import EmptyCommit
        dummy = EmptyCommit().__json__()
        if not self._changeset_cache:
            dummy['source_repo_id'] = self.repo_id
            return json.loads(json.dumps(dummy))

        try:
            return json.loads(self._changeset_cache)
        except TypeError:
            return dummy
        except Exception:
            log.error(traceback.format_exc())
            return dummy

    @changeset_cache.setter
    def changeset_cache(self, val):
        try:
            self._changeset_cache = json.dumps(val)
        except Exception:
            log.error(traceback.format_exc())

    @hybrid_property
    def repo_name(self):
        return self._repo_name

    @repo_name.setter
    def repo_name(self, value):
        self._repo_name = value
        self._repo_name_hash = hashlib.sha1(safe_str(value)).hexdigest()

    @classmethod
    def normalize_repo_name(cls, repo_name):
        """
        Normalizes os specific repo_name to the format internally stored inside
        database using URL_SEP

        :param cls:
        :param repo_name:
        """
        return cls.NAME_SEP.join(repo_name.split(os.sep))

    @classmethod
    def get_by_repo_name(cls, repo_name, cache=False, identity_cache=False):
        session = Session()
        q = session.query(cls).filter(cls.repo_name == repo_name)

        if cache:
            if identity_cache:
                val = cls.identity_cache(session, 'repo_name', repo_name)
                if val:
                    return val
            else:
                cache_key = "get_repo_by_name_%s" % _hash_key(repo_name)
                q = q.options(
                    FromCache("sql_cache_short", cache_key))

        return q.scalar()

    @classmethod
    def get_by_id_or_repo_name(cls, repoid):
        if isinstance(repoid, (int, long)):
            try:
                repo = cls.get(repoid)
            except ValueError:
                repo = None
        else:
            repo = cls.get_by_repo_name(repoid)
        return repo

    @classmethod
    def get_by_full_path(cls, repo_full_path):
        repo_name = repo_full_path.split(cls.base_path(), 1)[-1]
        repo_name = cls.normalize_repo_name(repo_name)
        return cls.get_by_repo_name(repo_name.strip(URL_SEP))

    @classmethod
    def get_repo_forks(cls, repo_id):
        return cls.query().filter(Repository.fork_id == repo_id)

    @classmethod
    def base_path(cls):
        """
        Returns base path when all repos are stored

        :param cls:
        """
        q = Session().query(RhodeCodeUi)\
            .filter(RhodeCodeUi.ui_key == cls.NAME_SEP)
        q = q.options(FromCache("sql_cache_short", "repository_repo_path"))
        return q.one().ui_value

    @classmethod
    def get_all_repos(cls, user_id=Optional(None), group_id=Optional(None),
                      case_insensitive=True, archived=False):
        q = Repository.query()

        if not archived:
            q = q.filter(Repository.archived.isnot(true()))

        if not isinstance(user_id, Optional):
            q = q.filter(Repository.user_id == user_id)

        if not isinstance(group_id, Optional):
            q = q.filter(Repository.group_id == group_id)

        if case_insensitive:
            q = q.order_by(func.lower(Repository.repo_name))
        else:
            q = q.order_by(Repository.repo_name)

        return q.all()

    @property
    def repo_uid(self):
        return '_{}'.format(self.repo_id)

    @property
    def forks(self):
        """
        Return forks of this repo
        """
        return Repository.get_repo_forks(self.repo_id)

    @property
    def parent(self):
        """
        Returns fork parent
        """
        return self.fork

    @property
    def just_name(self):
        return self.repo_name.split(self.NAME_SEP)[-1]

    @property
    def groups_with_parents(self):
        groups = []
        if self.group is None:
            return groups

        cur_gr = self.group
        groups.insert(0, cur_gr)
        while 1:
            gr = getattr(cur_gr, 'parent_group', None)
            cur_gr = cur_gr.parent_group
            if gr is None:
                break
            groups.insert(0, gr)

        return groups

    @property
    def groups_and_repo(self):
        return self.groups_with_parents, self

    @LazyProperty
    def repo_path(self):
        """
        Returns base full path for that repository means where it actually
        exists on a filesystem
        """
        q = Session().query(RhodeCodeUi).filter(
            RhodeCodeUi.ui_key == self.NAME_SEP)
        q = q.options(FromCache("sql_cache_short", "repository_repo_path"))
        return q.one().ui_value

    @property
    def repo_full_path(self):
        p = [self.repo_path]
        # we need to split the name by / since this is how we store the
        # names in the database, but that eventually needs to be converted
        # into a valid system path
        p += self.repo_name.split(self.NAME_SEP)
        return os.path.join(*map(safe_unicode, p))

    @property
    def cache_keys(self):
        """
        Returns associated cache keys for that repo
        """
        invalidation_namespace = CacheKey.REPO_INVALIDATION_NAMESPACE.format(
            repo_id=self.repo_id)
        return CacheKey.query()\
            .filter(CacheKey.cache_args == invalidation_namespace)\
            .order_by(CacheKey.cache_key)\
            .all()

    @property
    def cached_diffs_relative_dir(self):
        """
        Return a relative to the repository store path of cached diffs
        used for safe display for users, who shouldn't know the absolute store
        path
        """
        return os.path.join(
            os.path.dirname(self.repo_name),
            self.cached_diffs_dir.split(os.path.sep)[-1])

    @property
    def cached_diffs_dir(self):
        path = self.repo_full_path
        return os.path.join(
            os.path.dirname(path),
            '.__shadow_diff_cache_repo_{}'.format(self.repo_id))

    def cached_diffs(self):
        diff_cache_dir = self.cached_diffs_dir
        if os.path.isdir(diff_cache_dir):
            return os.listdir(diff_cache_dir)
        return []

    def shadow_repos(self):
        shadow_repos_pattern = '.__shadow_repo_{}'.format(self.repo_id)
        return [
            x for x in os.listdir(os.path.dirname(self.repo_full_path))
            if x.startswith(shadow_repos_pattern)]

    def get_new_name(self, repo_name):
        """
        returns new full repository name based on assigned group and new new

        :param group_name:
        """
        path_prefix = self.group.full_path_splitted if self.group else []
        return self.NAME_SEP.join(path_prefix + [repo_name])

    @property
    def _config(self):
        """
        Returns db based config object.
        """
        from rhodecode.lib.utils import make_db_config
        return make_db_config(clear_session=False, repo=self)

    def permissions(self, with_admins=True, with_owner=True,
                    expand_from_user_groups=False):
        """
        Permissions for repositories
        """
        _admin_perm = 'repository.admin'

        owner_row = []
        if with_owner:
            usr = AttributeDict(self.user.get_dict())
            usr.owner_row = True
            usr.permission = _admin_perm
            usr.permission_id = None
            owner_row.append(usr)

        super_admin_ids = []
        super_admin_rows = []
        if with_admins:
            for usr in User.get_all_super_admins():
                super_admin_ids.append(usr.user_id)
                # if this admin is also owner, don't double the record
                if usr.user_id == owner_row[0].user_id:
                    owner_row[0].admin_row = True
                else:
                    usr = AttributeDict(usr.get_dict())
                    usr.admin_row = True
                    usr.permission = _admin_perm
                    usr.permission_id = None
                    super_admin_rows.append(usr)

        q = UserRepoToPerm.query().filter(UserRepoToPerm.repository == self)
        q = q.options(joinedload(UserRepoToPerm.repository),
                      joinedload(UserRepoToPerm.user),
                      joinedload(UserRepoToPerm.permission),)

        # get owners and admins and permissions. We do a trick of re-writing
        # objects from sqlalchemy to named-tuples due to sqlalchemy session
        # has a global reference and changing one object propagates to all
        # others. This means if admin is also an owner admin_row that change
        # would propagate to both objects
        perm_rows = []
        for _usr in q.all():
            usr = AttributeDict(_usr.user.get_dict())
            # if this user is also owner/admin, mark as duplicate record
            if usr.user_id == owner_row[0].user_id or usr.user_id in super_admin_ids:
                usr.duplicate_perm = True
            # also check if this permission is maybe used by branch_permissions
            if _usr.branch_perm_entry:
                usr.branch_rules = [x.branch_rule_id for x in _usr.branch_perm_entry]

            usr.permission = _usr.permission.permission_name
            usr.permission_id = _usr.repo_to_perm_id
            perm_rows.append(usr)

        # filter the perm rows by 'default' first and then sort them by
        # admin,write,read,none permissions sorted again alphabetically in
        # each group
        perm_rows = sorted(perm_rows, key=display_user_sort)

        user_groups_rows = []
        if expand_from_user_groups:
            for ug in self.permission_user_groups(with_members=True):
                for user_data in ug.members:
                    user_groups_rows.append(user_data)

        return super_admin_rows + owner_row + perm_rows + user_groups_rows

    def permission_user_groups(self, with_members=True):
        q = UserGroupRepoToPerm.query()\
            .filter(UserGroupRepoToPerm.repository == self)
        q = q.options(joinedload(UserGroupRepoToPerm.repository),
                      joinedload(UserGroupRepoToPerm.users_group),
                      joinedload(UserGroupRepoToPerm.permission),)

        perm_rows = []
        for _user_group in q.all():
            entry = AttributeDict(_user_group.users_group.get_dict())
            entry.permission = _user_group.permission.permission_name
            if with_members:
                entry.members = [x.user.get_dict()
                                 for x in _user_group.users_group.members]
            perm_rows.append(entry)

        perm_rows = sorted(perm_rows, key=display_user_group_sort)
        return perm_rows

    def get_api_data(self, include_secrets=False):
        """
        Common function for generating repo api data

        :param include_secrets: See :meth:`User.get_api_data`.

        """
        # TODO: mikhail: Here there is an anti-pattern, we probably need to
        # move this methods on models level.
        from rhodecode.model.settings import SettingsModel
        from rhodecode.model.repo import RepoModel

        repo = self
        _user_id, _time, _reason = self.locked

        data = {
            'repo_id': repo.repo_id,
            'repo_name': repo.repo_name,
            'repo_type': repo.repo_type,
            'clone_uri': repo.clone_uri or '',
            'push_uri': repo.push_uri or '',
            'url': RepoModel().get_url(self),
            'private': repo.private,
            'created_on': repo.created_on,
            'description': repo.description_safe,
            'landing_rev': repo.landing_rev,
            'owner': repo.user.username,
            'fork_of': repo.fork.repo_name if repo.fork else None,
            'fork_of_id': repo.fork.repo_id if repo.fork else None,
            'enable_statistics': repo.enable_statistics,
            'enable_locking': repo.enable_locking,
            'enable_downloads': repo.enable_downloads,
            'last_changeset': repo.changeset_cache,
            'locked_by': User.get(_user_id).get_api_data(
                include_secrets=include_secrets) if _user_id else None,
            'locked_date': time_to_datetime(_time) if _time else None,
            'lock_reason': _reason if _reason else None,
        }

        # TODO: mikhail: should be per-repo settings here
        rc_config = SettingsModel().get_all_settings()
        repository_fields = str2bool(
            rc_config.get('rhodecode_repository_fields'))
        if repository_fields:
            for f in self.extra_fields:
                data[f.field_key_prefixed] = f.field_value

        return data

    @classmethod
    def lock(cls, repo, user_id, lock_time=None, lock_reason=None):
        if not lock_time:
            lock_time = time.time()
        if not lock_reason:
            lock_reason = cls.LOCK_AUTOMATIC
        repo.locked = [user_id, lock_time, lock_reason]
        Session().add(repo)
        Session().commit()

    @classmethod
    def unlock(cls, repo):
        repo.locked = None
        Session().add(repo)
        Session().commit()

    @classmethod
    def getlock(cls, repo):
        return repo.locked

    def is_user_lock(self, user_id):
        if self.lock[0]:
            lock_user_id = safe_int(self.lock[0])
            user_id = safe_int(user_id)
            # both are ints, and they are equal
            return all([lock_user_id, user_id]) and lock_user_id == user_id

        return False

    def get_locking_state(self, action, user_id, only_when_enabled=True):
        """
        Checks locking on this repository, if locking is enabled and lock is
        present returns a tuple of make_lock, locked, locked_by.
        make_lock can have 3 states None (do nothing) True, make lock
        False release lock, This value is later propagated to hooks, which
        do the locking. Think about this as signals passed to hooks what to do.

        """
        # TODO: johbo: This is part of the business logic and should be moved
        # into the RepositoryModel.

        if action not in ('push', 'pull'):
            raise ValueError("Invalid action value: %s" % repr(action))

        # defines if locked error should be thrown to user
        currently_locked = False
        # defines if new lock should be made, tri-state
        make_lock = None
        repo = self
        user = User.get(user_id)

        lock_info = repo.locked

        if repo and (repo.enable_locking or not only_when_enabled):
            if action == 'push':
                # check if it's already locked !, if it is compare users
                locked_by_user_id = lock_info[0]
                if user.user_id == locked_by_user_id:
                    log.debug(
                        'Got `push` action from user %s, now unlocking', user)
                    # unlock if we have push from user who locked
                    make_lock = False
                else:
                    # we're not the same user who locked, ban with
                    # code defined in settings (default is 423 HTTP Locked) !
                    log.debug('Repo %s is currently locked by %s', repo, user)
                    currently_locked = True
            elif action == 'pull':
                # [0] user [1] date
                if lock_info[0] and lock_info[1]:
                    log.debug('Repo %s is currently locked by %s', repo, user)
                    currently_locked = True
                else:
                    log.debug('Setting lock on repo %s by %s', repo, user)
                    make_lock = True

        else:
            log.debug('Repository %s do not have locking enabled', repo)

        log.debug('FINAL locking values make_lock:%s,locked:%s,locked_by:%s',
                  make_lock, currently_locked, lock_info)

        from rhodecode.lib.auth import HasRepoPermissionAny
        perm_check = HasRepoPermissionAny('repository.write', 'repository.admin')
        if make_lock and not perm_check(repo_name=repo.repo_name, user=user):
            # if we don't have at least write permission we cannot make a lock
            log.debug('lock state reset back to FALSE due to lack '
                      'of at least read permission')
            make_lock = False

        return make_lock, currently_locked, lock_info

    @property
    def last_commit_cache_update_diff(self):
        return time.time() - (safe_int(self.changeset_cache.get('updated_on')) or 0)

    @property
    def last_commit_change(self):
        from rhodecode.lib.vcs.utils.helpers import parse_datetime
        empty_date = datetime.datetime.fromtimestamp(0)
        date_latest = self.changeset_cache.get('date', empty_date)
        try:
            return parse_datetime(date_latest)
        except Exception:
            return empty_date

    @property
    def last_db_change(self):
        return self.updated_on

    @property
    def clone_uri_hidden(self):
        clone_uri = self.clone_uri
        if clone_uri:
            import urlobject
            url_obj = urlobject.URLObject(cleaned_uri(clone_uri))
            if url_obj.password:
                clone_uri = url_obj.with_password('*****')
        return clone_uri

    @property
    def push_uri_hidden(self):
        push_uri = self.push_uri
        if push_uri:
            import urlobject
            url_obj = urlobject.URLObject(cleaned_uri(push_uri))
            if url_obj.password:
                push_uri = url_obj.with_password('*****')
        return push_uri

    def clone_url(self, **override):
        from rhodecode.model.settings import SettingsModel

        uri_tmpl = None
        if 'with_id' in override:
            uri_tmpl = self.DEFAULT_CLONE_URI_ID
            del override['with_id']

        if 'uri_tmpl' in override:
            uri_tmpl = override['uri_tmpl']
            del override['uri_tmpl']

        ssh = False
        if 'ssh' in override:
            ssh = True
            del override['ssh']

        # we didn't override our tmpl from **overrides
        request = get_current_request()
        if not uri_tmpl:
            if hasattr(request, 'call_context') and hasattr(request.call_context, 'rc_config'):
                rc_config = request.call_context.rc_config
            else:
                rc_config = SettingsModel().get_all_settings(cache=True)
            if ssh:
                uri_tmpl = rc_config.get(
                    'rhodecode_clone_uri_ssh_tmpl') or self.DEFAULT_CLONE_URI_SSH
            else:
                uri_tmpl = rc_config.get(
                    'rhodecode_clone_uri_tmpl') or self.DEFAULT_CLONE_URI

        return get_clone_url(request=request,
                             uri_tmpl=uri_tmpl,
                             repo_name=self.repo_name,
                             repo_id=self.repo_id, **override)

    def set_state(self, state):
        self.repo_state = state
        Session().add(self)
    #==========================================================================
    # SCM PROPERTIES
    #==========================================================================

    def get_commit(self, commit_id=None, commit_idx=None, pre_load=None):
        return get_commit_safe(
            self.scm_instance(), commit_id, commit_idx, pre_load=pre_load)

    def get_changeset(self, rev=None, pre_load=None):
        warnings.warn("Use get_commit", DeprecationWarning)
        commit_id = None
        commit_idx = None
        if isinstance(rev, compat.string_types):
            commit_id = rev
        else:
            commit_idx = rev
        return self.get_commit(commit_id=commit_id, commit_idx=commit_idx,
                               pre_load=pre_load)

    def get_landing_commit(self):
        """
        Returns landing commit, or if that doesn't exist returns the tip
        """
        _rev_type, _rev = self.landing_rev
        commit = self.get_commit(_rev)
        if isinstance(commit, EmptyCommit):
            return self.get_commit()
        return commit

    def flush_commit_cache(self):
        self.update_commit_cache(cs_cache={'raw_id':'0'})
        self.update_commit_cache()

    def update_commit_cache(self, cs_cache=None, config=None):
        """
        Update cache of last commit for repository, keys should be::

            source_repo_id
            short_id
            raw_id
            revision
            parents
            message
            date
            author
            updated_on

        """
        from rhodecode.lib.vcs.backends.base import BaseChangeset
        if cs_cache is None:
            # use no-cache version here
            scm_repo = self.scm_instance(cache=False, config=config)

            empty = scm_repo is None or scm_repo.is_empty()
            if not empty:
                cs_cache = scm_repo.get_commit(
                    pre_load=["author", "date", "message", "parents", "branch"])
            else:
                cs_cache = EmptyCommit()

        if isinstance(cs_cache, BaseChangeset):
            cs_cache = cs_cache.__json__()

        def is_outdated(new_cs_cache):
            if (new_cs_cache['raw_id'] != self.changeset_cache['raw_id'] or
                new_cs_cache['revision'] != self.changeset_cache['revision']):
                return True
            return False

        # check if we have maybe already latest cached revision
        if is_outdated(cs_cache) or not self.changeset_cache:
            _default = datetime.datetime.utcnow()
            last_change = cs_cache.get('date') or _default
            # we check if last update is newer than the new value
            # if yes, we use the current timestamp instead. Imagine you get
            # old commit pushed 1y ago, we'd set last update 1y to ago.
            last_change_timestamp = datetime_to_time(last_change)
            current_timestamp = datetime_to_time(last_change)
            if last_change_timestamp > current_timestamp:
                cs_cache['date'] = _default

            cs_cache['updated_on'] = time.time()
            self.changeset_cache = cs_cache
            self.updated_on = last_change
            Session().add(self)
            Session().commit()

            log.debug('updated repo `%s` with new commit cache %s',
                      self.repo_name, cs_cache)
        else:
            cs_cache = self.changeset_cache
            cs_cache['updated_on'] = time.time()
            self.changeset_cache = cs_cache
            Session().add(self)
            Session().commit()

            log.debug('Skipping update_commit_cache for repo:`%s` '
                      'commit already with latest changes', self.repo_name)

    @property
    def tip(self):
        return self.get_commit('tip')

    @property
    def author(self):
        return self.tip.author

    @property
    def last_change(self):
        return self.scm_instance().last_change

    def get_comments(self, revisions=None):
        """
        Returns comments for this repository grouped by revisions

        :param revisions: filter query by revisions only
        """
        cmts = ChangesetComment.query()\
            .filter(ChangesetComment.repo == self)
        if revisions:
            cmts = cmts.filter(ChangesetComment.revision.in_(revisions))
        grouped = collections.defaultdict(list)
        for cmt in cmts.all():
            grouped[cmt.revision].append(cmt)
        return grouped

    def statuses(self, revisions=None):
        """
        Returns statuses for this repository

        :param revisions: list of revisions to get statuses for
        """
        statuses = ChangesetStatus.query()\
            .filter(ChangesetStatus.repo == self)\
            .filter(ChangesetStatus.version == 0)

        if revisions:
            # Try doing the filtering in chunks to avoid hitting limits
            size = 500
            status_results = []
            for chunk in xrange(0, len(revisions), size):
                status_results += statuses.filter(
                    ChangesetStatus.revision.in_(
                        revisions[chunk: chunk+size])
                ).all()
        else:
            status_results = statuses.all()

        grouped = {}

        # maybe we have open new pullrequest without a status?
        stat = ChangesetStatus.STATUS_UNDER_REVIEW
        status_lbl = ChangesetStatus.get_status_lbl(stat)
        for pr in PullRequest.query().filter(PullRequest.source_repo == self).all():
            for rev in pr.revisions:
                pr_id = pr.pull_request_id
                pr_repo = pr.target_repo.repo_name
                grouped[rev] = [stat, status_lbl, pr_id, pr_repo]

        for stat in status_results:
            pr_id = pr_repo = None
            if stat.pull_request:
                pr_id = stat.pull_request.pull_request_id
                pr_repo = stat.pull_request.target_repo.repo_name
            grouped[stat.revision] = [str(stat.status), stat.status_lbl,
                                      pr_id, pr_repo]
        return grouped

    # ==========================================================================
    # SCM CACHE INSTANCE
    # ==========================================================================

    def scm_instance(self, **kwargs):
        import rhodecode

        # Passing a config will not hit the cache currently only used
        # for repo2dbmapper
        config = kwargs.pop('config', None)
        cache = kwargs.pop('cache', None)
        vcs_full_cache = kwargs.pop('vcs_full_cache', None)
        if vcs_full_cache is not None:
            # allows override global config
            full_cache = vcs_full_cache
        else:
            full_cache = str2bool(rhodecode.CONFIG.get('vcs_full_cache'))
        # if cache is NOT defined use default global, else we have a full
        # control over cache behaviour
        if cache is None and full_cache and not config:
            log.debug('Initializing pure cached instance for %s', self.repo_path)
            return self._get_instance_cached()

        # cache here is sent to the "vcs server"
        return self._get_instance(cache=bool(cache), config=config)

    def _get_instance_cached(self):
        from rhodecode.lib import rc_cache

        cache_namespace_uid = 'cache_repo_instance.{}'.format(self.repo_id)
        invalidation_namespace = CacheKey.REPO_INVALIDATION_NAMESPACE.format(
            repo_id=self.repo_id)
        region = rc_cache.get_or_create_region('cache_repo_longterm', cache_namespace_uid)

        @region.conditional_cache_on_arguments(namespace=cache_namespace_uid)
        def get_instance_cached(repo_id, context_id, _cache_state_uid):
            return self._get_instance(repo_state_uid=_cache_state_uid)

        # we must use thread scoped cache here,
        # because each thread of gevent needs it's own not shared connection and cache
        # we also alter `args` so the cache key is individual for every green thread.
        inv_context_manager = rc_cache.InvalidationContext(
            uid=cache_namespace_uid, invalidation_namespace=invalidation_namespace,
            thread_scoped=True)
        with inv_context_manager as invalidation_context:
            cache_state_uid = invalidation_context.cache_data['cache_state_uid']
            args = (self.repo_id, inv_context_manager.cache_key, cache_state_uid)

            # re-compute and store cache if we get invalidate signal
            if invalidation_context.should_invalidate():
                instance = get_instance_cached.refresh(*args)
            else:
                instance = get_instance_cached(*args)

            log.debug('Repo instance fetched in %.4fs', inv_context_manager.compute_time)
            return instance

    def _get_instance(self, cache=True, config=None, repo_state_uid=None):
        log.debug('Initializing %s instance `%s` with cache flag set to: %s',
                  self.repo_type, self.repo_path, cache)
        config = config or self._config
        custom_wire = {
            'cache': cache,  # controls the vcs.remote cache
            'repo_state_uid': repo_state_uid
        }
        repo = get_vcs_instance(
            repo_path=safe_str(self.repo_full_path),
            config=config,
            with_wire=custom_wire,
            create=False,
            _vcs_alias=self.repo_type)
        if repo is not None:
            repo.count()  # cache rebuild
        return repo

    def get_shadow_repository_path(self, workspace_id):
        from rhodecode.lib.vcs.backends.base import BaseRepository
        shadow_repo_path = BaseRepository._get_shadow_repository_path(
            self.repo_full_path, self.repo_id, workspace_id)
        return shadow_repo_path

    def __json__(self):
        return {'landing_rev': self.landing_rev}

    def get_dict(self):

        # Since we transformed `repo_name` to a hybrid property, we need to
        # keep compatibility with the code which uses `repo_name` field.

        result = super(Repository, self).get_dict()
        result['repo_name'] = result.pop('_repo_name', None)
        return result


class RepoGroup(Base, BaseModel):
    __tablename__ = 'groups'
    __table_args__ = (
        UniqueConstraint('group_name', 'group_parent_id'),
        base_table_args,
    )
    __mapper_args__ = {'order_by': 'group_name'}

    CHOICES_SEPARATOR = '/'  # used to generate select2 choices for nested groups

    group_id = Column("group_id", Integer(), nullable=False, unique=True, default=None, primary_key=True)
    _group_name = Column("group_name", String(255), nullable=False, unique=True, default=None)
    group_name_hash = Column("repo_group_name_hash", String(1024), nullable=False, unique=False)
    group_parent_id = Column("group_parent_id", Integer(), ForeignKey('groups.group_id'), nullable=True, unique=None, default=None)
    group_description = Column("group_description", String(10000), nullable=True, unique=None, default=None)
    enable_locking = Column("enable_locking", Boolean(), nullable=False, unique=None, default=False)
    user_id = Column("user_id", Integer(), ForeignKey('users.user_id'), nullable=False, unique=False, default=None)
    created_on = Column('created_on', DateTime(timezone=False), nullable=False, default=datetime.datetime.now)
    updated_on = Column('updated_on', DateTime(timezone=False), nullable=True, unique=None, default=datetime.datetime.now)
    personal = Column('personal', Boolean(), nullable=True, unique=None, default=None)
    _changeset_cache = Column(
        "changeset_cache", LargeBinary(), nullable=True)  # JSON data

    repo_group_to_perm = relationship('UserRepoGroupToPerm', cascade='all', order_by='UserRepoGroupToPerm.group_to_perm_id')
    users_group_to_perm = relationship('UserGroupRepoGroupToPerm', cascade='all')
    parent_group = relationship('RepoGroup', remote_side=group_id)
    user = relationship('User')
    integrations = relationship('Integration', cascade="all, delete-orphan")

    # no cascade, set NULL
    scope_artifacts = relationship('FileStore', primaryjoin='FileStore.scope_repo_group_id==RepoGroup.group_id')

    def __init__(self, group_name='', parent_group=None):
        self.group_name = group_name
        self.parent_group = parent_group

    def __unicode__(self):
        return u"<%s('id:%s:%s')>" % (
            self.__class__.__name__, self.group_id, self.group_name)

    @hybrid_property
    def group_name(self):
        return self._group_name

    @group_name.setter
    def group_name(self, value):
        self._group_name = value
        self.group_name_hash = self.hash_repo_group_name(value)

    @hybrid_property
    def changeset_cache(self):
        from rhodecode.lib.vcs.backends.base import EmptyCommit
        dummy = EmptyCommit().__json__()
        if not self._changeset_cache:
            dummy['source_repo_id'] = ''
            return json.loads(json.dumps(dummy))

        try:
            return json.loads(self._changeset_cache)
        except TypeError:
            return dummy
        except Exception:
            log.error(traceback.format_exc())
            return dummy

    @changeset_cache.setter
    def changeset_cache(self, val):
        try:
            self._changeset_cache = json.dumps(val)
        except Exception:
            log.error(traceback.format_exc())

    @validates('group_parent_id')
    def validate_group_parent_id(self, key, val):
        """
        Check cycle references for a parent group to self
        """
        if self.group_id and val:
            assert val != self.group_id

        return val

    @hybrid_property
    def description_safe(self):
        from rhodecode.lib import helpers as h
        return h.escape(self.group_description)

    @classmethod
    def hash_repo_group_name(cls, repo_group_name):
        val = remove_formatting(repo_group_name)
        val = safe_str(val).lower()
        chars = []
        for c in val:
            if c not in string.ascii_letters:
                c = str(ord(c))
            chars.append(c)

        return ''.join(chars)

    @classmethod
    def _generate_choice(cls, repo_group):
        from webhelpers2.html import literal as _literal
        _name = lambda k: _literal(cls.CHOICES_SEPARATOR.join(k))
        return repo_group.group_id, _name(repo_group.full_path_splitted)

    @classmethod
    def groups_choices(cls, groups=None, show_empty_group=True):
        if not groups:
            groups = cls.query().all()

        repo_groups = []
        if show_empty_group:
            repo_groups = [(-1, u'-- %s --' % _('No parent'))]

        repo_groups.extend([cls._generate_choice(x) for x in groups])

        repo_groups = sorted(
            repo_groups, key=lambda t: t[1].split(cls.CHOICES_SEPARATOR)[0])
        return repo_groups

    @classmethod
    def url_sep(cls):
        return URL_SEP

    @classmethod
    def get_by_group_name(cls, group_name, cache=False, case_insensitive=False):
        if case_insensitive:
            gr = cls.query().filter(func.lower(cls.group_name)
                                    == func.lower(group_name))
        else:
            gr = cls.query().filter(cls.group_name == group_name)
        if cache:
            name_key = _hash_key(group_name)
            gr = gr.options(
                FromCache("sql_cache_short", "get_group_%s" % name_key))
        return gr.scalar()

    @classmethod
    def get_user_personal_repo_group(cls, user_id):
        user = User.get(user_id)
        if user.username == User.DEFAULT_USER:
            return None

        return cls.query()\
            .filter(cls.personal == true()) \
            .filter(cls.user == user) \
            .order_by(cls.group_id.asc()) \
            .first()

    @classmethod
    def get_all_repo_groups(cls, user_id=Optional(None), group_id=Optional(None),
                            case_insensitive=True):
        q = RepoGroup.query()

        if not isinstance(user_id, Optional):
            q = q.filter(RepoGroup.user_id == user_id)

        if not isinstance(group_id, Optional):
            q = q.filter(RepoGroup.group_parent_id == group_id)

        if case_insensitive:
            q = q.order_by(func.lower(RepoGroup.group_name))
        else:
            q = q.order_by(RepoGroup.group_name)
        return q.all()

    @property
    def parents(self, parents_recursion_limit = 10):
        groups = []
        if self.parent_group is None:
            return groups
        cur_gr = self.parent_group
        groups.insert(0, cur_gr)
        cnt = 0
        while 1:
            cnt += 1
            gr = getattr(cur_gr, 'parent_group', None)
            cur_gr = cur_gr.parent_group
            if gr is None:
                break
            if cnt == parents_recursion_limit:
                # this will prevent accidental infinit loops
                log.error('more than %s parents found for group %s, stopping '
                          'recursive parent fetching', parents_recursion_limit, self)
                break

            groups.insert(0, gr)
        return groups

    @property
    def last_commit_cache_update_diff(self):
        return time.time() - (safe_int(self.changeset_cache.get('updated_on')) or 0)

    @property
    def last_commit_change(self):
        from rhodecode.lib.vcs.utils.helpers import parse_datetime
        empty_date = datetime.datetime.fromtimestamp(0)
        date_latest = self.changeset_cache.get('date', empty_date)
        try:
            return parse_datetime(date_latest)
        except Exception:
            return empty_date

    @property
    def last_db_change(self):
        return self.updated_on

    @property
    def children(self):
        return RepoGroup.query().filter(RepoGroup.parent_group == self)

    @property
    def name(self):
        return self.group_name.split(RepoGroup.url_sep())[-1]

    @property
    def full_path(self):
        return self.group_name

    @property
    def full_path_splitted(self):
        return self.group_name.split(RepoGroup.url_sep())

    @property
    def repositories(self):
        return Repository.query()\
                .filter(Repository.group == self)\
                .order_by(Repository.repo_name)

    @property
    def repositories_recursive_count(self):
        cnt = self.repositories.count()

        def children_count(group):
            cnt = 0
            for child in group.children:
                cnt += child.repositories.count()
                cnt += children_count(child)
            return cnt

        return cnt + children_count(self)

    def _recursive_objects(self, include_repos=True, include_groups=True):
        all_ = []

        def _get_members(root_gr):
            if include_repos:
                for r in root_gr.repositories:
                    all_.append(r)
            childs = root_gr.children.all()
            if childs:
                for gr in childs:
                    if include_groups:
                        all_.append(gr)
                    _get_members(gr)

        root_group = []
        if include_groups:
            root_group = [self]

        _get_members(self)
        return root_group + all_

    def recursive_groups_and_repos(self):
        """
        Recursive return all groups, with repositories in those groups
        """
        return self._recursive_objects()

    def recursive_groups(self):
        """
        Returns all children groups for this group including children of children
        """
        return self._recursive_objects(include_repos=False)

    def recursive_repos(self):
        """
        Returns all children repositories for this group
        """
        return self._recursive_objects(include_groups=False)

    def get_new_name(self, group_name):
        """
        returns new full group name based on parent and new name

        :param group_name:
        """
        path_prefix = (self.parent_group.full_path_splitted if
                       self.parent_group else [])
        return RepoGroup.url_sep().join(path_prefix + [group_name])

    def update_commit_cache(self, config=None):
        """
        Update cache of last changeset for newest repository inside this group, keys should be::

            source_repo_id
            short_id
            raw_id
            revision
            parents
            message
            date
            author

        """
        from rhodecode.lib.vcs.utils.helpers import parse_datetime

        def repo_groups_and_repos():
            all_entries = OrderedDefaultDict(list)

            def _get_members(root_gr, pos=0):

                for repo in root_gr.repositories:
                    all_entries[root_gr].append(repo)

                # fill in all parent positions
                for parent_group in root_gr.parents:
                    all_entries[parent_group].extend(all_entries[root_gr])

                children_groups = root_gr.children.all()
                if children_groups:
                    for cnt, gr in enumerate(children_groups, 1):
                        _get_members(gr, pos=pos+cnt)

            _get_members(root_gr=self)
            return all_entries

        empty_date = datetime.datetime.fromtimestamp(0)
        for repo_group, repos in repo_groups_and_repos().items():

            latest_repo_cs_cache = {}
            _date_latest = empty_date
            for repo in repos:
                repo_cs_cache = repo.changeset_cache
                date_latest = latest_repo_cs_cache.get('date', empty_date)
                date_current = repo_cs_cache.get('date', empty_date)
                current_timestamp = datetime_to_time(parse_datetime(date_latest))
                if current_timestamp < datetime_to_time(parse_datetime(date_current)):
                    latest_repo_cs_cache = repo_cs_cache
                    latest_repo_cs_cache['source_repo_id'] = repo.repo_id
                    _date_latest = parse_datetime(latest_repo_cs_cache['date'])

            latest_repo_cs_cache['updated_on'] = time.time()
            repo_group.changeset_cache = latest_repo_cs_cache
            repo_group.updated_on = _date_latest
            Session().add(repo_group)
            Session().commit()

            log.debug('updated repo group `%s` with new commit cache %s',
                      repo_group.group_name, latest_repo_cs_cache)

    def permissions(self, with_admins=True, with_owner=True,
                    expand_from_user_groups=False):
        """
        Permissions for repository groups
        """
        _admin_perm = 'group.admin'

        owner_row = []
        if with_owner:
            usr = AttributeDict(self.user.get_dict())
            usr.owner_row = True
            usr.permission = _admin_perm
            owner_row.append(usr)

        super_admin_ids = []
        super_admin_rows = []
        if with_admins:
            for usr in User.get_all_super_admins():
                super_admin_ids.append(usr.user_id)
                # if this admin is also owner, don't double the record
                if usr.user_id == owner_row[0].user_id:
                    owner_row[0].admin_row = True
                else:
                    usr = AttributeDict(usr.get_dict())
                    usr.admin_row = True
                    usr.permission = _admin_perm
                    super_admin_rows.append(usr)

        q = UserRepoGroupToPerm.query().filter(UserRepoGroupToPerm.group == self)
        q = q.options(joinedload(UserRepoGroupToPerm.group),
                      joinedload(UserRepoGroupToPerm.user),
                      joinedload(UserRepoGroupToPerm.permission),)

        # get owners and admins and permissions. We do a trick of re-writing
        # objects from sqlalchemy to named-tuples due to sqlalchemy session
        # has a global reference and changing one object propagates to all
        # others. This means if admin is also an owner admin_row that change
        # would propagate to both objects
        perm_rows = []
        for _usr in q.all():
            usr = AttributeDict(_usr.user.get_dict())
            # if this user is also owner/admin, mark as duplicate record
            if usr.user_id == owner_row[0].user_id or usr.user_id in super_admin_ids:
                usr.duplicate_perm = True
            usr.permission = _usr.permission.permission_name
            perm_rows.append(usr)

        # filter the perm rows by 'default' first and then sort them by
        # admin,write,read,none permissions sorted again alphabetically in
        # each group
        perm_rows = sorted(perm_rows, key=display_user_sort)

        user_groups_rows = []
        if expand_from_user_groups:
            for ug in self.permission_user_groups(with_members=True):
                for user_data in ug.members:
                    user_groups_rows.append(user_data)

        return super_admin_rows + owner_row + perm_rows + user_groups_rows

    def permission_user_groups(self, with_members=False):
        q = UserGroupRepoGroupToPerm.query()\
            .filter(UserGroupRepoGroupToPerm.group == self)
        q = q.options(joinedload(UserGroupRepoGroupToPerm.group),
                      joinedload(UserGroupRepoGroupToPerm.users_group),
                      joinedload(UserGroupRepoGroupToPerm.permission),)

        perm_rows = []
        for _user_group in q.all():
            entry = AttributeDict(_user_group.users_group.get_dict())
            entry.permission = _user_group.permission.permission_name
            if with_members:
                entry.members = [x.user.get_dict()
                                 for x in _user_group.users_group.members]
            perm_rows.append(entry)

        perm_rows = sorted(perm_rows, key=display_user_group_sort)
        return perm_rows

    def get_api_data(self):
        """
        Common function for generating api data

        """
        group = self
        data = {
            'group_id': group.group_id,
            'group_name': group.group_name,
            'group_description': group.description_safe,
            'parent_group': group.parent_group.group_name if group.parent_group else None,
            'repositories': [x.repo_name for x in group.repositories],
            'owner': group.user.username,
        }
        return data

    def get_dict(self):
        # Since we transformed `group_name` to a hybrid property, we need to
        # keep compatibility with the code which uses `group_name` field.
        result = super(RepoGroup, self).get_dict()
        result['group_name'] = result.pop('_group_name', None)
        return result


class Permission(Base, BaseModel):
    __tablename__ = 'permissions'
    __table_args__ = (
        Index('p_perm_name_idx', 'permission_name'),
        base_table_args,
    )

    PERMS = [
        ('hg.admin', _('RhodeCode Super Administrator')),

        ('repository.none', _('Repository no access')),
        ('repository.read', _('Repository read access')),
        ('repository.write', _('Repository write access')),
        ('repository.admin', _('Repository admin access')),

        ('group.none', _('Repository group no access')),
        ('group.read', _('Repository group read access')),
        ('group.write', _('Repository group write access')),
        ('group.admin', _('Repository group admin access')),

        ('usergroup.none', _('User group no access')),
        ('usergroup.read', _('User group read access')),
        ('usergroup.write', _('User group write access')),
        ('usergroup.admin', _('User group admin access')),

        ('branch.none', _('Branch no permissions')),
        ('branch.merge', _('Branch access by web merge')),
        ('branch.push', _('Branch access by push')),
        ('branch.push_force', _('Branch access by push with force')),

        ('hg.repogroup.create.false', _('Repository Group creation disabled')),
        ('hg.repogroup.create.true', _('Repository Group creation enabled')),

        ('hg.usergroup.create.false', _('User Group creation disabled')),
        ('hg.usergroup.create.true', _('User Group creation enabled')),

        ('hg.create.none', _('Repository creation disabled')),
        ('hg.create.repository', _('Repository creation enabled')),
        ('hg.create.write_on_repogroup.true', _('Repository creation enabled with write permission to a repository group')),
        ('hg.create.write_on_repogroup.false', _('Repository creation disabled with write permission to a repository group')),

        ('hg.fork.none', _('Repository forking disabled')),
        ('hg.fork.repository', _('Repository forking enabled')),

        ('hg.register.none', _('Registration disabled')),
        ('hg.register.manual_activate', _('User Registration with manual account activation')),
        ('hg.register.auto_activate', _('User Registration with automatic account activation')),

        ('hg.password_reset.enabled', _('Password reset enabled')),
        ('hg.password_reset.hidden', _('Password reset hidden')),
        ('hg.password_reset.disabled', _('Password reset disabled')),

        ('hg.extern_activate.manual', _('Manual activation of external account')),
        ('hg.extern_activate.auto', _('Automatic activation of external account')),

        ('hg.inherit_default_perms.false', _('Inherit object permissions from default user disabled')),
        ('hg.inherit_default_perms.true', _('Inherit object permissions from default user enabled')),
    ]

    # definition of system default permissions for DEFAULT user, created on
    # system setup
    DEFAULT_USER_PERMISSIONS = [
        # object perms
        'repository.read',
        'group.read',
        'usergroup.read',
        # branch, for backward compat we need same value as before so forced pushed
        'branch.push_force',
        # global
        'hg.create.repository',
        'hg.repogroup.create.false',
        'hg.usergroup.create.false',
        'hg.create.write_on_repogroup.true',
        'hg.fork.repository',
        'hg.register.manual_activate',
        'hg.password_reset.enabled',
        'hg.extern_activate.auto',
        'hg.inherit_default_perms.true',
    ]

    # defines which permissions are more important higher the more important
    # Weight defines which permissions are more important.
    # The higher number the more important.
    PERM_WEIGHTS = {
        'repository.none': 0,
        'repository.read': 1,
        'repository.write': 3,
        'repository.admin': 4,

        'group.none': 0,
        'group.read': 1,
        'group.write': 3,
        'group.admin': 4,

        'usergroup.none': 0,
        'usergroup.read': 1,
        'usergroup.write': 3,
        'usergroup.admin': 4,

        'branch.none': 0,
        'branch.merge': 1,
        'branch.push': 3,
        'branch.push_force': 4,

        'hg.repogroup.create.false': 0,
        'hg.repogroup.create.true': 1,

        'hg.usergroup.create.false': 0,
        'hg.usergroup.create.true': 1,

        'hg.fork.none': 0,
        'hg.fork.repository': 1,
        'hg.create.none': 0,
        'hg.create.repository': 1
    }

    permission_id = Column("permission_id", Integer(), nullable=False, unique=True, default=None, primary_key=True)
    permission_name = Column("permission_name", String(255), nullable=True, unique=None, default=None)
    permission_longname = Column("permission_longname", String(255), nullable=True, unique=None, default=None)

    def __unicode__(self):
        return u"<%s('%s:%s')>" % (
            self.__class__.__name__, self.permission_id, self.permission_name
        )

    @classmethod
    def get_by_key(cls, key):
        return cls.query().filter(cls.permission_name == key).scalar()

    @classmethod
    def get_default_repo_perms(cls, user_id, repo_id=None):
        q = Session().query(UserRepoToPerm, Repository, Permission)\
            .join((Permission, UserRepoToPerm.permission_id == Permission.permission_id))\
            .join((Repository, UserRepoToPerm.repository_id == Repository.repo_id))\
            .filter(UserRepoToPerm.user_id == user_id)
        if repo_id:
            q = q.filter(UserRepoToPerm.repository_id == repo_id)
        return q.all()

    @classmethod
    def get_default_repo_branch_perms(cls, user_id, repo_id=None):
        q = Session().query(UserToRepoBranchPermission, UserRepoToPerm, Permission) \
            .join(
                Permission,
                UserToRepoBranchPermission.permission_id == Permission.permission_id) \
            .join(
                UserRepoToPerm,
                UserToRepoBranchPermission.rule_to_perm_id == UserRepoToPerm.repo_to_perm_id) \
            .filter(UserRepoToPerm.user_id == user_id)

        if repo_id:
            q = q.filter(UserToRepoBranchPermission.repository_id == repo_id)
        return q.order_by(UserToRepoBranchPermission.rule_order).all()

    @classmethod
    def get_default_repo_perms_from_user_group(cls, user_id, repo_id=None):
        q = Session().query(UserGroupRepoToPerm, Repository, Permission)\
            .join(
                Permission,
                UserGroupRepoToPerm.permission_id == Permission.permission_id)\
            .join(
                Repository,
                UserGroupRepoToPerm.repository_id == Repository.repo_id)\
            .join(
                UserGroup,
                UserGroupRepoToPerm.users_group_id ==
                UserGroup.users_group_id)\
            .join(
                UserGroupMember,
                UserGroupRepoToPerm.users_group_id ==
                UserGroupMember.users_group_id)\
            .filter(
                UserGroupMember.user_id == user_id,
                UserGroup.users_group_active == true())
        if repo_id:
            q = q.filter(UserGroupRepoToPerm.repository_id == repo_id)
        return q.all()

    @classmethod
    def get_default_repo_branch_perms_from_user_group(cls, user_id, repo_id=None):
        q = Session().query(UserGroupToRepoBranchPermission, UserGroupRepoToPerm, Permission) \
            .join(
                Permission,
                UserGroupToRepoBranchPermission.permission_id == Permission.permission_id) \
            .join(
                UserGroupRepoToPerm,
                UserGroupToRepoBranchPermission.rule_to_perm_id == UserGroupRepoToPerm.users_group_to_perm_id) \
            .join(
                UserGroup,
                UserGroupRepoToPerm.users_group_id == UserGroup.users_group_id) \
            .join(
                UserGroupMember,
                UserGroupRepoToPerm.users_group_id == UserGroupMember.users_group_id) \
            .filter(
                UserGroupMember.user_id == user_id,
                UserGroup.users_group_active == true())

        if repo_id:
            q = q.filter(UserGroupToRepoBranchPermission.repository_id == repo_id)
        return q.order_by(UserGroupToRepoBranchPermission.rule_order).all()

    @classmethod
    def get_default_group_perms(cls, user_id, repo_group_id=None):
        q = Session().query(UserRepoGroupToPerm, RepoGroup, Permission)\
            .join(
                Permission,
                UserRepoGroupToPerm.permission_id == Permission.permission_id)\
            .join(
                RepoGroup,
                UserRepoGroupToPerm.group_id == RepoGroup.group_id)\
            .filter(UserRepoGroupToPerm.user_id == user_id)
        if repo_group_id:
            q = q.filter(UserRepoGroupToPerm.group_id == repo_group_id)
        return q.all()

    @classmethod
    def get_default_group_perms_from_user_group(
            cls, user_id, repo_group_id=None):
        q = Session().query(UserGroupRepoGroupToPerm, RepoGroup, Permission)\
            .join(
                Permission,
                UserGroupRepoGroupToPerm.permission_id ==
                Permission.permission_id)\
            .join(
                RepoGroup,
                UserGroupRepoGroupToPerm.group_id == RepoGroup.group_id)\
            .join(
                UserGroup,
                UserGroupRepoGroupToPerm.users_group_id ==
                UserGroup.users_group_id)\
            .join(
                UserGroupMember,
                UserGroupRepoGroupToPerm.users_group_id ==
                UserGroupMember.users_group_id)\
            .filter(
                UserGroupMember.user_id == user_id,
                UserGroup.users_group_active == true())
        if repo_group_id:
            q = q.filter(UserGroupRepoGroupToPerm.group_id == repo_group_id)
        return q.all()

    @classmethod
    def get_default_user_group_perms(cls, user_id, user_group_id=None):
        q = Session().query(UserUserGroupToPerm, UserGroup, Permission)\
            .join((Permission, UserUserGroupToPerm.permission_id == Permission.permission_id))\
            .join((UserGroup, UserUserGroupToPerm.user_group_id == UserGroup.users_group_id))\
            .filter(UserUserGroupToPerm.user_id == user_id)
        if user_group_id:
            q = q.filter(UserUserGroupToPerm.user_group_id == user_group_id)
        return q.all()

    @classmethod
    def get_default_user_group_perms_from_user_group(
            cls, user_id, user_group_id=None):
        TargetUserGroup = aliased(UserGroup, name='target_user_group')
        q = Session().query(UserGroupUserGroupToPerm, UserGroup, Permission)\
            .join(
                Permission,
                UserGroupUserGroupToPerm.permission_id ==
                Permission.permission_id)\
            .join(
                TargetUserGroup,
                UserGroupUserGroupToPerm.target_user_group_id ==
                TargetUserGroup.users_group_id)\
            .join(
                UserGroup,
                UserGroupUserGroupToPerm.user_group_id ==
                UserGroup.users_group_id)\
            .join(
                UserGroupMember,
                UserGroupUserGroupToPerm.user_group_id ==
                UserGroupMember.users_group_id)\
            .filter(
                UserGroupMember.user_id == user_id,
                UserGroup.users_group_active == true())
        if user_group_id:
            q = q.filter(
                UserGroupUserGroupToPerm.user_group_id == user_group_id)

        return q.all()


class UserRepoToPerm(Base, BaseModel):
    __tablename__ = 'repo_to_perm'
    __table_args__ = (
        UniqueConstraint('user_id', 'repository_id', 'permission_id'),
        base_table_args
    )

    repo_to_perm_id = Column("repo_to_perm_id", Integer(), nullable=False, unique=True, default=None, primary_key=True)
    user_id = Column("user_id", Integer(), ForeignKey('users.user_id'), nullable=False, unique=None, default=None)
    permission_id = Column("permission_id", Integer(), ForeignKey('permissions.permission_id'), nullable=False, unique=None, default=None)
    repository_id = Column("repository_id", Integer(), ForeignKey('repositories.repo_id'), nullable=False, unique=None, default=None)

    user = relationship('User')
    repository = relationship('Repository')
    permission = relationship('Permission')

    branch_perm_entry = relationship('UserToRepoBranchPermission', cascade="all, delete-orphan", lazy='joined')

    @classmethod
    def create(cls, user, repository, permission):
        n = cls()
        n.user = user
        n.repository = repository
        n.permission = permission
        Session().add(n)
        return n

    def __unicode__(self):
        return u'<%s => %s >' % (self.user, self.repository)


class UserUserGroupToPerm(Base, BaseModel):
    __tablename__ = 'user_user_group_to_perm'
    __table_args__ = (
        UniqueConstraint('user_id', 'user_group_id', 'permission_id'),
        base_table_args
    )

    user_user_group_to_perm_id = Column("user_user_group_to_perm_id", Integer(), nullable=False, unique=True, default=None, primary_key=True)
    user_id = Column("user_id", Integer(), ForeignKey('users.user_id'), nullable=False, unique=None, default=None)
    permission_id = Column("permission_id", Integer(), ForeignKey('permissions.permission_id'), nullable=False, unique=None, default=None)
    user_group_id = Column("user_group_id", Integer(), ForeignKey('users_groups.users_group_id'), nullable=False, unique=None, default=None)

    user = relationship('User')
    user_group = relationship('UserGroup')
    permission = relationship('Permission')

    @classmethod
    def create(cls, user, user_group, permission):
        n = cls()
        n.user = user
        n.user_group = user_group
        n.permission = permission
        Session().add(n)
        return n

    def __unicode__(self):
        return u'<%s => %s >' % (self.user, self.user_group)


class UserToPerm(Base, BaseModel):
    __tablename__ = 'user_to_perm'
    __table_args__ = (
        UniqueConstraint('user_id', 'permission_id'),
        base_table_args
    )

    user_to_perm_id = Column("user_to_perm_id", Integer(), nullable=False, unique=True, default=None, primary_key=True)
    user_id = Column("user_id", Integer(), ForeignKey('users.user_id'), nullable=False, unique=None, default=None)
    permission_id = Column("permission_id", Integer(), ForeignKey('permissions.permission_id'), nullable=False, unique=None, default=None)

    user = relationship('User')
    permission = relationship('Permission', lazy='joined')

    def __unicode__(self):
        return u'<%s => %s >' % (self.user, self.permission)


class UserGroupRepoToPerm(Base, BaseModel):
    __tablename__ = 'users_group_repo_to_perm'
    __table_args__ = (
        UniqueConstraint('repository_id', 'users_group_id', 'permission_id'),
        base_table_args
    )

    users_group_to_perm_id = Column("users_group_to_perm_id", Integer(), nullable=False, unique=True, default=None, primary_key=True)
    users_group_id = Column("users_group_id", Integer(), ForeignKey('users_groups.users_group_id'), nullable=False, unique=None, default=None)
    permission_id = Column("permission_id", Integer(), ForeignKey('permissions.permission_id'), nullable=False, unique=None, default=None)
    repository_id = Column("repository_id", Integer(), ForeignKey('repositories.repo_id'), nullable=False, unique=None, default=None)

    users_group = relationship('UserGroup')
    permission = relationship('Permission')
    repository = relationship('Repository')
    user_group_branch_perms = relationship('UserGroupToRepoBranchPermission', cascade='all')

    @classmethod
    def create(cls, users_group, repository, permission):
        n = cls()
        n.users_group = users_group
        n.repository = repository
        n.permission = permission
        Session().add(n)
        return n

    def __unicode__(self):
        return u'<UserGroupRepoToPerm:%s => %s >' % (self.users_group, self.repository)


class UserGroupUserGroupToPerm(Base, BaseModel):
    __tablename__ = 'user_group_user_group_to_perm'
    __table_args__ = (
        UniqueConstraint('target_user_group_id', 'user_group_id', 'permission_id'),
        CheckConstraint('target_user_group_id != user_group_id'),
        base_table_args
    )

    user_group_user_group_to_perm_id = Column("user_group_user_group_to_perm_id", Integer(), nullable=False, unique=True, default=None, primary_key=True)
    target_user_group_id = Column("target_user_group_id", Integer(), ForeignKey('users_groups.users_group_id'), nullable=False, unique=None, default=None)
    permission_id = Column("permission_id", Integer(), ForeignKey('permissions.permission_id'), nullable=False, unique=None, default=None)
    user_group_id = Column("user_group_id", Integer(), ForeignKey('users_groups.users_group_id'), nullable=False, unique=None, default=None)

    target_user_group = relationship('UserGroup', primaryjoin='UserGroupUserGroupToPerm.target_user_group_id==UserGroup.users_group_id')
    user_group = relationship('UserGroup', primaryjoin='UserGroupUserGroupToPerm.user_group_id==UserGroup.users_group_id')
    permission = relationship('Permission')

    @classmethod
    def create(cls, target_user_group, user_group, permission):
        n = cls()
        n.target_user_group = target_user_group
        n.user_group = user_group
        n.permission = permission
        Session().add(n)
        return n

    def __unicode__(self):
        return u'<UserGroupUserGroup:%s => %s >' % (self.target_user_group, self.user_group)


class UserGroupToPerm(Base, BaseModel):
    __tablename__ = 'users_group_to_perm'
    __table_args__ = (
        UniqueConstraint('users_group_id', 'permission_id',),
        base_table_args
    )

    users_group_to_perm_id = Column("users_group_to_perm_id", Integer(), nullable=False, unique=True, default=None, primary_key=True)
    users_group_id = Column("users_group_id", Integer(), ForeignKey('users_groups.users_group_id'), nullable=False, unique=None, default=None)
    permission_id = Column("permission_id", Integer(), ForeignKey('permissions.permission_id'), nullable=False, unique=None, default=None)

    users_group = relationship('UserGroup')
    permission = relationship('Permission')


class UserRepoGroupToPerm(Base, BaseModel):
    __tablename__ = 'user_repo_group_to_perm'
    __table_args__ = (
        UniqueConstraint('user_id', 'group_id', 'permission_id'),
        base_table_args
    )

    group_to_perm_id = Column("group_to_perm_id", Integer(), nullable=False, unique=True, default=None, primary_key=True)
    user_id = Column("user_id", Integer(), ForeignKey('users.user_id'), nullable=False, unique=None, default=None)
    group_id = Column("group_id", Integer(), ForeignKey('groups.group_id'), nullable=False, unique=None, default=None)
    permission_id = Column("permission_id", Integer(), ForeignKey('permissions.permission_id'), nullable=False, unique=None, default=None)

    user = relationship('User')
    group = relationship('RepoGroup')
    permission = relationship('Permission')

    @classmethod
    def create(cls, user, repository_group, permission):
        n = cls()
        n.user = user
        n.group = repository_group
        n.permission = permission
        Session().add(n)
        return n


class UserGroupRepoGroupToPerm(Base, BaseModel):
    __tablename__ = 'users_group_repo_group_to_perm'
    __table_args__ = (
        UniqueConstraint('users_group_id', 'group_id'),
        base_table_args
    )

    users_group_repo_group_to_perm_id = Column("users_group_repo_group_to_perm_id", Integer(), nullable=False, unique=True, default=None, primary_key=True)
    users_group_id = Column("users_group_id", Integer(), ForeignKey('users_groups.users_group_id'), nullable=False, unique=None, default=None)
    group_id = Column("group_id", Integer(), ForeignKey('groups.group_id'), nullable=False, unique=None, default=None)
    permission_id = Column("permission_id", Integer(), ForeignKey('permissions.permission_id'), nullable=False, unique=None, default=None)

    users_group = relationship('UserGroup')
    permission = relationship('Permission')
    group = relationship('RepoGroup')

    @classmethod
    def create(cls, user_group, repository_group, permission):
        n = cls()
        n.users_group = user_group
        n.group = repository_group
        n.permission = permission
        Session().add(n)
        return n

    def __unicode__(self):
        return u'<UserGroupRepoGroupToPerm:%s => %s >' % (self.users_group, self.group)


class Statistics(Base, BaseModel):
    __tablename__ = 'statistics'
    __table_args__ = (
         base_table_args
    )

    stat_id = Column("stat_id", Integer(), nullable=False, unique=True, default=None, primary_key=True)
    repository_id = Column("repository_id", Integer(), ForeignKey('repositories.repo_id'), nullable=False, unique=True, default=None)
    stat_on_revision = Column("stat_on_revision", Integer(), nullable=False)
    commit_activity = Column("commit_activity", LargeBinary(1000000), nullable=False)#JSON data
    commit_activity_combined = Column("commit_activity_combined", LargeBinary(), nullable=False)#JSON data
    languages = Column("languages", LargeBinary(1000000), nullable=False)#JSON data

    repository = relationship('Repository', single_parent=True)


class UserFollowing(Base, BaseModel):
    __tablename__ = 'user_followings'
    __table_args__ = (
        UniqueConstraint('user_id', 'follows_repository_id'),
        UniqueConstraint('user_id', 'follows_user_id'),
        base_table_args
    )

    user_following_id = Column("user_following_id", Integer(), nullable=False, unique=True, default=None, primary_key=True)
    user_id = Column("user_id", Integer(), ForeignKey('users.user_id'), nullable=False, unique=None, default=None)
    follows_repo_id = Column("follows_repository_id", Integer(), ForeignKey('repositories.repo_id'), nullable=True, unique=None, default=None)
    follows_user_id = Column("follows_user_id", Integer(), ForeignKey('users.user_id'), nullable=True, unique=None, default=None)
    follows_from = Column('follows_from', DateTime(timezone=False), nullable=True, unique=None, default=datetime.datetime.now)

    user = relationship('User', primaryjoin='User.user_id==UserFollowing.user_id')

    follows_user = relationship('User', primaryjoin='User.user_id==UserFollowing.follows_user_id')
    follows_repository = relationship('Repository', order_by='Repository.repo_name')

    @classmethod
    def get_repo_followers(cls, repo_id):
        return cls.query().filter(cls.follows_repo_id == repo_id)


class CacheKey(Base, BaseModel):
    __tablename__ = 'cache_invalidation'
    __table_args__ = (
        UniqueConstraint('cache_key'),
        Index('key_idx', 'cache_key'),
        base_table_args,
    )

    CACHE_TYPE_FEED = 'FEED'

    # namespaces used to register process/thread aware caches
    REPO_INVALIDATION_NAMESPACE = 'repo_cache:{repo_id}'
    SETTINGS_INVALIDATION_NAMESPACE = 'system_settings'

    cache_id = Column("cache_id", Integer(), nullable=False, unique=True, default=None, primary_key=True)
    cache_key = Column("cache_key", String(255), nullable=True, unique=None, default=None)
    cache_args = Column("cache_args", String(255), nullable=True, unique=None, default=None)
    cache_state_uid = Column("cache_state_uid", String(255), nullable=True, unique=None, default=None)
    cache_active = Column("cache_active", Boolean(), nullable=True, unique=None, default=False)

    def __init__(self, cache_key, cache_args='', cache_state_uid=None):
        self.cache_key = cache_key
        self.cache_args = cache_args
        self.cache_active = False
        # first key should be same for all entries, since all workers should share it
        self.cache_state_uid = cache_state_uid or self.generate_new_state_uid()

    def __unicode__(self):
        return u"<%s('%s:%s[%s]')>" % (
            self.__class__.__name__,
            self.cache_id, self.cache_key, self.cache_active)

    def _cache_key_partition(self):
        prefix, repo_name, suffix = self.cache_key.partition(self.cache_args)
        return prefix, repo_name, suffix

    def get_prefix(self):
        """
        Try to extract prefix from existing cache key. The key could consist
        of prefix, repo_name, suffix
        """
        # this returns prefix, repo_name, suffix
        return self._cache_key_partition()[0]

    def get_suffix(self):
        """
        get suffix that might have been used in _get_cache_key to
        generate self.cache_key. Only used for informational purposes
        in repo_edit.mako.
        """
        # prefix, repo_name, suffix
        return self._cache_key_partition()[2]

    @classmethod
    def generate_new_state_uid(cls, based_on=None):
        if based_on:
            return str(uuid.uuid5(uuid.NAMESPACE_URL, safe_str(based_on)))
        else:
            return str(uuid.uuid4())

    @classmethod
    def delete_all_cache(cls):
        """
        Delete all cache keys from database.
        Should only be run when all instances are down and all entries
        thus stale.
        """
        cls.query().delete()
        Session().commit()

    @classmethod
    def set_invalidate(cls, cache_uid, delete=False):
        """
        Mark all caches of a repo as invalid in the database.
        """

        try:
            qry = Session().query(cls).filter(cls.cache_args == cache_uid)
            if delete:
                qry.delete()
                log.debug('cache objects deleted for cache args %s',
                          safe_str(cache_uid))
            else:
                qry.update({"cache_active": False,
                            "cache_state_uid": cls.generate_new_state_uid()})
                log.debug('cache objects marked as invalid for cache args %s',
                          safe_str(cache_uid))

            Session().commit()
        except Exception:
            log.exception(
                'Cache key invalidation failed for cache args %s',
                safe_str(cache_uid))
            Session().rollback()

    @classmethod
    def get_active_cache(cls, cache_key):
        inv_obj = cls.query().filter(cls.cache_key == cache_key).scalar()
        if inv_obj:
            return inv_obj
        return None

    @classmethod
    def get_namespace_map(cls, namespace):
        return {
            x.cache_key: x
            for x in cls.query().filter(cls.cache_args == namespace)}


class ChangesetComment(Base, BaseModel):
    __tablename__ = 'changeset_comments'
    __table_args__ = (
        Index('cc_revision_idx', 'revision'),
        base_table_args,
    )

    COMMENT_OUTDATED = u'comment_outdated'
    COMMENT_TYPE_NOTE = u'note'
    COMMENT_TYPE_TODO = u'todo'
    COMMENT_TYPES = [COMMENT_TYPE_NOTE, COMMENT_TYPE_TODO]

    comment_id = Column('comment_id', Integer(), nullable=False, primary_key=True)
    repo_id = Column('repo_id', Integer(), ForeignKey('repositories.repo_id'), nullable=False)
    revision = Column('revision', String(40), nullable=True)
    pull_request_id = Column("pull_request_id", Integer(), ForeignKey('pull_requests.pull_request_id'), nullable=True)
    pull_request_version_id = Column("pull_request_version_id", Integer(), ForeignKey('pull_request_versions.pull_request_version_id'), nullable=True)
    line_no = Column('line_no', Unicode(10), nullable=True)
    hl_lines = Column('hl_lines', Unicode(512), nullable=True)
    f_path = Column('f_path', Unicode(1000), nullable=True)
    user_id = Column('user_id', Integer(), ForeignKey('users.user_id'), nullable=False)
    text = Column('text', UnicodeText().with_variant(UnicodeText(25000), 'mysql'), nullable=False)
    created_on = Column('created_on', DateTime(timezone=False), nullable=False, default=datetime.datetime.now)
    modified_at = Column('modified_at', DateTime(timezone=False), nullable=False, default=datetime.datetime.now)
    renderer = Column('renderer', Unicode(64), nullable=True)
    display_state = Column('display_state',  Unicode(128), nullable=True)

    comment_type = Column('comment_type',  Unicode(128), nullable=True, default=COMMENT_TYPE_NOTE)
    resolved_comment_id = Column('resolved_comment_id', Integer(), ForeignKey('changeset_comments.comment_id'), nullable=True)

    resolved_comment = relationship('ChangesetComment', remote_side=comment_id, back_populates='resolved_by')
    resolved_by = relationship('ChangesetComment', back_populates='resolved_comment')

    author = relationship('User', lazy='joined')
    repo = relationship('Repository')
    status_change = relationship('ChangesetStatus', cascade="all, delete-orphan", lazy='joined')
    pull_request = relationship('PullRequest', lazy='joined')
    pull_request_version = relationship('PullRequestVersion')

    @classmethod
    def get_users(cls, revision=None, pull_request_id=None):
        """
        Returns user associated with this ChangesetComment. ie those
        who actually commented

        :param cls:
        :param revision:
        """
        q = Session().query(User)\
                .join(ChangesetComment.author)
        if revision:
            q = q.filter(cls.revision == revision)
        elif pull_request_id:
            q = q.filter(cls.pull_request_id == pull_request_id)
        return q.all()

    @classmethod
    def get_index_from_version(cls, pr_version, versions):
        num_versions = [x.pull_request_version_id for x in versions]
        try:
            return num_versions.index(pr_version) +1
        except (IndexError, ValueError):
            return

    @property
    def outdated(self):
        return self.display_state == self.COMMENT_OUTDATED

    def outdated_at_version(self, version):
        """
        Checks if comment is outdated for given pull request version
        """
        return self.outdated and self.pull_request_version_id != version

    def older_than_version(self, version):
        """
        Checks if comment is made from previous version than given
        """
        if version is None:
            return self.pull_request_version_id is not None

        return self.pull_request_version_id < version

    @property
    def resolved(self):
        return self.resolved_by[0] if self.resolved_by else None

    @property
    def is_todo(self):
        return self.comment_type == self.COMMENT_TYPE_TODO

    @property
    def is_inline(self):
        return self.line_no and self.f_path

    def get_index_version(self, versions):
        return self.get_index_from_version(
            self.pull_request_version_id, versions)

    def __repr__(self):
        if self.comment_id:
            return '<DB:Comment #%s>' % self.comment_id
        else:
            return '<DB:Comment at %#x>' % id(self)

    def get_api_data(self):
        comment = self
        data = {
            'comment_id': comment.comment_id,
            'comment_type': comment.comment_type,
            'comment_text': comment.text,
            'comment_status': comment.status_change,
            'comment_f_path': comment.f_path,
            'comment_lineno': comment.line_no,
            'comment_author': comment.author,
            'comment_created_on': comment.created_on,
            'comment_resolved_by': self.resolved
        }
        return data

    def __json__(self):
        data = dict()
        data.update(self.get_api_data())
        return data


class ChangesetStatus(Base, BaseModel):
    __tablename__ = 'changeset_statuses'
    __table_args__ = (
        Index('cs_revision_idx', 'revision'),
        Index('cs_version_idx', 'version'),
        UniqueConstraint('repo_id', 'revision', 'version'),
        base_table_args
    )

    STATUS_NOT_REVIEWED = DEFAULT = 'not_reviewed'
    STATUS_APPROVED = 'approved'
    STATUS_REJECTED = 'rejected'
    STATUS_UNDER_REVIEW = 'under_review'

    STATUSES = [
        (STATUS_NOT_REVIEWED, _("Not Reviewed")),  # (no icon) and default
        (STATUS_APPROVED, _("Approved")),
        (STATUS_REJECTED, _("Rejected")),
        (STATUS_UNDER_REVIEW, _("Under Review")),
    ]

    changeset_status_id = Column('changeset_status_id', Integer(), nullable=False, primary_key=True)
    repo_id = Column('repo_id', Integer(), ForeignKey('repositories.repo_id'), nullable=False)
    user_id = Column("user_id", Integer(), ForeignKey('users.user_id'), nullable=False, unique=None)
    revision = Column('revision', String(40), nullable=False)
    status = Column('status', String(128), nullable=False, default=DEFAULT)
    changeset_comment_id = Column('changeset_comment_id', Integer(), ForeignKey('changeset_comments.comment_id'))
    modified_at = Column('modified_at', DateTime(), nullable=False, default=datetime.datetime.now)
    version = Column('version', Integer(), nullable=False, default=0)
    pull_request_id = Column("pull_request_id", Integer(), ForeignKey('pull_requests.pull_request_id'), nullable=True)

    author = relationship('User', lazy='joined')
    repo = relationship('Repository')
    comment = relationship('ChangesetComment', lazy='joined')
    pull_request = relationship('PullRequest', lazy='joined')

    def __unicode__(self):
        return u"<%s('%s[v%s]:%s')>" % (
            self.__class__.__name__,
            self.status, self.version, self.author
        )

    @classmethod
    def get_status_lbl(cls, value):
        return dict(cls.STATUSES).get(value)

    @property
    def status_lbl(self):
        return ChangesetStatus.get_status_lbl(self.status)

    def get_api_data(self):
        status = self
        data = {
            'status_id': status.changeset_status_id,
            'status': status.status,
        }
        return data

    def __json__(self):
        data = dict()
        data.update(self.get_api_data())
        return data


class _SetState(object):
    """
    Context processor allowing changing state for sensitive operation such as
    pull request update or merge
    """

    def __init__(self, pull_request, pr_state, back_state=None):
        self._pr = pull_request
        self._org_state = back_state or pull_request.pull_request_state
        self._pr_state = pr_state
        self._current_state = None

    def __enter__(self):
        log.debug('StateLock: entering set state context, setting state to: `%s`',
                  self._pr_state)
        self.set_pr_state(self._pr_state)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_val is not None:
            log.error(traceback.format_exc(exc_tb))
            return None

        self.set_pr_state(self._org_state)
        log.debug('StateLock: exiting set state context, setting state to: `%s`',
                  self._org_state)
    @property
    def state(self):
        return self._current_state

    def set_pr_state(self, pr_state):
        try:
            self._pr.pull_request_state = pr_state
            Session().add(self._pr)
            Session().commit()
            self._current_state = pr_state
        except Exception:
            log.exception('Failed to set PullRequest %s state to %s', self._pr, pr_state)
            raise


class _PullRequestBase(BaseModel):
    """
    Common attributes of pull request and version entries.
    """

    # .status values
    STATUS_NEW = u'new'
    STATUS_OPEN = u'open'
    STATUS_CLOSED = u'closed'

    # available states
    STATE_CREATING = u'creating'
    STATE_UPDATING = u'updating'
    STATE_MERGING = u'merging'
    STATE_CREATED = u'created'

    title = Column('title', Unicode(255), nullable=True)
    description = Column(
        'description', UnicodeText().with_variant(UnicodeText(10240), 'mysql'),
        nullable=True)
    description_renderer = Column('description_renderer', Unicode(64), nullable=True)

    # new/open/closed status of pull request (not approve/reject/etc)
    status = Column('status', Unicode(255), nullable=False, default=STATUS_NEW)
    created_on = Column(
        'created_on', DateTime(timezone=False), nullable=False,
        default=datetime.datetime.now)
    updated_on = Column(
        'updated_on', DateTime(timezone=False), nullable=False,
        default=datetime.datetime.now)

    pull_request_state = Column("pull_request_state", String(255), nullable=True)

    @declared_attr
    def user_id(cls):
        return Column(
            "user_id", Integer(), ForeignKey('users.user_id'), nullable=False,
            unique=None)

    # 500 revisions max
    _revisions = Column(
        'revisions', UnicodeText().with_variant(UnicodeText(20500), 'mysql'))

    @declared_attr
    def source_repo_id(cls):
        # TODO: dan: rename column to source_repo_id
        return Column(
            'org_repo_id', Integer(), ForeignKey('repositories.repo_id'),
            nullable=False)

    _source_ref = Column('org_ref', Unicode(255), nullable=False)

    @hybrid_property
    def source_ref(self):
        return self._source_ref

    @source_ref.setter
    def source_ref(self, val):
        parts = (val or '').split(':')
        if len(parts) != 3:
            raise ValueError(
                'Invalid reference format given: {}, expected X:Y:Z'.format(val))
        self._source_ref = safe_unicode(val)

    _target_ref = Column('other_ref', Unicode(255), nullable=False)

    @hybrid_property
    def target_ref(self):
        return self._target_ref

    @target_ref.setter
    def target_ref(self, val):
        parts = (val or '').split(':')
        if len(parts) != 3:
            raise ValueError(
                'Invalid reference format given: {}, expected X:Y:Z'.format(val))
        self._target_ref = safe_unicode(val)

    @declared_attr
    def target_repo_id(cls):
        # TODO: dan: rename column to target_repo_id
        return Column(
            'other_repo_id', Integer(), ForeignKey('repositories.repo_id'),
            nullable=False)

    _shadow_merge_ref = Column('shadow_merge_ref', Unicode(255), nullable=True)

    # TODO: dan: rename column to last_merge_source_rev
    _last_merge_source_rev = Column(
        'last_merge_org_rev', String(40), nullable=True)
    # TODO: dan: rename column to last_merge_target_rev
    _last_merge_target_rev = Column(
        'last_merge_other_rev', String(40), nullable=True)
    _last_merge_status = Column('merge_status', Integer(), nullable=True)
    merge_rev = Column('merge_rev', String(40), nullable=True)

    reviewer_data = Column(
        'reviewer_data_json', MutationObj.as_mutable(
            JsonType(dialect_map=dict(mysql=UnicodeText(16384)))))

    @property
    def reviewer_data_json(self):
        return json.dumps(self.reviewer_data)

    @hybrid_property
    def description_safe(self):
        from rhodecode.lib import helpers as h
        return h.escape(self.description)

    @hybrid_property
    def revisions(self):
        return self._revisions.split(':') if self._revisions else []

    @revisions.setter
    def revisions(self, val):
        self._revisions = u':'.join(val)

    @hybrid_property
    def last_merge_status(self):
        return safe_int(self._last_merge_status)

    @last_merge_status.setter
    def last_merge_status(self, val):
        self._last_merge_status = val

    @declared_attr
    def author(cls):
        return relationship('User', lazy='joined')

    @declared_attr
    def source_repo(cls):
        return relationship(
            'Repository',
            primaryjoin='%s.source_repo_id==Repository.repo_id' % cls.__name__)

    @property
    def source_ref_parts(self):
        return self.unicode_to_reference(self.source_ref)

    @declared_attr
    def target_repo(cls):
        return relationship(
            'Repository',
            primaryjoin='%s.target_repo_id==Repository.repo_id' % cls.__name__)

    @property
    def target_ref_parts(self):
        return self.unicode_to_reference(self.target_ref)

    @property
    def shadow_merge_ref(self):
        return self.unicode_to_reference(self._shadow_merge_ref)

    @shadow_merge_ref.setter
    def shadow_merge_ref(self, ref):
        self._shadow_merge_ref = self.reference_to_unicode(ref)

    @staticmethod
    def unicode_to_reference(raw):
        """
        Convert a unicode (or string) to a reference object.
        If unicode evaluates to False it returns None.
        """
        if raw:
            refs = raw.split(':')
            return Reference(*refs)
        else:
            return None

    @staticmethod
    def reference_to_unicode(ref):
        """
        Convert a reference object to unicode.
        If reference is None it returns None.
        """
        if ref:
            return u':'.join(ref)
        else:
            return None

    def get_api_data(self, with_merge_state=True):
        from rhodecode.model.pull_request import PullRequestModel

        pull_request = self
        if with_merge_state:
            merge_status = PullRequestModel().merge_status(pull_request)
            merge_state = {
                'status': merge_status[0],
                'message': safe_unicode(merge_status[1]),
            }
        else:
            merge_state = {'status': 'not_available',
                           'message': 'not_available'}

        merge_data = {
            'clone_url': PullRequestModel().get_shadow_clone_url(pull_request),
            'reference': (
                pull_request.shadow_merge_ref._asdict()
                if pull_request.shadow_merge_ref else None),
        }

        data = {
            'pull_request_id': pull_request.pull_request_id,
            'url': PullRequestModel().get_url(pull_request),
            'title': pull_request.title,
            'description': pull_request.description,
            'status': pull_request.status,
            'state': pull_request.pull_request_state,
            'created_on': pull_request.created_on,
            'updated_on': pull_request.updated_on,
            'commit_ids': pull_request.revisions,
            'review_status': pull_request.calculated_review_status(),
            'mergeable': merge_state,
            'source': {
                'clone_url': pull_request.source_repo.clone_url(),
                'repository': pull_request.source_repo.repo_name,
                'reference': {
                    'name': pull_request.source_ref_parts.name,
                    'type': pull_request.source_ref_parts.type,
                    'commit_id': pull_request.source_ref_parts.commit_id,
                },
            },
            'target': {
                'clone_url': pull_request.target_repo.clone_url(),
                'repository': pull_request.target_repo.repo_name,
                'reference': {
                    'name': pull_request.target_ref_parts.name,
                    'type': pull_request.target_ref_parts.type,
                    'commit_id': pull_request.target_ref_parts.commit_id,
                },
            },
            'merge': merge_data,
            'author': pull_request.author.get_api_data(include_secrets=False,
                                                       details='basic'),
            'reviewers': [
                {
                    'user': reviewer.get_api_data(include_secrets=False,
                                                  details='basic'),
                    'reasons': reasons,
                    'review_status': st[0][1].status if st else 'not_reviewed',
                }
                for obj, reviewer, reasons, mandatory, st in
                pull_request.reviewers_statuses()
            ]
        }

        return data

    def set_state(self, pull_request_state, final_state=None):
        """
        # goes from initial state to updating to initial state.
        # initial state can be changed by specifying back_state=
        with pull_request_obj.set_state(PullRequest.STATE_UPDATING):
           pull_request.merge()

        :param pull_request_state:
        :param final_state:

        """

        return _SetState(self, pull_request_state, back_state=final_state)


class PullRequest(Base, _PullRequestBase):
    __tablename__ = 'pull_requests'
    __table_args__ = (
        base_table_args,
    )

    pull_request_id = Column(
        'pull_request_id', Integer(), nullable=False, primary_key=True)

    def __repr__(self):
        if self.pull_request_id:
            return '<DB:PullRequest #%s>' % self.pull_request_id
        else:
            return '<DB:PullRequest at %#x>' % id(self)

    reviewers = relationship('PullRequestReviewers', cascade="all, delete-orphan")
    statuses = relationship('ChangesetStatus', cascade="all, delete-orphan")
    comments = relationship('ChangesetComment', cascade="all, delete-orphan")
    versions = relationship('PullRequestVersion', cascade="all, delete-orphan",
                            lazy='dynamic')

    @classmethod
    def get_pr_display_object(cls, pull_request_obj, org_pull_request_obj,
                              internal_methods=None):

        class PullRequestDisplay(object):
            """
            Special object wrapper for showing PullRequest data via Versions
            It mimics PR object as close as possible. This is read only object
            just for display
            """

            def __init__(self, attrs, internal=None):
                self.attrs = attrs
                # internal have priority over the given ones via attrs
                self.internal = internal or ['versions']

            def __getattr__(self, item):
                if item in self.internal:
                    return getattr(self, item)
                try:
                    return self.attrs[item]
                except KeyError:
                    raise AttributeError(
                        '%s object has no attribute %s' % (self, item))

            def __repr__(self):
                return '<DB:PullRequestDisplay #%s>' % self.attrs.get('pull_request_id')

            def versions(self):
                return pull_request_obj.versions.order_by(
                    PullRequestVersion.pull_request_version_id).all()

            def is_closed(self):
                return pull_request_obj.is_closed()

            @property
            def pull_request_version_id(self):
                return getattr(pull_request_obj, 'pull_request_version_id', None)

        attrs = StrictAttributeDict(pull_request_obj.get_api_data(with_merge_state=False))

        attrs.author = StrictAttributeDict(
            pull_request_obj.author.get_api_data())
        if pull_request_obj.target_repo:
            attrs.target_repo = StrictAttributeDict(
                pull_request_obj.target_repo.get_api_data())
            attrs.target_repo.clone_url = pull_request_obj.target_repo.clone_url

        if pull_request_obj.source_repo:
            attrs.source_repo = StrictAttributeDict(
                pull_request_obj.source_repo.get_api_data())
            attrs.source_repo.clone_url = pull_request_obj.source_repo.clone_url

        attrs.source_ref_parts = pull_request_obj.source_ref_parts
        attrs.target_ref_parts = pull_request_obj.target_ref_parts
        attrs.revisions = pull_request_obj.revisions

        attrs.shadow_merge_ref = org_pull_request_obj.shadow_merge_ref
        attrs.reviewer_data = org_pull_request_obj.reviewer_data
        attrs.reviewer_data_json = org_pull_request_obj.reviewer_data_json

        return PullRequestDisplay(attrs, internal=internal_methods)

    def is_closed(self):
        return self.status == self.STATUS_CLOSED

    def __json__(self):
        return {
            'revisions': self.revisions,
        }

    def calculated_review_status(self):
        from rhodecode.model.changeset_status import ChangesetStatusModel
        return ChangesetStatusModel().calculated_review_status(self)

    def reviewers_statuses(self):
        from rhodecode.model.changeset_status import ChangesetStatusModel
        return ChangesetStatusModel().reviewers_statuses(self)

    @property
    def workspace_id(self):
        from rhodecode.model.pull_request import PullRequestModel
        return PullRequestModel()._workspace_id(self)

    def get_shadow_repo(self):
        workspace_id = self.workspace_id
        shadow_repository_path = self.target_repo.get_shadow_repository_path(workspace_id)
        if os.path.isdir(shadow_repository_path):
            vcs_obj = self.target_repo.scm_instance()
            return vcs_obj.get_shadow_instance(shadow_repository_path)


class PullRequestVersion(Base, _PullRequestBase):
    __tablename__ = 'pull_request_versions'
    __table_args__ = (
        base_table_args,
    )

    pull_request_version_id = Column(
        'pull_request_version_id', Integer(), nullable=False, primary_key=True)
    pull_request_id = Column(
        'pull_request_id', Integer(),
        ForeignKey('pull_requests.pull_request_id'), nullable=False)
    pull_request = relationship('PullRequest')

    def __repr__(self):
        if self.pull_request_version_id:
            return '<DB:PullRequestVersion #%s>' % self.pull_request_version_id
        else:
            return '<DB:PullRequestVersion at %#x>' % id(self)

    @property
    def reviewers(self):
        return self.pull_request.reviewers

    @property
    def versions(self):
        return self.pull_request.versions

    def is_closed(self):
        # calculate from original
        return self.pull_request.status == self.STATUS_CLOSED

    def calculated_review_status(self):
        return self.pull_request.calculated_review_status()

    def reviewers_statuses(self):
        return self.pull_request.reviewers_statuses()


class PullRequestReviewers(Base, BaseModel):
    __tablename__ = 'pull_request_reviewers'
    __table_args__ = (
        base_table_args,
    )

    @hybrid_property
    def reasons(self):
        if not self._reasons:
            return []
        return self._reasons

    @reasons.setter
    def reasons(self, val):
        val = val or []
        if any(not isinstance(x, compat.string_types) for x in val):
            raise Exception('invalid reasons type, must be list of strings')
        self._reasons = val

    pull_requests_reviewers_id = Column(
        'pull_requests_reviewers_id', Integer(), nullable=False,
        primary_key=True)
    pull_request_id = Column(
        "pull_request_id", Integer(),
        ForeignKey('pull_requests.pull_request_id'), nullable=False)
    user_id = Column(
        "user_id", Integer(), ForeignKey('users.user_id'), nullable=True)
    _reasons = Column(
        'reason', MutationList.as_mutable(
            JsonType('list', dialect_map=dict(mysql=UnicodeText(16384)))))

    mandatory = Column("mandatory", Boolean(), nullable=False, default=False)
    user = relationship('User')
    pull_request = relationship('PullRequest')

    rule_data = Column(
        'rule_data_json',
        JsonType(dialect_map=dict(mysql=UnicodeText(16384))))

    def rule_user_group_data(self):
        """
        Returns the voting user group rule data for this reviewer
        """

        if self.rule_data and 'vote_rule' in self.rule_data:
            user_group_data = {}
            if 'rule_user_group_entry_id' in self.rule_data:
                # means a group with voting rules !
                user_group_data['id'] = self.rule_data['rule_user_group_entry_id']
                user_group_data['name'] = self.rule_data['rule_name']
                user_group_data['vote_rule'] = self.rule_data['vote_rule']

            return user_group_data

    def __unicode__(self):
        return u"<%s('id:%s')>" % (self.__class__.__name__,
                                   self.pull_requests_reviewers_id)


class Notification(Base, BaseModel):
    __tablename__ = 'notifications'
    __table_args__ = (
        Index('notification_type_idx', 'type'),
        base_table_args,
    )

    TYPE_CHANGESET_COMMENT = u'cs_comment'
    TYPE_MESSAGE = u'message'
    TYPE_MENTION = u'mention'
    TYPE_REGISTRATION = u'registration'
    TYPE_PULL_REQUEST = u'pull_request'
    TYPE_PULL_REQUEST_COMMENT = u'pull_request_comment'

    notification_id = Column('notification_id', Integer(), nullable=False, primary_key=True)
    subject = Column('subject', Unicode(512), nullable=True)
    body = Column('body', UnicodeText().with_variant(UnicodeText(50000), 'mysql'), nullable=True)
    created_by = Column("created_by", Integer(), ForeignKey('users.user_id'), nullable=True)
    created_on = Column('created_on', DateTime(timezone=False), nullable=False, default=datetime.datetime.now)
    type_ = Column('type', Unicode(255))

    created_by_user = relationship('User')
    notifications_to_users = relationship('UserNotification', lazy='joined',
                                          cascade="all, delete-orphan")

    @property
    def recipients(self):
        return [x.user for x in UserNotification.query()\
                .filter(UserNotification.notification == self)\
                .order_by(UserNotification.user_id.asc()).all()]

    @classmethod
    def create(cls, created_by, subject, body, recipients, type_=None):
        if type_ is None:
            type_ = Notification.TYPE_MESSAGE

        notification = cls()
        notification.created_by_user = created_by
        notification.subject = subject
        notification.body = body
        notification.type_ = type_
        notification.created_on = datetime.datetime.now()

        # For each recipient link the created notification to his account
        for u in recipients:
            assoc = UserNotification()
            assoc.user_id = u.user_id
            assoc.notification = notification

            # if created_by is inside recipients mark his notification
            # as read
            if u.user_id == created_by.user_id:
                assoc.read = True
            Session().add(assoc)

        Session().add(notification)

        return notification


class UserNotification(Base, BaseModel):
    __tablename__ = 'user_to_notification'
    __table_args__ = (
        UniqueConstraint('user_id', 'notification_id'),
        base_table_args
    )

    user_id = Column('user_id', Integer(), ForeignKey('users.user_id'), primary_key=True)
    notification_id = Column("notification_id", Integer(), ForeignKey('notifications.notification_id'), primary_key=True)
    read = Column('read', Boolean, default=False)
    sent_on = Column('sent_on', DateTime(timezone=False), nullable=True, unique=None)

    user = relationship('User', lazy="joined")
    notification = relationship('Notification', lazy="joined",
                                order_by=lambda: Notification.created_on.desc(),)

    def mark_as_read(self):
        self.read = True
        Session().add(self)


class Gist(Base, BaseModel):
    __tablename__ = 'gists'
    __table_args__ = (
        Index('g_gist_access_id_idx', 'gist_access_id'),
        Index('g_created_on_idx', 'created_on'),
        base_table_args
    )

    GIST_PUBLIC = u'public'
    GIST_PRIVATE = u'private'
    DEFAULT_FILENAME = u'gistfile1.txt'

    ACL_LEVEL_PUBLIC = u'acl_public'
    ACL_LEVEL_PRIVATE = u'acl_private'

    gist_id = Column('gist_id', Integer(), primary_key=True)
    gist_access_id = Column('gist_access_id', Unicode(250))
    gist_description = Column('gist_description', UnicodeText().with_variant(UnicodeText(1024), 'mysql'))
    gist_owner = Column('user_id', Integer(), ForeignKey('users.user_id'), nullable=True)
    gist_expires = Column('gist_expires', Float(53), nullable=False)
    gist_type = Column('gist_type', Unicode(128), nullable=False)
    created_on = Column('created_on', DateTime(timezone=False), nullable=False, default=datetime.datetime.now)
    modified_at = Column('modified_at', DateTime(timezone=False), nullable=False, default=datetime.datetime.now)
    acl_level = Column('acl_level', Unicode(128), nullable=True)

    owner = relationship('User')

    def __repr__(self):
        return '<Gist:[%s]%s>' % (self.gist_type, self.gist_access_id)

    @hybrid_property
    def description_safe(self):
        from rhodecode.lib import helpers as h
        return h.escape(self.gist_description)

    @classmethod
    def get_or_404(cls, id_):
        from pyramid.httpexceptions import HTTPNotFound

        res = cls.query().filter(cls.gist_access_id == id_).scalar()
        if not res:
            raise HTTPNotFound()
        return res

    @classmethod
    def get_by_access_id(cls, gist_access_id):
        return cls.query().filter(cls.gist_access_id == gist_access_id).scalar()

    def gist_url(self):
        from rhodecode.model.gist import GistModel
        return GistModel().get_url(self)

    @classmethod
    def base_path(cls):
        """
        Returns base path when all gists are stored

        :param cls:
        """
        from rhodecode.model.gist import GIST_STORE_LOC
        q = Session().query(RhodeCodeUi)\
            .filter(RhodeCodeUi.ui_key == URL_SEP)
        q = q.options(FromCache("sql_cache_short", "repository_repo_path"))
        return os.path.join(q.one().ui_value, GIST_STORE_LOC)

    def get_api_data(self):
        """
        Common function for generating gist related data for API
        """
        gist = self
        data = {
            'gist_id': gist.gist_id,
            'type': gist.gist_type,
            'access_id': gist.gist_access_id,
            'description': gist.gist_description,
            'url': gist.gist_url(),
            'expires': gist.gist_expires,
            'created_on': gist.created_on,
            'modified_at': gist.modified_at,
            'content': None,
            'acl_level': gist.acl_level,
        }
        return data

    def __json__(self):
        data = dict(
        )
        data.update(self.get_api_data())
        return data
    # SCM functions

    def scm_instance(self, **kwargs):
        """
        Get an instance of VCS Repository

        :param kwargs:
        """
        from rhodecode.model.gist import GistModel
        full_repo_path = os.path.join(self.base_path(), self.gist_access_id)
        return get_vcs_instance(
            repo_path=safe_str(full_repo_path), create=False,
            _vcs_alias=GistModel.vcs_backend)


class ExternalIdentity(Base, BaseModel):
    __tablename__ = 'external_identities'
    __table_args__ = (
        Index('local_user_id_idx', 'local_user_id'),
        Index('external_id_idx', 'external_id'),
        base_table_args
    )

    external_id = Column('external_id', Unicode(255), default=u'', primary_key=True)
    external_username = Column('external_username', Unicode(1024), default=u'')
    local_user_id = Column('local_user_id', Integer(), ForeignKey('users.user_id'), primary_key=True)
    provider_name = Column('provider_name', Unicode(255), default=u'', primary_key=True)
    access_token = Column('access_token', String(1024), default=u'')
    alt_token = Column('alt_token', String(1024), default=u'')
    token_secret = Column('token_secret', String(1024), default=u'')

    @classmethod
    def by_external_id_and_provider(cls, external_id, provider_name, local_user_id=None):
        """
        Returns ExternalIdentity instance based on search params

        :param external_id:
        :param provider_name:
        :return: ExternalIdentity
        """
        query = cls.query()
        query = query.filter(cls.external_id == external_id)
        query = query.filter(cls.provider_name == provider_name)
        if local_user_id:
            query = query.filter(cls.local_user_id == local_user_id)
        return query.first()

    @classmethod
    def user_by_external_id_and_provider(cls, external_id, provider_name):
        """
        Returns User instance based on search params

        :param external_id:
        :param provider_name:
        :return: User
        """
        query = User.query()
        query = query.filter(cls.external_id == external_id)
        query = query.filter(cls.provider_name == provider_name)
        query = query.filter(User.user_id == cls.local_user_id)
        return query.first()

    @classmethod
    def by_local_user_id(cls, local_user_id):
        """
        Returns all tokens for user

        :param local_user_id:
        :return: ExternalIdentity
        """
        query = cls.query()
        query = query.filter(cls.local_user_id == local_user_id)
        return query

    @classmethod
    def load_provider_plugin(cls, plugin_id):
        from rhodecode.authentication.base import loadplugin
        _plugin_id = 'egg:rhodecode-enterprise-ee#{}'.format(plugin_id)
        auth_plugin = loadplugin(_plugin_id)
        return auth_plugin


class Integration(Base, BaseModel):
    __tablename__ = 'integrations'
    __table_args__ = (
        base_table_args
    )

    integration_id = Column('integration_id', Integer(), primary_key=True)
    integration_type = Column('integration_type', String(255))
    enabled = Column('enabled', Boolean(), nullable=False)
    name = Column('name', String(255), nullable=False)
    child_repos_only = Column('child_repos_only', Boolean(), nullable=False,
        default=False)

    settings = Column(
        'settings_json', MutationObj.as_mutable(
            JsonType(dialect_map=dict(mysql=UnicodeText(16384)))))
    repo_id = Column(
        'repo_id', Integer(), ForeignKey('repositories.repo_id'),
        nullable=True, unique=None, default=None)
    repo = relationship('Repository', lazy='joined')

    repo_group_id = Column(
        'repo_group_id', Integer(), ForeignKey('groups.group_id'),
        nullable=True, unique=None, default=None)
    repo_group = relationship('RepoGroup', lazy='joined')

    @property
    def scope(self):
        if self.repo:
            return repr(self.repo)
        if self.repo_group:
            if self.child_repos_only:
                return repr(self.repo_group) + ' (child repos only)'
            else:
                return repr(self.repo_group) + ' (recursive)'
        if self.child_repos_only:
            return 'root_repos'
        return 'global'

    def __repr__(self):
        return '<Integration(%r, %r)>' % (self.integration_type, self.scope)


class RepoReviewRuleUser(Base, BaseModel):
    __tablename__ = 'repo_review_rules_users'
    __table_args__ = (
        base_table_args
    )

    repo_review_rule_user_id = Column('repo_review_rule_user_id', Integer(), primary_key=True)
    repo_review_rule_id = Column("repo_review_rule_id", Integer(), ForeignKey('repo_review_rules.repo_review_rule_id'))
    user_id = Column("user_id", Integer(), ForeignKey('users.user_id'), nullable=False)
    mandatory = Column("mandatory", Boolean(), nullable=False, default=False)
    user = relationship('User')

    def rule_data(self):
        return {
            'mandatory': self.mandatory
        }


class RepoReviewRuleUserGroup(Base, BaseModel):
    __tablename__ = 'repo_review_rules_users_groups'
    __table_args__ = (
        base_table_args
    )

    VOTE_RULE_ALL = -1

    repo_review_rule_users_group_id = Column('repo_review_rule_users_group_id', Integer(), primary_key=True)
    repo_review_rule_id = Column("repo_review_rule_id", Integer(), ForeignKey('repo_review_rules.repo_review_rule_id'))
    users_group_id = Column("users_group_id", Integer(),ForeignKey('users_groups.users_group_id'), nullable=False)
    mandatory = Column("mandatory", Boolean(), nullable=False, default=False)
    vote_rule = Column("vote_rule", Integer(), nullable=True, default=VOTE_RULE_ALL)
    users_group = relationship('UserGroup')

    def rule_data(self):
        return {
            'mandatory': self.mandatory,
            'vote_rule': self.vote_rule
        }

    @property
    def vote_rule_label(self):
        if not self.vote_rule or self.vote_rule == self.VOTE_RULE_ALL:
            return 'all must vote'
        else:
            return 'min. vote {}'.format(self.vote_rule)


class RepoReviewRule(Base, BaseModel):
    __tablename__ = 'repo_review_rules'
    __table_args__ = (
        base_table_args
    )

    repo_review_rule_id = Column(
        'repo_review_rule_id', Integer(), primary_key=True)
    repo_id = Column(
        "repo_id", Integer(), ForeignKey('repositories.repo_id'))
    repo = relationship('Repository', backref='review_rules')

    review_rule_name = Column('review_rule_name', String(255))
    _branch_pattern = Column("branch_pattern", UnicodeText().with_variant(UnicodeText(255), 'mysql'), default=u'*')  # glob
    _target_branch_pattern = Column("target_branch_pattern", UnicodeText().with_variant(UnicodeText(255), 'mysql'), default=u'*')  # glob
    _file_pattern = Column("file_pattern", UnicodeText().with_variant(UnicodeText(255), 'mysql'), default=u'*')  # glob

    use_authors_for_review = Column("use_authors_for_review", Boolean(), nullable=False, default=False)
    forbid_author_to_review = Column("forbid_author_to_review", Boolean(), nullable=False, default=False)
    forbid_commit_author_to_review = Column("forbid_commit_author_to_review", Boolean(), nullable=False, default=False)
    forbid_adding_reviewers = Column("forbid_adding_reviewers", Boolean(), nullable=False, default=False)

    rule_users = relationship('RepoReviewRuleUser')
    rule_user_groups = relationship('RepoReviewRuleUserGroup')

    def _validate_pattern(self, value):
        re.compile('^' + glob2re(value) + '$')

    @hybrid_property
    def source_branch_pattern(self):
        return self._branch_pattern or '*'

    @source_branch_pattern.setter
    def source_branch_pattern(self, value):
        self._validate_pattern(value)
        self._branch_pattern = value or '*'

    @hybrid_property
    def target_branch_pattern(self):
        return self._target_branch_pattern or '*'

    @target_branch_pattern.setter
    def target_branch_pattern(self, value):
        self._validate_pattern(value)
        self._target_branch_pattern = value or '*'

    @hybrid_property
    def file_pattern(self):
        return self._file_pattern or '*'

    @file_pattern.setter
    def file_pattern(self, value):
        self._validate_pattern(value)
        self._file_pattern = value or '*'

    def matches(self, source_branch, target_branch, files_changed):
        """
        Check if this review rule matches a branch/files in a pull request

        :param source_branch: source branch name for the commit
        :param target_branch: target branch name for the commit
        :param files_changed: list of file paths changed in the pull request
        """

        source_branch = source_branch or ''
        target_branch = target_branch or ''
        files_changed = files_changed or []

        branch_matches = True
        if source_branch or target_branch:
            if self.source_branch_pattern == '*':
                source_branch_match = True
            else:
                if self.source_branch_pattern.startswith('re:'):
                    source_pattern = self.source_branch_pattern[3:]
                else:
                    source_pattern = '^' + glob2re(self.source_branch_pattern) + '$'
                source_branch_regex = re.compile(source_pattern)
                source_branch_match = bool(source_branch_regex.search(source_branch))
            if self.target_branch_pattern == '*':
                target_branch_match = True
            else:
                if self.target_branch_pattern.startswith('re:'):
                    target_pattern = self.target_branch_pattern[3:]
                else:
                    target_pattern = '^' + glob2re(self.target_branch_pattern) + '$'
                target_branch_regex = re.compile(target_pattern)
                target_branch_match = bool(target_branch_regex.search(target_branch))

            branch_matches = source_branch_match and target_branch_match

        files_matches = True
        if self.file_pattern != '*':
            files_matches = False
            if self.file_pattern.startswith('re:'):
                file_pattern = self.file_pattern[3:]
            else:
                file_pattern = glob2re(self.file_pattern)
            file_regex = re.compile(file_pattern)
            for filename in files_changed:
                if file_regex.search(filename):
                    files_matches = True
                    break

        return branch_matches and files_matches

    @property
    def review_users(self):
        """ Returns the users which this rule applies to """

        users = collections.OrderedDict()

        for rule_user in self.rule_users:
            if rule_user.user.active:
                if rule_user.user not in users:
                    users[rule_user.user.username] = {
                        'user': rule_user.user,
                        'source': 'user',
                        'source_data': {},
                        'data': rule_user.rule_data()
                    }

        for rule_user_group in self.rule_user_groups:
            source_data = {
                'user_group_id': rule_user_group.users_group.users_group_id,
                'name': rule_user_group.users_group.users_group_name,
                'members': len(rule_user_group.users_group.members)
            }
            for member in rule_user_group.users_group.members:
                if member.user.active:
                    key = member.user.username
                    if key in users:
                        # skip this member as we have him already
                        # this prevents from override the "first" matched
                        # users with duplicates in multiple groups
                        continue

                    users[key] = {
                        'user': member.user,
                        'source': 'user_group',
                        'source_data': source_data,
                        'data': rule_user_group.rule_data()
                    }

        return users

    def user_group_vote_rule(self, user_id):

        rules = []
        if not self.rule_user_groups:
            return rules

        for user_group in self.rule_user_groups:
            user_group_members = [x.user_id for x in user_group.users_group.members]
            if user_id in user_group_members:
                rules.append(user_group)
        return rules

    def __repr__(self):
        return '<RepoReviewerRule(id=%r, repo=%r)>' % (
            self.repo_review_rule_id, self.repo)


class ScheduleEntry(Base, BaseModel):
    __tablename__ = 'schedule_entries'
    __table_args__ = (
        UniqueConstraint('schedule_name', name='s_schedule_name_idx'),
        UniqueConstraint('task_uid', name='s_task_uid_idx'),
        base_table_args,
    )

    schedule_types = ['crontab', 'timedelta', 'integer']
    schedule_entry_id = Column('schedule_entry_id', Integer(), primary_key=True)

    schedule_name = Column("schedule_name", String(255), nullable=False, unique=None, default=None)
    schedule_description = Column("schedule_description", String(10000), nullable=True, unique=None, default=None)
    schedule_enabled = Column("schedule_enabled", Boolean(), nullable=False, unique=None, default=True)

    _schedule_type = Column("schedule_type", String(255), nullable=False, unique=None, default=None)
    schedule_definition = Column('schedule_definition_json', MutationObj.as_mutable(JsonType(default=lambda: "", dialect_map=dict(mysql=LONGTEXT()))))

    schedule_last_run = Column('schedule_last_run', DateTime(timezone=False), nullable=True, unique=None, default=None)
    schedule_total_run_count = Column('schedule_total_run_count', Integer(), nullable=True, unique=None, default=0)

    # task
    task_uid = Column("task_uid", String(255), nullable=False, unique=None, default=None)
    task_dot_notation = Column("task_dot_notation", String(4096), nullable=False, unique=None, default=None)
    task_args = Column('task_args_json', MutationObj.as_mutable(JsonType(default=list, dialect_map=dict(mysql=LONGTEXT()))))
    task_kwargs = Column('task_kwargs_json', MutationObj.as_mutable(JsonType(default=dict, dialect_map=dict(mysql=LONGTEXT()))))

    created_on = Column('created_on', DateTime(timezone=False), nullable=False, default=datetime.datetime.now)
    updated_on = Column('updated_on', DateTime(timezone=False), nullable=True, unique=None, default=None)

    @hybrid_property
    def schedule_type(self):
        return self._schedule_type

    @schedule_type.setter
    def schedule_type(self, val):
        if val not in self.schedule_types:
            raise ValueError('Value must be on of `{}` and got `{}`'.format(
                val, self.schedule_type))

        self._schedule_type = val

    @classmethod
    def get_uid(cls, obj):
        args = obj.task_args
        kwargs = obj.task_kwargs
        if isinstance(args, JsonRaw):
            try:
                args = json.loads(args)
            except ValueError:
                args = tuple()

        if isinstance(kwargs, JsonRaw):
            try:
                kwargs = json.loads(kwargs)
            except ValueError:
                kwargs = dict()

        dot_notation = obj.task_dot_notation
        val = '.'.join(map(safe_str, [
            sorted(dot_notation), args, sorted(kwargs.items())]))
        return hashlib.sha1(val).hexdigest()

    @classmethod
    def get_by_schedule_name(cls, schedule_name):
        return cls.query().filter(cls.schedule_name == schedule_name).scalar()

    @classmethod
    def get_by_schedule_id(cls, schedule_id):
        return cls.query().filter(cls.schedule_entry_id == schedule_id).scalar()

    @property
    def task(self):
        return self.task_dot_notation

    @property
    def schedule(self):
        from rhodecode.lib.celerylib.utils import raw_2_schedule
        schedule = raw_2_schedule(self.schedule_definition, self.schedule_type)
        return schedule

    @property
    def args(self):
        try:
            return list(self.task_args or [])
        except ValueError:
            return list()

    @property
    def kwargs(self):
        try:
            return dict(self.task_kwargs or {})
        except ValueError:
            return dict()

    def _as_raw(self, val):
        if hasattr(val, 'de_coerce'):
            val = val.de_coerce()
            if val:
                val = json.dumps(val)

        return val

    @property
    def schedule_definition_raw(self):
        return self._as_raw(self.schedule_definition)

    @property
    def args_raw(self):
        return self._as_raw(self.task_args)

    @property
    def kwargs_raw(self):
        return self._as_raw(self.task_kwargs)

    def __repr__(self):
        return '<DB:ScheduleEntry({}:{})>'.format(
            self.schedule_entry_id, self.schedule_name)


@event.listens_for(ScheduleEntry, 'before_update')
def update_task_uid(mapper, connection, target):
    target.task_uid = ScheduleEntry.get_uid(target)


@event.listens_for(ScheduleEntry, 'before_insert')
def set_task_uid(mapper, connection, target):
    target.task_uid = ScheduleEntry.get_uid(target)


class _BaseBranchPerms(BaseModel):
    @classmethod
    def compute_hash(cls, value):
        return sha1_safe(value)

    @hybrid_property
    def branch_pattern(self):
        return self._branch_pattern or '*'

    @hybrid_property
    def branch_hash(self):
        return self._branch_hash

    def _validate_glob(self, value):
        re.compile('^' + glob2re(value) + '$')

    @branch_pattern.setter
    def branch_pattern(self, value):
        self._validate_glob(value)
        self._branch_pattern = value or '*'
        # set the Hash when setting the branch pattern
        self._branch_hash = self.compute_hash(self._branch_pattern)

    def matches(self, branch):
        """
        Check if this the branch matches entry

        :param branch: branch name for the commit
        """

        branch = branch or ''

        branch_matches = True
        if branch:
            branch_regex = re.compile('^' + glob2re(self.branch_pattern) + '$')
            branch_matches = bool(branch_regex.search(branch))

        return branch_matches


class UserToRepoBranchPermission(Base, _BaseBranchPerms):
    __tablename__ = 'user_to_repo_branch_permissions'
    __table_args__ = (
        base_table_args
    )

    branch_rule_id = Column('branch_rule_id', Integer(), primary_key=True)

    repository_id = Column('repository_id', Integer(), ForeignKey('repositories.repo_id'), nullable=False, unique=None, default=None)
    repo = relationship('Repository', backref='user_branch_perms')

    permission_id = Column('permission_id', Integer(), ForeignKey('permissions.permission_id'), nullable=False, unique=None, default=None)
    permission = relationship('Permission')

    rule_to_perm_id = Column('rule_to_perm_id', Integer(), ForeignKey('repo_to_perm.repo_to_perm_id'), nullable=False, unique=None, default=None)
    user_repo_to_perm = relationship('UserRepoToPerm')

    rule_order = Column('rule_order', Integer(), nullable=False)
    _branch_pattern = Column('branch_pattern', UnicodeText().with_variant(UnicodeText(2048), 'mysql'), default=u'*')  # glob
    _branch_hash = Column('branch_hash', UnicodeText().with_variant(UnicodeText(2048), 'mysql'))

    def __unicode__(self):
        return u'<UserBranchPermission(%s => %r)>' % (
            self.user_repo_to_perm, self.branch_pattern)


class UserGroupToRepoBranchPermission(Base, _BaseBranchPerms):
    __tablename__ = 'user_group_to_repo_branch_permissions'
    __table_args__ = (
        base_table_args
    )

    branch_rule_id = Column('branch_rule_id', Integer(), primary_key=True)

    repository_id = Column('repository_id', Integer(), ForeignKey('repositories.repo_id'), nullable=False, unique=None, default=None)
    repo = relationship('Repository', backref='user_group_branch_perms')

    permission_id = Column('permission_id', Integer(), ForeignKey('permissions.permission_id'), nullable=False, unique=None, default=None)
    permission = relationship('Permission')

    rule_to_perm_id = Column('rule_to_perm_id', Integer(), ForeignKey('users_group_repo_to_perm.users_group_to_perm_id'), nullable=False, unique=None, default=None)
    user_group_repo_to_perm = relationship('UserGroupRepoToPerm')

    rule_order = Column('rule_order', Integer(), nullable=False)
    _branch_pattern = Column('branch_pattern', UnicodeText().with_variant(UnicodeText(2048), 'mysql'), default=u'*')  # glob
    _branch_hash = Column('branch_hash', UnicodeText().with_variant(UnicodeText(2048), 'mysql'))

    def __unicode__(self):
        return u'<UserBranchPermission(%s => %r)>' % (
            self.user_group_repo_to_perm, self.branch_pattern)


class UserBookmark(Base, BaseModel):
    __tablename__ = 'user_bookmarks'
    __table_args__ = (
        UniqueConstraint('user_id', 'bookmark_repo_id'),
        UniqueConstraint('user_id', 'bookmark_repo_group_id'),
        UniqueConstraint('user_id', 'bookmark_position'),
        base_table_args
    )

    user_bookmark_id = Column("user_bookmark_id", Integer(), nullable=False, unique=True, default=None, primary_key=True)
    user_id = Column("user_id", Integer(), ForeignKey('users.user_id'), nullable=False, unique=None, default=None)
    position = Column("bookmark_position", Integer(), nullable=False)
    title = Column("bookmark_title", String(255), nullable=True, unique=None, default=None)
    redirect_url = Column("bookmark_redirect_url", String(10240), nullable=True, unique=None, default=None)
    created_on = Column("created_on", DateTime(timezone=False), nullable=False, default=datetime.datetime.now)

    bookmark_repo_id = Column("bookmark_repo_id", Integer(), ForeignKey("repositories.repo_id"), nullable=True, unique=None, default=None)
    bookmark_repo_group_id = Column("bookmark_repo_group_id", Integer(), ForeignKey("groups.group_id"), nullable=True, unique=None, default=None)

    user = relationship("User")

    repository = relationship("Repository")
    repository_group = relationship("RepoGroup")

    @classmethod
    def get_by_position_for_user(cls, position, user_id):
        return cls.query() \
            .filter(UserBookmark.user_id == user_id) \
            .filter(UserBookmark.position == position).scalar()

    @classmethod
    def get_bookmarks_for_user(cls, user_id):
        return cls.query() \
            .filter(UserBookmark.user_id == user_id) \
            .options(joinedload(UserBookmark.repository)) \
            .options(joinedload(UserBookmark.repository_group)) \
            .order_by(UserBookmark.position.asc()) \
            .all()

    def __unicode__(self):
        return u'<UserBookmark(%s @ %r)>' % (self.position, self.redirect_url)


class FileStore(Base, BaseModel):
    __tablename__ = 'file_store'
    __table_args__ = (
        base_table_args
    )

    file_store_id = Column('file_store_id', Integer(), primary_key=True)
    file_uid = Column('file_uid', String(1024), nullable=False)
    file_display_name = Column('file_display_name', UnicodeText().with_variant(UnicodeText(2048), 'mysql'), nullable=True)
    file_description = Column('file_description', UnicodeText().with_variant(UnicodeText(10240), 'mysql'), nullable=True)
    file_org_name = Column('file_org_name', UnicodeText().with_variant(UnicodeText(10240), 'mysql'), nullable=False)

    # sha256 hash
    file_hash = Column('file_hash', String(512), nullable=False)
    file_size = Column('file_size', BigInteger(), nullable=False)

    created_on = Column('created_on', DateTime(timezone=False), nullable=False, default=datetime.datetime.now)
    accessed_on = Column('accessed_on', DateTime(timezone=False), nullable=True)
    accessed_count = Column('accessed_count', Integer(), default=0)

    enabled = Column('enabled', Boolean(), nullable=False, default=True)

    # if repo/repo_group reference is set, check for permissions
    check_acl = Column('check_acl', Boolean(), nullable=False, default=True)

    # hidden defines an attachment that should be hidden from showing in artifact listing
    hidden = Column('hidden', Boolean(), nullable=False, default=False)

    user_id = Column('user_id', Integer(), ForeignKey('users.user_id'), nullable=False)
    upload_user = relationship('User', lazy='joined', primaryjoin='User.user_id==FileStore.user_id')

    file_metadata = relationship('FileStoreMetadata', lazy='joined')

    # scope limited to user, which requester have access to
    scope_user_id = Column(
        'scope_user_id', Integer(), ForeignKey('users.user_id'),
        nullable=True, unique=None, default=None)
    user = relationship('User', lazy='joined', primaryjoin='User.user_id==FileStore.scope_user_id')

    # scope limited to user group, which requester have access to
    scope_user_group_id = Column(
        'scope_user_group_id', Integer(), ForeignKey('users_groups.users_group_id'),
        nullable=True, unique=None, default=None)
    user_group = relationship('UserGroup', lazy='joined')

    # scope limited to repo, which requester have access to
    scope_repo_id = Column(
        'scope_repo_id', Integer(), ForeignKey('repositories.repo_id'),
        nullable=True, unique=None, default=None)
    repo = relationship('Repository', lazy='joined')

    # scope limited to repo group, which requester have access to
    scope_repo_group_id = Column(
        'scope_repo_group_id', Integer(), ForeignKey('groups.group_id'),
        nullable=True, unique=None, default=None)
    repo_group = relationship('RepoGroup', lazy='joined')

    @classmethod
    def get_by_store_uid(cls, file_store_uid):
        return FileStore.query().filter(FileStore.file_uid == file_store_uid).scalar()

    @classmethod
    def create(cls, file_uid, filename, file_hash, file_size, file_display_name='',
               file_description='', enabled=True, hidden=False, check_acl=True,
               user_id=None, scope_user_id=None, scope_repo_id=None, scope_repo_group_id=None):

        store_entry = FileStore()
        store_entry.file_uid = file_uid
        store_entry.file_display_name = file_display_name
        store_entry.file_org_name = filename
        store_entry.file_size = file_size
        store_entry.file_hash = file_hash
        store_entry.file_description = file_description

        store_entry.check_acl = check_acl
        store_entry.enabled = enabled
        store_entry.hidden = hidden

        store_entry.user_id = user_id
        store_entry.scope_user_id = scope_user_id
        store_entry.scope_repo_id = scope_repo_id
        store_entry.scope_repo_group_id = scope_repo_group_id

        return store_entry

    @classmethod
    def store_metadata(cls, file_store_id, args, commit=True):
        file_store = FileStore.get(file_store_id)
        if file_store is None:
            return

        for section, key, value, value_type in args:
            has_key = FileStoreMetadata().query() \
                .filter(FileStoreMetadata.file_store_id == file_store.file_store_id) \
                .filter(FileStoreMetadata.file_store_meta_section == section) \
                .filter(FileStoreMetadata.file_store_meta_key == key) \
                .scalar()
            if has_key:
                msg = 'key `{}` already defined under section `{}` for this file.'\
                    .format(key, section)
                raise ArtifactMetadataDuplicate(msg, err_section=section, err_key=key)

            # NOTE(marcink): raises ArtifactMetadataBadValueType
            FileStoreMetadata.valid_value_type(value_type)

            meta_entry = FileStoreMetadata()
            meta_entry.file_store = file_store
            meta_entry.file_store_meta_section = section
            meta_entry.file_store_meta_key = key
            meta_entry.file_store_meta_value_type = value_type
            meta_entry.file_store_meta_value = value

            Session().add(meta_entry)

        try:
            if commit:
                Session().commit()
        except IntegrityError:
            Session().rollback()
            raise ArtifactMetadataDuplicate('Duplicate section/key found for this file.')

    @classmethod
    def bump_access_counter(cls, file_uid, commit=True):
        FileStore().query()\
            .filter(FileStore.file_uid == file_uid)\
            .update({FileStore.accessed_count: (FileStore.accessed_count + 1),
                     FileStore.accessed_on: datetime.datetime.now()})
        if commit:
            Session().commit()

    def __json__(self):
        data = {
            'filename': self.file_display_name,
            'filename_org': self.file_org_name,
            'file_uid': self.file_uid,
            'description': self.file_description,
            'hidden': self.hidden,
            'size': self.file_size,
            'created_on': self.created_on,
            'uploaded_by': self.upload_user.get_api_data(details='basic'),
            'downloaded_times': self.accessed_count,
            'sha256': self.file_hash,
            'metadata': self.file_metadata,
        }

        return data

    def __repr__(self):
        return '<FileStore({})>'.format(self.file_store_id)


class FileStoreMetadata(Base, BaseModel):
    __tablename__ = 'file_store_metadata'
    __table_args__ = (
        UniqueConstraint('file_store_id', 'file_store_meta_section_hash', 'file_store_meta_key_hash'),
        Index('file_store_meta_section_idx', 'file_store_meta_section', mysql_length=255),
        Index('file_store_meta_key_idx', 'file_store_meta_key', mysql_length=255),
        base_table_args
    )
    SETTINGS_TYPES = {
        'str': safe_str,
        'int': safe_int,
        'unicode': safe_unicode,
        'bool': str2bool,
        'list': functools.partial(aslist, sep=',')
    }

    file_store_meta_id = Column(
        "file_store_meta_id", Integer(), nullable=False, unique=True, default=None,
        primary_key=True)
    _file_store_meta_section = Column(
        "file_store_meta_section", UnicodeText().with_variant(UnicodeText(1024), 'mysql'),
        nullable=True, unique=None, default=None)
    _file_store_meta_section_hash = Column(
        "file_store_meta_section_hash", String(255),
        nullable=True, unique=None, default=None)
    _file_store_meta_key = Column(
        "file_store_meta_key", UnicodeText().with_variant(UnicodeText(1024), 'mysql'),
        nullable=True, unique=None, default=None)
    _file_store_meta_key_hash = Column(
        "file_store_meta_key_hash", String(255), nullable=True, unique=None, default=None)
    _file_store_meta_value = Column(
        "file_store_meta_value", UnicodeText().with_variant(UnicodeText(20480), 'mysql'),
        nullable=True, unique=None, default=None)
    _file_store_meta_value_type = Column(
        "file_store_meta_value_type", String(255), nullable=True, unique=None,
        default='unicode')

    file_store_id = Column(
        'file_store_id', Integer(), ForeignKey('file_store.file_store_id'),
        nullable=True, unique=None, default=None)

    file_store = relationship('FileStore', lazy='joined')

    @classmethod
    def valid_value_type(cls, value):
        if value.split('.')[0] not in cls.SETTINGS_TYPES:
            raise ArtifactMetadataBadValueType(
                'value_type must be one of %s got %s' % (cls.SETTINGS_TYPES.keys(), value))

    @hybrid_property
    def file_store_meta_section(self):
        return self._file_store_meta_section

    @file_store_meta_section.setter
    def file_store_meta_section(self, value):
        self._file_store_meta_section = value
        self._file_store_meta_section_hash = _hash_key(value)

    @hybrid_property
    def file_store_meta_key(self):
        return self._file_store_meta_key

    @file_store_meta_key.setter
    def file_store_meta_key(self, value):
        self._file_store_meta_key = value
        self._file_store_meta_key_hash = _hash_key(value)

    @hybrid_property
    def file_store_meta_value(self):
        val = self._file_store_meta_value

        if self._file_store_meta_value_type:
            # e.g unicode.encrypted == unicode
            _type = self._file_store_meta_value_type.split('.')[0]
            # decode the encrypted value if it's encrypted field type
            if '.encrypted' in self._file_store_meta_value_type:
                cipher = EncryptedTextValue()
                val = safe_unicode(cipher.process_result_value(val, None))
            # do final type conversion
            converter = self.SETTINGS_TYPES.get(_type) or self.SETTINGS_TYPES['unicode']
            val = converter(val)

        return val

    @file_store_meta_value.setter
    def file_store_meta_value(self, val):
        val = safe_unicode(val)
        # encode the encrypted value
        if '.encrypted' in self.file_store_meta_value_type:
            cipher = EncryptedTextValue()
            val = safe_unicode(cipher.process_bind_param(val, None))
        self._file_store_meta_value = val

    @hybrid_property
    def file_store_meta_value_type(self):
        return self._file_store_meta_value_type

    @file_store_meta_value_type.setter
    def file_store_meta_value_type(self, val):
        # e.g unicode.encrypted
        self.valid_value_type(val)
        self._file_store_meta_value_type = val

    def __json__(self):
        data = {
            'artifact': self.file_store.file_uid,
            'section': self.file_store_meta_section,
            'key': self.file_store_meta_key,
            'value': self.file_store_meta_value,
        }

        return data

    def __repr__(self):
        return '<%s[%s]%s=>%s]>' % (self.__class__.__name__, self.file_store_meta_section,
                                    self.file_store_meta_key, self.file_store_meta_value)


class DbMigrateVersion(Base, BaseModel):
    __tablename__ = 'db_migrate_version'
    __table_args__ = (
        base_table_args,
    )

    repository_id = Column('repository_id', String(250), primary_key=True)
    repository_path = Column('repository_path', Text)
    version = Column('version', Integer)

    @classmethod
    def set_version(cls, version):
        """
        Helper for forcing a different version, usually for debugging purposes via ishell.
        """
        ver = DbMigrateVersion.query().first()
        ver.version = version
        Session().commit()


class DbSession(Base, BaseModel):
    __tablename__ = 'db_session'
    __table_args__ = (
        base_table_args,
    )

    def __repr__(self):
        return '<DB:DbSession({})>'.format(self.id)

    id = Column('id', Integer())
    namespace = Column('namespace', String(255), primary_key=True)
    accessed = Column('accessed', DateTime, nullable=False)
    created = Column('created', DateTime, nullable=False)
    data = Column('data', PickleType, nullable=False)
