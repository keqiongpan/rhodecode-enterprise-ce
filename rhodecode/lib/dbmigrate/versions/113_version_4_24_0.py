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

    # issue fixups
    fixups(db, meta.Session)


def downgrade(migrate_engine):
    meta = MetaData()
    meta.bind = migrate_engine


def fixups(models, _SESSION):
    # now create new changed value of clone_url
    Optional = models.Optional

    def get_by_name(cls, key):
        return cls.query().filter(cls.app_settings_name == key).scalar()

    def create_or_update(cls, key, val=Optional(''), type_=Optional('unicode')):
        res = get_by_name(cls, key)
        if not res:
            val = Optional.extract(val)
            type_ = Optional.extract(type_)
            res = cls(key, val, type_)
        else:
            res.app_settings_name = key
            if not isinstance(val, Optional):
                # update if set
                res.app_settings_value = val
            if not isinstance(type_, Optional):
                # update if set
                res.app_settings_type = type_
        return res

    clone_uri_tmpl = models.Repository.DEFAULT_CLONE_URI_ID
    print('settings new clone by url template to %s' % clone_uri_tmpl)

    sett = create_or_update(models.RhodeCodeSetting,
        'clone_uri_id_tmpl', clone_uri_tmpl, 'unicode')
    _SESSION().add(sett)
    _SESSION.commit()
