# -*- coding: utf-8 -*-

# Copyright (C) 2016-2017 RhodeCode GmbH
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

"""
interactive shell for pyramid
"""

import os
import sys
import logging

# fix rhodecode import
from os.path import dirname as dn
rc_path = dn(dn(dn(os.path.realpath(__file__))))
sys.path.append(rc_path)

log = logging.getLogger(__name__)

welcome_banner = """Welcome to RhodeCode iShell.\n
Type `exit` to exit the shell.
iShell is interactive shell to interact directly with the
internal RhodeCode APIs. You can rescue your lost password,
or reset some user/system settings.
"""


def ipython_shell_runner(env, help):

    # imports, used in ipython shell
    import os
    import sys
    import time
    import shutil
    import datetime
    from rhodecode.model import user, user_group, repo, repo_group
    from rhodecode.model.db import *

    try:
        import IPython
        from traitlets.config import Config

        cfg = Config()
        cfg.InteractiveShellEmbed.confirm_exit = False
        cfg.TerminalInteractiveShell.banner2 = \
            welcome_banner + '\n' + help + '\n'
        IPython.start_ipython(argv=[], user_ns=env, config=cfg)

    except ImportError:
        print('ipython installation required for ishell')
        sys.exit(-1)
