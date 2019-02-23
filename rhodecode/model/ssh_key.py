# -*- coding: utf-8 -*-

# Copyright (C) 2013-2019 RhodeCode GmbH
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
import traceback

import sshpubkeys
import sshpubkeys.exceptions

from rhodecode.model import BaseModel
from rhodecode.model.db import UserSshKeys
from rhodecode.model.meta import Session

log = logging.getLogger(__name__)


class SshKeyModel(BaseModel):
    cls = UserSshKeys

    def parse_key(self, key_data):
        """
        print(ssh.bits)  # 768
        print(ssh.hash_md5())  # 56:84:1e:90:08:3b:60:c7:29:70:5f:5e:25:a6:3b:86
        print(ssh.hash_sha256())  # SHA256:xk3IEJIdIoR9MmSRXTP98rjDdZocmXJje/28ohMQEwM
        print(ssh.hash_sha512())  # SHA512:1C3lNBhjpDVQe39hnyy+xvlZYU3IPwzqK1rVneGavy6O3/ebjEQSFvmeWoyMTplIanmUK1hmr9nA8Skmj516HA
        print(ssh.comment)  # ojar@ojar-laptop
        print(ssh.options_raw)  # None (string of optional options at the beginning of public key)
        print(ssh.options)  # None (options as a dictionary, parsed and validated)

        :param key_data:
        :return:
        """
        ssh = sshpubkeys.SSHKey(strict_mode=True)
        try:
            ssh.parse(key_data)
            return ssh
        except sshpubkeys.exceptions.InvalidKeyException as err:
            log.error("Invalid key: %s", err)
            raise
        except NotImplementedError as err:
            log.error("Invalid key type: %s", err)
            raise
        except Exception as err:
            log.error("Key Parse error: %s", err)
            raise

    def generate_keypair(self, comment=None):
        from Crypto.PublicKey import RSA

        key = RSA.generate(2048)
        private = key.exportKey('PEM')

        pubkey = key.publickey()
        public = pubkey.exportKey('OpenSSH')
        if comment:
            public = public + " " + comment
        return private, public

    def create(self, user, fingerprint, key_data, description):
        """
        """
        user = self._get_user(user)

        new_ssh_key = UserSshKeys()
        new_ssh_key.ssh_key_fingerprint = fingerprint
        new_ssh_key.ssh_key_data = key_data
        new_ssh_key.user_id = user.user_id
        new_ssh_key.description = description

        Session().add(new_ssh_key)

        return new_ssh_key

    def delete(self, ssh_key_id, user=None):
        """
        Deletes given api_key, if user is set it also filters the object for
        deletion by given user.
        """
        ssh_key = UserSshKeys.query().filter(
            UserSshKeys.ssh_key_id == ssh_key_id)

        if user:
            user = self._get_user(user)
            ssh_key = ssh_key.filter(UserSshKeys.user_id == user.user_id)
            ssh_key = ssh_key.scalar()

        if ssh_key:
            try:
                Session().delete(ssh_key)
            except Exception:
                log.error(traceback.format_exc())
                raise

    def get_ssh_keys(self, user):
        user = self._get_user(user)
        user_ssh_keys = UserSshKeys.query()\
            .filter(UserSshKeys.user_id == user.user_id)
        user_ssh_keys = user_ssh_keys.order_by(UserSshKeys.ssh_key_id)
        return user_ssh_keys

    def get_ssh_key_by_fingerprint(self, ssh_key_fingerprint):
        user_ssh_key = UserSshKeys.query()\
            .filter(UserSshKeys.ssh_key_fingerprint == ssh_key_fingerprint)\
            .first()

        return user_ssh_key
