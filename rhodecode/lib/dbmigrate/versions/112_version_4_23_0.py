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

    table = db.RepoReviewRule.__table__
    with op.batch_alter_table(table.name) as batch_op:

        new_column = Column('pr_author', UnicodeText().with_variant(UnicodeText(255), 'mysql'), nullable=True)
        batch_op.add_column(new_column)

        new_column = Column('commit_author', UnicodeText().with_variant(UnicodeText(255), 'mysql'), nullable=True)
        batch_op.add_column(new_column)

    _migrate_review_flags_to_new_cols(op, meta.Session)


def downgrade(migrate_engine):
    meta = MetaData()
    meta.bind = migrate_engine


def fixups(models, _SESSION):
    pass


def _migrate_review_flags_to_new_cols(op, session):

    # set defaults for pr_author
    query = text(
        'UPDATE repo_review_rules SET pr_author = :val'
    ).bindparams(val='no_rule')
    op.execute(query)

    # set defaults for commit_author
    query = text(
        'UPDATE repo_review_rules SET commit_author = :val'
    ).bindparams(val='no_rule')
    op.execute(query)

    session().commit()

    # now change the flags to forbid based on
    # forbid_author_to_review, forbid_commit_author_to_review
    query = text(
        'UPDATE repo_review_rules SET pr_author = :val WHERE forbid_author_to_review = TRUE'
    ).bindparams(val='forbid_pr_author')
    op.execute(query)

    query = text(
        'UPDATE repo_review_rules SET commit_author = :val WHERE forbid_commit_author_to_review = TRUE'
    ).bindparams(val='forbid_commit_author')
    op.execute(query)

    session().commit()
