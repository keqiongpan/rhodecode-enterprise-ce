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
import threading
import traceback


# GLOBAL
errorlog = '-'
accesslog = '-'
loglevel = 'debug'

# SECURITY
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190

# SERVER MECHANICS
# None == system temp dir
worker_tmp_dir = None
tmp_upload_dir = None

# Custom log format
access_log_format = (
    '%(t)s GNCRN %(p)-8s %(h)-15s rqt:%(L)s %(s)s %(b)s "%(m)s:%(U)s %(q)s" usr:%(u)s "%(f)s" "%(a)s"')

# self adjust workers based on CPU count
# workers = multiprocessing.cpu_count() * 2 + 1


def post_fork(server, worker):
    server.log.info("[<%-10s>] WORKER spawned", worker.pid)


def pre_fork(server, worker):
    pass


def pre_exec(server):
    server.log.info("Forked child, re-executing.")


def when_ready(server):
    server.log.info("Server is ready. Spawning workers")


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


def pre_request(worker, req):
    return
    worker.log.debug("[<%-10s>] PRE WORKER: %s %s",
                     worker.pid, req.method, req.path)


def post_request(worker, req, environ, resp):
    return
    worker.log.debug("[<%-10s>] POST WORKER: %s %s resp: %s", worker.pid,
                     req.method, req.path, resp.status_code)