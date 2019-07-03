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
import os
import pytest

from rhodecode.lib.ext_json import json
from rhodecode.model.db import Session, FileStore
from rhodecode.tests import TestController
from rhodecode.apps.file_store import utils, config_keys


def route_path(name, params=None, **kwargs):
    import urllib

    base_url = {
        'upload_file': '/_file_store/upload',
        'download_file': '/_file_store/download/{fid}',

    }[name].format(**kwargs)

    if params:
        base_url = '{}?{}'.format(base_url, urllib.urlencode(params))
    return base_url


class TestFileStoreViews(TestController):

    @pytest.mark.parametrize("fid, content, exists", [
        ('abcde-0.jpg', "xxxxx", True),
        ('abcde-0.exe', "1234567", True),
        ('abcde-0.jpg', "xxxxx", False),
    ])
    def test_get_files_from_store(self, fid, content, exists, tmpdir, user_util):
        user = self.log_user()
        user_id = user['user_id']
        repo_id = user_util.create_repo().repo_id
        store_path = self.app._pyramid_settings[config_keys.store_path]
        store_uid = fid

        if exists:
            status = 200
            store = utils.get_file_storage({config_keys.store_path: store_path})
            filesystem_file = os.path.join(str(tmpdir), fid)
            with open(filesystem_file, 'wb') as f:
                f.write(content)

            with open(filesystem_file, 'rb') as f:
                store_uid, metadata = store.save_file(f, fid, extra_metadata={'filename': fid})

            entry = FileStore.create(
                file_uid=store_uid, filename=metadata["filename"],
                file_hash=metadata["sha256"], file_size=metadata["size"],
                file_display_name='file_display_name',
                file_description='repo artifact `{}`'.format(metadata["filename"]),
                check_acl=True, user_id=user_id,
                scope_repo_id=repo_id
            )
            Session().add(entry)
            Session().commit()

        else:
            status = 404

        response = self.app.get(route_path('download_file', fid=store_uid), status=status)

        if exists:
            assert response.text == content
            file_store_path = os.path.dirname(store.resolve_name(store_uid, store_path)[1])
            metadata_file = os.path.join(file_store_path, store_uid + '.meta')
            assert os.path.exists(metadata_file)
            with open(metadata_file, 'rb') as f:
                json_data = json.loads(f.read())

            assert json_data
            assert 'size' in json_data

    def test_upload_files_without_content_to_store(self):
        self.log_user()
        response = self.app.post(
            route_path('upload_file'),
            params={'csrf_token': self.csrf_token},
            status=200)

        assert response.json == {
            u'error': u'store_file data field is missing',
            u'access_path': None,
            u'store_fid': None}

    def test_upload_files_bogus_content_to_store(self):
        self.log_user()
        response = self.app.post(
            route_path('upload_file'),
            params={'csrf_token': self.csrf_token, 'store_file': 'bogus'},
            status=200)

        assert response.json == {
            u'error': u'filename cannot be read from the data field',
            u'access_path': None,
            u'store_fid': None}

    def test_upload_content_to_store(self):
        self.log_user()
        response = self.app.post(
            route_path('upload_file'),
            upload_files=[('store_file', 'myfile.txt', 'SOME CONTENT')],
            params={'csrf_token': self.csrf_token},
            status=200)

        assert response.json['store_fid']
