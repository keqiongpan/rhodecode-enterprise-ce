import os
import logging
import datetime

from sqlalchemy import *
from sqlalchemy.exc import DatabaseError
from sqlalchemy.orm import relation, backref, class_mapper, joinedload
from sqlalchemy.orm.session import Session
from sqlalchemy.ext.declarative import declarative_base

from rhodecode.lib.dbmigrate.migrate import *
from rhodecode.lib.dbmigrate.migrate.changeset import *
from rhodecode.lib.utils2 import str2bool

from rhodecode.model.meta import Base
from rhodecode.model import meta
from rhodecode.lib.dbmigrate.versions import _reset_base, notify

log = logging.getLogger(__name__)


def get_by_key(cls, key):
    return cls.query().filter(cls.ui_key == key).scalar()


def get_repos_location(cls):
    return get_by_key(cls, '/').ui_value


def upgrade(migrate_engine):
    """
    Upgrade operations go here.
    Don't create your own engine; bind migrate_engine to your metadata
    """
    _reset_base(migrate_engine)
    from rhodecode.lib.dbmigrate.schema import db_4_7_0_1 as db

    # add last_activity
    user_log_table = db.UserLog.__table__

    user_data = Column('user_data_json', db.JsonType(dialect_map=dict(mysql=UnicodeText(16384))))
    user_data.create(table=user_log_table)

    version = Column("version", String(255), nullable=True, default='v2')
    version.create(table=user_log_table)

    action_data = Column('action_data_json', db.JsonType(dialect_map=dict(mysql=UnicodeText(16384))))
    action_data.create(table=user_log_table)

    # issue fixups
    fixups(db, meta.Session)


def downgrade(migrate_engine):
    meta = MetaData()
    meta.bind = migrate_engine


def fixups(models, _SESSION):
    pass

