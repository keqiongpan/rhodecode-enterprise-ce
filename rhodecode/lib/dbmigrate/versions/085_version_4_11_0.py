import logging

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
    from rhodecode.lib.dbmigrate.schema import db_4_11_0_0 as db

    user_group_review_table = db.RepoReviewRuleUserGroup.__table__

    vote_rule = Column("vote_rule", Integer(), nullable=True,
                       default=-1)
    vote_rule.create(table=user_group_review_table)

    # issue fixups
    fixups(db, meta.Session)


def downgrade(migrate_engine):
    meta = MetaData()
    meta.bind = migrate_engine


def fixups(models, _SESSION):
    pass


