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

import os
import time
import shutil
import hashlib

from rhodecode.lib.ext_json import json
from rhodecode.apps.file_store import utils
from rhodecode.apps.file_store.extensions import resolve_extensions
from rhodecode.apps.file_store.exceptions import FileNotAllowedException

METADATA_VER = 'v1'


class LocalFileStorage(object):

    @classmethod
    def resolve_name(cls, name, directory):
        """
        Resolves a unique name and the correct path. If a filename
        for that path already exists then a numeric prefix with values > 0 will be
        added, for example test.jpg -> 1-test.jpg etc. initially file would have 0 prefix.

        :param name: base name of file
        :param directory: absolute directory path
        """

        counter = 0
        while True:
            name = '%d-%s' % (counter, name)

            # sub_store prefix to optimize disk usage, e.g some_path/ab/final_file
            sub_store = cls._sub_store_from_filename(name)
            sub_store_path = os.path.join(directory, sub_store)
            if not os.path.exists(sub_store_path):
                os.makedirs(sub_store_path)

            path = os.path.join(sub_store_path, name)
            if not os.path.exists(path):
                return name, path
            counter += 1

    @classmethod
    def _sub_store_from_filename(cls, filename):
        return filename[:2]

    @classmethod
    def calculate_path_hash(cls, file_path):
        """
        Efficient calculation of file_path sha256 sum

        :param file_path:
        :return: sha256sum
        """
        digest = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(1024 * 100), b""):
                digest.update(chunk)

        return digest.hexdigest()

    def __init__(self, base_path, extension_groups=None):

        """
        Local file storage

        :param base_path: the absolute base path where uploads are stored
        :param extension_groups: extensions string
        """

        extension_groups = extension_groups or ['any']
        self.base_path = base_path
        self.extensions = resolve_extensions([], groups=extension_groups)

    def __repr__(self):
        return '{}@{}'.format(self.__class__, self.base_path)

    def store_path(self, filename):
        """
        Returns absolute file path of the filename, joined to the
        base_path.

        :param filename: base name of file
        """
        sub_store = self._sub_store_from_filename(filename)
        return os.path.join(self.base_path, sub_store, filename)

    def delete(self, filename):
        """
        Deletes the filename. Filename is resolved with the
        absolute path based on base_path. If file does not exist,
        returns **False**, otherwise **True**

        :param filename: base name of file
        """
        if self.exists(filename):
            os.remove(self.store_path(filename))
            return True
        return False

    def exists(self, filename):
        """
        Checks if file exists. Resolves filename's absolute
        path based on base_path.

        :param filename: base name of file
        """
        return os.path.exists(self.store_path(filename))

    def filename_allowed(self, filename, extensions=None):
        """Checks if a filename has an allowed extension

        :param filename: base name of file
        :param extensions: iterable of extensions (or self.extensions)
        """
        _, ext = os.path.splitext(filename)
        return self.extension_allowed(ext, extensions)

    def extension_allowed(self, ext, extensions=None):
        """
        Checks if an extension is permitted. Both e.g. ".jpg" and
        "jpg" can be passed in. Extension lookup is case-insensitive.

        :param ext: extension to check
        :param extensions: iterable of extensions to validate against (or self.extensions)
        """

        extensions = extensions or self.extensions
        if not extensions:
            return True
        if ext.startswith('.'):
            ext = ext[1:]
        return ext.lower() in extensions

    def save_file(self, file_obj, filename, directory=None, extensions=None,
                  extra_metadata=None, **kwargs):
        """
        Saves a file object to the uploads location.
        Returns the resolved filename, i.e. the directory +
        the (randomized/incremented) base name.

        :param file_obj: **cgi.FieldStorage** object (or similar)
        :param filename: original filename
        :param directory: relative path of sub-directory
        :param extensions: iterable of allowed extensions, if not default
        :param extra_metadata: extra JSON metadata to store next to the file with .meta suffix
        """

        extensions = extensions or self.extensions

        if not self.filename_allowed(filename, extensions):
            raise FileNotAllowedException()

        if directory:
            dest_directory = os.path.join(self.base_path, directory)
        else:
            dest_directory = self.base_path

        if not os.path.exists(dest_directory):
            os.makedirs(dest_directory)

        filename = utils.uid_filename(filename)

        # resolve also produces special sub-dir for file optimized store
        filename, path = self.resolve_name(filename, dest_directory)
        stored_file_dir = os.path.dirname(path)

        file_obj.seek(0)

        with open(path, "wb") as dest:
            shutil.copyfileobj(file_obj, dest)

        metadata = {}
        if extra_metadata:
            metadata = extra_metadata

        size = os.stat(path).st_size
        file_hash = self.calculate_path_hash(path)

        metadata.update(
            {"filename": filename,
             "size": size,
             "time": time.time(),
             "sha256": file_hash,
             "meta_ver": METADATA_VER})

        filename_meta = filename + '.meta'
        with open(os.path.join(stored_file_dir, filename_meta), "wb") as dest_meta:
            dest_meta.write(json.dumps(metadata))

        if directory:
            filename = os.path.join(directory, filename)

        return filename, metadata

    def get_metadata(self, filename):
        """
        Reads JSON stored metadata for a file

        :param filename:
        :return:
        """
        filename = self.store_path(filename)
        filename_meta = filename + '.meta'

        with open(filename_meta, "rb") as source_meta:
            return json.loads(source_meta.read())
