# -*- coding: utf-8 -*-

# Copyright (C) 2012-2020 RhodeCode GmbH
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
import time

from pyramid import compat
from pyramid_mailer.mailer import Mailer
from pyramid_mailer.message import Message
from email.utils import formatdate

import rhodecode
from rhodecode.lib import audit_logger
from rhodecode.lib.celerylib import get_logger, async_task, RequestContextTask, run_task
from rhodecode.lib import hooks_base
from rhodecode.lib.utils2 import safe_int, str2bool, aslist
from rhodecode.model.db import (
    Session, IntegrityError, true, Repository, RepoGroup, User)
from rhodecode.model.permission import PermissionModel


@async_task(ignore_result=True, base=RequestContextTask)
def send_email(recipients, subject, body='', html_body='', email_config=None,
               extra_headers=None):
    """
    Sends an email with defined parameters from the .ini files.

    :param recipients: list of recipients, it this is empty the defined email
        address from field 'email_to' is used instead
    :param subject: subject of the mail
    :param body: body of the mail
    :param html_body: html version of body
    :param email_config: specify custom configuration for mailer
    :param extra_headers: specify custom headers
    """
    log = get_logger(send_email)

    email_config = email_config or rhodecode.CONFIG

    mail_server = email_config.get('smtp_server') or None
    if mail_server is None:
        log.error("SMTP server information missing. Sending email failed. "
                  "Make sure that `smtp_server` variable is configured "
                  "inside the .ini file")
        return False

    subject = "%s %s" % (email_config.get('email_prefix', ''), subject)

    if recipients:
        if isinstance(recipients, compat.string_types):
            recipients = recipients.split(',')
    else:
        # if recipients are not defined we send to email_config + all admins
        admins = []
        for u in User.query().filter(User.admin == true()).all():
            if u.email:
                admins.append(u.email)
        recipients = []
        config_email = email_config.get('email_to')
        if config_email:
            recipients += [config_email]
        recipients += admins

    # translate our LEGACY config into the one that pyramid_mailer supports
    email_conf = dict(
        host=mail_server,
        port=email_config.get('smtp_port', 25),
        username=email_config.get('smtp_username'),
        password=email_config.get('smtp_password'),

        tls=str2bool(email_config.get('smtp_use_tls')),
        ssl=str2bool(email_config.get('smtp_use_ssl')),

        # SSL key file
        # keyfile='',

        # SSL certificate file
        # certfile='',

        # Location of maildir
        # queue_path='',

        default_sender=email_config.get('app_email_from', 'RhodeCode-noreply@rhodecode.com'),

        debug=str2bool(email_config.get('smtp_debug')),
        # /usr/sbin/sendmail	Sendmail executable
        # sendmail_app='',

        # {sendmail_app} -t -i -f {sender}	Template for sendmail execution
        # sendmail_template='',
    )

    if extra_headers is None:
        extra_headers = {}

    extra_headers.setdefault('Date', formatdate(time.time()))

    if 'thread_ids' in extra_headers:
        thread_ids = extra_headers.pop('thread_ids')
        extra_headers['References'] = ' '.join('<{}>'.format(t) for t in thread_ids)

    try:
        mailer = Mailer(**email_conf)

        message = Message(subject=subject,
                          sender=email_conf['default_sender'],
                          recipients=recipients,
                          body=body, html=html_body,
                          extra_headers=extra_headers)
        mailer.send_immediately(message)

    except Exception:
        log.exception('Mail sending failed')
        return False
    return True


