# -*- coding: utf-8 -*-

# Copyright (C) 2012-2017 RhodeCode GmbH
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License, version 3
# (only), as published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# This program is dual-licensed. If you wish to learn more about the
# RhodeCode Enterprise Edition, including its added features, Support services,
# and proprietary license terms, please see https://rhodecode.com/licenses/

"""
RhodeCode task modules, containing all task that suppose to be run
by celery daemon
"""

import os

import rhodecode
from rhodecode.lib import audit_logger
from rhodecode.lib.celerylib import get_logger, async_task, RequestContextTask
from rhodecode.lib.hooks_base import log_create_repository
from rhodecode.lib.rcmail.smtp_mailer import SmtpMailer
from rhodecode.lib.utils2 import safe_int, str2bool
from rhodecode.model.db import Session, Repository, User


@async_task(ignore_result=True, base=RequestContextTask)
def send_email(recipients, subject, body='', html_body='', email_config=None):
    """
    Sends an email with defined parameters from the .ini files.

    :param recipients: list of recipients, it this is empty the defined email
        address from field 'email_to' is used instead
    :param subject: subject of the mail
    :param body: body of the mail
    :param html_body: html version of body
    """
    log = get_logger(send_email)

    email_config = email_config or rhodecode.CONFIG
    subject = "%s %s" % (email_config.get('email_prefix', ''), subject)
    if not recipients:
        # if recipients are not defined we send to email_config + all admins
        admins = [
            u.email for u in User.query().filter(User.admin == True).all()]
        recipients = [email_config.get('email_to')] + admins

    mail_server = email_config.get('smtp_server') or None
    if mail_server is None:
        log.error("SMTP server information missing. Sending email failed. "
                  "Make sure that `smtp_server` variable is configured "
                  "inside the .ini file")
        return False

    mail_from = email_config.get('app_email_from', 'RhodeCode')
    user = email_config.get('smtp_username')
    passwd = email_config.get('smtp_password')
    mail_port = email_config.get('smtp_port')
    tls = str2bool(email_config.get('smtp_use_tls'))
    ssl = str2bool(email_config.get('smtp_use_ssl'))
    debug = str2bool(email_config.get('debug'))
    smtp_auth = email_config.get('smtp_auth')

    try:
        m = SmtpMailer(mail_from, user, passwd, mail_server, smtp_auth,
                       mail_port, ssl, tls, debug=debug)
        m.send(recipients, subject, body, html_body)
    except Exception:
        log.exception('Mail sending failed')
        return False
    return True


@async_task(ignore_result=True, base=RequestContextTask)
def create_repo(form_data, cur_user):
    from rhodecode.model.repo import RepoModel
    from rhodecode.model.user import UserModel
    from rhodecode.model.settings import SettingsModel

    log = get_logger(create_repo)

    cur_user = UserModel()._get_user(cur_user)
    owner = cur_user

    repo_name = form_data['repo_name']
    repo_name_full = form_data['repo_name_full']
    repo_type = form_data['repo_type']
    description = form_data['repo_description']
    private = form_data['repo_private']
    clone_uri = form_data.get('clone_uri')
    repo_group = safe_int(form_data['repo_group'])
    landing_rev = form_data['repo_landing_rev']
    copy_fork_permissions = form_data.get('copy_permissions')
    copy_group_permissions = form_data.get('repo_copy_permissions')
    fork_of = form_data.get('fork_parent_id')
    state = form_data.get('repo_state', Repository.STATE_PENDING)

    # repo creation defaults, private and repo_type are filled in form
    defs = SettingsModel().get_default_repo_settings(strip_prefix=True)
    enable_statistics = form_data.get(
        'enable_statistics', defs.get('repo_enable_statistics'))
    enable_locking = form_data.get(
        'enable_locking', defs.get('repo_enable_locking'))
    enable_downloads = form_data.get(
        'enable_downloads', defs.get('repo_enable_downloads'))

    try:
        repo = RepoModel()._create_repo(
            repo_name=repo_name_full,
            repo_type=repo_type,
            description=description,
            owner=owner,
            private=private,
            clone_uri=clone_uri,
            repo_group=repo_group,
            landing_rev=landing_rev,
            fork_of=fork_of,
            copy_fork_permissions=copy_fork_permissions,
            copy_group_permissions=copy_group_permissions,
            enable_statistics=enable_statistics,
            enable_locking=enable_locking,
            enable_downloads=enable_downloads,
            state=state
        )
        Session().commit()

        # now create this repo on Filesystem
        RepoModel()._create_filesystem_repo(
            repo_name=repo_name,
            repo_type=repo_type,
            repo_group=RepoModel()._get_repo_group(repo_group),
            clone_uri=clone_uri,
        )
        repo = Repository.get_by_repo_name(repo_name_full)
        log_create_repository(created_by=owner.username, **repo.get_dict())

        # update repo commit caches initially
        repo.update_commit_cache()

        # set new created state
        repo.set_state(Repository.STATE_CREATED)
        repo_id = repo.repo_id
        repo_data = repo.get_api_data()

        audit_logger.store(
            'repo.create', action_data={'data': repo_data},
            user=cur_user,
            repo=audit_logger.RepoWrap(repo_name=repo_name, repo_id=repo_id))

        Session().commit()
    except Exception:
        log.warning('Exception occurred when creating repository, '
                    'doing cleanup...', exc_info=True)
        # rollback things manually !
        repo = Repository.get_by_repo_name(repo_name_full)
        if repo:
            Repository.delete(repo.repo_id)
            Session().commit()
            RepoModel()._delete_filesystem_repo(repo)
        raise

    # it's an odd fix to make celery fail task when exception occurs
    def on_failure(self, *args, **kwargs):
        pass

    return True


