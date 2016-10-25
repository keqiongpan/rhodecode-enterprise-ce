import logging

from sqlalchemy import Column, MetaData, Unicode

from rhodecode.lib.dbmigrate.versions import _reset_base

log = logging.getLogger(__name__)


def upgrade(migrate_engine):
    """
    Upgrade operations go here.
    Don't create your own engine; bind migrate_engine to your metadata
    """
    _reset_base(migrate_engine)
    from rhodecode.lib.dbmigrate.schema import db_4_5_0_0 as db

    # Add shadow merge ref column to pull request table.
    pr_table = db.PullRequest.__table__
    pr_col = Column('shadow_merge_ref', Unicode(255), nullable=True)
    pr_col.create(table=pr_table)

    # Add shadow merge ref column to pull request version table.
    pr_version_table = db.PullRequestVersion.__table__
    pr_version_col = Column('shadow_merge_ref', Unicode(255), nullable=True)
    pr_version_col.create(table=pr_version_table)


def downgrade(migrate_engine):
    meta = MetaData()
    meta.bind = migrate_engine
