"""
gunicorn config extension and hooks. Sets additional configuration that is
available post the .ini config.

- workers = ${cpu_number}
- threads = 1
- proc_name = ${gunicorn_proc_name}
- worker_class = sync
- worker_connections = 10
- max_requests = 1000
- max_requests_jitter = 30
- timeout = 21600

"""

import gc
import os
import sys
import math
import time
import threading
import traceback
import random
from gunicorn.glogging import Logger


def get_workers():
    import multiprocessing
    return multiprocessing.cpu_count() * 2 + 1

# GLOBAL
errorlog = '-'
accesslog = '-'
loglevel = 'info'


# SERVER MECHANICS
# None == system temp dir
# worker_tmp_dir is recommended to be set to some tmpfs
worker_tmp_dir = None
tmp_upload_dir = None

# Custom log format
access_log_format = (
    '%(t)s %(p)s INFO  [GNCRN] %(h)-15s rqt:%(L)s %(s)s %(b)-6s "%(m)s:%(U)s %(q)s" usr:%(u)s "%(f)s" "%(a)s"')

# self adjust workers based on CPU count
# workers = get_workers()


def _get_process_rss(pid=None):
    try:
        import psutil
        if pid:
            proc = psutil.Process(pid)
        else:
            proc = psutil.Process()
        return proc.memory_info().rss
    except Exception:
        return None


def _get_config(ini_path):

    try:
        import configparser
    except ImportError:
        import ConfigParser as configparser
    try:
        config = configparser.ConfigParser()
        config.read(ini_path)
        return config
    except Exception:
        return None


def _time_with_offset(memory_usage_check_interval):
    return time.time() - random.randint(0, memory_usage_check_interval/2.0)


def pre_fork(server, worker):
    pass


def post_fork(server, worker):

    # memory spec defaults
    _memory_max_usage = 0
    _memory_usage_check_interval = 60
    _memory_usage_recovery_threshold = 0.8

    ini_path = os.path.abspath(server.cfg.paste)
    conf = _get_config(ini_path)
    if conf and 'server:main' in conf:
        section = conf['server:main']

        if section.get('memory_max_usage'):
            _memory_max_usage = int(section.get('memory_max_usage'))
        if section.get('memory_usage_check_interval'):
            _memory_usage_check_interval = int(section.get('memory_usage_check_interval'))
        if section.get('memory_usage_recovery_threshold'):
            _memory_usage_recovery_threshold = float(section.get('memory_usage_recovery_threshold'))

    worker._memory_max_usage = _memory_max_usage
    worker._memory_usage_check_interval = _memory_usage_check_interval
    worker._memory_usage_recovery_threshold = _memory_usage_recovery_threshold

    # register memory last check time, with some random offset so we don't recycle all
    # at once
    worker._last_memory_check_time = _time_with_offset(_memory_usage_check_interval)

    if _memory_max_usage:
        server.log.info("[%-10s] WORKER spawned with max memory set at %s", worker.pid,
                        _format_data_size(_memory_max_usage))
    else:
        server.log.info("[%-10s] WORKER spawned", worker.pid)


def pre_exec(server):
    server.log.info("Forked child, re-executing.")


def on_starting(server):
    server_lbl = '{} {}'.format(server.proc_name, server.address)
    server.log.info("Server %s is starting.", server_lbl)


def when_ready(server):
    server.log.info("Server %s is ready. Spawning workers", server)


def on_reload(server):
    pass


