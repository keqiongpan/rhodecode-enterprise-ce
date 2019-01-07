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
    from rhodecode.lib.dbmigrate.schema import db_4_13_0_0 as db

    pull_request = db.PullRequest.__table__
    pull_request_version = db.PullRequestVersion.__table__

    repo_state_1 = Column("pull_request_state", String(255), nullable=True)
    repo_state_1.create(table=pull_request)

    repo_state_2 = Column("pull_request_state", String(255), nullable=True)
    repo_state_2.create(table=pull_request_version)

    fixups(db, meta.Session)


def downgrade(migrate_engine):
    meta = MetaData()
    meta.bind = migrate_engine


def fixups(models, _SESSION):
    pass
