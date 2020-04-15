# -*- coding: utf-8 -*-

# Copyright (C) 2011-2020 RhodeCode GmbH
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
import re
import logging


import ipaddress
import colander

from rhodecode.translation import _
from rhodecode.lib.utils2 import glob2re, safe_unicode
from rhodecode.lib.ext_json import json

log = logging.getLogger(__name__)


def ip_addr_validator(node, value):
    try:
        # this raises an ValueError if address is not IpV4 or IpV6
        ipaddress.ip_network(safe_unicode(value), strict=False)
    except ValueError:
        msg = _(u'Please enter a valid IPv4 or IpV6 address')
        raise colander.Invalid(node, msg)


class IpAddrValidator(object):
    def __init__(self, strict=True):
        self.strict = strict

    def __call__(self, node, value):
        try:
            # this raises an ValueError if address is not IpV4 or IpV6
            ipaddress.ip_network(safe_unicode(value), strict=self.strict)
        except ValueError:
            msg = _(u'Please enter a valid IPv4 or IpV6 address')
            raise colander.Invalid(node, msg)


def glob_validator(node, value):
    try:
        re.compile('^' + glob2re(value) + '$')
    except Exception:
        msg = _(u'Invalid glob pattern')
        raise colander.Invalid(node, msg)


def valid_name_validator(node, value):
    from rhodecode.model.validation_schema import types
    if value is types.RootLocation:
        return

    msg = _('Name must start with a letter or number. Got `{}`').format(value)
    if not re.match(r'^[a-zA-z0-9]{1,}', value):
        raise colander.Invalid(node, msg)


class InvalidCloneUrl(Exception):
    allowed_prefixes = ()


def url_validator(url, repo_type, config):
    from rhodecode.lib.vcs.backends.hg import MercurialRepository
    from rhodecode.lib.vcs.backends.git import GitRepository
    from rhodecode.lib.vcs.backends.svn import SubversionRepository

    if repo_type == 'hg':
        allowed_prefixes = ('http', 'svn+http', 'git+http')

        if 'http' in url[:4]:
            # initially check if it's at least the proper URL
            # or does it pass basic auth

            return MercurialRepository.check_url(url, config)
        elif 'svn+http' in url[:8]:  # svn->hg import
            SubversionRepository.check_url(url, config)
        elif 'git+http' in url[:8]:  # git->hg import
            raise NotImplementedError()
        else:
            exc = InvalidCloneUrl('Clone from URI %s not allowed. '
                                  'Allowed url must start with one of %s'
                                  % (url, ','.join(allowed_prefixes)))
            exc.allowed_prefixes = allowed_prefixes
            raise exc

    elif repo_type == 'git':
        allowed_prefixes = ('http', 'svn+http', 'hg+http')
        if 'http' in url[:4]:
            # initially check if it's at least the proper URL
            # or does it pass basic auth
            return GitRepository.check_url(url, config)
        elif 'svn+http' in url[:8]:  # svn->git import
            raise NotImplementedError()
        elif 'hg+http' in url[:8]:  # hg->git import
            raise NotImplementedError()
        else:
            exc = InvalidCloneUrl('Clone from URI %s not allowed. '
                                  'Allowed url must start with one of %s'
                                  % (url, ','.join(allowed_prefixes)))
            exc.allowed_prefixes = allowed_prefixes
            raise exc
    elif repo_type == 'svn':
        # no validation for SVN yet
        return

    raise InvalidCloneUrl('Invalid repo type specified: `{}`'.format(repo_type))


class CloneUriValidator(object):
    def __init__(self, repo_type):
        self.repo_type = repo_type

    def __call__(self, node, value):

        from rhodecode.lib.utils import make_db_config
        try:
            config = make_db_config(clear_session=False)
            url_validator(value, self.repo_type, config)
        except InvalidCloneUrl as e:
            log.warning(e)
            raise colander.Invalid(node, e.message)
        except Exception:
            log.exception('Url validation failed')
            msg = _(u'invalid clone url for {repo_type} repository').format(
                repo_type=self.repo_type)
            raise colander.Invalid(node, msg)


def json_validator(node, value):
    try:
        json.loads(value)
    except (Exception,):
        msg = _(u'Please enter a valid json object')
        raise colander.Invalid(node, msg)
