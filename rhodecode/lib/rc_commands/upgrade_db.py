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

import click
import pyramid.paster

from rhodecode.lib.pyramid_utils import bootstrap
from rhodecode.lib.db_manage import DbManage

log = logging.getLogger(__name__)


@click.command()
@click.argument('ini_path', type=click.Path(exists=True))
@click.option('--force-yes/--force-no', default=None,
              help="Force yes/no to every question")
def main(ini_path, force_yes):
    return command(ini_path, force_yes)


def command(ini_path, force_yes):
    pyramid.paster.setup_logging(ini_path)

    with bootstrap(ini_path, env={'RC_CMD_UPGRADE_DB': '1'}) as env:
        config = env['registry'].settings
        db_uri = config['sqlalchemy.db1.url']
        options = {}
        if force_yes is not None:
            options['force_ask'] = force_yes
        dbmanage = DbManage(
            log_sql=True, dbconf=db_uri, root='.', tests=False,
            cli_args=options)
        dbmanage.upgrade()
