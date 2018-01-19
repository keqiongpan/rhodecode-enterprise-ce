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

    reviewers_table = db.PullRequestReviewers.__table__

    rule_data = Column(
        'rule_data_json',
        db.JsonType(dialect_map=dict(mysql=UnicodeText(16384))))
    rule_data.create(table=reviewers_table)

    # issue fixups
    fixups(db, meta.Session)


def downgrade(migrate_engine):
    meta = MetaData()
    meta.bind = migrate_engine


def fixups(models, _SESSION):
    pass


