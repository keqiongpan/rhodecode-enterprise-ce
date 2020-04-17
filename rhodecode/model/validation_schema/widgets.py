# -*- coding: utf-8 -*-

# Copyright (C) 2011-2020 RhodeCode GmbH
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

import deform.widget
from deform.widget import null, OptGroup, string_types

log = logging.getLogger(__name__)


def _normalize_choices(values):
    result = []
    for item in values:
        if isinstance(item, OptGroup):
            normalized_options = _normalize_choices(item.options)
            result.append(OptGroup(item.label, *normalized_options))
        else:
            value, description, help_block = item
            if not isinstance(value, string_types):
                value = str(value)
            result.append((value, description, help_block))
    return result


class CodeMirrorWidget(deform.widget.TextAreaWidget):
    template = 'codemirror'
    requirements = (('deform', None), ('codemirror', None))


class CheckboxChoiceWidgetDesc(deform.widget.CheckboxChoiceWidget):
    template = "checkbox_choice_desc"

    def serialize(self, field, cstruct, **kw):
        if cstruct in (null, None):
            cstruct = ()
        readonly = kw.get("readonly", self.readonly)
        values = kw.get("values", self.values)
        kw["values"] = _normalize_choices(values)
        template = readonly and self.readonly_template or self.template
        tmpl_values = self.get_template_values(field, cstruct, kw)
        return field.renderer(template, **tmpl_values)
