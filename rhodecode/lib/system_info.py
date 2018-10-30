# -*- coding: utf-8 -*-

# Copyright (C) 2017-2018 RhodeCode GmbH
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
import sys
import time
import platform
import collections
import pkg_resources
import logging
import resource

from pyramid.compat import configparser

log = logging.getLogger(__name__)


psutil = None

try:
    # cygwin cannot have yet psutil support.
    import psutil as psutil
except ImportError:
    pass


_NA = 'NOT AVAILABLE'

STATE_OK = 'ok'
STATE_ERR = 'error'
STATE_WARN = 'warning'

STATE_OK_DEFAULT = {'message': '', 'type': STATE_OK}


# HELPERS
def percentage(part, whole):
    whole = float(whole)
    if whole > 0:
        return round(100 * float(part) / whole, 1)
    return 0.0


def get_storage_size(storage_path):
    sizes = []
    for file_ in os.listdir(storage_path):
        storage_file = os.path.join(storage_path, file_)
        if os.path.isfile(storage_file):
            try:
                sizes.append(os.path.getsize(storage_file))
            except OSError:
                log.exception('Failed to get size of storage file %s',
                              storage_file)
                pass

    return sum(sizes)


def get_resource(resource_type):
    try:
        return resource.getrlimit(resource_type)
    except Exception:
        return 'NOT_SUPPORTED'


class SysInfoRes(object):
    def __init__(self, value, state=None, human_value=None):
        self.value = value
        self.state = state or STATE_OK_DEFAULT
        self.human_value = human_value or value

    def __json__(self):
        return {
            'value': self.value,
            'state': self.state,
            'human_value': self.human_value,
        }

    def get_value(self):
        return self.__json__()

    def __str__(self):
        return '<SysInfoRes({})>'.format(self.__json__())


class SysInfo(object):

    def __init__(self, func_name, **kwargs):
        self.func_name = func_name
        self.value = _NA
        self.state = None
        self.kwargs = kwargs or {}

    def __call__(self):
        computed = self.compute(**self.kwargs)
        if not isinstance(computed, SysInfoRes):
            raise ValueError(
                'computed value for {} is not instance of '
                '{}, got {} instead'.format(
                    self.func_name, SysInfoRes, type(computed)))
        return computed.__json__()

    def __str__(self):
        return '<SysInfo({})>'.format(self.func_name)

    def compute(self, **kwargs):
        return self.func_name(**kwargs)


# SysInfo functions
def python_info():
    value = dict(version=' '.join(platform._sys_version()),
                 executable=sys.executable)
    return SysInfoRes(value=value)


def py_modules():
    mods = dict([(p.project_name, p.version)
                 for p in pkg_resources.working_set])
    value = sorted(mods.items(), key=lambda k: k[0].lower())
    return SysInfoRes(value=value)


def platform_type():
    from rhodecode.lib.utils import safe_unicode, generate_platform_uuid

    value = dict(
        name=safe_unicode(platform.platform()),
        uuid=generate_platform_uuid()
    )
    return SysInfoRes(value=value)


def locale_info():
    import locale

    value = dict(
        locale_default=locale.getdefaultlocale(),
        locale_lc_all=locale.getlocale(locale.LC_ALL),
        lang_env=os.environ.get('LANG'),
        lc_all_env=os.environ.get('LC_ALL'),
        local_archive_env=os.environ.get('LOCALE_ARCHIVE'),
    )
    human_value = 'LANG: {}, locale LC_ALL: {},  Default locales: {}'.format(
        value['lang_env'], value['locale_lc_all'], value['locale_default'])
    return SysInfoRes(value=value, human_value=human_value)


