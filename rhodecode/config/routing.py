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

    # ping and pylons error test
    rmap.connect('ping', '%s/ping' % (ADMIN_PREFIX,), controller='home', action='ping')
    rmap.connect('error_test', '%s/error_test' % (ADMIN_PREFIX,), controller='home', action='error_test')

    # ADMIN REPOSITORY ROUTES
    with rmap.submapper(path_prefix=ADMIN_PREFIX,
                        controller='admin/repos') as m:
        m.connect('repos', '/repos',
                  action='create', conditions={'method': ['POST']})
        m.connect('repos', '/repos',
                  action='index', conditions={'method': ['GET']})
        m.connect('new_repo', '/create_repository', jsroute=True,
                  action='create_repository', conditions={'method': ['GET']})
        m.connect('delete_repo', '/repos/{repo_name}',
                  action='delete', conditions={'method': ['DELETE']},
                  requirements=URL_NAME_REQUIREMENTS)
        m.connect('repo', '/repos/{repo_name}',
                  action='show', conditions={'method': ['GET'],
                                             'function': check_repo},
                  requirements=URL_NAME_REQUIREMENTS)

    # ADMIN REPOSITORY GROUPS ROUTES
    with rmap.submapper(path_prefix=ADMIN_PREFIX,
                        controller='admin/repo_groups') as m:
        m.connect('repo_groups', '/repo_groups',
                  action='create', conditions={'method': ['POST']})
        m.connect('repo_groups', '/repo_groups',
                  action='index', conditions={'method': ['GET']})
        m.connect('new_repo_group', '/repo_groups/new',
                  action='new', conditions={'method': ['GET']})
        m.connect('update_repo_group', '/repo_groups/{group_name}',
                  action='update', conditions={'method': ['PUT'],
                                               'function': check_group},
                  requirements=URL_NAME_REQUIREMENTS)

        # EXTRAS REPO GROUP ROUTES
        m.connect('edit_repo_group', '/repo_groups/{group_name}/edit',
                  action='edit',
                  conditions={'method': ['GET'], 'function': check_group},
                  requirements=URL_NAME_REQUIREMENTS)
        m.connect('edit_repo_group', '/repo_groups/{group_name}/edit',
                  action='edit',
                  conditions={'method': ['PUT'], 'function': check_group},
                  requirements=URL_NAME_REQUIREMENTS)

        m.connect('edit_repo_group_advanced', '/repo_groups/{group_name}/edit/advanced',
                  action='edit_repo_group_advanced',
                  conditions={'method': ['GET'], 'function': check_group},
                  requirements=URL_NAME_REQUIREMENTS)
        m.connect('edit_repo_group_advanced', '/repo_groups/{group_name}/edit/advanced',
                  action='edit_repo_group_advanced',
                  conditions={'method': ['PUT'], 'function': check_group},
                  requirements=URL_NAME_REQUIREMENTS)

        m.connect('edit_repo_group_perms', '/repo_groups/{group_name}/edit/permissions',
                  action='edit_repo_group_perms',
                  conditions={'method': ['GET'], 'function': check_group},
                  requirements=URL_NAME_REQUIREMENTS)
        m.connect('edit_repo_group_perms', '/repo_groups/{group_name}/edit/permissions',
                  action='update_perms',
                  conditions={'method': ['PUT'], 'function': check_group},
                  requirements=URL_NAME_REQUIREMENTS)

        m.connect('delete_repo_group', '/repo_groups/{group_name}',
                  action='delete', conditions={'method': ['DELETE'],
                                               'function': check_group},
                  requirements=URL_NAME_REQUIREMENTS)

    # ADMIN USER ROUTES
    with rmap.submapper(path_prefix=ADMIN_PREFIX,
                        controller='admin/users') as m:
        m.connect('users', '/users',
                  action='create', conditions={'method': ['POST']})
        m.connect('new_user', '/users/new',
                  action='new', conditions={'method': ['GET']})
        m.connect('update_user', '/users/{user_id}',
                  action='update', conditions={'method': ['PUT']})
        m.connect('delete_user', '/users/{user_id}',
                  action='delete', conditions={'method': ['DELETE']})
        m.connect('edit_user', '/users/{user_id}/edit',
                  action='edit', conditions={'method': ['GET']}, jsroute=True)
        m.connect('user', '/users/{user_id}',
                  action='show', conditions={'method': ['GET']})
        m.connect('force_password_reset_user', '/users/{user_id}/password_reset',
                  action='reset_password', conditions={'method': ['POST']})
        m.connect('create_personal_repo_group', '/users/{user_id}/create_repo_group',
                  action='create_personal_repo_group', conditions={'method': ['POST']})

        # EXTRAS USER ROUTES
        m.connect('edit_user_advanced', '/users/{user_id}/edit/advanced',
                  action='edit_advanced', conditions={'method': ['GET']})
        m.connect('edit_user_advanced', '/users/{user_id}/edit/advanced',
                  action='update_advanced', conditions={'method': ['PUT']})

        m.connect('edit_user_global_perms', '/users/{user_id}/edit/global_permissions',
                  action='edit_global_perms', conditions={'method': ['GET']})
        m.connect('edit_user_global_perms', '/users/{user_id}/edit/global_permissions',
                  action='update_global_perms', conditions={'method': ['PUT']})

        m.connect('edit_user_perms_summary', '/users/{user_id}/edit/permissions_summary',
                  action='edit_perms_summary', conditions={'method': ['GET']})

    # ADMIN USER GROUPS REST ROUTES
    with rmap.submapper(path_prefix=ADMIN_PREFIX,
                        controller='admin/user_groups') as m:
        m.connect('users_groups', '/user_groups',
                  action='create', conditions={'method': ['POST']})
        m.connect('new_users_group', '/user_groups/new',
                  action='new', conditions={'method': ['GET']})
        m.connect('update_users_group', '/user_groups/{user_group_id}',
                  action='update', conditions={'method': ['PUT']})
        m.connect('delete_users_group', '/user_groups/{user_group_id}',
                  action='delete', conditions={'method': ['DELETE']})
        m.connect('edit_users_group', '/user_groups/{user_group_id}/edit',
                  action='edit', conditions={'method': ['GET']},
                  function=check_user_group)

        # EXTRAS USER GROUP ROUTES
        m.connect('edit_user_group_global_perms',
                  '/user_groups/{user_group_id}/edit/global_permissions',
                  action='edit_global_perms', conditions={'method': ['GET']})
        m.connect('edit_user_group_global_perms',
                  '/user_groups/{user_group_id}/edit/global_permissions',
                  action='update_global_perms', conditions={'method': ['PUT']})
        m.connect('edit_user_group_perms_summary',
                  '/user_groups/{user_group_id}/edit/permissions_summary',
                  action='edit_perms_summary', conditions={'method': ['GET']})

        m.connect('edit_user_group_perms',
                  '/user_groups/{user_group_id}/edit/permissions',
                  action='edit_perms', conditions={'method': ['GET']})
        m.connect('edit_user_group_perms',
                  '/user_groups/{user_group_id}/edit/permissions',
                  action='update_perms', conditions={'method': ['PUT']})

        m.connect('edit_user_group_advanced',
                  '/user_groups/{user_group_id}/edit/advanced',
                  action='edit_advanced', conditions={'method': ['GET']})

        m.connect('edit_user_group_advanced_sync',
                  '/user_groups/{user_group_id}/edit/advanced/sync',
                  action='edit_advanced_set_synchronization', conditions={'method': ['POST']})

    # ADMIN DEFAULTS REST ROUTES
    with rmap.submapper(path_prefix=ADMIN_PREFIX,
                        controller='admin/defaults') as m:
        m.connect('admin_defaults_repositories', '/defaults/repositories',
                  action='update_repository_defaults', conditions={'method': ['POST']})
        m.connect('admin_defaults_repositories', '/defaults/repositories',
                  action='index', conditions={'method': ['GET']})

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

        m.connect('admin_settings_supervisor', '/settings/supervisor',
                  action='settings_supervisor', conditions={'method': ['GET']})
        m.connect('admin_settings_supervisor_log', '/settings/supervisor/{procid}/log',
                  action='settings_supervisor_log', conditions={'method': ['GET']})

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

    #==========================================================================
    # REPOSITORY ROUTES
    #==========================================================================

    rmap.connect('repo_creating_home', '/{repo_name}/repo_creating',
                 controller='admin/repos', action='repo_creating',
                 requirements=URL_NAME_REQUIREMENTS)
    rmap.connect('repo_check_home', '/{repo_name}/crepo_check',
                 controller='admin/repos', action='repo_check',
                 requirements=URL_NAME_REQUIREMENTS)

    # repo edit options
    rmap.connect('edit_repo_fields', '/{repo_name}/settings/fields',
                 controller='admin/repos', action='edit_fields',
                 conditions={'method': ['GET'], 'function': check_repo},
                 requirements=URL_NAME_REQUIREMENTS)
    rmap.connect('create_repo_fields', '/{repo_name}/settings/fields/new',
                 controller='admin/repos', action='create_repo_field',
                 conditions={'method': ['PUT'], 'function': check_repo},
                 requirements=URL_NAME_REQUIREMENTS)
    rmap.connect('delete_repo_fields', '/{repo_name}/settings/fields/{field_id}',
                 controller='admin/repos', action='delete_repo_field',
                 conditions={'method': ['DELETE'], 'function': check_repo},
                 requirements=URL_NAME_REQUIREMENTS)

    rmap.connect('toggle_locking', '/{repo_name}/settings/advanced/locking_toggle',
                 controller='admin/repos', action='toggle_locking',
                 conditions={'method': ['GET'], 'function': check_repo},
                 requirements=URL_NAME_REQUIREMENTS)

    rmap.connect('edit_repo_remote', '/{repo_name}/settings/remote',
                 controller='admin/repos', action='edit_remote_form',
                 conditions={'method': ['GET'], 'function': check_repo},
                 requirements=URL_NAME_REQUIREMENTS)
    rmap.connect('edit_repo_remote', '/{repo_name}/settings/remote',
                 controller='admin/repos', action='edit_remote',
                 conditions={'method': ['PUT'], 'function': check_repo},
                 requirements=URL_NAME_REQUIREMENTS)

    rmap.connect('edit_repo_statistics', '/{repo_name}/settings/statistics',
                 controller='admin/repos', action='edit_statistics_form',
                 conditions={'method': ['GET'], 'function': check_repo},
                 requirements=URL_NAME_REQUIREMENTS)
    rmap.connect('edit_repo_statistics', '/{repo_name}/settings/statistics',
                 controller='admin/repos', action='edit_statistics',
                 conditions={'method': ['PUT'], 'function': check_repo},
                 requirements=URL_NAME_REQUIREMENTS)
    rmap.connect('repo_settings_issuetracker',
                 '/{repo_name}/settings/issue-tracker',
                 controller='admin/repos', action='repo_issuetracker',
                 conditions={'method': ['GET'], 'function': check_repo},
                 requirements=URL_NAME_REQUIREMENTS)
    rmap.connect('repo_issuetracker_test',
                 '/{repo_name}/settings/issue-tracker/test',
                 controller='admin/repos', action='repo_issuetracker_test',
                 conditions={'method': ['POST'], 'function': check_repo},
                 requirements=URL_NAME_REQUIREMENTS)
    rmap.connect('repo_issuetracker_delete',
                 '/{repo_name}/settings/issue-tracker/delete',
                 controller='admin/repos', action='repo_issuetracker_delete',
                 conditions={'method': ['DELETE'], 'function': check_repo},
                 requirements=URL_NAME_REQUIREMENTS)
    rmap.connect('repo_issuetracker_save',
                 '/{repo_name}/settings/issue-tracker/save',
                 controller='admin/repos', action='repo_issuetracker_save',
                 conditions={'method': ['POST'], 'function': check_repo},
                 requirements=URL_NAME_REQUIREMENTS)
    rmap.connect('repo_vcs_settings', '/{repo_name}/settings/vcs',
                 controller='admin/repos', action='repo_settings_vcs_update',
                 conditions={'method': ['POST'], 'function': check_repo},
                 requirements=URL_NAME_REQUIREMENTS)
    rmap.connect('repo_vcs_settings', '/{repo_name}/settings/vcs',
                 controller='admin/repos', action='repo_settings_vcs',
                 conditions={'method': ['GET'], 'function': check_repo},
                 requirements=URL_NAME_REQUIREMENTS)
    rmap.connect('repo_vcs_settings', '/{repo_name}/settings/vcs',
                 controller='admin/repos', action='repo_delete_svn_pattern',
                 conditions={'method': ['DELETE'], 'function': check_repo},
                 requirements=URL_NAME_REQUIREMENTS)
    rmap.connect('repo_pullrequest_settings', '/{repo_name}/settings/pullrequest',
                 controller='admin/repos', action='repo_settings_pullrequest',
                 conditions={'method': ['GET', 'POST'], 'function': check_repo},
                 requirements=URL_NAME_REQUIREMENTS)


    rmap.connect('repo_fork_create_home', '/{repo_name}/fork',
                 controller='forks', action='fork_create',
                 conditions={'function': check_repo, 'method': ['POST']},
                 requirements=URL_NAME_REQUIREMENTS)

    rmap.connect('repo_fork_home', '/{repo_name}/fork',
                 controller='forks', action='fork',
                 conditions={'function': check_repo},
                 requirements=URL_NAME_REQUIREMENTS)

    rmap.connect('repo_forks_home', '/{repo_name}/forks',
                 controller='forks', action='forks',
                 conditions={'function': check_repo},
                 requirements=URL_NAME_REQUIREMENTS)

    return rmap
