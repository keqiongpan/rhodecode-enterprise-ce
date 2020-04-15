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
import itertools
import base64

from pyramid import compat

from rhodecode.api import (
    jsonrpc_method, JSONRPCError, JSONRPCForbidden, find_methods)

from rhodecode.api.utils import (
    Optional, OAttr, has_superadmin_permission, get_user_or_error)
from rhodecode.lib.utils import repo2db_mapper
from rhodecode.lib import system_info
from rhodecode.lib import user_sessions
from rhodecode.lib import exc_tracking
from rhodecode.lib.ext_json import json
from rhodecode.lib.utils2 import safe_int
from rhodecode.model.db import UserIpMap
from rhodecode.model.scm import ScmModel
from rhodecode.model.settings import VcsSettingsModel
from rhodecode.apps.file_store import utils
from rhodecode.apps.file_store.exceptions import FileNotAllowedException, \
    FileOverSizeException

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
def get_repo_store(request, apiuser):
    """
    Returns the |RCE| repository storage information.

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

    path = VcsSettingsModel().get_repos_location()
    return {"path": path}


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


@jsonrpc_method()
def get_method(request, apiuser, pattern=Optional('*')):
    """
    Returns list of all available API methods. By default match pattern
    os "*" but any other pattern can be specified. eg *comment* will return
    all methods with comment inside them. If just single method is matched
    returned data will also include method specification

    This command can only be run using an |authtoken| with admin rights to
    the specified repository.

    This command takes the following options:

    :param apiuser: This is filled automatically from the |authtoken|.
    :type apiuser: AuthUser
    :param pattern: pattern to match method names against
    :type pattern: Optional("*")

    Example output:

    .. code-block:: bash

      id : <id_given_in_input>
      "result": [
        "changeset_comment",
        "comment_pull_request",
        "comment_commit"
      ]
      error :  null

    .. code-block:: bash

      id : <id_given_in_input>
      "result": [
        "comment_commit",
        {
          "apiuser": "<RequiredType>",
          "comment_type": "<Optional:u'note'>",
          "commit_id": "<RequiredType>",
          "message": "<RequiredType>",
          "repoid": "<RequiredType>",
          "request": "<RequiredType>",
          "resolves_comment_id": "<Optional:None>",
          "status": "<Optional:None>",
          "userid": "<Optional:<OptionalAttr:apiuser>>"
        }
      ]
      error :  null
    """
    from rhodecode.config.patches import inspect_getargspec
    inspect = inspect_getargspec()

    if not has_superadmin_permission(apiuser):
        raise JSONRPCForbidden()

    pattern = Optional.extract(pattern)

    matches = find_methods(request.registry.jsonrpc_methods, pattern)

    args_desc = []
    if len(matches) == 1:
        func = matches[matches.keys()[0]]

        argspec = inspect.getargspec(func)
        arglist = argspec[0]
        defaults = map(repr, argspec[3] or [])

        default_empty = '<RequiredType>'

        # kw arguments required by this method
        func_kwargs = dict(itertools.izip_longest(
            reversed(arglist), reversed(defaults), fillvalue=default_empty))
        args_desc.append(func_kwargs)

    return matches.keys() + args_desc


@jsonrpc_method()
def store_exception(request, apiuser, exc_data_json, prefix=Optional('rhodecode')):
    """
    Stores sent exception inside the built-in exception tracker in |RCE| server.

    This command can only be run using an |authtoken| with admin rights to
    the specified repository.

    This command takes the following options:

    :param apiuser: This is filled automatically from the |authtoken|.
    :type apiuser: AuthUser

    :param exc_data_json: JSON data with exception e.g
        {"exc_traceback": "Value `1` is not allowed", "exc_type_name": "ValueError"}
    :type exc_data_json: JSON data

    :param prefix: prefix for error type, e.g 'rhodecode', 'vcsserver', 'rhodecode-tools'
    :type prefix: Optional("rhodecode")

    Example output:

    .. code-block:: bash

      id : <id_given_in_input>
      "result": {
        "exc_id": 139718459226384,
        "exc_url": "http://localhost:8080/_admin/settings/exceptions/139718459226384"
      }
      error :  null
    """
    if not has_superadmin_permission(apiuser):
        raise JSONRPCForbidden()

    prefix = Optional.extract(prefix)
    exc_id = exc_tracking.generate_id()

    try:
        exc_data = json.loads(exc_data_json)
    except Exception:
        log.error('Failed to parse JSON: %r', exc_data_json)
        raise JSONRPCError('Failed to parse JSON data from exc_data_json field. '
                           'Please make sure it contains a valid JSON.')

    try:
        exc_traceback = exc_data['exc_traceback']
        exc_type_name = exc_data['exc_type_name']
    except KeyError as err:
        raise JSONRPCError('Missing exc_traceback, or exc_type_name '
                           'in exc_data_json field. Missing: {}'.format(err))

    exc_tracking._store_exception(
        exc_id=exc_id, exc_traceback=exc_traceback,
        exc_type_name=exc_type_name, prefix=prefix)

    exc_url = request.route_url(
        'admin_settings_exception_tracker_show', exception_id=exc_id)
    return {'exc_id': exc_id, 'exc_url': exc_url}
