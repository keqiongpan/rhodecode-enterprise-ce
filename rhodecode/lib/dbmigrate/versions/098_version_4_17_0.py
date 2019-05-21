# -*- coding: utf-8 -*-

import logging

from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import Column, LargeBinary

from rhodecode.lib.dbmigrate.versions import _reset_base
from rhodecode.model import init_model_encryption


log = logging.getLogger(__name__)


def upgrade(migrate_engine):
    """
    Upgrade operations go here.
    Don't create your own engine; bind migrate_engine to your metadata
    """
    _reset_base(migrate_engine)
    from rhodecode.lib.dbmigrate.schema import db_4_16_0_2

    init_model_encryption(db_4_16_0_2)

    context = MigrationContext.configure(migrate_engine.connect())
    op = Operations(context)

    repo_group = db_4_16_0_2.RepoGroup.__table__

    with op.batch_alter_table(repo_group.name) as batch_op:
        batch_op.add_column(
            Column("changeset_cache", LargeBinary(1024), nullable=True))


def downgrade(migrate_engine):
    pass
