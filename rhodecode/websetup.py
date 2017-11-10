# -*- coding: utf-8 -*-

# Copyright (C) 2010-2017 RhodeCode GmbH
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

from rhodecode.lib.rc_commands.setup_rc import command as setup_command

log = logging.getLogger(__name__)


def setup_app(command, conf, vars):
    opts = command.options.__dict__

    # mapping of old parameters to new CLI from click
    options = dict(
        ini_path=command.args[0],
        force_yes=opts.get('force_ask'),
        user=opts.get('username'),
        email=opts.get('email'),
        password=opts.get('password'),
        api_key=opts.get('api_key'),
        repos=opts.get('repos_location'),
        public_access=opts.get('public_access')
    )
    setup_command(**options)

