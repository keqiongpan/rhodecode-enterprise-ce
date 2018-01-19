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

import sys
import logging


BLACK, RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE = xrange(30, 38)

# Sequences
RESET_SEQ = "\033[0m"
COLOR_SEQ = "\033[0;%dm"
BOLD_SEQ = "\033[1m"

COLORS = {
    'CRITICAL': MAGENTA,
    'ERROR': RED,
    'WARNING': CYAN,
    'INFO': GREEN,
    'DEBUG': BLUE,
    'SQL': YELLOW
}


def one_space_trim(s):
    if s.find("  ") == -1:
        return s
    else:
        s = s.replace('  ', ' ')
        return one_space_trim(s)


def format_sql(sql):
    sql = sql.replace('\n', '')
    sql = one_space_trim(sql)
    sql = sql\
        .replace(',', ',\n\t')\
        .replace('SELECT', '\n\tSELECT \n\t')\
        .replace('UPDATE', '\n\tUPDATE \n\t')\
        .replace('DELETE', '\n\tDELETE \n\t')\
        .replace('FROM', '\n\tFROM')\
        .replace('ORDER BY', '\n\tORDER BY')\
        .replace('LIMIT', '\n\tLIMIT')\
        .replace('WHERE', '\n\tWHERE')\
        .replace('AND', '\n\tAND')\
        .replace('LEFT', '\n\tLEFT')\
        .replace('INNER', '\n\tINNER')\
        .replace('INSERT', '\n\tINSERT')\
        .replace('DELETE', '\n\tDELETE')
    return sql


class ExceptionAwareFormatter(logging.Formatter):
    """
    Extended logging formatter which prints out remote tracebacks.
    """

    def formatException(self, ei):
        ex_type, ex_value, ex_tb = ei

        local_tb = logging.Formatter.formatException(self, ei)
        if hasattr(ex_value, '_vcs_server_traceback'):

            def formatRemoteTraceback(remote_tb_lines):
                result = ["\n +--- This exception occured remotely on VCSServer - Remote traceback:\n\n"]
                result.append(remote_tb_lines)
                result.append("\n +--- End of remote traceback\n")
                return result

            try:
                if ex_type is not None and ex_value is None and ex_tb is None:
                    # possible old (3.x) call syntax where caller is only
                    # providing exception object
                    if type(ex_type) is not type:
                        raise TypeError(
                            "invalid argument: ex_type should be an exception "
                            "type, or just supply no arguments at all")
                if ex_type is None and ex_tb is None:
                    ex_type, ex_value, ex_tb = sys.exc_info()

                remote_tb = getattr(ex_value, "_vcs_server_traceback", None)

                if remote_tb:
                    remote_tb = formatRemoteTraceback(remote_tb)
                    return local_tb + ''.join(remote_tb)
            finally:
                # clean up cycle to traceback, to allow proper GC
                del ex_type, ex_value, ex_tb

        return local_tb


class ColorFormatter(ExceptionAwareFormatter):

    def format(self, record):
        """
        Changes record's levelname to use with COLORS enum
        """

        levelname = record.levelname
        start = COLOR_SEQ % (COLORS[levelname])
        def_record = logging.Formatter.format(self, record)
        end = RESET_SEQ

        colored_record = ''.join([start, def_record, end])
        return colored_record


class ColorFormatterSql(logging.Formatter):

    def format(self, record):
        """
        Changes record's levelname to use with COLORS enum
        """

        start = COLOR_SEQ % (COLORS['SQL'])
        def_record = format_sql(logging.Formatter.format(self, record))
        end = RESET_SEQ

        colored_record = ''.join([start, def_record, end])
        return colored_record

# marcink: needs to stay with this name for backward .ini compatability
Pyro4AwareFormatter = ExceptionAwareFormatter
