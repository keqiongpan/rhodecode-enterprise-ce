import os

import ipaddress
import colander

from rhodecode.translation import _


def ip_addr_validator(node, value):
    try:
        # this raises an ValueError if address is not IpV4 or IpV6
        ipaddress.ip_network(value, strict=False)
    except ValueError:
        msg = _(u'Please enter a valid IPv4 or IpV6 address')
        raise colander.Invalid(node, msg)




