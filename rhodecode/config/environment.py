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


import os
import logging
import rhodecode

# ------------------------------------------------------------------------------
# CELERY magic until refactor - issue #4163 - import order matters here:
#from rhodecode.lib import celerypylons  # this must be first, celerypylons
                                        # sets config settings upon import

import rhodecode.integrations           # any modules using celery task
                                        # decorators should be added afterwards:
# ------------------------------------------------------------------------------

from rhodecode.config import utils

from rhodecode.lib.utils import load_rcextensions
from rhodecode.lib.utils2 import str2bool
from rhodecode.lib.vcs import connect_vcs, start_vcs_server

log = logging.getLogger(__name__)


def load_pyramid_environment(global_config, settings):
    # Some parts of the code expect a merge of global and app settings.
    settings_merged = global_config.copy()
    settings_merged.update(settings)

    # TODO(marcink): probably not required anymore
    # configure channelstream,
    settings_merged['channelstream_config'] = {
        'enabled': str2bool(settings_merged.get('channelstream.enabled', False)),
        'server': settings_merged.get('channelstream.server'),
        'secret': settings_merged.get('channelstream.secret')
    }


    # TODO(marcink): celery
    # # store some globals into rhodecode
    # rhodecode.CELERY_ENABLED = str2bool(config['app_conf'].get('use_celery'))
    # rhodecode.CELERY_EAGER = str2bool(
    #     config['app_conf'].get('celery.always.eager'))


    # If this is a test run we prepare the test environment like
    # creating a test database, test search index and test repositories.
    # This has to be done before the database connection is initialized.
    if settings['is_test']:
        rhodecode.is_test = True
        rhodecode.disable_error_handler = True

        utils.initialize_test_environment(settings_merged)

    # Initialize the database connection.
    utils.initialize_database(settings_merged)

    load_rcextensions(root_path=settings_merged['here'])

    # Limit backends to `vcs.backends` from configuration
    for alias in rhodecode.BACKENDS.keys():
        if alias not in settings['vcs.backends']:
            del rhodecode.BACKENDS[alias]
    log.info('Enabled VCS backends: %s', rhodecode.BACKENDS.keys())

    # initialize vcs client and optionally run the server if enabled
    vcs_server_uri = settings['vcs.server']
    vcs_server_enabled = settings['vcs.server.enable']
    start_server = (
        settings['vcs.start_server'] and
        not int(os.environ.get('RC_VCSSERVER_TEST_DISABLE', '0')))

    if vcs_server_enabled and start_server:
        log.info("Starting vcsserver")
        start_vcs_server(server_and_port=vcs_server_uri,
                         protocol=utils.get_vcs_server_protocol(settings),
                         log_level=settings['vcs.server.log_level'])

    utils.configure_vcs(settings)

    # Store the settings to make them available to other modules.

    rhodecode.PYRAMID_SETTINGS = settings_merged
    rhodecode.CONFIG = settings_merged

    if vcs_server_enabled:
        connect_vcs(vcs_server_uri, utils.get_vcs_server_protocol(settings))
