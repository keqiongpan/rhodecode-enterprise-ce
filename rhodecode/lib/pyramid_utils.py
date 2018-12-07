# -*- coding: utf-8 -*-

# Copyright (C) 2016-2018 RhodeCode GmbH
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
from pyramid.compat import configparser
from pyramid.paster import bootstrap as pyramid_bootstrap, setup_logging  # pragma: no cover
from pyramid.scripting import prepare

from rhodecode.lib.request import Request


def get_config(ini_path, **kwargs):
    parser = configparser.ConfigParser(**kwargs)
    parser.read(ini_path)
    return parser


def get_app_config(ini_path):
    from paste.deploy.loadwsgi import appconfig
    return appconfig('config:{}'.format(ini_path), relative_to=os.getcwd())


class BootstrappedRequest(Request):
    """
    Special version of Request Which has some available methods like in pyramid.
    Some code (used for template rendering) requires this, and we unsure it's present.
    """

    def translate(self, msg):
        return msg

    def plularize(self, singular, plural, n):
        return singular

    def get_partial_renderer(self, tmpl_name):
        from rhodecode.lib.partial_renderer import get_partial_renderer
        return get_partial_renderer(request=self, tmpl_name=tmpl_name)


def bootstrap(config_uri, request=None, options=None, env=None):
    if env:
        os.environ.update(env)

    config = get_config(config_uri)
    base_url = 'http://rhodecode.local'
    try:
        base_url = config.get('app:main', 'app.base_url')
    except (configparser.NoSectionError, configparser.NoOptionError):
        pass

    request = request or BootstrappedRequest.blank('/', base_url=base_url)

    return pyramid_bootstrap(config_uri, request=request, options=options)


def prepare_request(environ):
    request = Request.blank('/', environ=environ)
    prepare(request)  # set pyramid threadlocal request
    return request
