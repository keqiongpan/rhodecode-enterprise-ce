# -*- coding: utf-8 -*-

# Copyright (C) 2016-2020 RhodeCode GmbH
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


ANY = []
TEXT_EXT = ['txt', 'md', 'rst', 'log']
DOCUMENTS_EXT = ['pdf', 'rtf', 'odf', 'ods', 'gnumeric', 'abw', 'doc', 'docx', 'xls', 'xlsx']
IMAGES_EXT = ['jpg', 'jpe', 'jpeg', 'png', 'gif', 'svg', 'bmp', 'tiff']
AUDIO_EXT = ['wav', 'mp3', 'aac', 'ogg', 'oga', 'flac']
VIDEO_EXT = ['mpeg', '3gp', 'avi', 'divx', 'dvr', 'flv', 'mp4', 'wmv']
DATA_EXT = ['csv', 'ini', 'json', 'plist', 'xml', 'yaml', 'yml']
SCRIPTS_EXT = ['js', 'php', 'pl', 'py', 'rb', 'sh', 'go', 'c', 'h']
ARCHIVES_EXT = ['gz', 'bz2', 'zip', 'tar', 'tgz', 'txz', '7z']
EXECUTABLES_EXT = ['so', 'exe', 'dll']


DEFAULT = DOCUMENTS_EXT + TEXT_EXT + IMAGES_EXT + DATA_EXT

GROUPS = dict((
    ('any', ANY),
    ('text', TEXT_EXT),
    ('documents', DOCUMENTS_EXT),
    ('images', IMAGES_EXT),
    ('audio', AUDIO_EXT),
    ('video', VIDEO_EXT),
    ('data', DATA_EXT),
    ('scripts', SCRIPTS_EXT),
    ('archives', ARCHIVES_EXT),
    ('executables', EXECUTABLES_EXT),
    ('default', DEFAULT),
))


def resolve_extensions(extensions, groups=None):
    """
    Calculate allowed extensions based on a list of extensions provided, and optional
    groups of extensions from the available lists.

    :param extensions: a list of extensions e.g ['py', 'txt']
    :param groups: additionally groups to extend the extensions.
    """
    groups = groups or []
    valid_exts = set([x.lower() for x in extensions])

    for group in groups:
        if group in GROUPS:
            valid_exts.update(GROUPS[group])

    return valid_exts
