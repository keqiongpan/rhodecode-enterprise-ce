# -*- coding: utf-8 -*-

# Copyright (C) 2016-2019 RhodeCode GmbH
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

import logging

from pyramid.httpexceptions import HTTPFound
from pyramid.view import view_config

from rhodecode.apps._base import BaseAppView, DataGridAppView
from rhodecode.apps.ssh_support import SshKeyFileChangeEvent
from rhodecode.events import trigger
from rhodecode.lib import helpers as h
from rhodecode.lib import audit_logger
from rhodecode.lib.auth import LoginRequired, NotAnonymous, CSRFRequired
from rhodecode.model.db import IntegrityError, UserSshKeys
from rhodecode.model.meta import Session
from rhodecode.model.ssh_key import SshKeyModel

log = logging.getLogger(__name__)


class MyAccountSshKeysView(BaseAppView, DataGridAppView):

    def load_default_context(self):
        c = self._get_local_tmpl_context()
        c.user = c.auth_user.get_instance()

        c.ssh_enabled = self.request.registry.settings.get(
            'ssh.generate_authorized_keyfile')

        return c

    @LoginRequired()
    @NotAnonymous()
    @view_config(
        route_name='my_account_ssh_keys', request_method='GET',
        renderer='rhodecode:templates/admin/my_account/my_account.mako')
    def my_account_ssh_keys(self):
        _ = self.request.translate

        c = self.load_default_context()
        c.active = 'ssh_keys'
        c.default_key = self.request.GET.get('default_key')
        c.user_ssh_keys = SshKeyModel().get_ssh_keys(c.user.user_id)
        return self._get_template_context(c)

    @LoginRequired()
    @NotAnonymous()
    @view_config(
        route_name='my_account_ssh_keys_generate', request_method='GET',
        renderer='rhodecode:templates/admin/my_account/my_account.mako')
    def ssh_keys_generate_keypair(self):
        _ = self.request.translate
        c = self.load_default_context()

        c.active = 'ssh_keys_generate'
        if c.ssh_key_generator_enabled:
            private_format = self.request.GET.get('private_format') \
                             or SshKeyModel.DEFAULT_PRIVATE_KEY_FORMAT
            comment = 'RhodeCode-SSH {}'.format(c.user.email or '')
            c.private, c.public = SshKeyModel().generate_keypair(
                comment=comment, private_format=private_format)
            c.target_form_url = h.route_path(
                'my_account_ssh_keys', _query=dict(default_key=c.public))
        return self._get_template_context(c)

    @LoginRequired()
    @NotAnonymous()
    @CSRFRequired()
    @view_config(
        route_name='my_account_ssh_keys_add', request_method='POST',)
    def my_account_ssh_keys_add(self):
        _ = self.request.translate
        c = self.load_default_context()

        user_data = c.user.get_api_data()
        key_data = self.request.POST.get('key_data')
        description = self.request.POST.get('description')
        fingerprint = 'unknown'
        try:
            if not key_data:
                raise ValueError('Please add a valid public key')

            key = SshKeyModel().parse_key(key_data.strip())
            fingerprint = key.hash_md5()

            ssh_key = SshKeyModel().create(
                c.user.user_id, fingerprint, key.keydata, description)
            ssh_key_data = ssh_key.get_api_data()

            audit_logger.store_web(
                'user.edit.ssh_key.add', action_data={
                    'data': {'ssh_key': ssh_key_data, 'user': user_data}},
                user=self._rhodecode_user, )
            Session().commit()

            # Trigger an event on change of keys.
            trigger(SshKeyFileChangeEvent(), self.request.registry)

            h.flash(_("Ssh Key successfully created"), category='success')

        except IntegrityError:
            log.exception("Exception during ssh key saving")
            err = 'Such key with fingerprint `{}` already exists, ' \
                  'please use a different one'.format(fingerprint)
            h.flash(_('An error occurred during ssh key saving: {}').format(err),
                    category='error')
        except Exception as e:
            log.exception("Exception during ssh key saving")
            h.flash(_('An error occurred during ssh key saving: {}').format(e),
                    category='error')

        return HTTPFound(h.route_path('my_account_ssh_keys'))

    @LoginRequired()
    @NotAnonymous()
    @CSRFRequired()
    @view_config(
        route_name='my_account_ssh_keys_delete', request_method='POST')
    def my_account_ssh_keys_delete(self):
        _ = self.request.translate
        c = self.load_default_context()

        user_data = c.user.get_api_data()

        del_ssh_key = self.request.POST.get('del_ssh_key')

        if del_ssh_key:
            ssh_key = UserSshKeys.get_or_404(del_ssh_key)
            ssh_key_data = ssh_key.get_api_data()

            SshKeyModel().delete(del_ssh_key, c.user.user_id)
            audit_logger.store_web(
                'user.edit.ssh_key.delete', action_data={
                    'data': {'ssh_key': ssh_key_data, 'user': user_data}},
                user=self._rhodecode_user,)
            Session().commit()
            # Trigger an event on change of keys.
            trigger(SshKeyFileChangeEvent(), self.request.registry)
            h.flash(_("Ssh key successfully deleted"), category='success')

        return HTTPFound(h.route_path('my_account_ssh_keys'))
