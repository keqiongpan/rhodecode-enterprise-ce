# -*- coding: utf-8 -*-

# Copyright (C) 2011-2018 RhodeCode GmbH
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
from pyramid.view import view_config

from rhodecode.apps._base import BaseReferencesView
from rhodecode.lib.ext_json import json
from rhodecode.lib.auth import (LoginRequired, HasRepoPermissionAnyDecorator)


log = logging.getLogger(__name__)


class RepoBranchesView(BaseReferencesView):

    @LoginRequired()
    @HasRepoPermissionAnyDecorator(
        'repository.read', 'repository.write', 'repository.admin')
    @view_config(
        route_name='branches_home', request_method='GET',
        renderer='rhodecode:templates/branches/branches.mako')
    def branches(self):
        c = self.load_default_context()

        ref_items = self.rhodecode_vcs_repo.branches_all.items()
        data = self.load_refs_context(
            ref_items=ref_items, partials_template='branches/branches_data.mako')

        c.has_references = bool(data)
        c.data = json.dumps(data)
        return self._get_template_context(c)
