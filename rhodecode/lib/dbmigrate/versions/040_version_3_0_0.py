import logging

from sqlalchemy import *

from rhodecode.model import meta
from rhodecode.lib.dbmigrate.versions import _reset_base, notify
from rhodecode.lib.dbmigrate.utils import (
    create_default_object_permission, create_default_permissions)
log = logging.getLogger(__name__)


def upgrade(migrate_engine):
    """
    Upgrade operations go here.
    Don't create your own engine; bind migrate_engine to your metadata
    """
    _reset_base(migrate_engine)
    from rhodecode.lib.dbmigrate.schema import db_3_0_0_0

    # issue fixups
    fixups(db_3_0_0_0, meta.Session)


def downgrade(migrate_engine):
    meta = MetaData()
    meta.bind = migrate_engine


def fixups(models, _SESSION):
    # create default permissions
    create_default_permissions(_SESSION, models)
    log.info('created default global permissions definitions')
    _SESSION().commit()

    # fix default object permissions
    create_default_object_permission(_SESSION, models)

    log.info('created default permission')
    _SESSION().commit()
