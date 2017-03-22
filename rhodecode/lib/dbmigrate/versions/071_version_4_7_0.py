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
    from rhodecode.lib.dbmigrate.schema import db_4_7_0_1

    # issue fixups
    fixups(db_4_7_0_1, meta.Session)


def downgrade(migrate_engine):
    meta = MetaData()
    meta.bind = migrate_engine


def fixups(models, _SESSION):

    repo_store_path = get_repos_location(models.RhodeCodeUi)
    _store = os.path.join(repo_store_path, '.cache', 'lfs_store')
    notify('Setting lfs_store to:%s' % _store)

    if not models.RhodeCodeUi.query().filter(
                    models.RhodeCodeUi.ui_key == 'store_location').scalar():
        lfsstore = models.RhodeCodeUi()
        lfsstore.ui_section = 'vcs_git_lfs'
        lfsstore.ui_key = 'store_location'
        lfsstore.ui_value = _store
        _SESSION().add(lfsstore)
        _SESSION().commit()

