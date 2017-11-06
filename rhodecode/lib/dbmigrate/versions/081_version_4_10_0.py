import logging

from sqlalchemy import *
from sqlalchemy.engine import reflection
from sqlalchemy.dialects.mysql import LONGTEXT

from alembic.migration import MigrationContext
from alembic.operations import Operations

from rhodecode.model import meta
from rhodecode.lib.dbmigrate.versions import _reset_base, notify

log = logging.getLogger(__name__)


def upgrade(migrate_engine):
    """
    Upgrade operations go here.
    Don't create your own engine; bind migrate_engine to your metadata
    """
    _reset_base(migrate_engine)
    from rhodecode.lib.dbmigrate.schema import db_4_9_0_0

    if migrate_engine.name in ['mysql']:

        context = MigrationContext.configure(migrate_engine.connect())
        op = Operations(context)

        user_log_table = db_4_9_0_0.UserLog.__table__
        with op.batch_alter_table(user_log_table.name) as batch_op:

            action_data_json = user_log_table.columns.action_data_json
            user_data_json = user_log_table.columns.user_data_json

            batch_op.alter_column(action_data_json.name, type_=LONGTEXT)
            batch_op.alter_column(user_data_json.name, type_=LONGTEXT)

    # issue fixups
    fixups(db_4_9_0_0, meta.Session)


def downgrade(migrate_engine):
    meta = MetaData()
    meta.bind = migrate_engine


def fixups(models, _SESSION):
    pass


