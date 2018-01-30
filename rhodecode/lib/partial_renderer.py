# -*- coding: utf-8 -*-

# Copyright (C) 2010-2018 RhodeCode GmbH
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
from mako import exceptions
from pyramid.renderers import get_renderer

log = logging.getLogger(__name__)


def get_partial_renderer(request, tmpl_name):
    return PyramidPartialRenderer(request, tmpl_name=tmpl_name)


class PyramidPartialRenderer(object):

    """
    Partial renderer used to render chunks of html used in datagrids
    use like::

        _renderer = request.get_partial_renderer(
            'rhodecode:templates/_dt/template_base.mako')
        _render('quick_menu', args, kwargs)

    :param tmpl_name: template path relate to /templates/ dir
    """

    def __init__(self, request, tmpl_name):
        self.tmpl_name = tmpl_name
        self.request = request

    def _mako_lookup(self):
        _tmpl_lookup = get_renderer('root.mako').lookup
        return _tmpl_lookup.get_template(self.tmpl_name)

    def get_call_context(self):
        return self.request.call_context

    def get_helpers(self):
        from rhodecode.lib import helpers
        return helpers

    def _update_kwargs_for_render(self, kwargs):
        """
        Inject params required for Mako rendering
        """

        _kwargs = {
            '_': self.request.translate,
            '_ungettext': self.request.plularize,
            'h': self.get_helpers(),
            'c': self.get_call_context(),

            'request': self.request,
        }
        _kwargs.update(kwargs)
        return _kwargs

    def _render_with_exc(self, render_func, args, kwargs):
        try:
            return render_func.render(*args, **kwargs)
        except:
            log.error(exceptions.text_error_template().render())
            raise

    def _get_template(self, template_obj, def_name):
        if def_name:
            tmpl = template_obj.get_def(def_name)
        else:
            tmpl = template_obj
        return tmpl

    def render(self, def_name, *args, **kwargs):
        lookup_obj = self._mako_lookup()
        tmpl = self._get_template(lookup_obj, def_name=def_name)
        kwargs = self._update_kwargs_for_render(kwargs)
        return self._render_with_exc(tmpl, args, kwargs)

    def __call__(self, tmpl, *args, **kwargs):
        return self.render(tmpl, *args, **kwargs)
