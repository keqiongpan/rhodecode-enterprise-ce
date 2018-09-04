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

    pull_request_table = db.PullRequest.__table__
    pull_request_version_table = db.PullRequestVersion.__table__

    renderer = Column('description_renderer', Unicode(64), nullable=True)
    renderer.create(table=pull_request_table)

    renderer_ver = Column('description_renderer', Unicode(64), nullable=True)
    renderer_ver.create(table=pull_request_version_table)

    # issue fixups
    fixups(db, meta.Session)


def downgrade(migrate_engine):
    meta = MetaData()
    meta.bind = migrate_engine


def fixups(models, _SESSION):
    pass


