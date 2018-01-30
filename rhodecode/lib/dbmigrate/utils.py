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

import logging

log = logging.getLogger(__name__)


def create_default_permissions(_SESSION, db):
    for p in db.Permission.PERMS:
        if not db.Permission.get_by_key(p[0]):
            new_perm = db.Permission()
            new_perm.permission_name = p[0]
            new_perm.permission_longname = p[0]  # translation err with p[1]
            _SESSION().add(new_perm)


def create_default_object_permission(_SESSION, db):

    obj = db.User.get_by_username(db.User.DEFAULT_USER)
    obj_perms = db.UserToPerm.query().filter(db.UserToPerm.user == obj).all()

    def _get_group(perm_name):
        return '.'.join(perm_name.split('.')[:1])

    defined_perms_groups = map(
        _get_group, (x.permission.permission_name for x in obj_perms))
    log.debug('GOT ALREADY DEFINED:%s', obj_perms)

    # for every default permission that needs to be created, we check if
    # it's group is already defined, if it's not we create default perm
    for perm_name in db.Permission.DEFAULT_USER_PERMISSIONS:
        gr = _get_group(perm_name)
        if gr not in defined_perms_groups:
            log.debug('GR:%s not found, creating permission %s', gr, perm_name)
            new_perm = db.UserToPerm()
            new_perm.user = obj
            new_perm.permission = db.Permission.get_by_key(perm_name)
            _SESSION().add(new_perm)
