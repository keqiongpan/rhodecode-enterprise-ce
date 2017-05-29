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
    from rhodecode.lib.dbmigrate.schema import db_4_7_0_1 as db

    repo_review_rule_user_table = db.RepoReviewRuleUser.__table__
    repo_review_rule_user_group_table = db.RepoReviewRuleUserGroup.__table__

    mandatory_user = Column(
        "mandatory", Boolean(), nullable=True, default=False)
    mandatory_user.create(table=repo_review_rule_user_table)

    mandatory_user_group = Column(
        "mandatory", Boolean(), nullable=True, default=False)
    mandatory_user_group.create(table=repo_review_rule_user_group_table)

    fixups(db, meta.Session)


def downgrade(migrate_engine):
    meta = MetaData()
    meta.bind = migrate_engine


def fixups(models, _SESSION):
    pass
