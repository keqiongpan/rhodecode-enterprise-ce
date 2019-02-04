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
    def test_get_files_from_store(self, fid, content, exists, tmpdir):
        self.log_user()
        store_path = self.app._pyramid_settings[config_keys.store_path]

        if exists:
            status = 200
            store = utils.get_file_storage({config_keys.store_path: store_path})
            filesystem_file = os.path.join(str(tmpdir), fid)
            with open(filesystem_file, 'wb') as f:
                f.write(content)

            with open(filesystem_file, 'rb') as f:
                fid, metadata = store.save_file(f, fid, extra_metadata={'filename': fid})

        else:
            status = 404

        response = self.app.get(route_path('download_file', fid=fid), status=status)

        if exists:
            assert response.text == content
            file_store_path = os.path.dirname(store.resolve_name(fid, store_path)[1])
            metadata_file = os.path.join(file_store_path, fid + '.meta')
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
