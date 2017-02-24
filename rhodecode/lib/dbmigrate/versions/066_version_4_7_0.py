import logging

from sqlalchemy import *
from sqlalchemy.engine import reflection

from alembic.migration import MigrationContext
from alembic.operations import Operations

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

    # make sure we re-create api-keys indexes

    context = MigrationContext.configure(migrate_engine.connect())
    op = Operations(context)

    existing_indexes = _get_indexes_list(
        migrate_engine, db_4_7_0_0.UserApiKeys.__tablename__)

    names = [idx['name'] for idx in existing_indexes]

    with op.batch_alter_table(db_4_7_0_0.UserApiKeys.__tablename__) as batch_op:
        if 'uak_api_key_idx' not in names:
            batch_op.create_index(
             'uak_api_key_idx', ['api_key'])
        if 'uak_api_key_expires_idx' not in names:
            batch_op.create_index(
             'uak_api_key_expires_idx', ['api_key', 'expires'])

    # issue fixups
    fixups(db_4_7_0_0, meta.Session)


def downgrade(migrate_engine):
    meta = MetaData()
    meta.bind = migrate_engine


def fixups(models, _SESSION):
    pass


def _get_unique_constraint_list(migrate_engine, table_name):
    inspector = reflection.Inspector.from_engine(migrate_engine)
    return inspector.get_unique_constraints(table_name)


def _get_indexes_list(migrate_engine, table_name):
    inspector = reflection.Inspector.from_engine(migrate_engine)
    return inspector.get_indexes(table_name)
