from __future__ import absolute_import, division, unicode_literals

import logging

from .stream import TCPStatsClient, UnixSocketStatsClient  # noqa
from .udp import StatsClient  # noqa

HOST = 'localhost'
PORT = 8125
IPV6 = False
PREFIX = None
MAXUDPSIZE = 512

log = logging.getLogger('rhodecode.statsd')


def statsd_config(config, prefix='statsd.'):
    _config = {}
    for key in config.keys():
        if key.startswith(prefix):
            _config[key[len(prefix):]] = config[key]
    return _config


def client_from_config(configuration, prefix='statsd.', **kwargs):
    from pyramid.settings import asbool

    _config = statsd_config(configuration, prefix)
    statsd_enabled = asbool(_config.pop('enabled', False))
    if not statsd_enabled:
        log.debug('statsd client not enabled by statsd.enabled =  flag, skipping...')
        return

    host = _config.pop('statsd_host', HOST)
    port = _config.pop('statsd_port', PORT)
    prefix = _config.pop('statsd_prefix', PREFIX)
    maxudpsize = _config.pop('statsd_maxudpsize', MAXUDPSIZE)
    ipv6 = asbool(_config.pop('statsd_ipv6', IPV6))
    log.debug('configured statsd client %s:%s', host, port)

    return StatsClient(
        host=host, port=port, prefix=prefix, maxudpsize=maxudpsize, ipv6=ipv6)


def get_statsd_client(request):
    return client_from_config(request.registry.settings)
