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
from rhodecode.tests import HG_REPO
from rhodecode.api.tests.utils import (
    build_data, api_call, assert_error, assert_ok)


@pytest.mark.usefixtures("testuser_api", "app")
class TestApiSearch(object):

    @pytest.mark.parametrize("sort_dir", [
        "asc",
        "desc",
    ])
    @pytest.mark.parametrize("sort", [
        "xxx",
        "author_email",
        "date",
        "message",
    ])
    @pytest.mark.parametrize("query, expected_hits, expected_paths", [
        ('todo', 23, [
            'vcs/backends/hg/inmemory.py',
            'vcs/tests/test_git.py']),
        ('extension:rst installation', 6, [
            'docs/index.rst',
            'docs/installation.rst']),
        ('def repo', 87, [
            'vcs/tests/test_git.py',
            'vcs/tests/test_changesets.py']),
        ('repository:%s def test' % HG_REPO, 18, [
            'vcs/tests/test_git.py',
            'vcs/tests/test_changesets.py']),
        ('"def main"', 9, [
            'vcs/__init__.py',
            'vcs/tests/__init__.py',
            'vcs/utils/progressbar.py']),
        ('owner:test_admin', 358, [
            'vcs/tests/base.py',
            'MANIFEST.in',
            'vcs/utils/termcolors.py',
            'docs/theme/ADC/static/documentation.png']),
        ('owner:test_admin def main', 72, [
            'vcs/__init__.py',
            'vcs/tests/test_utils_filesize.py',
            'vcs/tests/test_cli.py']),
        ('owner:michał test', 0, []),
    ])
    def test_search_content_results(self, sort_dir, sort, query, expected_hits, expected_paths):
        id_, params = build_data(
            self.apikey_regular, 'search',
            search_query=query,
            search_sort='{}:{}'.format(sort_dir, sort),
            search_type='content')

        response = api_call(self.app, params)
        json_response = response.json

        assert json_response['result']['item_count'] == expected_hits
        paths = [x['f_path'] for x in json_response['result']['results']]

        for expected_path in expected_paths:
            assert expected_path in paths

    @pytest.mark.parametrize("sort_dir", [
        "asc",
        "desc",
    ])
    @pytest.mark.parametrize("sort", [
        "xxx",
        "date",
        "file",
        "size",
    ])
    @pytest.mark.parametrize("query, expected_hits, expected_paths", [
        ('readme.rst', 3, []),
        ('test*', 75, []),
        ('*model*', 1, []),
        ('extension:rst', 48, []),
        ('extension:rst api', 24, []),
    ])
    def test_search_file_paths(self, sort_dir, sort, query, expected_hits, expected_paths):
        id_, params = build_data(
            self.apikey_regular, 'search',
            search_query=query,
            search_sort='{}:{}'.format(sort_dir, sort),
            search_type='path')

        response = api_call(self.app, params)
        json_response = response.json

        assert json_response['result']['item_count'] == expected_hits
        paths = [x['f_path'] for x in json_response['result']['results']]

        for expected_path in expected_paths:
            assert expected_path in paths
