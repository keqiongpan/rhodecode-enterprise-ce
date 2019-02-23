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

"""
Base module for form rendering / validation - currently just a wrapper for
deform - later can be replaced with something custom.
"""

from rhodecode.translation import _
from rhodecode.translation import TranslationString

from mako.template import Template
from deform import Button, Form, widget, ValidationFailure


class buttons:
    save = Button(name='Save', type='submit')
    reset = Button(name=_('Reset'), type='reset')
    delete = Button(name=_('Delete'), type='submit')


class RcForm(Form):
    def render_error(self, request, field):
        html = ''
        if field.error:
            for err in field.error.messages():
                if isinstance(err, TranslationString):
                    err = request.translate(err)
                html = Template(
                    '<span class="error-message">${err}</span>').render(err=err)

        return html
