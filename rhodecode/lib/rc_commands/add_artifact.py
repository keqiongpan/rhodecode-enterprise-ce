# -*- coding: utf-8 -*-

# Copyright (C) 2016-2020 RhodeCode GmbH
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

import sys
import logging

import click

from rhodecode.lib.pyramid_utils import bootstrap
from rhodecode.model.db import Session, User, Repository
from rhodecode.model.user import UserModel
from rhodecode.apps.file_store import utils as store_utils

log = logging.getLogger(__name__)


@click.command()
@click.argument('ini_path', type=click.Path(exists=True))
@click.option(
    '--filename',
    required=True,
    help='Filename for artifact.')
@click.option(
    '--file-path',
    required=True,
    type=click.Path(exists=True, dir_okay=False, readable=True),
    help='Path to a file to be added as artifact')
@click.option(
    '--repo-id',
    required=True,
    type=int,
    help='ID of repository to add this artifact to.')
@click.option(
    '--user-id',
    default=None,
    type=int,
    help='User ID for creator of artifact. '
         'Default would be first super admin.')
@click.option(
    '--description',
    default=None,
    type=str,
    help='Add description to this artifact')
def main(ini_path, filename, file_path, repo_id, user_id, description):
    return command(ini_path, filename, file_path, repo_id, user_id, description)


def command(ini_path, filename, file_path, repo_id, user_id, description):
    with bootstrap(ini_path, env={'RC_CMD_SETUP_RC': '1'}) as env:
        try:
            from rc_ee.api.views.store_api import _store_file
        except ImportError:
            click.secho('ERROR: Unable to import store_api. '
                        'store_api is only available in EE edition of RhodeCode',
                        fg='red')
            sys.exit(-1)

        request = env['request']

        repo = Repository.get(repo_id)
        if not repo:
            click.secho('ERROR: Unable to find repository with id `{}`'.format(repo_id),
                        fg='red')
            sys.exit(-1)

        # if we don't give user, or it's "DEFAULT" user we pick super-admin
        if user_id is not None or user_id == 1:
            db_user = User.get(user_id)
        else:
            db_user = User.get_first_super_admin()

        if not db_user:
            click.secho('ERROR: Unable to find user with id/username `{}`'.format(user_id),
                        fg='red')
            sys.exit(-1)

        auth_user = db_user.AuthUser(ip_addr='127.0.0.1')

        storage = store_utils.get_file_storage(request.registry.settings)

        with open(file_path, 'rb') as f:
            click.secho('Adding new artifact from path: `{}`'.format(file_path),
                        fg='green')

            file_data = _store_file(
                storage, auth_user, filename, content=None, check_acl=True,
                file_obj=f, description=description,
                scope_repo_id=repo.repo_id)
            click.secho('File Data: {}'.format(file_data),
                        fg='green')
