# -*- coding: utf-8 -*-

# Copyright (C) 2016-2017  RhodeCode GmbH
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
import urllib2
import packaging.version

from pylons import tmpl_context as c
from pyramid.view import view_config

import rhodecode
from rhodecode.lib import helpers as h
from rhodecode.lib.auth import (LoginRequired, HasPermissionAllDecorator)
from rhodecode.lib.utils2 import str2bool
from rhodecode.lib import system_info
from rhodecode.lib.ext_json import json

from rhodecode.admin.views.base import AdminSettingsView
from rhodecode.admin.navigation import navigation_list
from rhodecode.model.settings import SettingsModel

log = logging.getLogger(__name__)


class AdminSystemInfoSettingsView(AdminSettingsView):

    @staticmethod
    def get_update_data(update_url):
        """Return the JSON update data."""
        ver = rhodecode.__version__
        log.debug('Checking for upgrade on `%s` server', update_url)
        opener = urllib2.build_opener()
        opener.addheaders = [('User-agent', 'RhodeCode-SCM/%s' % ver)]
        response = opener.open(update_url)
        response_data = response.read()
        data = json.loads(response_data)

        return data

    def get_update_url(self):
        settings = SettingsModel().get_all_settings()
        return settings.get('rhodecode_update_url')

    @LoginRequired()
    @HasPermissionAllDecorator('hg.admin')
    @view_config(
        route_name='admin_settings_system', request_method='GET',
        renderer='rhodecode:templates/admin/settings/settings.mako')
    def settings_system_info(self):
        _ = self.request.translate

        c.active = 'system'
        c.navlist = navigation_list(self.request)

        # TODO(marcink), figure out how to allow only selected users to do this
        c.allowed_to_snapshot = self._rhodecode_user.admin

        snapshot = str2bool(self.request.params.get('snapshot'))

        c.rhodecode_update_url = self.get_update_url()
        server_info = system_info.get_system_info(self.request.environ)

        for key, val in server_info.items():
            setattr(c, key, val)

        def val(name, subkey='human_value'):
            return server_info[name][subkey]

        def state(name):
            return server_info[name]['state']

        def val2(name):
            val = server_info[name]['human_value']
            state = server_info[name]['state']
            return val, state

        update_info_msg = _('Note: please make sure this server can '
                            'access `${url}` for the update link to work',
                            mapping=dict(url=c.rhodecode_update_url))
        c.data_items = [
            # update info
            (_('Update info'), h.literal(
                '<span class="link" id="check_for_update" >%s.</span>' % (
                _('Check for updates')) +
                '<br/> <span >%s.</span>' % (update_info_msg)
            ), ''),

            # RhodeCode specific
            (_('RhodeCode Version'), val('rhodecode_app')['text'], state('rhodecode_app')),
            (_('RhodeCode Server IP'), val('server')['server_ip'], state('server')),
            (_('RhodeCode Server ID'), val('server')['server_id'], state('server')),
            (_('RhodeCode Configuration'), val('rhodecode_config')['path'], state('rhodecode_config')),
            (_('Workers'), val('rhodecode_config')['config']['server:main'].get('workers', '?'), state('rhodecode_config')),
            (_('Worker Type'), val('rhodecode_config')['config']['server:main'].get('worker_class', 'sync'), state('rhodecode_config')),
            ('', '', ''),  # spacer

            # Database
            (_('Database'), val('database')['url'], state('database')),
            (_('Database version'), val('database')['version'], state('database')),
            ('', '', ''),  # spacer

            # Platform/Python
            (_('Platform'), val('platform')['name'], state('platform')),
            (_('Platform UUID'), val('platform')['uuid'], state('platform')),
            (_('Python version'), val('python')['version'], state('python')),
            (_('Python path'), val('python')['executable'], state('python')),
            ('', '', ''),  # spacer

            # Systems stats
            (_('CPU'), val('cpu')['text'], state('cpu')),
            (_('Load'), val('load')['text'], state('load')),
            (_('Memory'), val('memory')['text'], state('memory')),
            (_('Uptime'), val('uptime')['text'], state('uptime')),
            ('', '', ''),  # spacer

            # Repo storage
            (_('Storage location'), val('storage')['path'], state('storage')),
            (_('Storage info'), val('storage')['text'], state('storage')),
            (_('Storage inodes'), val('storage_inodes')['text'], state('storage_inodes')),

            (_('Gist storage location'), val('storage_gist')['path'], state('storage_gist')),
            (_('Gist storage info'), val('storage_gist')['text'], state('storage_gist')),

            (_('Archive cache storage location'), val('storage_archive')['path'], state('storage_archive')),
            (_('Archive cache info'), val('storage_archive')['text'], state('storage_archive')),

            (_('Temp storage location'), val('storage_temp')['path'], state('storage_temp')),
            (_('Temp storage info'), val('storage_temp')['text'], state('storage_temp')),

            (_('Search info'), val('search')['text'], state('search')),
            (_('Search location'), val('search')['location'], state('search')),
            ('', '', ''),  # spacer

            # VCS specific
            (_('VCS Backends'), val('vcs_backends'), state('vcs_backends')),
            (_('VCS Server'), val('vcs_server')['text'], state('vcs_server')),
            (_('GIT'), val('git'), state('git')),
            (_('HG'), val('hg'), state('hg')),
            (_('SVN'), val('svn'), state('svn')),

        ]

        if snapshot:
            if c.allowed_to_snapshot:
                c.data_items.pop(0)  # remove server info
                self.request.override_renderer = 'admin/settings/settings_system_snapshot.mako'
            else:
                self.request.session.flash(
                    'You are not allowed to do this', queue='warning')
        return {}

    @LoginRequired()
    @HasPermissionAllDecorator('hg.admin')
    @view_config(
        route_name='admin_settings_system_update', request_method='GET',
        renderer='rhodecode:templates/admin/settings/settings_system_update.mako')
    def settings_system_info_check_update(self):
        _ = self.request.translate

        update_url = self.get_update_url()

        _err = lambda s: '<div style="color:#ff8888; padding:4px 0px">{}</div>'.format(s)
        try:
            data = self.get_update_data(update_url)
        except urllib2.URLError as e:
            log.exception("Exception contacting upgrade server")
            self.request.override_renderer = 'string'
            return _err('Failed to contact upgrade server: %r' % e)
        except ValueError as e:
            log.exception("Bad data sent from update server")
            self.request.override_renderer = 'string'
            return _err('Bad data sent from update server')

        latest = data['versions'][0]

        c.update_url = update_url
        c.latest_data = latest
        c.latest_ver = latest['version']
        c.cur_ver = rhodecode.__version__
        c.should_upgrade = False

        if (packaging.version.Version(c.latest_ver) >
                packaging.version.Version(c.cur_ver)):
            c.should_upgrade = True
        c.important_notices = latest['general']

        return {}