def ulimit_info():
    data = collections.OrderedDict([
        ('cpu time (seconds)', get_resource(resource.RLIMIT_CPU)),
        ('file size', get_resource(resource.RLIMIT_FSIZE)),
        ('stack size', get_resource(resource.RLIMIT_STACK)),
        ('core file size', get_resource(resource.RLIMIT_CORE)),
        ('address space size', get_resource(resource.RLIMIT_AS)),
        ('locked in mem size', get_resource(resource.RLIMIT_MEMLOCK)),
        ('heap size', get_resource(resource.RLIMIT_DATA)),
        ('rss size', get_resource(resource.RLIMIT_RSS)),
        ('number of processes', get_resource(resource.RLIMIT_NPROC)),
        ('open files', get_resource(resource.RLIMIT_NOFILE)),
    ])

    text = ', '.join('{}:{}'.format(k,v) for k,v in data.items())

    value = {
        'limits': data,
        'text': text,
    }
    return SysInfoRes(value=value)


def uptime():
    from rhodecode.lib.helpers import age, time_to_datetime
    from rhodecode.translation import TranslationString

    value = dict(boot_time=0, uptime=0, text='')
    state = STATE_OK_DEFAULT
    if not psutil:
        return SysInfoRes(value=value, state=state)

    boot_time = psutil.boot_time()
    value['boot_time'] = boot_time
    value['uptime'] = time.time() - boot_time

    date_or_age = age(time_to_datetime(boot_time))
    if isinstance(date_or_age, TranslationString):
        date_or_age = date_or_age.interpolate()

    human_value = value.copy()
    human_value['boot_time'] = time_to_datetime(boot_time)
    human_value['uptime'] = age(time_to_datetime(boot_time), show_suffix=False)

    human_value['text'] = u'Server started {}'.format(date_or_age)
    return SysInfoRes(value=value, human_value=human_value)


def memory():
    from rhodecode.lib.helpers import format_byte_size_binary
    value = dict(available=0, used=0, used_real=0, cached=0, percent=0,
                 percent_used=0, free=0, inactive=0, active=0, shared=0,
                 total=0, buffers=0, text='')

    state = STATE_OK_DEFAULT
    if not psutil:
        return SysInfoRes(value=value, state=state)

    value.update(dict(psutil.virtual_memory()._asdict()))
    value['used_real'] = value['total'] - value['available']
    value['percent_used'] = psutil._common.usage_percent(
        value['used_real'], value['total'], 1)

    human_value = value.copy()
    human_value['text'] = '%s/%s, %s%% used' % (
        format_byte_size_binary(value['used_real']),
        format_byte_size_binary(value['total']),
        value['percent_used'],)

    keys = value.keys()[::]
    keys.pop(keys.index('percent'))
    keys.pop(keys.index('percent_used'))
    keys.pop(keys.index('text'))
    for k in keys:
        human_value[k] = format_byte_size_binary(value[k])

    if state['type'] == STATE_OK and value['percent_used'] > 90:
        msg = 'Critical: your available RAM memory is very low.'
        state = {'message': msg, 'type': STATE_ERR}

    elif state['type'] == STATE_OK and value['percent_used'] > 70:
        msg = 'Warning: your available RAM memory is running low.'
        state = {'message': msg, 'type': STATE_WARN}

    return SysInfoRes(value=value, state=state, human_value=human_value)


def machine_load():
    value = {'1_min': _NA, '5_min': _NA, '15_min': _NA, 'text': ''}
    state = STATE_OK_DEFAULT
    if not psutil:
        return SysInfoRes(value=value, state=state)

    # load averages
    if hasattr(psutil.os, 'getloadavg'):
        value.update(dict(
            zip(['1_min', '5_min', '15_min'], psutil.os.getloadavg())))

    human_value = value.copy()
    human_value['text'] = '1min: {}, 5min: {}, 15min: {}'.format(
        value['1_min'], value['5_min'], value['15_min'])

    if state['type'] == STATE_OK and value['15_min'] > 5:
        msg = 'Warning: your machine load is very high.'
        state = {'message': msg, 'type': STATE_WARN}

    return SysInfoRes(value=value, state=state, human_value=human_value)


