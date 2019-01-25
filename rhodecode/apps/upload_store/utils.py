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


import os
import uuid


def get_file_storage(settings):
    from rhodecode.apps.upload_store.local_store import LocalFileStorage
    from rhodecode.apps.upload_store import config_keys
    store_path = settings.get(config_keys.store_path)
    return LocalFileStorage(base_path=store_path)


def uid_filename(filename, randomized=True):
    """
    Generates a randomized or stable (uuid) filename,
    preserving the original extension.

    :param filename: the original filename
    :param randomized: define if filename should be stable (sha1 based) or randomized
    """
    _, ext = os.path.splitext(filename)
    if randomized:
        uid = uuid.uuid4()
    else:
        hash_key = '{}.{}'.format(filename, 'store')
        uid = uuid.uuid5(uuid.NAMESPACE_URL, hash_key)
    return str(uid) + ext.lower()
