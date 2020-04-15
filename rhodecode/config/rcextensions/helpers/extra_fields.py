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
example usage in hooks::

    from .helpers import extra_fields
    # returns list of dicts with key-val fetched from extra fields
    repo_extra_fields = extra_fields.run(**kwargs)
    repo_extra_fields.get('endpoint_url')

    # the field stored the following example values
    {u'created_on': datetime.datetime(),
     u'field_key': u'endpoint_url',
     u'field_label': u'Endpoint URL',
     u'field_desc': u'Full HTTP endpoint to call if given',
     u'field_type': u'str',
     u'field_value': u'http://server.com/post',
     u'repo_field_id': 1,
     u'repository_id': 1}
    # for example to obtain the value:
    endpoint_field = repo_extra_fields.get('endpoint_url')
    if endpoint_field:
        url = endpoint_field['field_value']

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


class _Undefined(object):
    pass


def get_field(extra_fields_data, key, default=_Undefined(), convert_type=True):
    """
    field_value = get_field(extra_fields, key='ci_endpoint_url', default='')
    """
    from ..utils import str2bool, aslist

    if key not in extra_fields_data:
        if isinstance(default, _Undefined):
            raise ValueError('key {} not present in extra_fields'.format(key))
        return default

    # NOTE(dan): from metadata we get field_label, field_value, field_desc, field_type
    field_metadata = extra_fields_data[key]

    field_value = field_metadata['field_value']

    # NOTE(dan): empty value, use default
    if not field_value and not isinstance(default, _Undefined):
        return default

    if convert_type:
        # 'str', 'unicode', 'list', 'tuple'
        _type = field_metadata['field_type']
        if _type in ['list', 'tuple']:
            field_value = aslist(field_value)

    return field_value
