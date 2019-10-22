# -*- coding: utf-8 -*-

# Copyright (C) 2016-2019 RhodeCode GmbH
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
from pyramid.response import FileResponse
from pyramid.httpexceptions import HTTPFound, HTTPNotFound

from rhodecode.apps._base import BaseAppView
from rhodecode.apps.file_store import utils
from rhodecode.apps.file_store.exceptions import (
    FileNotAllowedException, FileOverSizeException)

from rhodecode.lib import helpers as h
from rhodecode.lib import audit_logger
from rhodecode.lib.auth import (
    CSRFRequired, NotAnonymous, HasRepoPermissionAny, HasRepoGroupPermissionAny,
    LoginRequired)
from rhodecode.model.db import Session, FileStore, UserApiKeys

log = logging.getLogger(__name__)


class FileStoreView(BaseAppView):
    upload_key = 'store_file'

    def load_default_context(self):
        c = self._get_local_tmpl_context()
        self.storage = utils.get_file_storage(self.request.registry.settings)
        return c

    @LoginRequired()
    @NotAnonymous()
    @CSRFRequired()
    @view_config(route_name='upload_file', request_method='POST', renderer='json_ext')
    def upload_file(self):
        self.load_default_context()
        file_obj = self.request.POST.get(self.upload_key)

        if file_obj is None:
            return {'store_fid': None,
                    'access_path': None,
                    'error': '{} data field is missing'.format(self.upload_key)}

        if not hasattr(file_obj, 'filename'):
            return {'store_fid': None,
                    'access_path': None,
                    'error': 'filename cannot be read from the data field'}

        filename = file_obj.filename

        metadata = {
            'user_uploaded': {'username': self._rhodecode_user.username,
                              'user_id': self._rhodecode_user.user_id,
                              'ip': self._rhodecode_user.ip_addr}}
        try:
            store_uid, metadata = self.storage.save_file(
                file_obj.file, filename, extra_metadata=metadata)
        except FileNotAllowedException:
            return {'store_fid': None,
                    'access_path': None,
                    'error': 'File {} is not allowed.'.format(filename)}

        except FileOverSizeException:
            return {'store_fid': None,
                    'access_path': None,
                    'error': 'File {} is exceeding allowed limit.'.format(filename)}

        try:
            entry = FileStore.create(
                file_uid=store_uid, filename=metadata["filename"],
                file_hash=metadata["sha256"], file_size=metadata["size"],
                file_description='upload attachment',
                check_acl=False, user_id=self._rhodecode_user.user_id
            )
            Session().add(entry)
            Session().commit()
            log.debug('Stored upload in DB as %s', entry)
        except Exception:
            log.exception('Failed to store file %s', filename)
            return {'store_fid': None,
                    'access_path': None,
                    'error': 'File {} failed to store in DB.'.format(filename)}

        return {'store_fid': store_uid,
                'access_path': h.route_path('download_file', fid=store_uid)}

    def _serve_file(self, file_uid):

        if not self.storage.exists(file_uid):
            store_path = self.storage.store_path(file_uid)
            log.debug('File with FID:%s not found in the store under `%s`',
                      file_uid, store_path)
            raise HTTPNotFound()

        db_obj = FileStore().query().filter(FileStore.file_uid == file_uid).scalar()
        if not db_obj:
            raise HTTPNotFound()

        # private upload for user
        if db_obj.check_acl and db_obj.scope_user_id:
            user = db_obj.user
            if self._rhodecode_db_user.user_id != user.user_id:
                log.warning('Access to file store object forbidden')
                raise HTTPNotFound()

        # scoped to repository permissions
        if db_obj.check_acl and db_obj.scope_repo_id:
            repo = db_obj.repo
            perm_set = ['repository.read', 'repository.write', 'repository.admin']
            has_perm = HasRepoPermissionAny(*perm_set)(repo.repo_name, 'FileStore check')
            if not has_perm:
                log.warning('Access to file store object `%s` forbidden', file_uid)
                raise HTTPNotFound()

        # scoped to repository group permissions
        if db_obj.check_acl and db_obj.scope_repo_group_id:
            repo_group = db_obj.repo_group
            perm_set = ['group.read', 'group.write', 'group.admin']
            has_perm = HasRepoGroupPermissionAny(*perm_set)(repo_group.group_name, 'FileStore check')
            if not has_perm:
                log.warning('Access to file store object `%s` forbidden', file_uid)
                raise HTTPNotFound()

        FileStore.bump_access_counter(file_uid)

        file_path = self.storage.store_path(file_uid)
        return FileResponse(file_path)

    # ACL is checked by scopes, if no scope the file is accessible to all
    @view_config(route_name='download_file')
    def download_file(self):
        self.load_default_context()
        file_uid = self.request.matchdict['fid']
        log.debug('Requesting FID:%s from store %s', file_uid, self.storage)
        return self._serve_file(file_uid)

    @LoginRequired(auth_token_access=[UserApiKeys.ROLE_ARTIFACT_DOWNLOAD])
    @view_config(route_name='download_file_by_token')
    def download_file_by_token(self):
        """
        Special view that allows to access the download file by special URL that
        is stored inside the URL.

        http://example.com/_file_store/token-download/TOKEN/FILE_UID
        """
        self.load_default_context()
        file_uid = self.request.matchdict['fid']
        return self._serve_file(file_uid)
