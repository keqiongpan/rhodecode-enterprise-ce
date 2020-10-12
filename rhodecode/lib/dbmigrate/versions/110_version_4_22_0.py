# -*- coding: utf-8 -*-

import logging
from sqlalchemy import *

from alembic.migration import MigrationContext
from alembic.operations import Operations

from rhodecode.lib.dbmigrate.versions import _reset_base
from rhodecode.model import meta, init_model_encryption


log = logging.getLogger(__name__)


def upgrade(migrate_engine):
    """
    Upgrade operations go here.
    Don't create your own engine; bind migrate_engine to your metadata
    """
    _reset_base(migrate_engine)
    from rhodecode.lib.dbmigrate.schema import db_4_20_0_0 as db

    init_model_encryption(db)

    context = MigrationContext.configure(migrate_engine.connect())
    op = Operations(context)

    table = db.RepoReviewRuleUser.__table__
    with op.batch_alter_table(table.name) as batch_op:
        new_column = Column('role', Unicode(255), nullable=True)
        batch_op.add_column(new_column)

    _fill_rule_user_role(op, meta.Session)

    table = db.RepoReviewRuleUserGroup.__table__
    with op.batch_alter_table(table.name) as batch_op:
        new_column = Column('role', Unicode(255), nullable=True)
        batch_op.add_column(new_column)

    _fill_rule_user_group_role(op, meta.Session)


def downgrade(migrate_engine):
    meta = MetaData()
    meta.bind = migrate_engine


def fixups(models, _SESSION):
    pass


def _fill_rule_user_role(op, session):
    params = {'role': 'reviewer'}
    query = text(
        'UPDATE repo_review_rules_users SET role = :role'
    ).bindparams(**params)
    op.execute(query)
    session().commit()


def _fill_rule_user_group_role(op, session):
    params = {'role': 'reviewer'}
    query = text(
        'UPDATE repo_review_rules_users_groups SET role = :role'
    ).bindparams(**params)
    op.execute(query)
    session().commit()
