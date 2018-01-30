# -*- coding: utf-8 -*-

# Copyright (C) 2010-2018 RhodeCode GmbH
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
import logging

from paste.script.command import Command, BadCommand


class BasePasterCommand(Command):
    """
    Abstract Base Class for paster commands.

    The celery commands are somewhat aggressive about loading
    celery.conf, and since our module sets the `CELERY_LOADER`
    environment variable to our loader, we have to bootstrap a bit and
    make sure we've had a chance to load the pylons config off of the
    command line, otherwise everything fails.
    """
    min_args = 1
    min_args_error = "Please provide a paster config file as an argument."
    takes_config_file = 1
    requires_config_file = True

    def notify_msg(self, msg, log=False):
        """Make a notification to user, additionally if logger is passed
        it logs this action using given logger

        :param msg: message that will be printed to user
        :param log: logging instance, to use to additionally log this message

        """
        if log and isinstance(log, logging):
            log(msg)

    def run(self, args):
        """
        Overrides Command.run

        Checks for a config file argument and loads it.
        """
        if len(args) < self.min_args:
            raise BadCommand(
                self.min_args_error % {'min_args': self.min_args,
                                       'actual_args': len(args)})

        # Decrement because we're going to lob off the first argument.
        # @@ This is hacky
        self.min_args -= 1
        self.bootstrap_config(args[0])
        self.update_parser()
        return super(BasePasterCommand, self).run(args[1:])

    def update_parser(self):
        """
        Abstract method.  Allows for the class' parser to be updated
        before the superclass' `run` method is called.  Necessary to
        allow options/arguments to be passed through to the underlying
        celery command.
        """
        raise NotImplementedError("Abstract Method.")

    def bootstrap_config(self, conf):
        """
        Loads the pylons configuration.
        """
        self.path_to_ini_file = os.path.realpath(conf)

    def _init_session(self):
        """
        Inits SqlAlchemy Session
        """
        logging.config.fileConfig(self.path_to_ini_file)

