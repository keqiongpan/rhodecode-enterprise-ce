# -*- coding: utf-8 -*-

# Copyright (C) 2016-2016  RhodeCode GmbH
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
import subprocess32
from threading import Thread


from .utils import generate_mod_dav_svn_config


log = logging.getLogger(__name__)


def generate_config_subscriber(event):
    """
    Subscriber to the `rhodcode.events.RepoGroupEvent`. This triggers the
    automatic generation of mod_dav_svn config file on repository group
    changes.
    """
    try:
        generate_mod_dav_svn_config(event.request.registry)
    except Exception:
        log.exception(
            'Exception while generating subversion mod_dav_svn configuration.')


class Subscriber(object):
    def __call__(self, event):
        self.run(event)

    def run(self, event):
        raise NotImplementedError('Subclass has to implement this.')


class AsyncSubscriber(Subscriber):
    def __init__(self, *args, **kwargs):
        self._init_args = args
        self._init_kwargs = kwargs

    def __call__(self, event):
        kwargs = {'event': event}
        kwargs.update(self._init_kwargs)
        self.thread = Thread(
            target=self.run, args=self._init_args, kwargs=kwargs)
        self.thread.start()


class AsyncSubprocessSubscriber(AsyncSubscriber):
    def run(self, event, cmd, timeout=None):
        log.debug('Executing command %s.', cmd)
        try:
            output = subprocess32.check_output(
                cmd, timeout=timeout, stderr=subprocess32.STDOUT)
            log.debug('Command finished %s', cmd)
            if output:
                log.debug('Command output: %s', output)
        except subprocess32.TimeoutExpired as e:
            log.exception('Timeout while executing command.')
            if e.output:
                log.error('Command output: %s', e.output)
        except subprocess32.CalledProcessError as e:
            log.exception('Error while executing command.')
            if e.output:
                log.error('Command output: %s', e.output)
        except:
            log.exception(
                'Exception while executing command %s.', cmd)


# class ReloadApacheSubscriber(object):
#     """
#     Subscriber to pyramids event system. It executes the Apache reload command
#     if set in ini-file. The command is executed asynchronously in a separate
#     task. This is done to prevent a delay of the function which triggered the
#     event in case of a longer running command. If a timeout is passed to the
#     constructor the command will be terminated after expiration.
#     """
#     def __init__(self, settings, timeout=None):
#         self.thread = None
#         cmd = self.get_command_from_settings(settings)
#         if cmd:
#             kwargs = {
#                 'cmd': cmd,
#                 'timeout': timeout,
#             }
#             self.thread = Thread(target=self.run, kwargs=kwargs)

#     def __call__(self, event):
#         if self.thread is not None:
#             self.thread.start()

#     def get_command_from_settings(self, settings):
#         cmd = settings[config_keys.reload_command]
#         return cmd.split(' ') if cmd else cmd

#     def run(self, cmd, timeout=None):
#         log.debug('Executing svn proxy reload command %s.', cmd)
#         try:
#             output = subprocess32.check_output(
#                 cmd, timeout=timeout, stderr=subprocess32.STDOUT)
#             log.debug('Svn proxy reload command finished.')
#             if output:
#                 log.debug('Command output: %s', output)
#         except subprocess32.TimeoutExpired as e:
#             log.exception('Timeout while executing svn proxy reload command.')
#             if e.output:
#                 log.error('Command output: %s', e.output)
#         except subprocess32.CalledProcessError as e:
#             log.exception('Error while executing svn proxy reload command.')
#             if e.output:
#                 log.error('Command output: %s', e.output)
#         except:
#             log.exception(
#                 'Exception while executing svn proxy reload command %s.', cmd)
