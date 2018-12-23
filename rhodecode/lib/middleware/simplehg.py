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

"""
SimpleHG middleware for handling mercurial protocol request
(push/clone etc.). It's implemented with basic auth function
"""

import logging
import urlparse
import urllib

from rhodecode.lib import utils
from rhodecode.lib.ext_json import json
from rhodecode.lib.middleware import simplevcs

log = logging.getLogger(__name__)


class SimpleHg(simplevcs.SimpleVCS):

    SCM = 'hg'

    def _get_repository_name(self, environ):
        """
        Gets repository name out of PATH_INFO header

        :param environ: environ where PATH_INFO is stored
        """
        repo_name = environ['PATH_INFO']
        if repo_name and repo_name.startswith('/'):
            # remove only the first leading /
            repo_name = repo_name[1:]
        return repo_name.rstrip('/')

    _ACTION_MAPPING = {
        'changegroup': 'pull',
        'changegroupsubset': 'pull',
        'getbundle': 'pull',
        'stream_out': 'pull',
        'listkeys': 'pull',
        'between': 'pull',
        'branchmap': 'pull',
        'branches': 'pull',
        'clonebundles': 'pull',
        'capabilities': 'pull',
        'debugwireargs': 'pull',
        'heads': 'pull',
        'lookup': 'pull',
        'hello': 'pull',
        'known': 'pull',

        # largefiles
        'putlfile': 'push',
        'getlfile': 'pull',
        'statlfile': 'pull',
        'lheads': 'pull',

        # evolve
        'evoext_obshashrange_v1': 'pull',
        'evoext_obshash': 'pull',
        'evoext_obshash1': 'pull',

        'unbundle': 'push',
        'pushkey': 'push',
    }

    @classmethod
    def _get_xarg_headers(cls, environ):
        i = 1
        chunks = []  # gather chunks stored in multiple 'hgarg_N'
        while True:
            head = environ.get('HTTP_X_HGARG_{}'.format(i))
            if not head:
                break
            i += 1
            chunks.append(urllib.unquote_plus(head))
        full_arg = ''.join(chunks)
        pref = 'cmds='
        if full_arg.startswith(pref):
            # strip the cmds= header defining our batch commands
            full_arg = full_arg[len(pref):]
        cmds = full_arg.split(';')
        return cmds

    @classmethod
    def _get_batch_cmd(cls, environ):
        """
        Handle batch command send commands. Those are ';' separated commands
        sent by batch command that server needs to execute. We need to extract
        those, and map them to our ACTION_MAPPING to get all push/pull commands
        specified in the batch
        """
        default = 'push'
        batch_cmds = []
        try:
            cmds = cls._get_xarg_headers(environ)
            for pair in cmds:
                parts = pair.split(' ', 1)
                if len(parts) != 2:
                    continue
                # entry should be in a format `key ARGS`
                cmd, args = parts
                action = cls._ACTION_MAPPING.get(cmd, default)
                batch_cmds.append(action)
        except Exception:
            log.exception('Failed to extract batch commands operations')

        # in case we failed, (e.g malformed data) assume it's PUSH sub-command
        # for safety
        return batch_cmds or [default]

    def _get_action(self, environ):
        """
        Maps mercurial request commands into a pull or push command.
        In case of unknown/unexpected data, it returns 'push' to be safe.

        :param environ:
        """
        default = 'push'
        query = urlparse.parse_qs(environ['QUERY_STRING'],
                                  keep_blank_values=True)

        if 'cmd' in query:
            cmd = query['cmd'][0]
            if cmd == 'batch':
                cmds = self._get_batch_cmd(environ)
                if 'push' in cmds:
                    return 'push'
                else:
                    return 'pull'
            return self._ACTION_MAPPING.get(cmd, default)

        return default

    def _create_wsgi_app(self, repo_path, repo_name, config):
        return self.scm_app.create_hg_wsgi_app(repo_path, repo_name, config)

    def _create_config(self, extras, repo_name):
        config = utils.make_db_config(repo=repo_name)
        config.set('rhodecode', 'RC_SCM_DATA', json.dumps(extras))

        return config.serialize()
