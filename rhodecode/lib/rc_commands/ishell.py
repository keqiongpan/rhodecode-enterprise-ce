# -*- coding: utf-8 -*-

# Copyright (C) 2016-2019 RhodeCode GmbH
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

import click

from rhodecode.lib.pyramid_utils import bootstrap
import pyramid.paster

# imports, used in ipython shell
import os
import sys
import time
import shutil
import datetime
from rhodecode.model.db import *

welcome_banner = """Welcome to RhodeCode iShell.
Type `exit` to exit the shell.
iShell is interactive shell to interact directly with the
internal RhodeCode APIs. You can rescue your lost password,
or reset some user/system settings.
"""


@click.command()
@click.argument('ini_path', type=click.Path(exists=True))
def main(ini_path):
    pyramid.paster.setup_logging(ini_path)

    with bootstrap(ini_path) as env:

        try:
            from IPython import embed
            from traitlets.config import Config
            cfg = Config()
            cfg.InteractiveShellEmbed.confirm_exit = False
            embed(config=cfg, banner1=welcome_banner)
        except ImportError:
            print('ipython installation required for ishell')
            sys.exit(-1)


