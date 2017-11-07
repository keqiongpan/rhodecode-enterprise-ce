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

"""
Pylons environment configuration
"""

import os
import logging
import rhodecode

from mako.lookup import TemplateLookup
from pyramid.settings import asbool

# ------------------------------------------------------------------------------
# CELERY magic until refactor - issue #4163 - import order matters here:
from rhodecode.lib import celerypylons  # this must be first, celerypylons
                                        # sets config settings upon import

import rhodecode.integrations           # any modules using celery task
                                        # decorators should be added afterwards:
# ------------------------------------------------------------------------------

from rhodecode.lib import app_globals
from rhodecode.config import utils
from rhodecode.config.routing import make_map

from rhodecode.lib import helpers
from rhodecode.lib.utils import (
    make_db_config, set_rhodecode_config, load_rcextensions)
from rhodecode.lib.utils2 import str2bool, aslist
from rhodecode.lib.vcs import connect_vcs, start_vcs_server

log = logging.getLogger(__name__)


def load_environment(global_conf, app_conf, initial=False,
                     test_env=None, test_index=None):
    """
    Configure the Pylons environment via the ``pylons.config``
    object
    """
    from pylons.configuration import PylonsConfig
    from pylons.error import handle_mako_error

    config = PylonsConfig()


    # Pylons paths
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    paths = {
        'root': root,
        'controllers': os.path.join(root, 'controllers'),
        'static_files': os.path.join(root, 'public'),
        'templates': [os.path.join(root, 'templates')],
    }

    # Initialize config with the basic options
    config.init_app(global_conf, app_conf, package='rhodecode', paths=paths)

    # store some globals into rhodecode
    rhodecode.CELERY_ENABLED = str2bool(config['app_conf'].get('use_celery'))
    rhodecode.CELERY_EAGER = str2bool(
        config['app_conf'].get('celery.always.eager'))

    config['routes.map'] = make_map(config)

    config['pylons.app_globals'] = app_globals.Globals(config)
    config['pylons.h'] = helpers
    rhodecode.CONFIG = config

    load_rcextensions(root_path=config['here'])

    # Setup cache object as early as possible
    import pylons
    pylons.cache._push_object(config['pylons.app_globals'].cache)

    # Create the Mako TemplateLookup, with the default auto-escaping
    config['pylons.app_globals'].mako_lookup = TemplateLookup(
        directories=paths['templates'],
        error_handler=handle_mako_error,
        module_directory=os.path.join(app_conf['cache_dir'], 'templates'),
        input_encoding='utf-8', default_filters=['escape'],
        imports=['from webhelpers.html import escape'])

    # sets the c attribute access when don't existing attribute are accessed
    config['pylons.strict_tmpl_context'] = True

    # configure channelstream
    config['channelstream_config'] = {
        'enabled': asbool(config.get('channelstream.enabled', False)),
        'server': config.get('channelstream.server'),
        'secret': config.get('channelstream.secret')
    }

    db_cfg = make_db_config(clear_session=True)

    repos_path = list(db_cfg.items('paths'))[0][1]
    config['base_path'] = repos_path

    # store db config also in main global CONFIG
    set_rhodecode_config(config)

    # configure instance id
    utils.set_instance_id(config)

    # CONFIGURATION OPTIONS HERE (note: all config options will override
    # any Pylons config options)

    # store config reference into our module to skip import magic of pylons
    rhodecode.CONFIG.update(config)

    return config


def load_pyramid_environment(global_config, settings):
    # Some parts of the code expect a merge of global and app settings.
    settings_merged = global_config.copy()
    settings_merged.update(settings)

    # Store the settings to make them available to other modules.
    rhodecode.PYRAMID_SETTINGS = settings_merged
    # NOTE(marcink): needs to be enabled after full port to pyramid
    # rhodecode.CONFIG = config

    # If this is a test run we prepare the test environment like
    # creating a test database, test search index and test repositories.
    # This has to be done before the database connection is initialized.
    if settings['is_test']:
        rhodecode.is_test = True
        rhodecode.disable_error_handler = True

        utils.initialize_test_environment(settings_merged)

    # Initialize the database connection.
    utils.initialize_database(settings_merged)

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

    if vcs_server_enabled:
        connect_vcs(vcs_server_uri, utils.get_vcs_server_protocol(settings))
