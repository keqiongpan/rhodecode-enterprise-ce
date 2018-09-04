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

# Import early to make sure things are patched up properly
from setuptools import setup, find_packages

import os
import sys
import pkgutil
import platform
import codecs

try:  # for pip >= 10
    from pip._internal.req import parse_requirements
except ImportError:  # for pip <= 9.0.3
    from pip.req import parse_requirements

try:  # for pip >= 10
    from pip._internal.download import PipSession
except ImportError:  # for pip <= 9.0.3
    from pip.download import PipSession


if sys.version_info < (2, 7):
    raise Exception('RhodeCode requires Python 2.7 or later')

here = os.path.abspath(os.path.dirname(__file__))

# defines current platform
__platform__ = platform.system()
__license__ = 'AGPLv3, and Commercial License'
__author__ = 'RhodeCode GmbH'
__url__ = 'https://code.rhodecode.com'
is_windows = __platform__ in ('Windows',)


def _get_requirements(req_filename, exclude=None, extras=None):
    extras = extras or []
    exclude = exclude or []

    try:
        parsed = parse_requirements(
            os.path.join(here, req_filename), session=PipSession())
    except TypeError:
        # try pip < 6.0.0, that doesn't support session
        parsed = parse_requirements(os.path.join(here, req_filename))

    requirements = []
    for ir in parsed:
        if ir.req and ir.name not in exclude:
            requirements.append(str(ir.req))
    return requirements + extras


# requirements extract
setup_requirements = ['PasteScript', 'pytest-runner']
install_requirements = _get_requirements(
    'requirements.txt', exclude=['setuptools', 'entrypoints'])
test_requirements = _get_requirements(
    'requirements_test.txt', extras=['configobj'])


def get_version():
    version = pkgutil.get_data('rhodecode', 'VERSION')
    return version.strip()


# additional files that goes into package itself
package_data = {
    '': ['*.txt', '*.rst'],
    'configs': ['*.ini'],
    'rhodecode': ['VERSION', 'i18n/*/LC_MESSAGES/*.mo', ],
}

description = 'Source Code Management Platform'
keywords = ' '.join([
    'rhodecode', 'mercurial', 'git', 'svn',
    'code review',
    'repo groups', 'ldap', 'repository management', 'hgweb',
    'hgwebdir', 'gitweb', 'serving hgweb',
])


# README/DESCRIPTION generation
readme_file = 'README.rst'
changelog_file = 'CHANGES.rst'
try:
    long_description = codecs.open(readme_file).read() + '\n\n' + \
                       codecs.open(changelog_file).read()
except IOError as err:
    sys.stderr.write(
        "[WARNING] Cannot find file specified as long_description (%s)\n "
        "or changelog (%s) skipping that file" % (readme_file, changelog_file))
    long_description = description


setup(
    name='rhodecode-enterprise-ce',
    version=get_version(),
    description=description,
    long_description=long_description,
    keywords=keywords,
    license=__license__,
    author=__author__,
    author_email='support@rhodecode.com',
    url=__url__,
    setup_requires=setup_requirements,
    install_requires=install_requirements,
    tests_require=test_requirements,
    zip_safe=False,
    packages=find_packages(exclude=["docs", "tests*"]),
    package_data=package_data,
    include_package_data=True,
    classifiers=[
        'Development Status :: 6 - Mature',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'Topic :: Software Development :: Version Control',
        'License :: OSI Approved :: Affero GNU General Public License v3 or later (AGPLv3+)',
        'Programming Language :: Python :: 2.7',
    ],
    message_extractors={
        'rhodecode': [
            ('**.py', 'python', None),
            ('**.js', 'javascript', None),
            ('templates/**.mako', 'mako', {'input_encoding': 'utf-8'}),
            ('templates/**.html', 'mako', {'input_encoding': 'utf-8'}),
            ('public/**', 'ignore', None),
        ]
    },
    paster_plugins=['PasteScript'],
    entry_points={
        'enterprise.plugins1': [
            'crowd=rhodecode.authentication.plugins.auth_crowd:plugin_factory',
            'headers=rhodecode.authentication.plugins.auth_headers:plugin_factory',
            'jasig_cas=rhodecode.authentication.plugins.auth_jasig_cas:plugin_factory',
            'ldap=rhodecode.authentication.plugins.auth_ldap:plugin_factory',
            'pam=rhodecode.authentication.plugins.auth_pam:plugin_factory',
            'rhodecode=rhodecode.authentication.plugins.auth_rhodecode:plugin_factory',
            'token=rhodecode.authentication.plugins.auth_token:plugin_factory',
        ],
        'paste.app_factory': [
            'main=rhodecode.config.middleware:make_pyramid_app',
        ],
        'paste.global_paster_command': [
            'ishell=rhodecode.lib.paster_commands.ishell:Command',
            'upgrade-db=rhodecode.lib.paster_commands.upgrade_db:UpgradeDb',

            'setup-rhodecode=rhodecode.lib.paster_commands.deprecated.setup_rhodecode:Command',
            'celeryd=rhodecode.lib.paster_commands.deprecated.celeryd:Command',
        ],
        'pyramid.pshell_runner': [
            'ipython = rhodecode.lib.pyramid_shell:ipython_shell_runner',
        ],
        'pytest11': [
            'pylons=rhodecode.tests.pylons_plugin',
            'enterprise=rhodecode.tests.plugin',
        ],
        'console_scripts': [
            'rc-server=rhodecode.rcserver:main',
            'rc-setup-app=rhodecode.lib.rc_commands.setup_rc:main',
            'rc-upgrade-db=rhodecode.lib.rc_commands.upgrade_db:main',
            'rc-ishell=rhodecode.lib.rc_commands.ishell:main',
            'rc-ssh-wrapper=rhodecode.apps.ssh_support.lib.ssh_wrapper:main',
        ],
        'beaker.backends': [
            'memorylru_base=rhodecode.lib.memory_lru_dict:MemoryLRUNamespaceManagerBase',
            'memorylru_debug=rhodecode.lib.memory_lru_dict:MemoryLRUNamespaceManagerDebug'
        ]
    },
)