def cpu():
    value = {'cpu': 0, 'cpu_count': 0, 'cpu_usage': []}
    state = STATE_OK_DEFAULT

    if not psutil:
        return SysInfoRes(value=value, state=state)

    value['cpu'] = psutil.cpu_percent(0.5)
    value['cpu_usage'] = psutil.cpu_percent(0.5, percpu=True)
    value['cpu_count'] = psutil.cpu_count()

    human_value = value.copy()
    human_value['text'] = '{} cores at {} %'.format(
        value['cpu_count'], value['cpu'])

    return SysInfoRes(value=value, state=state, human_value=human_value)


def storage():
    from rhodecode.lib.helpers import format_byte_size_binary
    from rhodecode.model.settings import VcsSettingsModel
    path = VcsSettingsModel().get_repos_location()

    value = dict(percent=0, used=0, total=0, path=path, text='')
    state = STATE_OK_DEFAULT
    if not psutil:
        return SysInfoRes(value=value, state=state)

    try:
        value.update(dict(psutil.disk_usage(path)._asdict()))
    except Exception as e:
        log.exception('Failed to fetch disk info')
        state = {'message': str(e), 'type': STATE_ERR}

    human_value = value.copy()
    human_value['used'] = format_byte_size_binary(value['used'])
    human_value['total'] = format_byte_size_binary(value['total'])
    human_value['text'] = "{}/{}, {}% used".format(
        format_byte_size_binary(value['used']),
        format_byte_size_binary(value['total']),
        value['percent'])

    if state['type'] == STATE_OK and value['percent'] > 90:
        msg = 'Critical: your disk space is very low.'
        state = {'message': msg, 'type': STATE_ERR}

    elif state['type'] == STATE_OK and value['percent'] > 70:
        msg = 'Warning: your disk space is running low.'
        state = {'message': msg, 'type': STATE_WARN}

    return SysInfoRes(value=value, state=state, human_value=human_value)


def storage_inodes():
    from rhodecode.model.settings import VcsSettingsModel
    path = VcsSettingsModel().get_repos_location()

    value = dict(percent=0, free=0, used=0, total=0, path=path, text='')
    state = STATE_OK_DEFAULT
    if not psutil:
        return SysInfoRes(value=value, state=state)

    try:
        i_stat = os.statvfs(path)
        value['free'] = i_stat.f_ffree
        value['used'] = i_stat.f_files-i_stat.f_favail
        value['total'] = i_stat.f_files
        value['percent'] = percentage(value['used'], value['total'])
    except Exception as e:
        log.exception('Failed to fetch disk inodes info')
        state = {'message': str(e), 'type': STATE_ERR}

    human_value = value.copy()
    human_value['text'] = "{}/{}, {}% used".format(
        value['used'], value['total'], value['percent'])

    if state['type'] == STATE_OK and value['percent'] > 90:
        msg = 'Critical: your disk free inodes are very low.'
        state = {'message': msg, 'type': STATE_ERR}

    elif state['type'] == STATE_OK and value['percent'] > 70:
        msg = 'Warning: your disk free inodes are running low.'
        state = {'message': msg, 'type': STATE_WARN}

    return SysInfoRes(value=value, state=state, human_value=human_value)


def storage_archives():
    import rhodecode
    from rhodecode.lib.utils import safe_str
    from rhodecode.lib.helpers import format_byte_size_binary

    msg = 'Enable this by setting ' \
          'archive_cache_dir=/path/to/cache option in the .ini file'
    path = safe_str(rhodecode.CONFIG.get('archive_cache_dir', msg))

    value = dict(percent=0, used=0, total=0, items=0, path=path, text='')
    state = STATE_OK_DEFAULT
    try:
        items_count = 0
        used = 0
        for root, dirs, files in os.walk(path):
            if root == path:
                items_count = len(files)

            for f in files:
                try:
                    used += os.path.getsize(os.path.join(root, f))
                except OSError:
                    pass
        value.update({
            'percent': 100,
            'used': used,
            'total': used,
            'items': items_count
        })

    except Exception as e:
        log.exception('failed to fetch archive cache storage')
        state = {'message': str(e), 'type': STATE_ERR}

    human_value = value.copy()
    human_value['used'] = format_byte_size_binary(value['used'])
    human_value['total'] = format_byte_size_binary(value['total'])
    human_value['text'] = "{} ({} items)".format(
        human_value['used'], value['items'])

    return SysInfoRes(value=value, state=state, human_value=human_value)


