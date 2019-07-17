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

import multiprocessing
import sys
import time
import datetime
import threading
import traceback
from gunicorn.glogging import Logger


# GLOBAL
errorlog = '-'
accesslog = '-'
loglevel = 'debug'

# SECURITY

# The maximum size of HTTP request line in bytes.
# 0 for unlimited
limit_request_line = 0

# Limit the number of HTTP headers fields in a request.
# By default this value is 100 and can’t be larger than 32768.
limit_request_fields = 10240

# Limit the allowed size of an HTTP request header field.
# Value is a positive number or 0.
# Setting it to 0 will allow unlimited header field sizes.
limit_request_field_size = 0


# Timeout for graceful workers restart.
# After receiving a restart signal, workers have this much time to finish
# serving requests. Workers still alive after the timeout (starting from the
# receipt of the restart signal) are force killed.
graceful_timeout = 30


# The number of seconds to wait for requests on a Keep-Alive connection.
# Generally set in the 1-5 seconds range.
keepalive = 2


# SERVER MECHANICS
# None == system temp dir
# worker_tmp_dir is recommended to be set to some tmpfs
worker_tmp_dir = None
tmp_upload_dir = None

# Custom log format
access_log_format = (
    '%(t)s [%(p)-8s] GNCRN %(h)-15s rqt:%(L)s %(s)s %(b)-6s "%(m)s:%(U)s %(q)s" usr:%(u)s "%(f)s" "%(a)s"')

# self adjust workers based on CPU count
# workers = multiprocessing.cpu_count() * 2 + 1


def post_fork(server, worker):
    server.log.info("[<%-10s>] WORKER spawned", worker.pid)


def pre_fork(server, worker):
    pass


def pre_exec(server):
    server.log.info("Forked child, re-executing.")


def on_starting(server):
    server.log.info("Server is starting.")


def when_ready(server):
    server.log.info("Server is ready. Spawning workers")


def on_reload(server):
    pass


def worker_int(worker):
    worker.log.info("[<%-10s>] worker received INT or QUIT signal", worker.pid)

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
    worker.log.info("[<%-10s>] worker received SIGABRT signal", worker.pid)


def worker_exit(server, worker):
    worker.log.info("[<%-10s>] worker exit", worker.pid)


def child_exit(server, worker):
    worker.log.info("[<%-10s>] worker child exit", worker.pid)


def pre_request(worker, req):
    worker.start_time = time.time()
    worker.log.debug(
        "GNCRN PRE  WORKER [cnt:%s]: %s %s", worker.nr, req.method, req.path)


def post_request(worker, req, environ, resp):
    total_time = time.time() - worker.start_time
    worker.log.debug(
        "GNCRN POST WORKER [cnt:%s]: %s %s resp: %s, Load Time: %.4fs",
        worker.nr, req.method, req.path, resp.status_code, total_time)


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
