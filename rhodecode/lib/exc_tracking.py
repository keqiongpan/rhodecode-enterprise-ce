# -*- coding: utf-8 -*-

# Copyright (C) 2010-2020 RhodeCode GmbH
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

import os
import time
import datetime
import msgpack
import logging
import traceback
import tempfile
import glob

log = logging.getLogger(__name__)

# NOTE: Any changes should be synced with exc_tracking at vcsserver.lib.exc_tracking
global_prefix = 'rhodecode'
exc_store_dir_name = 'rc_exception_store_v1'


def exc_serialize(exc_id, tb, exc_type, extra_data=None):

    data = {
        'version': 'v1',
        'exc_id': exc_id,
        'exc_utc_date': datetime.datetime.utcnow().isoformat(),
        'exc_timestamp': repr(time.time()),
        'exc_message': tb,
        'exc_type': exc_type,
    }
    if extra_data:
        data.update(extra_data)
    return msgpack.packb(data), data


def exc_unserialize(tb):
    return msgpack.unpackb(tb)

_exc_store = None


def get_exc_store():
    """
    Get and create exception store if it's not existing
    """
    global _exc_store
    import rhodecode as app

    if _exc_store is not None:
        # quick global cache
        return _exc_store

    exc_store_dir = app.CONFIG.get('exception_tracker.store_path', '') or tempfile.gettempdir()
    _exc_store_path = os.path.join(exc_store_dir, exc_store_dir_name)

    _exc_store_path = os.path.abspath(_exc_store_path)
    if not os.path.isdir(_exc_store_path):
        os.makedirs(_exc_store_path)
        log.debug('Initializing exceptions store at %s', _exc_store_path)
        _exc_store = _exc_store_path

    return _exc_store_path


def _store_exception(exc_id, exc_type_name, exc_traceback, prefix, send_email=None):
    """
    Low level function to store exception in the exception tracker
    """
    from pyramid.threadlocal import get_current_request
    import rhodecode as app
    request = get_current_request()
    extra_data = {}
    # NOTE(marcink): store request information into exc_data
    if request:
        extra_data['client_address'] = getattr(request, 'client_addr', '')
        extra_data['user_agent'] = getattr(request, 'user_agent', '')
        extra_data['method'] = getattr(request, 'method', '')
        extra_data['url'] = getattr(request, 'url', '')

    exc_store_path = get_exc_store()
    exc_data, org_data = exc_serialize(exc_id, exc_traceback, exc_type_name, extra_data=extra_data)

    exc_pref_id = '{}_{}_{}'.format(exc_id, prefix, org_data['exc_timestamp'])
    if not os.path.isdir(exc_store_path):
        os.makedirs(exc_store_path)
    stored_exc_path = os.path.join(exc_store_path, exc_pref_id)
    with open(stored_exc_path, 'wb') as f:
        f.write(exc_data)
    log.debug('Stored generated exception %s as: %s', exc_id, stored_exc_path)

    if send_email is None:
        # NOTE(marcink): read app config unless we specify explicitly
        send_email = app.CONFIG.get('exception_tracker.send_email', False)

    mail_server = app.CONFIG.get('smtp_server') or None
    send_email = send_email and mail_server
    if send_email and request:
        try:
            send_exc_email(request, exc_id, exc_type_name)
        except Exception:
            log.exception('Failed to send exception email')
            pass


def send_exc_email(request, exc_id, exc_type_name):
    import rhodecode as app
    from rhodecode.apps._base import TemplateArgs
    from rhodecode.lib.utils2 import aslist
    from rhodecode.lib.celerylib import run_task, tasks
    from rhodecode.lib.base import attach_context_attributes
    from rhodecode.model.notification import EmailNotificationModel

    recipients = aslist(app.CONFIG.get('exception_tracker.send_email_recipients', ''))
    log.debug('Sending Email exception to: `%s`', recipients or 'all super admins')

    # NOTE(marcink): needed for email template rendering
    user_id = None
    if hasattr(request, 'user'):
        user_id = request.user.user_id
    attach_context_attributes(TemplateArgs(), request, user_id=user_id, is_api=True)

    email_kwargs = {
        'email_prefix': app.CONFIG.get('exception_tracker.email_prefix', '') or '[RHODECODE ERROR]',
        'exc_url': request.route_url('admin_settings_exception_tracker_show', exception_id=exc_id),
        'exc_id': exc_id,
        'exc_type_name': exc_type_name,
        'exc_traceback': read_exception(exc_id, prefix=None),
    }

    (subject, email_body, email_body_plaintext) = EmailNotificationModel().render_email(
        EmailNotificationModel.TYPE_EMAIL_EXCEPTION, **email_kwargs)

    run_task(tasks.send_email, recipients, subject,
             email_body_plaintext, email_body)


def _prepare_exception(exc_info):
    exc_type, exc_value, exc_traceback = exc_info
    exc_type_name = exc_type.__name__

    tb = ''.join(traceback.format_exception(
        exc_type, exc_value, exc_traceback, None))

    return exc_type_name, tb


def store_exception(exc_id, exc_info, prefix=global_prefix):
    """
    Example usage::

        exc_info = sys.exc_info()
        store_exception(id(exc_info), exc_info)
    """

    try:
        exc_type_name, exc_traceback = _prepare_exception(exc_info)
        _store_exception(exc_id=exc_id, exc_type_name=exc_type_name,
                         exc_traceback=exc_traceback, prefix=prefix)
        return exc_id, exc_type_name
    except Exception:
        log.exception('Failed to store exception `%s` information', exc_id)
        # there's no way this can fail, it will crash server badly if it does.
        pass


def _find_exc_file(exc_id, prefix=global_prefix):
    exc_store_path = get_exc_store()
    if prefix:
        exc_id = '{}_{}'.format(exc_id, prefix)
    else:
        # search without a prefix
        exc_id = '{}'.format(exc_id)

    found_exc_id = None
    matches = glob.glob(os.path.join(exc_store_path, exc_id) + '*')
    if matches:
        found_exc_id = matches[0]

    return found_exc_id


def _read_exception(exc_id, prefix):
    exc_id_file_path = _find_exc_file(exc_id=exc_id, prefix=prefix)
    if exc_id_file_path:
        with open(exc_id_file_path, 'rb') as f:
            return exc_unserialize(f.read())
    else:
        log.debug('Exception File `%s` not found', exc_id_file_path)
    return None


def read_exception(exc_id, prefix=global_prefix):
    try:
        return _read_exception(exc_id=exc_id, prefix=prefix)
    except Exception:
        log.exception('Failed to read exception `%s` information', exc_id)
        # there's no way this can fail, it will crash server badly if it does.
    return None


def delete_exception(exc_id, prefix=global_prefix):
    try:
        exc_id_file_path = _find_exc_file(exc_id, prefix=prefix)
        if exc_id_file_path:
            os.remove(exc_id_file_path)

    except Exception:
        log.exception('Failed to remove exception `%s` information', exc_id)
        # there's no way this can fail, it will crash server badly if it does.
        pass


def generate_id():
    return id(object())
