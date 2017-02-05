import logging

from sqlalchemy import Column, MetaData, Integer, Unicode, ForeignKey

from rhodecode.lib.dbmigrate.versions import _reset_base

log = logging.getLogger(__name__)


def upgrade(migrate_engine):
    """
    Upgrade operations go here.
    Don't create your own engine; bind migrate_engine to your metadata
    """
    _reset_base(migrate_engine)
    from rhodecode.lib.dbmigrate.schema import db_4_5_0_0 as db

    # add comment type and link to resolve by id
    comment_table = db.ChangesetComment.__table__
    col1 = Column('comment_type', Unicode(128), nullable=True)
    col1.create(table=comment_table)

    col1 = Column('resolved_comment_id', Integer(),
                  ForeignKey('changeset_comments.comment_id'), nullable=True)
    col1.create(table=comment_table)


def downgrade(migrate_engine):
    meta = MetaData()
    meta.bind = migrate_engine