def _format_data_size(size, unit="B", precision=1, binary=True):
    """Format a number using SI units (kilo, mega, etc.).

    ``size``: The number as a float or int.

    ``unit``: The unit name in plural form. Examples: "bytes", "B".

    ``precision``: How many digits to the right of the decimal point. Default
    is 1.  0 suppresses the decimal point.

    ``binary``: If false, use base-10 decimal prefixes (kilo = K = 1000).
    If true, use base-2 binary prefixes (kibi = Ki = 1024).

    ``full_name``: If false (default), use the prefix abbreviation ("k" or
    "Ki").  If true, use the full prefix ("kilo" or "kibi"). If false,
    use abbreviation ("k" or "Ki").

    """

    if not binary:
        base = 1000
        multiples = ('', 'k', 'M', 'G', 'T', 'P', 'E', 'Z', 'Y')
    else:
        base = 1024
        multiples = ('', 'Ki', 'Mi', 'Gi', 'Ti', 'Pi', 'Ei', 'Zi', 'Yi')

    sign = ""
    if size > 0:
        m = int(math.log(size, base))
    elif size < 0:
        sign = "-"
        size = -size
        m = int(math.log(size, base))
    else:
        m = 0
    if m > 8:
        m = 8

    if m == 0:
        precision = '%.0f'
    else:
        precision = '%%.%df' % precision

    size = precision % (size / math.pow(base, m))

    return '%s%s %s%s' % (sign, size.strip(), multiples[m], unit)


def _check_memory_usage(worker):
    memory_max_usage = worker._memory_max_usage
    if not memory_max_usage:
        return

    memory_usage_check_interval = worker._memory_usage_check_interval
    memory_usage_recovery_threshold = memory_max_usage * worker._memory_usage_recovery_threshold

    elapsed = time.time() - worker._last_memory_check_time
    if elapsed > memory_usage_check_interval:
        mem_usage = _get_process_rss()
        if mem_usage and mem_usage > memory_max_usage:
            worker.log.info(
                "memory usage %s > %s, forcing gc",
                _format_data_size(mem_usage), _format_data_size(memory_max_usage))
            # Try to clean it up by forcing a full collection.
            gc.collect()
            mem_usage = _get_process_rss()
            if mem_usage > memory_usage_recovery_threshold:
                # Didn't clean up enough, we'll have to terminate.
                worker.log.warning(
                    "memory usage %s > %s after gc, quitting",
                    _format_data_size(mem_usage), _format_data_size(memory_max_usage))
                # This will cause worker to auto-restart itself
                worker.alive = False
        worker._last_memory_check_time = time.time()


def worker_int(worker):
    worker.log.info("[%-10s] worker received INT or QUIT signal", worker.pid)

    # get traceback info, on worker crash
    id2name = dict([(th.ident, th.name) for th in threading.enumerate()])
    code = []
    for thread_id, stack in sys._current_frames().items():
        code.append(
            "\n# Thread: %s(%d)" % (id2name.get(thread_id, ""), thread_id))
        for fname, lineno, name, line in traceback.extract_stack(stack):
            code.append('File: "%s", line %d, in %s' % (fname, lineno, name))
            if line:
                code.append("  %s" % (line.strip()))
    worker.log.debug("\n".join(code))


def worker_abort(worker):
    worker.log.info("[%-10s] worker received SIGABRT signal", worker.pid)


def worker_exit(server, worker):
    worker.log.info("[%-10s] worker exit", worker.pid)


def child_exit(server, worker):
    worker.log.info("[%-10s] worker child exit", worker.pid)


def pre_request(worker, req):
    worker.start_time = time.time()
    worker.log.debug(
        "GNCRN PRE  WORKER [cnt:%s]: %s %s", worker.nr, req.method, req.path)


def post_request(worker, req, environ, resp):
    total_time = time.time() - worker.start_time
    worker.log.debug(
        "GNCRN POST WORKER [cnt:%s]: %s %s resp: %s, Load Time: %.4fs",
        worker.nr, req.method, req.path, resp.status_code, total_time)
    _check_memory_usage(worker)


class RhodeCodeLogger(Logger):
    """
    Custom Logger that allows some customization that gunicorn doesn't allow
    """

    datefmt = r"%Y-%m-%d %H:%M:%S"

    def __init__(self, cfg):
        Logger.__init__(self, cfg)

    def now(self):
        """ return date in RhodeCode Log format """
        now = time.time()
        msecs = int((now - long(now)) * 1000)
        return time.strftime(self.datefmt, time.localtime(now)) + '.{0:03d}'.format(msecs)


logger_class = RhodeCodeLogger
