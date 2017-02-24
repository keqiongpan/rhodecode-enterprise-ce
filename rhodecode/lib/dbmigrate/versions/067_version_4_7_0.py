import logging

from sqlalchemy import *
from rhodecode.model import meta
from rhodecode.lib.dbmigrate.versions import _reset_base, notify

log = logging.getLogger(__name__)


def get_by_key(cls, key):
    return cls.query().filter(cls.ui_key == key).scalar()


def upgrade(migrate_engine):
    """
    Upgrade operations go here.
    Don't create your own engine; bind migrate_engine to your metadata
    """
    _reset_base(migrate_engine)
    from rhodecode.lib.dbmigrate.schema import db_4_7_0_0

    auth_token_table = db_4_7_0_0.UserApiKeys.__table__

    repo_id = Column(
        'repo_id', Integer(), ForeignKey('repositories.repo_id'),
        nullable=True, unique=None, default=None)
    repo_id.create(table=auth_token_table)

    repo_group_id = Column(
        'repo_group_id', Integer(), ForeignKey('groups.group_id'),
        nullable=True, unique=None, default=None)
    repo_group_id.create(table=auth_token_table)

    # issue fixups
    fixups(db_4_7_0_0, meta.Session)


def downgrade(migrate_engine):
    meta = MetaData()
    meta.bind = migrate_engine


def fixups(models, _SESSION):
    pass
