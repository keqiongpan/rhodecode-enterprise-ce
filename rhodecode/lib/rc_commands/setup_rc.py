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
import logging

import click
import pyramid.paster

from rhodecode.lib.pyramid_utils import bootstrap, get_app_config
from rhodecode.lib.db_manage import DbManage
from rhodecode.model.db import Session


log = logging.getLogger(__name__)


@click.command()
@click.argument('ini_path', type=click.Path(exists=True))
@click.option(
    '--force-yes/--force-no', default=None,
    help="Force yes/no to every question")
@click.option(
    '--user',
    default=None,
    help='Initial super-admin username')
@click.option(
    '--email',
    default=None,
    help='Initial super-admin email address.')
@click.option(
    '--password',
    default=None,
    help='Initial super-admin password. Minimum 6 chars.')
@click.option(
    '--api-key',
    help='Initial API key for the admin user')
@click.option(
    '--repos',
    default=None,
    help='Absolute path to storage location. This is storage for all '
         'existing and future repositories, and repository groups.')
@click.option(
    '--public-access/--no-public-access',
    default=None,
    help='Enable public access on this installation. '
         'Default is public access enabled.')
def main(ini_path, force_yes, user, email, password, api_key, repos,
         public_access):
    return command(ini_path, force_yes, user, email, password, api_key,
                   repos, public_access)


def command(ini_path, force_yes, user, email, password, api_key, repos,
            public_access):
    # mapping of old parameters to new CLI from click
    options = dict(
        username=user,
        email=email,
        password=password,
        api_key=api_key,
        repos_location=repos,
        force_ask=force_yes,
        public_access=public_access
    )
    pyramid.paster.setup_logging(ini_path)

    config = get_app_config(ini_path)

    db_uri = config['sqlalchemy.db1.url']
    dbmanage = DbManage(log_sql=True, dbconf=db_uri, root='.',
                        tests=False, cli_args=options)
    dbmanage.create_tables(override=True)
    dbmanage.set_db_version()
    opts = dbmanage.config_prompt(None)
    dbmanage.create_settings(opts)
    dbmanage.create_default_user()
    dbmanage.create_admin_and_prompt()
    dbmanage.create_permissions()
    dbmanage.populate_default_permissions()
    Session().commit()

    with bootstrap(ini_path, env={'RC_CMD_SETUP_RC': '1'}) as env:
        msg = 'Successfully initialized database, schema and default data.'
        print()
        print('*' * len(msg))
        print(msg.upper())
        print('*' * len(msg))
