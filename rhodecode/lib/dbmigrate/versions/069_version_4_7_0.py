import logging

from sqlalchemy import Column, MetaData, Integer, Unicode, ForeignKey, DateTime

from rhodecode.lib.dbmigrate.versions import _reset_base

log = logging.getLogger(__name__)


def upgrade(migrate_engine):
    """
    Upgrade operations go here.
    Don't create your own engine; bind migrate_engine to your metadata
    """
    _reset_base(migrate_engine)
    from rhodecode.lib.dbmigrate.schema import db_4_7_0_0 as db

    # add last_activity
    user_table = db.User.__table__
    col1 = Column(
        'last_activity', DateTime(timezone=False), nullable=True, unique=None)
    col1.create(table=user_table)


def downgrade(migrate_engine):
    meta = MetaData()
    meta.bind = migrate_engine