def storage_gist():
    from rhodecode.model.gist import GIST_STORE_LOC
    from rhodecode.model.settings import VcsSettingsModel
    from rhodecode.lib.utils import safe_str
    from rhodecode.lib.helpers import format_byte_size_binary
    path = safe_str(os.path.join(
        VcsSettingsModel().get_repos_location(), GIST_STORE_LOC))

    # gist storage
    value = dict(percent=0, used=0, total=0, items=0, path=path, text='')
    state = STATE_OK_DEFAULT

    try:
        items_count = 0
        used = 0
        for root, dirs, files in os.walk(path):
            if root == path:
                items_count = len(dirs)

            for f in files:
                try:
                    used += os.path.getsize(os.path.join(root, f))
                except OSError:
                    pass
        value.update({
            'percent': 100,
            'used': used,
            'total': used,
            'items': items_count
        })
    except Exception as e:
        log.exception('failed to fetch gist storage items')
        state = {'message': str(e), 'type': STATE_ERR}

    human_value = value.copy()
    human_value['used'] = format_byte_size_binary(value['used'])
    human_value['total'] = format_byte_size_binary(value['total'])
    human_value['text'] = "{} ({} items)".format(
        human_value['used'], value['items'])

    return SysInfoRes(value=value, state=state, human_value=human_value)


def storage_temp():
    import tempfile
    from rhodecode.lib.helpers import format_byte_size_binary

    path = tempfile.gettempdir()
    value = dict(percent=0, used=0, total=0, items=0, path=path, text='')
    state = STATE_OK_DEFAULT

    if not psutil:
        return SysInfoRes(value=value, state=state)

    try:
        value.update(dict(psutil.disk_usage(path)._asdict()))
    except Exception as e:
        log.exception('Failed to fetch temp dir info')
        state = {'message': str(e), 'type': STATE_ERR}

    human_value = value.copy()
    human_value['used'] = format_byte_size_binary(value['used'])
    human_value['total'] = format_byte_size_binary(value['total'])
    human_value['text'] = "{}/{}, {}% used".format(
        format_byte_size_binary(value['used']),
        format_byte_size_binary(value['total']),
        value['percent'])

    return SysInfoRes(value=value, state=state, human_value=human_value)


def search_info():
    import rhodecode
    from rhodecode.lib.index import searcher_from_config

    backend = rhodecode.CONFIG.get('search.module', '')
    location = rhodecode.CONFIG.get('search.location', '')

    try:
        searcher = searcher_from_config(rhodecode.CONFIG)
        searcher = searcher.__class__.__name__
    except Exception:
        searcher = None

    value = dict(
        backend=backend, searcher=searcher, location=location, text='')
    state = STATE_OK_DEFAULT

    human_value = value.copy()
    human_value['text'] = "backend:`{}`".format(human_value['backend'])

    return SysInfoRes(value=value, state=state, human_value=human_value)


def git_info():
    from rhodecode.lib.vcs.backends import git
    state = STATE_OK_DEFAULT
    value = human_value = ''
    try:
        value = git.discover_git_version(raise_on_exc=True)
        human_value = 'version reported from VCSServer: {}'.format(value)
    except Exception as e:
        state = {'message': str(e), 'type': STATE_ERR}

    return SysInfoRes(value=value, state=state, human_value=human_value)


def hg_info():
    from rhodecode.lib.vcs.backends import hg
    state = STATE_OK_DEFAULT
    value = human_value = ''
    try:
        value = hg.discover_hg_version(raise_on_exc=True)
        human_value = 'version reported from VCSServer: {}'.format(value)
    except Exception as e:
        state = {'message': str(e), 'type': STATE_ERR}
    return SysInfoRes(value=value, state=state, human_value=human_value)


def svn_info():
    from rhodecode.lib.vcs.backends import svn
    state = STATE_OK_DEFAULT
    value = human_value = ''
    try:
        value = svn.discover_svn_version(raise_on_exc=True)
        human_value = 'version reported from VCSServer: {}'.format(value)
    except Exception as e:
        state = {'message': str(e), 'type': STATE_ERR}
    return SysInfoRes(value=value, state=state, human_value=human_value)


