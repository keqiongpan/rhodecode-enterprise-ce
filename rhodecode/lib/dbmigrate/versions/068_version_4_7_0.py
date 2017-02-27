import logging

from sqlalchemy import *

from rhodecode.lib.utils2 import safe_str
from rhodecode.model import meta
from rhodecode.lib.dbmigrate.versions import _reset_base, notify

log = logging.getLogger(__name__)


def get_by_key(cls, key):
    return cls.query().filter(cls.ui_key == key).scalar()


def upgrade(migrate_engine):
    """
    Upgrade operations go here.
    Don't create your own engine; bind migrate_engine to your metadata
    """
    _reset_base(migrate_engine)
    from rhodecode.lib.dbmigrate.schema import db_4_7_0_0

    # fixups
    fixups(db_4_7_0_0, meta.Session)


def downgrade(migrate_engine):
    meta = MetaData()
    meta.bind = migrate_engine


def _migrate_token(db, user):
    new_auth_token = db.UserApiKeys()
    new_auth_token.api_key = user.api_key
    new_auth_token.user_id = user.user_id
    new_auth_token.description = 'Migrated Builtin Token'
    new_auth_token.role = db.UserApiKeys.ROLE_ALL
    new_auth_token.expires = -1
    return new_auth_token


def fixups(models, _SESSION):
    # move the builtin token to external tokens

    query = models.User.query().all()
    for user in query:
        builtin_token = user.api_key
        if builtin_token:
            log.info("Migrating builtin token of user '%s'.", safe_str(user.username))
            migrated_token = _migrate_token(models, user)
            _SESSION.add(migrated_token)

    _SESSION().commit()
