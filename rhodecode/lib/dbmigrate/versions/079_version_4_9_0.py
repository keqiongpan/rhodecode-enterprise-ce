import logging
import datetime

from sqlalchemy import *
from rhodecode.model import meta
from rhodecode.lib.dbmigrate.versions import _reset_base, notify

log = logging.getLogger(__name__)


def upgrade(migrate_engine):
    """
    Upgrade operations go here.
    Don't create your own engine; bind migrate_engine to your metadata
    """
    _reset_base(migrate_engine)
    from rhodecode.lib.dbmigrate.schema import db_4_7_0_1 as db

    repo_group_table = db.RepoGroup.__table__

    updated_on = Column(
        'updated_on', DateTime(timezone=False), nullable=True, unique=None,
        default=datetime.datetime.now)
    updated_on.create(table=repo_group_table)

    fixups(db, meta.Session)


def downgrade(migrate_engine):
    meta = MetaData()
    meta.bind = migrate_engine


def fixups(models, _SESSION):
    pass
