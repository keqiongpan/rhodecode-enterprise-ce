# -*- coding: utf-8 -*-

# Copyright (C) 2013-2017 RhodeCode GmbH
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


from rhodecode.lib.paster_commands import BasePasterCommand


class Command(BasePasterCommand):
    """
    Start the celery worker

    Starts the celery worker that uses a paste.deploy configuration
    file.
    """
    usage = 'CONFIG_FILE [celeryd options...]'
    summary = __doc__.splitlines()[0]
    description = "".join(__doc__.splitlines()[2:])

    parser = BasePasterCommand.standard_parser(quiet=True)

    def update_parser(self):
        pass

    def command(self):
        cmd = 'celery worker --beat --app rhodecode.lib.celerylib.loader --loglevel DEBUG --ini=%s' % self.path_to_ini_file
        raise Exception('This Command is deprecated please run: %s' % cmd)