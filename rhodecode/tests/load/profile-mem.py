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

"""
Utility to gather certain statistics about a process.

Used to generate data about the memory consumption of the vcsserver. It is
quite generic and should work for every process. Use the parameter `--help`
to see all options.

Example call::

  python profile-mem.py --pid=89816 --ae --ae-key=YOUR_API_KEY

"""


import argparse
import json
import sys
import time

import datetime
import psutil

import logging
import socket

from webhelpers2.number import format_byte_size

logging.basicConfig(level=logging.DEBUG)


def parse_options():
    parser = argparse.ArgumentParser(
        description=__doc__)
    parser.add_argument(
        '--pid', required=True, type=int,
        help="Process ID to monitor.")
    parser.add_argument(
        '--human', action='store_true',
        help="Show Human numbers")
    parser.add_argument(
        '--interval', '-i', type=float, default=5,
        help="Interval in secods.")
    parser.add_argument(
        '--appenlight', '--ae', action='store_true')
    parser.add_argument(
        '--appenlight-url', '--ae-url',
        default='https://ae.rhodecode.com/api/logs',
        help='URL of the Appenlight API endpoint, defaults to "%(default)s".')
    parser.add_argument(
        '--appenlight-api-key', '--ae-key',
        help='API key to use when sending data to appenlight. This has to be '
             'set if Appenlight is enabled.')
    return parser.parse_args()


def profile():
    config = parse_options()
    try:
        process = psutil.Process(config.pid)
    except psutil.NoSuchProcess:
        print("Process {pid} does not exist!".format(pid=config.pid))
        sys.exit(1)

    prev_stats = None
    while True:
        stats = process_stats(process, prev_stats)
        prev_stats = stats
        dump_stats(stats, human=config.human)

        if config.appenlight:
            client = AppenlightClient(
                url=config.appenlight_url,
                api_key=config.appenlight_api_key)
            client.dump_stats(stats)
        time.sleep(config.interval)


def process_stats(process, prev_stats):
    mem = process.memory_info()
    iso_now = datetime.datetime.utcnow().isoformat()
    prev_rss_diff, prev_vms_diff = 0, 0
    cur_rss = mem.rss
    cur_vms = mem.vms

    if prev_stats:
        prev_rss_diff = cur_rss - prev_stats[0]['tags'][0][1]
        prev_vms_diff = cur_vms - prev_stats[0]['tags'][1][1]

    stats = [
        {'message': 'Memory stats of process {pid}'.format(pid=process.pid),
         'namespace': 'process.{pid}'.format(pid=process.pid),
         'server': socket.getfqdn(socket.gethostname()),
         'tags': [
            ['rss', cur_rss],
            ['vms', cur_vms]
         ],
         'diff': [
             ['rss', prev_rss_diff],
             ['vms', prev_vms_diff]
         ],
         'date': iso_now,
         },
    ]
    return stats


def dump_stats(stats, human=False):
    for sample in stats:
        if human:
            diff = stats[0]['diff'][0][1]
            if diff < 0:
                diff = '-' + format_byte_size(abs(diff), binary=True)
            elif diff > 0:
                diff = '+' + format_byte_size(diff, binary=True)
            else:
                diff = ' ' + format_byte_size(diff, binary=True)

            print('Sample:{message} RSS:{rss} RSS_DIFF:{rss_diff}'.format(
                message=stats[0]['message'],
                rss=format_byte_size(stats[0]['tags'][0][1], binary=True),
                rss_diff=diff,
            ))
        else:
            print(json.dumps(sample))


class AppenlightClient(object):

    url_template = '{url}?protocol_version=0.5'

    def __init__(self, url, api_key):
        self.url = self.url_template.format(url=url)
        self.api_key = api_key

    def dump_stats(self, stats):
        import requests
        response = requests.post(
            self.url,
            headers={
                'X-appenlight-api-key': self.api_key},
            data=json.dumps(stats))
        if not response.status_code == 200:
            logging.error(
                'Sending to appenlight failed\n%s\n%s',
                response.headers, response.text)


if __name__ == '__main__':
    try:
        profile()
    except KeyboardInterrupt:
        pass
