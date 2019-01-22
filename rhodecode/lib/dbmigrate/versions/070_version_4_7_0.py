import logging
import datetime

from sqlalchemy import *
from pyramid import compat

from rhodecode.lib.utils2 import safe_str
from rhodecode.model import meta
from rhodecode.lib.dbmigrate.versions import _reset_base, notify

log = logging.getLogger(__name__)


def time_to_datetime(tm):
    if tm:
        if isinstance(tm, compat.string_types):
            try:
                tm = float(tm)
            except ValueError:
                return
        return datetime.datetime.fromtimestamp(tm)


def upgrade(migrate_engine):
    """
    Upgrade operations go here.
    Don't create your own engine; bind migrate_engine to your metadata
    """
    _reset_base(migrate_engine)
    from rhodecode.lib.dbmigrate.schema import db_4_7_0_1

    # fixups
    fixups(db_4_7_0_1, meta.Session)


def downgrade(migrate_engine):
    meta = MetaData()
    meta.bind = migrate_engine


def _migrate_user(db, user):
    last_activity = time_to_datetime(user.user_data.get('last_activity', 0))
    user.last_activity = last_activity
    return user


def fixups(models, _SESSION):
    # move the builtin token to external tokens

    query = models.User.query().all()
    for user in query:
        migrated_user = _migrate_user(models, user)
        _SESSION.add(migrated_user)
        log.info(
            "Migrating last_activity of user '%s'.", safe_str(user.username))

    _SESSION().commit()
