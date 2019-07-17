# -*- coding: utf-8 -*-

# Copyright (C) 2010-2019 RhodeCode GmbH
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

import timeit
import logging
import click

log = logging.getLogger(__name__)


@click.command()
@click.option('--server', help='Server url to connect to. e.g http://rc.local.com', required=True)
@click.option('--pages', help='load pages to visit from a file', required=True, type=click.File())
@click.option('--repeat', help='number of times to repeat', default=10, type=int)
def main(server, repeat, pages):

    print("Repeating each URL %d times\n" % repeat)
    pages = pages.readlines()

    for page_url in pages:

        url = "%s/%s" % (server, page_url.strip())
        print(url)

        stmt = "requests.get('%s', timeout=120)" % url
        t = timeit.Timer(stmt=stmt, setup="import requests")

        result = t.repeat(repeat=repeat, number=1)
        print("  %.4f (min) - %.4f (max) - %.4f (avg)\n" %
              (min(result), max(result), sum(result) / len(result)))


if __name__ == '__main__':
    main()






















