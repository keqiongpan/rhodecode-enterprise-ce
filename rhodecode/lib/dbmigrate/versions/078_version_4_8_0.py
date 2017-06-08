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

    repo_review_rule_table = db.RepoReviewRule.__table__

    forbid_commit_author_to_review = Column(
        "forbid_commit_author_to_review", Boolean(), nullable=True, default=False)
    forbid_commit_author_to_review.create(table=repo_review_rule_table)

    fixups(db, meta.Session)


def downgrade(migrate_engine):
    meta = MetaData()
    meta.bind = migrate_engine


def fixups(models, _SESSION):
    pass
