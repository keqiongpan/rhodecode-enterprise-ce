# -*- coding: utf-8 -*-

# Copyright (C) 2012-2018 RhodeCode GmbH
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

import colander

from rhodecode.translation import _


class IntegrationOptionsSchemaBase(colander.MappingSchema):
    enabled = colander.SchemaNode(
        colander.Bool(),
        default=True,
        description=_('Enable or disable this integration.'),
        missing=False,
        title=_('Enabled'),
    )

    name = colander.SchemaNode(
        colander.String(),
        description=_('Short name for this integration.'),
        missing=colander.required,
        title=_('Integration name'),
    )


class RepoIntegrationOptionsSchema(IntegrationOptionsSchemaBase):
    pass


class RepoGroupIntegrationOptionsSchema(IntegrationOptionsSchemaBase):
    child_repos_only = colander.SchemaNode(
        colander.Bool(),
        default=True,
        description=_(
            'Limit integrations to to work only on the direct children '
            'repositories of this repository group (no subgroups)'),
        missing=False,
        title=_('Limit to childen repos only'),
    )


class GlobalIntegrationOptionsSchema(IntegrationOptionsSchemaBase):
    child_repos_only = colander.SchemaNode(
        colander.Bool(),
        default=False,
        description=_(
            'Limit integrations to to work only on root level repositories'),
        missing=False,
        title=_('Root repositories only'),
    )


class IntegrationSettingsSchemaBase(colander.MappingSchema):
    pass
