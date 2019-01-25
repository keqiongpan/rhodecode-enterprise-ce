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
from rhodecode.apps.upload_store import utils
from rhodecode.apps.upload_store.exceptions import (
    FileNotAllowedException,FileOverSizeException)

from rhodecode.lib import helpers as h
from rhodecode.lib import audit_logger
from rhodecode.lib.auth import (CSRFRequired, NotAnonymous)

log = logging.getLogger(__name__)


class FileStoreView(BaseAppView):
    upload_key = 'store_file'

    def load_default_context(self):
        c = self._get_local_tmpl_context()
        self.storage = utils.get_file_storage(self.request.registry.settings)
        return c

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
            'filename': filename,
            'size': '',  # filled by save_file
            'user_uploaded': {'username': self._rhodecode_user.username,
                              'user_id': self._rhodecode_user.user_id,
                              'ip': self._rhodecode_user.ip_addr}}
        try:
            store_fid = self.storage.save_file(file_obj.file, filename,
                                               metadata=metadata)
        except FileNotAllowedException:
            return {'store_fid': None,
                    'access_path': None,
                    'error': 'File {} is not allowed.'.format(filename)}

        except FileOverSizeException:
            return {'store_fid': None,
                    'access_path': None,
                    'error': 'File {} is exceeding allowed limit.'.format(filename)}

        return {'store_fid': store_fid,
                'access_path': h.route_path('download_file', fid=store_fid)}

    @view_config(route_name='download_file')
    def download_file(self):
        self.load_default_context()
        file_uid = self.request.matchdict['fid']
        log.debug('Requesting FID:%s from store %s', file_uid, self.storage)
        if not self.storage.exists(file_uid):
            log.debug('File with FID:%s not found in the store', file_uid)
            raise HTTPNotFound()

        file_path = self.storage.store_path(file_uid)
        return FileResponse(file_path)