def vcs_backends():
    import rhodecode
    value = rhodecode.CONFIG.get('vcs.backends')
    human_value = 'Enabled backends in order: {}'.format(','.join(value))
    return SysInfoRes(value=value, human_value=human_value)


def vcs_server():
    import rhodecode
    from rhodecode.lib.vcs.backends import get_vcsserver_service_data

    server_url = rhodecode.CONFIG.get('vcs.server')
    enabled = rhodecode.CONFIG.get('vcs.server.enable')
    protocol = rhodecode.CONFIG.get('vcs.server.protocol') or 'http'
    state = STATE_OK_DEFAULT
    version = None
    workers = 0

    try:
        data = get_vcsserver_service_data()
        if data and 'version' in data:
            version = data['version']

        if data and 'config' in data:
            conf = data['config']
            workers = conf.get('workers', 'NOT AVAILABLE')

        connection = 'connected'
    except Exception as e:
        connection = 'failed'
        state = {'message': str(e), 'type': STATE_ERR}

    value = dict(
        url=server_url,
        enabled=enabled,
        protocol=protocol,
        connection=connection,
        version=version,
        text='',
    )

    human_value = value.copy()
    human_value['text'] = \
        '{url}@ver:{ver} via {mode} mode[workers:{workers}], connection:{conn}'.format(
            url=server_url, ver=version, workers=workers, mode=protocol,
            conn=connection)

    return SysInfoRes(value=value, state=state, human_value=human_value)


def rhodecode_app_info():
    import rhodecode
    edition = rhodecode.CONFIG.get('rhodecode.edition')

    value = dict(
        rhodecode_version=rhodecode.__version__,
        rhodecode_lib_path=os.path.abspath(rhodecode.__file__),
        text=''
    )
    human_value = value.copy()
    human_value['text'] = 'RhodeCode {edition}, version {ver}'.format(
        edition=edition, ver=value['rhodecode_version']
    )
    return SysInfoRes(value=value, human_value=human_value)


def rhodecode_config():
    import rhodecode
    path = rhodecode.CONFIG.get('__file__')
    rhodecode_ini_safe = rhodecode.CONFIG.copy()

    try:
        config = configparser.ConfigParser()
        config.read(path)
        parsed_ini = config
        if parsed_ini.has_section('server:main'):
            parsed_ini = dict(parsed_ini.items('server:main'))
    except Exception:
        log.exception('Failed to read .ini file for display')
        parsed_ini = {}

    cert_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(path)))),
        '.rccontrol-profile/etc/ca-bundle.crt')

    rhodecode_ini_safe['server:main'] = parsed_ini

    blacklist = [
        'rhodecode_license_key',
        'routes.map',
        'sqlalchemy.db1.url',
        'channelstream.secret',
        'beaker.session.secret',
        'rhodecode.encrypted_values.secret',
        'rhodecode_auth_github_consumer_key',
        'rhodecode_auth_github_consumer_secret',
        'rhodecode_auth_google_consumer_key',
        'rhodecode_auth_google_consumer_secret',
        'rhodecode_auth_bitbucket_consumer_secret',
        'rhodecode_auth_bitbucket_consumer_key',
        'rhodecode_auth_twitter_consumer_secret',
        'rhodecode_auth_twitter_consumer_key',

        'rhodecode_auth_twitter_secret',
        'rhodecode_auth_github_secret',
        'rhodecode_auth_google_secret',
        'rhodecode_auth_bitbucket_secret',

        'appenlight.api_key',
        ('app_conf', 'sqlalchemy.db1.url')
    ]
    for k in blacklist:
        if isinstance(k, tuple):
            section, key = k
            if section in rhodecode_ini_safe:
                rhodecode_ini_safe[section] = '**OBFUSCATED**'
        else:
            rhodecode_ini_safe.pop(k, None)

    # TODO: maybe put some CONFIG checks here ?
    return SysInfoRes(value={'config': rhodecode_ini_safe,
                             'path': path, 'cert_path': cert_path})


