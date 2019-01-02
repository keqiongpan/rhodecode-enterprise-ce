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

"""
us in hooks::

    from .helpers import extra_fields
    # returns list of dicts with key-val fetched from extra fields
    repo_extra_fields = extra_fields.run(**kwargs)

"""


def run(*args, **kwargs):
    from rhodecode.model.db import Repository
    # use temp name then the main one propagated
    repo_name = kwargs.pop('REPOSITORY', None) or kwargs['repository']
    repo = Repository.get_by_repo_name(repo_name)

    fields = {}
    for field in repo.extra_fields:
        fields[field.field_key] = field.get_dict()

    return fields
