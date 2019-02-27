# -*- coding: utf-8 -*-

# Copyright (C) 2010-2019 RhodeCode GmbH
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

import pytest

from rhodecode.model.db import User, UserSshKeys

from rhodecode.tests import TestController, assert_session_flash
from rhodecode.tests.fixture import Fixture

fixture = Fixture()


def route_path(name, params=None, **kwargs):
    import urllib
    from rhodecode.apps._base import ADMIN_PREFIX

    base_url = {
        'edit_user_ssh_keys':
            ADMIN_PREFIX + '/users/{user_id}/edit/ssh_keys',
        'edit_user_ssh_keys_generate_keypair':
            ADMIN_PREFIX + '/users/{user_id}/edit/ssh_keys/generate',
        'edit_user_ssh_keys_add':
            ADMIN_PREFIX + '/users/{user_id}/edit/ssh_keys/new',
        'edit_user_ssh_keys_delete':
            ADMIN_PREFIX + '/users/{user_id}/edit/ssh_keys/delete',

    }[name].format(**kwargs)

    if params:
        base_url = '{}?{}'.format(base_url, urllib.urlencode(params))
    return base_url


class TestAdminUsersSshKeysView(TestController):
    INVALID_KEY = """\
            ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQDk+77sjDzVeB6vevJsuZds1iNU5
            LANOa5CU5G/9JYIA6RYsWWMO7mbsR82IUckdqOHmxSykfR1D1TdluyIpQLrwgH5kb
            n8FkVI8zBMCKakxowvN67B0R7b1BT4PPzW2JlOXei/m9W12ZY484VTow6/B+kf2Q8
            cP8tmCJmKWZma5Em7OTUhvjyQVNz3v7HfeY5Hq0Ci4ECJ59hepFDabJvtAXg9XrI6
            jvdphZTc30I4fG8+hBHzpeFxUGvSGNtXPUbwaAY8j/oHYrTpMgkj6pUEFsiKfC5zP
            qPFR5HyKTCHW0nFUJnZsbyFT5hMiF/hZkJc9A0ZbdSvJwCRQ/g3bmdL 
            your_email@example.com      
        """
    VALID_KEY = 'ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQDk+77sjDzVeB6vev' \
                   'JsuZds1iNU5LANOa5CU5G/9JYIA6RYsWWMO7mbsR82IUckdqOHmxSy' \
                   'kfR1D1TdluyIpQLrwgH5kbn8FkVI8zBMCKakxowvN67B0R7b1BT4PP' \
                   'zW2JlOXei/m9W12ZY484VTow6/B+kf2Q8cP8tmCJmKWZma5Em7OTUh' \
                   'vjyQVNz3v7HfeY5Hq0Ci4ECJ59hepFDabJvtAXg9XrI6jvdphZTc30' \
                   'I4fG8+hBHzpeFxUGvSGNtXPUbwaAY8j/oHYrTpMgkj6pUEFsiKfC5zPq' \
                   'PFR5HyKTCHW0nFUJnZsbyFT5hMiF/hZkJc9A0ZbdSvJwCRQ/g3bmdL ' \
                   'your_email@example.com'
    FINGERPRINT = 'MD5:01:4f:ad:29:22:6e:01:37:c9:d2:52:26:52:b0:2d:93'

    def test_ssh_keys_default_user(self):
        self.log_user()
        user = User.get_default_user()
        self.app.get(
            route_path('edit_user_ssh_keys', user_id=user.user_id),
            status=302)

    def test_add_ssh_key_error(self, user_util):
        self.log_user()
        user = user_util.create_user()
        user_id = user.user_id

        key_data = self.INVALID_KEY

        desc = 'MY SSH KEY'
        response = self.app.post(
            route_path('edit_user_ssh_keys_add', user_id=user_id),
            {'description': desc, 'key_data': key_data,
             'csrf_token': self.csrf_token})
        assert_session_flash(response, 'An error occurred during ssh '
                                       'key saving: Unable to decode the key')

    def test_ssh_key_duplicate(self, user_util):
        self.log_user()
        user = user_util.create_user()
        user_id = user.user_id

        key_data = self.VALID_KEY

        desc = 'MY SSH KEY'
        response = self.app.post(
            route_path('edit_user_ssh_keys_add', user_id=user_id),
            {'description': desc, 'key_data': key_data,
             'csrf_token': self.csrf_token})
        assert_session_flash(response, 'Ssh Key successfully created')
        response.follow()  # flush session flash

        # add the same key AGAIN
        desc = 'MY SSH KEY'
        response = self.app.post(
            route_path('edit_user_ssh_keys_add', user_id=user_id),
            {'description': desc, 'key_data': key_data,
             'csrf_token': self.csrf_token})

        err = 'Such key with fingerprint `{}` already exists, ' \
              'please use a different one'.format(self.FINGERPRINT)
        assert_session_flash(response, 'An error occurred during ssh key '
                                       'saving: {}'.format(err))

    def test_add_ssh_key(self, user_util):
        self.log_user()
        user = user_util.create_user()
        user_id = user.user_id

        key_data = self.VALID_KEY

        desc = 'MY SSH KEY'
        response = self.app.post(
            route_path('edit_user_ssh_keys_add', user_id=user_id),
            {'description': desc, 'key_data': key_data,
             'csrf_token': self.csrf_token})
        assert_session_flash(response, 'Ssh Key successfully created')

        response = response.follow()
        response.mustcontain(desc)

    def test_delete_ssh_key(self, user_util):
        self.log_user()
        user = user_util.create_user()
        user_id = user.user_id

        key_data = self.VALID_KEY

        desc = 'MY SSH KEY'
        response = self.app.post(
            route_path('edit_user_ssh_keys_add', user_id=user_id),
            {'description': desc, 'key_data': key_data,
             'csrf_token': self.csrf_token})
        assert_session_flash(response, 'Ssh Key successfully created')
        response = response.follow()  # flush the Session flash

        # now delete our key
        keys = UserSshKeys.query().filter(UserSshKeys.user_id == user_id).all()
        assert 1 == len(keys)

        response = self.app.post(
            route_path('edit_user_ssh_keys_delete', user_id=user_id),
            {'del_ssh_key': keys[0].ssh_key_id,
             'csrf_token': self.csrf_token})

        assert_session_flash(response, 'Ssh key successfully deleted')
        keys = UserSshKeys.query().filter(UserSshKeys.user_id == user_id).all()
        assert 0 == len(keys)

    def test_generate_keypair(self, user_util):
        self.log_user()
        user = user_util.create_user()
        user_id = user.user_id

        response = self.app.get(
            route_path('edit_user_ssh_keys_generate_keypair', user_id=user_id))

        response.mustcontain('Private key')
        response.mustcontain('Public key')
        response.mustcontain('-----BEGIN PRIVATE KEY-----')
