# -*- coding: utf-8 -*-

# Copyright (C) 2010-2020 RhodeCode GmbH
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
SimpleGit middleware for handling git protocol request (push/clone etc.)
It's implemented with basic auth function
"""
import os
import re
import logging
import urlparse

import rhodecode
from rhodecode.lib import utils
from rhodecode.lib import utils2
from rhodecode.lib.middleware import simplevcs

log = logging.getLogger(__name__)


GIT_PROTO_PAT = re.compile(
    r'^/(.+)/(info/refs|info/lfs/(.+)|git-upload-pack|git-receive-pack)')
GIT_LFS_PROTO_PAT = re.compile(r'^/(.+)/(info/lfs/(.+))')


def default_lfs_store():
    """
    Default lfs store location, it's consistent with Mercurials large file
    store which is in .cache/largefiles
    """
    from rhodecode.lib.vcs.backends.git import lfs_store
    user_home = os.path.expanduser("~")
    return lfs_store(user_home)


class SimpleGit(simplevcs.SimpleVCS):

    SCM = 'git'

    def _get_repository_name(self, environ):
        """
        Gets repository name out of PATH_INFO header

        :param environ: environ where PATH_INFO is stored
        """
        repo_name = GIT_PROTO_PAT.match(environ['PATH_INFO']).group(1)
        # for GIT LFS, and bare format strip .git suffix from names
        if repo_name.endswith('.git'):
            repo_name = repo_name[:-4]
        return repo_name

    def _get_lfs_action(self, path, request_method):
        """
        return an action based on LFS requests type.
        Those routes are handled inside vcsserver app.

        batch           -> POST to /info/lfs/objects/batch  => PUSH/PULL
                        batch is based on the `operation.
                        that could be download or upload, but those are only
                        instructions to fetch so we return pull always

        download        -> GET  to /info/lfs/{oid}          => PULL
        upload          -> PUT  to /info/lfs/{oid}          => PUSH

        verification    -> POST to /info/lfs/verify         => PULL

        """

        match_obj = GIT_LFS_PROTO_PAT.match(path)
        _parts = match_obj.groups()
        repo_name, path, operation = _parts
        log.debug(
            'LFS: detecting operation based on following '
            'data: %s, req_method:%s', _parts, request_method)

        if operation == 'verify':
            return 'pull'
        elif operation == 'objects/batch':
            # batch sends back instructions for API to dl/upl we report it
            # as pull
            if request_method == 'POST':
                return 'pull'

        elif operation:
            # probably a OID, upload  is PUT, download a GET
            if request_method == 'GET':
                return 'pull'
            else:
                return 'push'

        # if default not found require push, as action
        return 'push'

    _ACTION_MAPPING = {
        'git-receive-pack': 'push',
        'git-upload-pack': 'pull',
    }

    def _get_action(self, environ):
        """
        Maps git request commands into a pull or push command.
        In case of unknown/unexpected data, it returns 'pull' to be safe.

        :param environ:
        """
        path = environ['PATH_INFO']

        if path.endswith('/info/refs'):
            query = urlparse.parse_qs(environ['QUERY_STRING'])
            service_cmd = query.get('service', [''])[0]
            return self._ACTION_MAPPING.get(service_cmd, 'pull')

        elif GIT_LFS_PROTO_PAT.match(environ['PATH_INFO']):
            return self._get_lfs_action(
                environ['PATH_INFO'], environ['REQUEST_METHOD'])

        elif path.endswith('/git-receive-pack'):
            return 'push'
        elif path.endswith('/git-upload-pack'):
            return 'pull'

        return 'pull'

    def _create_wsgi_app(self, repo_path, repo_name, config):
        return self.scm_app.create_git_wsgi_app(
            repo_path, repo_name, config)

    def _create_config(self, extras, repo_name, scheme='http'):
        extras['git_update_server_info'] = utils2.str2bool(
            rhodecode.CONFIG.get('git_update_server_info'))

        config = utils.make_db_config(repo=repo_name)
        custom_store = config.get('vcs_git_lfs', 'store_location')

        extras['git_lfs_enabled'] = utils2.str2bool(
            config.get('vcs_git_lfs', 'enabled'))
        extras['git_lfs_store_path'] = custom_store or default_lfs_store()
        extras['git_lfs_http_scheme'] = scheme
        return extras
