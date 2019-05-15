# -*- coding: utf-8 -*-

import logging

from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import String, Column
from sqlalchemy.sql import text

from rhodecode.lib.dbmigrate.versions import _reset_base
from rhodecode.lib.utils2 import safe_str
from rhodecode.model import meta, init_model_encryption
from rhodecode.model.db import RepoGroup


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
            Column("repo_group_name_hash", String(1024), nullable=True, unique=False))

    _generate_repo_group_name_hashes(db_4_16_0_2, op, meta.Session)


def downgrade(migrate_engine):
    pass


def _generate_repo_group_name_hashes(models, op, session):
    repo_groups = models.RepoGroup.get_all()
    for repo_group in repo_groups:
        print(safe_str(repo_group.group_name))
        hash_ = RepoGroup.hash_repo_group_name(repo_group.group_name)
        params = {'hash': hash_, 'id': repo_group.group_id}
        query = text(
            'UPDATE groups SET repo_group_name_hash = :hash'
            ' WHERE group_id = :id').bindparams(**params)
        op.execute(query)
    session().commit()
