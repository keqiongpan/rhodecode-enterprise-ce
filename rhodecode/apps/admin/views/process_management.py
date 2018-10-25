# -*- coding: utf-8 -*-

# Copyright (C) 2016-2018 RhodeCode GmbH
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

import logging

import psutil
import signal
from pyramid.view import view_config

from rhodecode.apps._base import BaseAppView
from rhodecode.apps.admin.navigation import navigation_list
from rhodecode.lib import system_info
from rhodecode.lib.auth import (
    LoginRequired, HasPermissionAllDecorator, CSRFRequired)
from rhodecode.lib.utils2 import safe_int, StrictAttributeDict

log = logging.getLogger(__name__)


class AdminProcessManagementView(BaseAppView):
    def load_default_context(self):
        c = self._get_local_tmpl_context()
        return c

    def _format_proc(self, proc, with_children=False):
        try:
            mem = proc.memory_info()
            proc_formatted = StrictAttributeDict({
                'pid': proc.pid,
                'name': proc.name(),
                'mem_rss': mem.rss,
                'mem_vms': mem.vms,
                'cpu_percent': proc.cpu_percent(),
                'create_time': proc.create_time(),
                'cmd': ' '.join(proc.cmdline()),
            })

            if with_children:
                proc_formatted.update({
                    'children': [self._format_proc(x)
                                 for x in proc.children(recursive=True)]
                })
        except Exception:
            log.exception('Failed to load proc')
            proc_formatted = None
        return proc_formatted

    def get_processes(self):
        proc_list = []
        for p in psutil.process_iter():
            if 'gunicorn' in p.name():
                proc = self._format_proc(p, with_children=True)
                if proc:
                    proc_list.append(proc)

        return proc_list

    def get_workers(self):
        workers = None
        try:
            rc_config = system_info.rhodecode_config().value['config']
            workers = rc_config['server:main'].get('workers')
        except Exception:
            pass

        return workers or '?'

    @LoginRequired()
    @HasPermissionAllDecorator('hg.admin')
    @view_config(
        route_name='admin_settings_process_management', request_method='GET',
        renderer='rhodecode:templates/admin/settings/settings.mako')
    def process_management(self):
        _ = self.request.translate
        c = self.load_default_context()

        c.active = 'process_management'
        c.navlist = navigation_list(self.request)
        c.gunicorn_processes = self.get_processes()
        c.gunicorn_workers = self.get_workers()
        return self._get_template_context(c)

    @LoginRequired()
    @HasPermissionAllDecorator('hg.admin')
    @view_config(
        route_name='admin_settings_process_management_data', request_method='GET',
        renderer='rhodecode:templates/admin/settings/settings_process_management_data.mako')
    def process_management_data(self):
        _ = self.request.translate
        c = self.load_default_context()
        c.gunicorn_processes = self.get_processes()
        return self._get_template_context(c)

    @LoginRequired()
    @HasPermissionAllDecorator('hg.admin')
    @CSRFRequired()
    @view_config(
        route_name='admin_settings_process_management_signal',
        request_method='POST', renderer='json_ext')
    def process_management_signal(self):
        pids = self.request.json.get('pids', [])
        result = []

        def on_terminate(proc):
            msg = "process `PID:{}` terminated with exit code {}".format(
                proc.pid, proc.returncode or 0)
            result.append(msg)

        procs = []
        for pid in pids:
            pid = safe_int(pid)
            if pid:
                try:
                    proc = psutil.Process(pid)
                except psutil.NoSuchProcess:
                    continue

                children = proc.children(recursive=True)
                if children:
                    log.warning('Wont kill Master Process')
                else:
                    procs.append(proc)

        for p in procs:
            try:
                p.terminate()
            except psutil.AccessDenied as e:
                log.warning('Access denied: {}'.format(e))

        gone, alive = psutil.wait_procs(procs, timeout=10, callback=on_terminate)
        for p in alive:
            try:
                p.kill()
            except psutil.AccessDenied as e:
                log.warning('Access denied: {}'.format(e))

        return {'result': result}

    @LoginRequired()
    @HasPermissionAllDecorator('hg.admin')
    @CSRFRequired()
    @view_config(
        route_name='admin_settings_process_management_master_signal',
        request_method='POST', renderer='json_ext')
    def process_management_master_signal(self):
        pid_data = self.request.json.get('pid_data', {})
        pid = safe_int(pid_data['pid'])
        action = pid_data['action']
        if pid:
            try:
                proc = psutil.Process(pid)
            except psutil.NoSuchProcess:
                return {'result': 'failure_no_such_process'}

            children = proc.children(recursive=True)
            if children:
                # master process
                if action == '+' and len(children) <= 20:
                    proc.send_signal(signal.SIGTTIN)
                elif action == '-' and len(children) >= 2:
                    proc.send_signal(signal.SIGTTOU)
                else:
                    return {'result': 'failure_wrong_action'}
                return {'result': 'success'}

        return {'result': 'failure_not_master'}
