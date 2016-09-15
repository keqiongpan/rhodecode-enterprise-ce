import logging

from sqlalchemy import *

from rhodecode.model import init_model_encryption, meta
from rhodecode.lib.utils2 import safe_str
from rhodecode.lib.dbmigrate.versions import _reset_base, notify

log = logging.getLogger(__name__)


def get_all_settings(models):
    settings = {
        'rhodecode_' + result.app_settings_name: result.app_settings_value
        for result in models.RhodeCodeSetting.query()
    }
    return settings


def get_ui_by_section_and_key(models, section, key):
    q = models.RhodeCodeUi.query()
    q = q.filter(models.RhodeCodeUi.ui_section == section)
    q = q.filter(models.RhodeCodeUi.ui_key == key)
    return q.scalar()


def create_ui_section_value(models, Session, section, val, key=None, active=True):
    new_ui = models.RhodeCodeUi()
    new_ui.ui_section = section
    new_ui.ui_value = val
    new_ui.ui_active = active
    new_ui.ui_key = key

    Session().add(new_ui)
    return new_ui


def create_or_update_ui(
        models, Session, section, key, value=None, active=None):
    ui = get_ui_by_section_and_key(models, section, key)
    if not ui:
        active = True if active is None else active
        create_ui_section_value(
            models, Session, section, value, key=key, active=active)
    else:
        if active is not None:
            ui.ui_active = active
        if value is not None:
            ui.ui_value = value
        Session().add(ui)


def upgrade(migrate_engine):
    """
    Upgrade operations go here.
    Don't create your own engine; bind migrate_engine to your metadata
    """
    _reset_base(migrate_engine)
    from rhodecode.lib.dbmigrate.schema import db_4_4_0_1
    init_model_encryption(db_4_4_0_1)
    fixups(db_4_4_0_1, meta.Session)


def downgrade(migrate_engine):
    meta = MetaData()
    meta.bind = migrate_engine


def fixups(models, Session):
    current_settings = get_all_settings(models)

    svn_proxy_enabled = safe_str(current_settings.get(
        'rhodecode_proxy_subversion_http_requests', 'False'))
    svn_proxy_url = current_settings.get(
        'rhodecode_subversion_http_server_url', '')

    create_or_update_ui(
        models, Session, 'vcs_svn_proxy', 'http_requests_enabled',
        value=svn_proxy_enabled)

    create_or_update_ui(
        models, Session, 'vcs_svn_proxy', 'http_server_url',
        value=svn_proxy_url)

    Session().commit()