@async_task(ignore_result=True, base=RequestContextTask)
def create_repo(form_data, cur_user):
    from rhodecode.model.repo import RepoModel
    from rhodecode.model.user import UserModel
    from rhodecode.model.scm import ScmModel
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

    # set landing rev based on default branches for SCM
    landing_ref, _label = ScmModel.backend_landing_ref(repo_type)

    try:
        RepoModel()._create_repo(
            repo_name=repo_name_full,
            repo_type=repo_type,
            description=description,
            owner=owner,
            private=private,
            clone_uri=clone_uri,
            repo_group=repo_group,
            landing_rev=landing_ref,
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
        hooks_base.create_repository(created_by=owner.username, **repo.get_dict())

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

        PermissionModel().trigger_permission_flush()

    except Exception as e:
        log.warning('Exception occurred when creating repository, '
                    'doing cleanup...', exc_info=True)
        if isinstance(e, IntegrityError):
            Session().rollback()

        # rollback things manually !
        repo = Repository.get_by_repo_name(repo_name_full)
        if repo:
            Repository.delete(repo.repo_id)
            Session().commit()
            RepoModel()._delete_filesystem_repo(repo)
        log.info('Cleanup of repo %s finished', repo_name_full)
        raise

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
    landing_ref = form_data['landing_rev']
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
            landing_rev=landing_ref,
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
        hooks_base.create_repository(created_by=owner.username, **repo.get_dict())

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
        log.warning('Exception occurred when forking repository, '
                    'doing cleanup...', exc_info=True)
        if isinstance(e, IntegrityError):
            Session().rollback()

        # rollback things manually !
        repo = Repository.get_by_repo_name(repo_name_full)
        if repo:
            Repository.delete(repo.repo_id)
            Session().commit()
            RepoModel()._delete_filesystem_repo(repo)
        log.info('Cleanup of repo %s finished', repo_name_full)
        raise

    return True


@async_task(ignore_result=True)
def repo_maintenance(repoid):
    from rhodecode.lib import repo_maintenance as repo_maintenance_lib
    log = get_logger(repo_maintenance)
    repo = Repository.get_by_id_or_repo_name(repoid)
    if repo:
        maintenance = repo_maintenance_lib.RepoMaintenance()
        tasks = maintenance.get_tasks_for_repo(repo)
        log.debug('Executing %s tasks on repo `%s`', tasks, repoid)
        executed_types = maintenance.execute(repo)
        log.debug('Got execution results %s', executed_types)
    else:
        log.debug('Repo `%s` not found or without a clone_url', repoid)


@async_task(ignore_result=True)
def check_for_update(send_email_notification=True, email_recipients=None):
    from rhodecode.model.update import UpdateModel
    from rhodecode.model.notification import EmailNotificationModel

    log = get_logger(check_for_update)
    update_url = UpdateModel().get_update_url()
    cur_ver = rhodecode.__version__

    try:
        data = UpdateModel().get_update_data(update_url)

        current_ver = UpdateModel().get_stored_version(fallback=cur_ver)
        latest_ver = data['versions'][0]['version']
        UpdateModel().store_version(latest_ver)

        if send_email_notification:
            log.debug('Send email notification is enabled. '
                      'Current RhodeCode version: %s, latest known: %s', current_ver, latest_ver)
            if UpdateModel().is_outdated(current_ver, latest_ver):

                email_kwargs = {
                    'current_ver': current_ver,
                    'latest_ver': latest_ver,
                }

                (subject, email_body, email_body_plaintext) = EmailNotificationModel().render_email(
                    EmailNotificationModel.TYPE_UPDATE_AVAILABLE, **email_kwargs)

                email_recipients = aslist(email_recipients, sep=',') or \
                                   [user.email for user in User.get_all_super_admins()]
                run_task(send_email, email_recipients, subject,
                         email_body_plaintext, email_body)

    except Exception:
        pass


@async_task(ignore_result=False)
def beat_check(*args, **kwargs):
    log = get_logger(beat_check)
    log.info('%r: Got args: %r and kwargs %r', beat_check, args, kwargs)
    return time.time()


def sync_last_update_for_objects(*args, **kwargs):
    skip_repos = kwargs.get('skip_repos')
    if not skip_repos:
        repos = Repository.query() \
            .order_by(Repository.group_id.asc())

        for repo in repos:
            repo.update_commit_cache()

    skip_groups = kwargs.get('skip_groups')
    if not skip_groups:
        repo_groups = RepoGroup.query() \
            .filter(RepoGroup.group_parent_id == None)

        for root_gr in repo_groups:
            for repo_gr in reversed(root_gr.recursive_groups()):
                repo_gr.update_commit_cache()


@async_task(ignore_result=True)
def sync_last_update(*args, **kwargs):
    sync_last_update_for_objects(*args, **kwargs)
