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

    review_rule_table = db.RepoReviewRule.__table__

    target_branch_pattern = Column(
        "target_branch_pattern",
        UnicodeText().with_variant(UnicodeText(255), 'mysql'), default=u'*')
    target_branch_pattern.create(table=review_rule_table)

    review_rule_name = Column('review_rule_name', String(255))
    review_rule_name.create(table=review_rule_table)

    # issue fixups
    fixups(db, meta.Session)


def downgrade(migrate_engine):
    meta = MetaData()
    meta.bind = migrate_engine


def fixups(models, _SESSION):
    pass


