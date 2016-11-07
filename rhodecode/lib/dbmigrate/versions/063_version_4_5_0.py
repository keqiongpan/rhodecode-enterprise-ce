import logging

from sqlalchemy import Column, MetaData, Boolean

from rhodecode.lib.dbmigrate.versions import _reset_base

log = logging.getLogger(__name__)


def upgrade(migrate_engine):
    """
    Upgrade operations go here.
    Don't create your own engine; bind migrate_engine to your metadata
    """
    _reset_base(migrate_engine)
    from rhodecode.lib.dbmigrate.schema import db_4_5_0_0 as db

    # Add personal  column to RepoGroup table.
    rg_table = db.RepoGroup.__table__
    rg_col = Column(
        'personal', Boolean(), nullable=True, unique=None, default=None)
    rg_col.create(table=rg_table)


def downgrade(migrate_engine):
    meta = MetaData()
    meta.bind = migrate_engine
