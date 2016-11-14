import os
import sys
import time
import platform
import pkg_resources
import logging


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
        return 100 * float(part) / whole
    return 0


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


class SysInfoRes(object):
    def __init__(self, value, state=STATE_OK_DEFAULT, human_value=None):
        self.value = value
        self.state = state
        self.human_value = human_value or value

    def __json__(self):
        return {
            'value': self.value,
            'state': self.state,
            'human_value': self.human_value,
        }

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
    value = {
        'version': ' '.join(platform._sys_version()),
        'executable': sys.executable
    }
    return SysInfoRes(value=value)


def py_modules():
    mods = dict([(p.project_name, p.version)
                 for p in pkg_resources.working_set])
    value = sorted(mods.items(), key=lambda k: k[0].lower())
    return SysInfoRes(value=value)


def platform_type():
    from rhodecode.lib.utils import safe_unicode
    value = safe_unicode(platform.platform())
    return SysInfoRes(value=value)


def uptime():
    from rhodecode.lib.helpers import age, time_to_datetime
    from rhodecode.translation import _

    _uptime = _uptime_human = {'boot_time': 0, 'uptime': 0}
    state = STATE_OK_DEFAULT
    if not psutil:
        return SysInfoRes(value=_uptime, state=state)

    boot_time = psutil.boot_time()
    _uptime['boot_time'] = boot_time
    _uptime['uptime'] = time.time() - boot_time

    _uptime_human['boot_time'] = time_to_datetime(boot_time)
    _uptime_human['uptime'] = _('Server started {}').format(
        age(time_to_datetime(boot_time)))

    return SysInfoRes(value=_uptime, human_value=_uptime_human)


def memory():
    from rhodecode.lib.helpers import format_byte_size_binary
    _memory = {'available': 0, 'used': 0, 'cached': 0, 'percent': 0,
               'percent_used': 0, 'free': 0, 'inactive': 0, 'active': 0,
               'shared': 0, 'total': 0, 'buffers': 0}
    state = STATE_OK_DEFAULT
    if not psutil:
        return SysInfoRes(value=_memory, state=state)

    # memory
    _memory = dict(psutil.virtual_memory()._asdict())
    _memory['percent_used'] = psutil._common.usage_percent(
        (_memory['total'] - _memory['free']), _memory['total'], 1)

    try:
        human_value = '%s/%s, %s%% used' % (
            format_byte_size_binary(_memory['used']),
            format_byte_size_binary(_memory['total']),
            _memory['percent_used'],)
    except TypeError:
        human_value = 'NOT AVAILABLE'

    if state['type'] == STATE_OK and _memory['percent_used'] > 90:
        msg = 'Critical: your available RAM memory is very low.'
        state = {'message': msg, 'type': STATE_ERR}

    elif state['type'] == STATE_OK and  _memory['percent_used'] > 70:
        msg = 'Warning: your available RAM memory is running low.'
        state = {'message': msg, 'type': STATE_WARN}

    return SysInfoRes(value=_memory, state=state, human_value=human_value)


def machine_load():
    _load = {'1_min': _NA, '5_min': _NA, '15_min': _NA}

    state = STATE_OK_DEFAULT
    if not psutil:
        return SysInfoRes(value=_load, state=state)

    # load averages
    if hasattr(psutil.os, 'getloadavg'):
        _load = dict(zip(['1_min', '5_min', '15_min'], psutil.os.getloadavg()))

    human_value = '1min: %s, 5min: %s, 15min: %s' % (
    _load['1_min'], _load['5_min'], _load['15_min'])

    # TODO: warn about too-much load 15 min
    return SysInfoRes(value=_load, state=state, human_value=human_value)


def cpu():
    state = STATE_OK_DEFAULT
    cpu_value = 0
    if not psutil:
        return SysInfoRes(value=cpu_value, state=state)

    cpu_value = psutil.cpu_percent(0.5)
    human_value = '{} %'.format(cpu_value)
    return SysInfoRes(value=cpu_value, state=state, human_value=human_value)


