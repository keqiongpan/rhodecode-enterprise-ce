import logging

from sqlalchemy import *

from rhodecode.model import meta
from rhodecode.lib.dbmigrate.versions import _reset_base, notify

log = logging.getLogger(__name__)


def upgrade(migrate_engine):
    """
    Upgrade operations go here.
    Don't create your own engine; bind migrate_engine to your metadata
    """
    _reset_base(migrate_engine)
    from rhodecode.lib.dbmigrate.schema import db_4_16_0_0 as db

    fixups(db, meta.Session)


def downgrade(migrate_engine):
    meta = MetaData()
    meta.bind = migrate_engine


def fixups(models, _SESSION):
    # move the builtin token to external tokens

    log.info('Updating pull request pull_request_state to %s',
             models.PullRequest.STATE_CREATED)
    qry = _SESSION().query(models.PullRequest)
    qry.update({"pull_request_state": models.PullRequest.STATE_CREATED})
    _SESSION().commit()

    log.info('Updating pull_request_version pull_request_state to %s',
             models.PullRequest.STATE_CREATED)
    qry = _SESSION().query(models.PullRequestVersion)
    qry.update({"pull_request_state": models.PullRequest.STATE_CREATED})
    _SESSION().commit()

