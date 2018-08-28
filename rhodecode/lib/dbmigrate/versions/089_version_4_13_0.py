import logging

from sqlalchemy import *
from sqlalchemy.engine import reflection
from sqlalchemy.dialects.mysql import LONGTEXT

from alembic.migration import MigrationContext
from alembic.operations import Operations

from rhodecode.model import meta
from rhodecode.lib.dbmigrate.versions import _reset_base, notify

log = logging.getLogger(__name__)


def upgrade(migrate_engine):
    """
    Upgrade operations go here.
    Don't create your own engine; bind migrate_engine to your metadata
    """
    _reset_base(migrate_engine)
    from rhodecode.lib.dbmigrate.schema import db_4_13_0_0 as db

    db.UserToRepoBranchPermission.__table__.create()
    db.UserGroupToRepoBranchPermission.__table__.create()

    # issue fixups
    fixups(db, meta.Session)


def downgrade(migrate_engine):
    meta = MetaData()
    meta.bind = migrate_engine


def fixups(models, _SESSION):
    pass