def storage():
    from rhodecode.lib.helpers import format_byte_size_binary
    from rhodecode.model.settings import VcsSettingsModel
    path = VcsSettingsModel().get_repos_location()

    # disk storage
    disk = {'percent': 0, 'used': 0, 'total': 0, 'path': path, 'text': ''}
    state = STATE_OK_DEFAULT
    if not psutil:
        return SysInfoRes(value=disk, state=state)

    try:
        disk.update(dict(psutil.disk_usage(path)._asdict()))
    except Exception as e:
        log.exception('Failed to fetch disk info')
        state = {'message': str(e), 'type': STATE_ERR}

    human_value = disk
    human_value['text'] = "{}/{}, {}% used".format(
        format_byte_size_binary(disk['used']),
        format_byte_size_binary(disk['total']),
        (disk['percent']))

    if state['type'] == STATE_OK and disk['percent'] > 90:
        msg = 'Critical: your disk space is very low.'
        state = {'message': msg, 'type': STATE_ERR}

    elif state['type'] == STATE_OK and disk['percent'] > 70:
        msg = 'Warning: your disk space is running low.'
        state = {'message': msg, 'type': STATE_WARN}

    return SysInfoRes(value=disk, state=state, human_value=human_value)


def storage_inodes():
    from rhodecode.model.settings import VcsSettingsModel
    path = VcsSettingsModel().get_repos_location()

    _disk_inodes = dict(percent=0, free=0, used=0, total=0, path=path, text='')
    state = STATE_OK_DEFAULT
    if not psutil:
        return SysInfoRes(value=_disk_inodes, state=state)

    try:
        i_stat = os.statvfs(path)

        _disk_inodes['used'] = i_stat.f_ffree
        _disk_inodes['free'] = i_stat.f_favail
        _disk_inodes['total'] = i_stat.f_files
        _disk_inodes['percent'] = percentage(
            _disk_inodes['used'], _disk_inodes['total'])
    except Exception as e:
        log.exception('Failed to fetch disk inodes info')
        state = {'message': str(e), 'type': STATE_ERR}

    human_value = _disk_inodes
    human_value['text'] = "{}/{}, {}% used".format(
        _disk_inodes['used'], _disk_inodes['total'], _disk_inodes['percent'])

    if state['type'] == STATE_OK and _disk_inodes['percent'] > 90:
        msg = 'Critical: your disk free inodes are very low.'
        state = {'message': msg, 'type': STATE_ERR}

    elif state['type'] == STATE_OK and _disk_inodes['percent'] > 70:
        msg = 'Warning: your disk free inodes are running low.'
        state = {'message': msg, 'type': STATE_WARN}

    return SysInfoRes(value=_disk_inodes, state=state)


def storage_archives():
    import rhodecode
    from rhodecode.lib.utils import safe_str
    from rhodecode.lib.helpers import format_byte_size_binary

    msg = 'Enable this by setting ' \
          'archive_cache_dir=/path/to/cache option in the .ini file'
    path = safe_str(rhodecode.CONFIG.get('archive_cache_dir', msg))

    disk_archive = dict(percent=0, used=0, total=0, items=0, path=path, text='')
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
        disk_archive.update({
            'percent': 100,
            'used': used,
            'total': used,
            'items': items_count
        })

    except Exception as e:
        log.exception('failed to fetch archive cache storage')
        state = {'message': str(e), 'type': STATE_ERR}

    human_value = disk_archive
    human_value['text'] = "{} ({} items)".format(format_byte_size_binary(
        disk_archive['used']), disk_archive['total'])

    return SysInfoRes(value=disk_archive, state=state, human_value=human_value)


