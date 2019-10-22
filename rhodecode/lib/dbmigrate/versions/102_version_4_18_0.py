# -*- coding: utf-8 -*-

import logging
from sqlalchemy import *

from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import BigInteger

from rhodecode.lib.dbmigrate.versions import _reset_base
from rhodecode.model import init_model_encryption


log = logging.getLogger(__name__)


def upgrade(migrate_engine):
    """
    Upgrade operations go here.
    Don't create your own engine; bind migrate_engine to your metadata
    """
    _reset_base(migrate_engine)
    from rhodecode.lib.dbmigrate.schema import db_4_18_0_1

    init_model_encryption(db_4_18_0_1)

    context = MigrationContext.configure(migrate_engine.connect())
    op = Operations(context)

    file_store = db_4_18_0_1.FileStore.__table__

    with op.batch_alter_table(file_store.name) as batch_op:
        batch_op.alter_column("file_size", type_=BigInteger())


def downgrade(migrate_engine):
    meta = MetaData()
    meta.bind = migrate_engine


def fixups(models, _SESSION):
    pass
