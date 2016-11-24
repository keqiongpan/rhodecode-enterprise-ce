import os
import re

import ipaddress
import colander

from rhodecode.translation import _
from rhodecode.lib.utils2 import glob2re


def ip_addr_validator(node, value):
    try:
        # this raises an ValueError if address is not IpV4 or IpV6
        ipaddress.ip_network(value, strict=False)
    except ValueError:
        msg = _(u'Please enter a valid IPv4 or IpV6 address')
        raise colander.Invalid(node, msg)


class IpAddrValidator(object):
    def __init__(self, strict=True):
        self.strict = strict

    def __call__(self, node, value):
        try:
            # this raises an ValueError if address is not IpV4 or IpV6
            ipaddress.ip_network(value, strict=self.strict)
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