def storage_gist():
    from rhodecode.model.gist import GIST_STORE_LOC
    from rhodecode.model.settings import VcsSettingsModel
    from rhodecode.lib.utils import safe_str
    from rhodecode.lib.helpers import format_byte_size_binary
    path = safe_str(os.path.join(
        VcsSettingsModel().get_repos_location(), GIST_STORE_LOC))

    # gist storage
    _disk_gist = dict(percent=0, used=0, total=0, items=0, path=path, text='')
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
        _disk_gist.update({
            'percent': 100,
            'used': used,
            'total': used,
            'items': items_count
        })
    except Exception as e:
        log.exception('failed to fetch gist storage items')
        state = {'message': str(e), 'type': STATE_ERR}

    human_value = _disk_gist
    human_value['text'] = "{} ({} items)".format(format_byte_size_binary(
        _disk_gist['used']), _disk_gist['items'])
    return SysInfoRes(value=_disk_gist, state=state, human_value=human_value)


def storage_search():
    import rhodecode
    path = rhodecode.CONFIG.get('search.location', '')

    # search index storage
    _disk_index = dict(percent=0, used=0, total=0, path=path, text='')
    state = STATE_OK_DEFAULT
    try:
        search_index_storage_path_exists = os.path.isdir(path)
        if search_index_storage_path_exists:
            used = get_storage_size(path)
            _disk_index.update({
                'percent': 100,
                'used': used,
                'total': used,
            })
    except Exception as e:
        log.exception('failed to fetch search index storage')
        state = {'message': str(e), 'type': STATE_ERR}

    human_value = _disk_index
    human_value['text'] = "{}/{}, {}% used".format(
        _disk_index['used'], _disk_index['total'], _disk_index['percent'])

    return SysInfoRes(value=_disk_index, state=state, human_value=human_value)


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
    value = rhodecode.CONFIG.get('vcs.backends', '').split(',')
    human_value = 'Enabled backends in order: {}'.format(','.join(value))
    return SysInfoRes(value=value, human_value=human_value)


def vcs_server():
    import rhodecode
    from rhodecode.lib.vcs.backends import get_vcsserver_version

    server_url = rhodecode.CONFIG.get('vcs.server')
    enabled = rhodecode.CONFIG.get('vcs.server.enable')
    protocol = rhodecode.CONFIG.get('vcs.server.protocol')
    state = STATE_OK_DEFAULT
    version = None

    try:
        version = get_vcsserver_version()
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

    human_value = value
    human_value['text'] = \
        '{url}@ver:{ver} via {mode} mode, connection:{conn}'.format(
            url=server_url, ver=version, mode=protocol, conn=connection)

    return SysInfoRes(value='', state=state, human_value=human_value)


def rhodecode_app_info():
    import rhodecode
    return SysInfoRes(value={'rhodecode_version': rhodecode.__version__})


def rhodecode_config():
    import rhodecode
    path = rhodecode.CONFIG.get('__file__')
    rhodecode_ini_safe = rhodecode.CONFIG.copy()

    blacklist = [
        'rhodecode_license_key',
        'routes.map',
        'pylons.h',
        'pylons.app_globals',
        'pylons.environ_config',
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
    return SysInfoRes(value={'config': rhodecode_ini_safe, 'path': path})


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

    human_value = db_info
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


def get_system_info(environ):
    environ = environ or {}
    return {
        'rhodecode_app': SysInfo(rhodecode_app_info)(),
        'rhodecode_config': SysInfo(rhodecode_config)(),
        'python': SysInfo(python_info)(),
        'py_modules': SysInfo(py_modules)(),

        'platform': SysInfo(platform_type)(),
        'server': SysInfo(server_info, environ=environ)(),
        'database': SysInfo(database_info)(),

        'storage': SysInfo(storage)(),
        'storage_inodes': SysInfo(storage_inodes)(),
        'storage_archive': SysInfo(storage_archives)(),
        'storage_search': SysInfo(storage_search)(),
        'storage_gist': SysInfo(storage_gist)(),

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