def database_info():
    import rhodecode
    from sqlalchemy.engine import url as engine_url
    from rhodecode.model.meta import Base as sql_base, Session
    from rhodecode.model.db import DbMigrateVersion

    state = STATE_OK_DEFAULT

    db_migrate = DbMigrateVersion.query().filter(
        DbMigrateVersion.repository_id == 'rhodecode_db_migrations').one()

    db_url_obj = engine_url.make_url(rhodecode.CONFIG['sqlalchemy.db1.url'])

    try:
        engine = sql_base.metadata.bind
        db_server_info = engine.dialect._get_server_version_info(
            Session.connection(bind=engine))
        db_version = '.'.join(map(str, db_server_info))
    except Exception:
        log.exception('failed to fetch db version')
        db_version = 'UNKNOWN'

    db_info = dict(
        migrate_version=db_migrate.version,
        type=db_url_obj.get_backend_name(),
        version=db_version,
        url=repr(db_url_obj)
    )
    current_version = db_migrate.version
    expected_version = rhodecode.__dbversion__
    if state['type'] == STATE_OK and current_version != expected_version:
        msg = 'Critical: database schema mismatch, ' \
              'expected version {}, got {}. ' \
              'Please run migrations on your database.'.format(
            expected_version, current_version)
        state = {'message': msg, 'type': STATE_ERR}

    human_value = db_info.copy()
    human_value['url'] = "{} @ migration version: {}".format(
        db_info['url'], db_info['migrate_version'])
    human_value['version'] = "{} {}".format(db_info['type'], db_info['version'])
    return SysInfoRes(value=db_info, state=state, human_value=human_value)


def server_info(environ):
    import rhodecode
    from rhodecode.lib.base import get_server_ip_addr, get_server_port

    value = {
        'server_ip': '%s:%s' % (
            get_server_ip_addr(environ, log_errors=False),
            get_server_port(environ)
        ),
        'server_id': rhodecode.CONFIG.get('instance_id'),
    }
    return SysInfoRes(value=value)


def usage_info():
    from rhodecode.model.db import User, Repository
    value = {
        'users': User.query().count(),
        'users_active': User.query().filter(User.active == True).count(),
        'repositories': Repository.query().count(),
        'repository_types': {
            'hg': Repository.query().filter(
                Repository.repo_type == 'hg').count(),
            'git': Repository.query().filter(
                Repository.repo_type == 'git').count(),
            'svn': Repository.query().filter(
                Repository.repo_type == 'svn').count(),
        },
    }
    return SysInfoRes(value=value)


def get_system_info(environ):
    environ = environ or {}
    return {
        'rhodecode_app': SysInfo(rhodecode_app_info)(),
        'rhodecode_config': SysInfo(rhodecode_config)(),
        'rhodecode_usage': SysInfo(usage_info)(),
        'python': SysInfo(python_info)(),
        'py_modules': SysInfo(py_modules)(),

        'platform': SysInfo(platform_type)(),
        'locale': SysInfo(locale_info)(),
        'server': SysInfo(server_info, environ=environ)(),
        'database': SysInfo(database_info)(),
        'ulimit': SysInfo(ulimit_info)(),
        'storage': SysInfo(storage)(),
        'storage_inodes': SysInfo(storage_inodes)(),
        'storage_archive': SysInfo(storage_archives)(),
        'storage_gist': SysInfo(storage_gist)(),
        'storage_temp': SysInfo(storage_temp)(),

        'search': SysInfo(search_info)(),

        'uptime': SysInfo(uptime)(),
        'load': SysInfo(machine_load)(),
        'cpu': SysInfo(cpu)(),
        'memory': SysInfo(memory)(),

        'vcs_backends': SysInfo(vcs_backends)(),
        'vcs_server': SysInfo(vcs_server)(),

        'git': SysInfo(git_info)(),
        'hg': SysInfo(hg_info)(),
        'svn': SysInfo(svn_info)(),
    }
