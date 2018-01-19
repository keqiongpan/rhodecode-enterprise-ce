# -*- coding: utf-8 -*-

# Copyright (C) 2017-2018 RhodeCode GmbH
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
from pyramid.view import view_config

from rhodecode.apps._base import RepoAppView
from rhodecode.lib import audit_logger
from rhodecode.lib import helpers as h
from rhodecode.lib.auth import (
    LoginRequired, HasRepoPermissionAnyDecorator, CSRFRequired)
from rhodecode.lib.ext_json import json

log = logging.getLogger(__name__)


class StripView(RepoAppView):
    def load_default_context(self):
        c = self._get_local_tmpl_context()


        return c

    @LoginRequired()
    @HasRepoPermissionAnyDecorator('repository.admin')
    @view_config(
        route_name='edit_repo_strip', request_method='GET',
        renderer='rhodecode:templates/admin/repos/repo_edit.mako')
    def strip(self):
        c = self.load_default_context()
        c.active = 'strip'
        c.strip_limit = 10

        return self._get_template_context(c)

    @LoginRequired()
    @HasRepoPermissionAnyDecorator('repository.admin')
    @CSRFRequired()
    @view_config(
        route_name='strip_check', request_method='POST',
        renderer='json', xhr=True)
    def strip_check(self):
        from rhodecode.lib.vcs.backends.base import EmptyCommit
        data = {}
        rp = self.request.POST
        for i in range(1, 11):
            chset = 'changeset_id-%d' % (i,)
            check = rp.get(chset)

            if check:
                data[i] = self.db_repo.get_changeset(rp[chset])
                if isinstance(data[i], EmptyCommit):
                    data[i] = {'rev': None, 'commit': h.escape(rp[chset])}
                else:
                    data[i] = {'rev': data[i].raw_id, 'branch': data[i].branch,
                               'author': h.escape(data[i].author),
                               'comment': h.escape(data[i].message)}
            else:
                break
        return data

    @LoginRequired()
    @HasRepoPermissionAnyDecorator('repository.admin')
    @CSRFRequired()
    @view_config(
        route_name='strip_execute', request_method='POST',
        renderer='json', xhr=True)
    def strip_execute(self):
        from rhodecode.model.scm import ScmModel

        c = self.load_default_context()
        user = self._rhodecode_user
        rp = self.request.POST
        data = {}
        for idx in rp:
            commit = json.loads(rp[idx])
            # If someone put two times the same branch
            if commit['branch'] in data.keys():
                continue
            try:
                ScmModel().strip(
                    repo=self.db_repo,
                    commit_id=commit['rev'], branch=commit['branch'])
                log.info('Stripped commit %s from repo `%s` by %s' % (
                    commit['rev'], self.db_repo_name, user))
                data[commit['rev']] = True

                audit_logger.store_web(
                    'repo.commit.strip', action_data={'commit_id': commit['rev']},
                    repo=self.db_repo, user=self._rhodecode_user, commit=True)

            except Exception as e:
                data[commit['rev']] = False
                log.debug('Stripped commit %s from repo `%s` failed by %s, exeption %s' % (
                    commit['rev'], self.db_repo_name, user, e.message))
        return data