@async_task(ignore_result=True, base=RequestContextTask)
def create_repo_fork(form_data, cur_user):
    """
    Creates a fork of repository using internal VCS methods
    """
    from rhodecode.model.repo import RepoModel
    from rhodecode.model.user import UserModel

    log = get_logger(create_repo_fork)

    cur_user = UserModel()._get_user(cur_user)
    owner = cur_user

    repo_name = form_data['repo_name']  # fork in this case
    repo_name_full = form_data['repo_name_full']
    repo_type = form_data['repo_type']
    description = form_data['description']
    private = form_data['private']
    clone_uri = form_data.get('clone_uri')
    repo_group = safe_int(form_data['repo_group'])
    landing_rev = form_data['landing_rev']
    copy_fork_permissions = form_data.get('copy_permissions')
    fork_id = safe_int(form_data.get('fork_parent_id'))

    try:
        fork_of = RepoModel()._get_repo(fork_id)
        RepoModel()._create_repo(
            repo_name=repo_name_full,
            repo_type=repo_type,
            description=description,
            owner=owner,
            private=private,
            clone_uri=clone_uri,
            repo_group=repo_group,
            landing_rev=landing_rev,
            fork_of=fork_of,
            copy_fork_permissions=copy_fork_permissions
        )

        Session().commit()

        base_path = Repository.base_path()
        source_repo_path = os.path.join(base_path, fork_of.repo_name)

        # now create this repo on Filesystem
        RepoModel()._create_filesystem_repo(
            repo_name=repo_name,
            repo_type=repo_type,
            repo_group=RepoModel()._get_repo_group(repo_group),
            clone_uri=source_repo_path,
        )
        repo = Repository.get_by_repo_name(repo_name_full)
        log_create_repository(created_by=owner.username, **repo.get_dict())

        # update repo commit caches initially
        config = repo._config
        config.set('extensions', 'largefiles', '')
        repo.update_commit_cache(config=config)

        # set new created state
        repo.set_state(Repository.STATE_CREATED)

        repo_id = repo.repo_id
        repo_data = repo.get_api_data()
        audit_logger.store(
            'repo.fork', action_data={'data': repo_data},
            user=cur_user,
            repo=audit_logger.RepoWrap(repo_name=repo_name, repo_id=repo_id))

        Session().commit()
    except Exception as e:
        log.warning('Exception %s occurred when forking repository, '
                    'doing cleanup...', e)
        # rollback things manually !
        repo = Repository.get_by_repo_name(repo_name_full)
        if repo:
            Repository.delete(repo.repo_id)
            Session().commit()
            RepoModel()._delete_filesystem_repo(repo)
        raise

    # it's an odd fix to make celery fail task when exception occurs
    def on_failure(self, *args, **kwargs):
        pass

    return True


@async_task(ignore_result=True)
def sync_repo(*args, **kwargs):
    from rhodecode.model.scm import ScmModel
    log = get_logger(sync_repo)

    log.info('Pulling from %s', kwargs['repo_name'])
    ScmModel().pull_changes(kwargs['repo_name'], kwargs['username'])


