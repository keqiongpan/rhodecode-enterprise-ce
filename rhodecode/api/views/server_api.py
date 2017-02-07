# -*- coding: utf-8 -*-

# Copyright (C) 2011-2017 RhodeCode GmbH
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

from rhodecode.api import jsonrpc_method, JSONRPCError, JSONRPCForbidden

from rhodecode.api.utils import (
    Optional, OAttr, has_superadmin_permission, get_user_or_error)
from rhodecode.lib.utils import repo2db_mapper
from rhodecode.lib import system_info
from rhodecode.lib import user_sessions
from rhodecode.lib.utils2 import safe_int
from rhodecode.model.db import UserIpMap
from rhodecode.model.scm import ScmModel

log = logging.getLogger(__name__)


@jsonrpc_method()
def get_server_info(request, apiuser):
    """
    Returns the |RCE| server information.

    This includes the running version of |RCE| and all installed
    packages. This command takes the following options:

    :param apiuser: This is filled automatically from the |authtoken|.
    :type apiuser: AuthUser

    Example output:

    .. code-block:: bash

      id : <id_given_in_input>
      result : {
        'modules': [<module name>,...]
        'py_version': <python version>,
        'platform': <platform type>,
        'rhodecode_version': <rhodecode version>
      }
      error :  null
    """

    if not has_superadmin_permission(apiuser):
        raise JSONRPCForbidden()

    server_info = ScmModel().get_server_info(request.environ)
    # rhodecode-index requires those

    server_info['index_storage'] = server_info['search']['value']['location']
    server_info['storage'] = server_info['storage']['value']['path']

    return server_info


@jsonrpc_method()
def get_ip(request, apiuser, userid=Optional(OAttr('apiuser'))):
    """
    Displays the IP Address as seen from the |RCE| server.

    * This command displays the IP Address, as well as all the defined IP
      addresses for the specified user. If the ``userid`` is not set, the
      data returned is for the user calling the method.

    This command can only be run using an |authtoken| with admin rights to
    the specified repository.

    This command takes the following options:

    :param apiuser: This is filled automatically from |authtoken|.
    :type apiuser: AuthUser
    :param userid: Sets the userid for which associated IP Address data
        is returned.
    :type userid: Optional(str or int)

    Example output:

    .. code-block:: bash

        id : <id_given_in_input>
        result : {
                     "server_ip_addr": "<ip_from_clien>",
                     "user_ips": [
                                    {
                                       "ip_addr": "<ip_with_mask>",
                                       "ip_range": ["<start_ip>", "<end_ip>"],
                                    },
                                    ...
                                 ]
        }

    """
    if not has_superadmin_permission(apiuser):
        raise JSONRPCForbidden()

    userid = Optional.extract(userid, evaluate_locals=locals())
    userid = getattr(userid, 'user_id', userid)

    user = get_user_or_error(userid)
    ips = UserIpMap.query().filter(UserIpMap.user == user).all()
    return {
        'server_ip_addr': request.rpc_ip_addr,
        'user_ips': ips
    }


@jsonrpc_method()
def rescan_repos(request, apiuser, remove_obsolete=Optional(False)):
    """
    Triggers a rescan of the specified repositories.

    * If the ``remove_obsolete`` option is set, it also deletes repositories
      that are found in the database but not on the file system, so called
      "clean zombies".

    This command can only be run using an |authtoken| with admin rights to
    the specified repository.

    This command takes the following options:

    :param apiuser: This is filled automatically from the |authtoken|.
    :type apiuser: AuthUser
    :param remove_obsolete: Deletes repositories from the database that
        are not found on the filesystem.
    :type remove_obsolete: Optional(``True`` | ``False``)

    Example output:

    .. code-block:: bash

      id : <id_given_in_input>
      result : {
        'added': [<added repository name>,...]
        'removed': [<removed repository name>,...]
      }
      error :  null

    Example error output:

    .. code-block:: bash

      id : <id_given_in_input>
      result : null
      error :  {
        'Error occurred during rescan repositories action'
      }

    """
    if not has_superadmin_permission(apiuser):
        raise JSONRPCForbidden()

    try:
        rm_obsolete = Optional.extract(remove_obsolete)
        added, removed = repo2db_mapper(ScmModel().repo_scan(),
                                        remove_obsolete=rm_obsolete)
        return {'added': added, 'removed': removed}
    except Exception:
        log.exception('Failed to run repo rescann')
        raise JSONRPCError(
            'Error occurred during rescan repositories action'
        )


@jsonrpc_method()
def cleanup_sessions(request, apiuser, older_then=Optional(60)):
    """
    Triggers a session cleanup action.

    If the ``older_then`` option is set, only sessions that hasn't been
    accessed in the given number of days will be removed.

    This command can only be run using an |authtoken| with admin rights to
    the specified repository.

    This command takes the following options:

    :param apiuser: This is filled automatically from the |authtoken|.
    :type apiuser: AuthUser
    :param older_then: Deletes session that hasn't been accessed
        in given number of days.
    :type older_then: Optional(int)

    Example output:

    .. code-block:: bash

      id : <id_given_in_input>
      result: {
        "backend": "<type of backend>",
        "sessions_removed": <number_of_removed_sessions>
      }
      error :  null

    Example error output:

    .. code-block:: bash

      id : <id_given_in_input>
      result : null
      error :  {
        'Error occurred during session cleanup'
      }

    """
    if not has_superadmin_permission(apiuser):
        raise JSONRPCForbidden()

    older_then = safe_int(Optional.extract(older_then)) or 60
    older_than_seconds = 60 * 60 * 24 * older_then

    config = system_info.rhodecode_config().get_value()['value']['config']
    session_model = user_sessions.get_session_handler(
        config.get('beaker.session.type', 'memory'))(config)

    backend = session_model.SESSION_TYPE
    try:
        cleaned = session_model.clean_sessions(
            older_than_seconds=older_than_seconds)
        return {'sessions_removed': cleaned, 'backend': backend}
    except user_sessions.CleanupCommand as msg:
        return {'cleanup_command': msg.message, 'backend': backend}
    except Exception as e:
        log.exception('Failed session cleanup')
        raise JSONRPCError(
            'Error occurred during session cleanup'
        )
