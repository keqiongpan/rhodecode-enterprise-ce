# -*- coding: utf-8 -*-

# Copyright (C) 2010-2017 RhodeCode GmbH
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
Routes configuration

The more specific and detailed routes should be defined first so they
may take precedent over the more generic routes. For more information
refer to the routes manual at http://routes.groovie.org/docs/

IMPORTANT: if you change any routing here, make sure to take a look at lib/base.py
and _route_name variable which uses some of stored naming here to do redirects.
"""
import os
import re
from routes import Mapper

# prefix for non repository related links needs to be prefixed with `/`
ADMIN_PREFIX = '/_admin'
STATIC_FILE_PREFIX = '/_static'

# Default requirements for URL parts
URL_NAME_REQUIREMENTS = {
    # group name can have a slash in them, but they must not end with a slash
    'group_name': r'.*?[^/]',
    'repo_group_name': r'.*?[^/]',
    # repo names can have a slash in them, but they must not end with a slash
    'repo_name': r'.*?[^/]',
    # file path eats up everything at the end
    'f_path': r'.*',
    # reference types
    'source_ref_type': '(branch|book|tag|rev|\%\(source_ref_type\)s)',
    'target_ref_type': '(branch|book|tag|rev|\%\(target_ref_type\)s)',
}


class JSRoutesMapper(Mapper):
    """
    Wrapper for routes.Mapper to make pyroutes compatible url definitions
    """
    _named_route_regex = re.compile(r'^[a-z-_0-9A-Z]+$')
    _argument_prog = re.compile('\{(.*?)\}|:\((.*)\)')
    def __init__(self, *args, **kw):
        super(JSRoutesMapper, self).__init__(*args, **kw)
        self._jsroutes = []

    def connect(self, *args, **kw):
        """
        Wrapper for connect to take an extra argument jsroute=True

        :param jsroute: boolean, if True will add the route to the pyroutes list
        """
        if kw.pop('jsroute', False):
            if not self._named_route_regex.match(args[0]):
                raise Exception('only named routes can be added to pyroutes')
            self._jsroutes.append(args[0])

        super(JSRoutesMapper, self).connect(*args, **kw)

    def _extract_route_information(self, route):
        """
        Convert a route into tuple(name, path, args), eg:
            ('show_user', '/profile/%(username)s', ['username'])
        """
        routepath = route.routepath
        def replace(matchobj):
            if matchobj.group(1):
                return "%%(%s)s" % matchobj.group(1).split(':')[0]
            else:
                return "%%(%s)s" % matchobj.group(2)

        routepath = self._argument_prog.sub(replace, routepath)
        return (
            route.name,
            routepath,
            [(arg[0].split(':')[0] if arg[0] != '' else arg[1])
              for arg in self._argument_prog.findall(route.routepath)]
        )

    def jsroutes(self):
        """
        Return a list of pyroutes.js compatible routes
        """
        for route_name in self._jsroutes:
            yield self._extract_route_information(self._routenames[route_name])


def make_map(config):
    """Create, configure and return the routes Mapper"""
    rmap = JSRoutesMapper(
        directory=config['pylons.paths']['controllers'],
        always_scan=config['debug'])
    rmap.minimization = False
    rmap.explicit = False

    from rhodecode.lib.utils2 import str2bool
    from rhodecode.model import repo, repo_group

    def check_repo(environ, match_dict):
        """
        check for valid repository for proper 404 handling

        :param environ:
        :param match_dict:
        """
        repo_name = match_dict.get('repo_name')

        if match_dict.get('f_path'):
            # fix for multiple initial slashes that causes errors
            match_dict['f_path'] = match_dict['f_path'].lstrip('/')
        repo_model = repo.RepoModel()
        by_name_match = repo_model.get_by_repo_name(repo_name)
        # if we match quickly from database, short circuit the operation,
        # and validate repo based on the type.
        if by_name_match:
            return True

        by_id_match = repo_model.get_repo_by_id(repo_name)
        if by_id_match:
            repo_name = by_id_match.repo_name
            match_dict['repo_name'] = repo_name
            return True

        return False

    def check_group(environ, match_dict):
        """
        check for valid repository group path for proper 404 handling

        :param environ:
        :param match_dict:
        """
        repo_group_name = match_dict.get('group_name')
        repo_group_model = repo_group.RepoGroupModel()
        by_name_match = repo_group_model.get_by_group_name(repo_group_name)
        if by_name_match:
            return True

        return False

    def check_user_group(environ, match_dict):
        """
        check for valid user group for proper 404 handling

        :param environ:
        :param match_dict:
        """
        return True

    def check_int(environ, match_dict):
        return match_dict.get('id').isdigit()


    #==========================================================================
    # CUSTOM ROUTES HERE
    #==========================================================================

    # ADMIN SETTINGS ROUTES
    with rmap.submapper(path_prefix=ADMIN_PREFIX,
                        controller='admin/settings') as m:

        # default
        m.connect('admin_settings', '/settings',
                  action='settings_global_update',
                  conditions={'method': ['POST']})
        m.connect('admin_settings', '/settings',
                  action='settings_global', conditions={'method': ['GET']})

        m.connect('admin_settings_vcs', '/settings/vcs',
                  action='settings_vcs_update',
                  conditions={'method': ['POST']})
        m.connect('admin_settings_vcs', '/settings/vcs',
                  action='settings_vcs',
                  conditions={'method': ['GET']})
        m.connect('admin_settings_vcs', '/settings/vcs',
                  action='delete_svn_pattern',
                  conditions={'method': ['DELETE']})

        m.connect('admin_settings_mapping', '/settings/mapping',
                  action='settings_mapping_update',
                  conditions={'method': ['POST']})
        m.connect('admin_settings_mapping', '/settings/mapping',
                  action='settings_mapping', conditions={'method': ['GET']})

        m.connect('admin_settings_global', '/settings/global',
                  action='settings_global_update',
                  conditions={'method': ['POST']})
        m.connect('admin_settings_global', '/settings/global',
                  action='settings_global', conditions={'method': ['GET']})

        m.connect('admin_settings_visual', '/settings/visual',
                  action='settings_visual_update',
                  conditions={'method': ['POST']})
        m.connect('admin_settings_visual', '/settings/visual',
                  action='settings_visual', conditions={'method': ['GET']})

        m.connect('admin_settings_issuetracker',
                  '/settings/issue-tracker', action='settings_issuetracker',
                  conditions={'method': ['GET']})
        m.connect('admin_settings_issuetracker_save',
                  '/settings/issue-tracker/save',
                  action='settings_issuetracker_save',
                  conditions={'method': ['POST']})
        m.connect('admin_issuetracker_test', '/settings/issue-tracker/test',
                  action='settings_issuetracker_test',
                  conditions={'method': ['POST']})
        m.connect('admin_issuetracker_delete',
                  '/settings/issue-tracker/delete',
                  action='settings_issuetracker_delete',
                  conditions={'method': ['DELETE']})

        m.connect('admin_settings_email', '/settings/email',
                  action='settings_email_update',
                  conditions={'method': ['POST']})
        m.connect('admin_settings_email', '/settings/email',
                  action='settings_email', conditions={'method': ['GET']})

        m.connect('admin_settings_hooks', '/settings/hooks',
                  action='settings_hooks_update',
                  conditions={'method': ['POST', 'DELETE']})
        m.connect('admin_settings_hooks', '/settings/hooks',
                  action='settings_hooks', conditions={'method': ['GET']})

        m.connect('admin_settings_search', '/settings/search',
                  action='settings_search', conditions={'method': ['GET']})

        m.connect('admin_settings_labs', '/settings/labs',
                  action='settings_labs_update',
                  conditions={'method': ['POST']})
        m.connect('admin_settings_labs', '/settings/labs',
                  action='settings_labs', conditions={'method': ['GET']})

    # ADMIN MY ACCOUNT
    with rmap.submapper(path_prefix=ADMIN_PREFIX,
                        controller='admin/my_account') as m:

        # NOTE(marcink): this needs to be kept for password force flag to be
        # handled in pylons controllers, remove after full migration to pyramid
        m.connect('my_account_password', '/my_account/password',
                  action='my_account_password', conditions={'method': ['GET']})

    return rmap
