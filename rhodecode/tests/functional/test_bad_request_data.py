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

import pytest

from rhodecode.tests import TestController
from rhodecode.tests.fixture import Fixture


class TestBadRequestData(TestController):

    def test_bad_get_data(self):
        self.app.get(
            '/', params={'f\xfc': '\xfc%f6%22%20onmouseover%3dveA2(9352)%20'},
            status=400)

    def test_bad_url_data(self):
        self.app.post(
            '/f\xfc',
            status=400)

    def test_bad_post_data(self, csrf_token, xhr_header):
        self.app.post(
            '/_markup_preview',
            params={'f\xfc': '\xfc%f6%22%20onmouseover%3dveA2(9352)%20',
                    'csrf_token': csrf_token},
            extra_environ=xhr_header,
            status=400)
