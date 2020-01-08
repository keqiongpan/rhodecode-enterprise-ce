# Copyright (c) Django Software Foundation and individual contributors.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without modification,
# are permitted provided that the following conditions are met:
#
#     1. Redistributions of source code must retain the above copyright notice,
#        this list of conditions and the following disclaimer.
#
#     2. Redistributions in binary form must reproduce the above copyright
#        notice, this list of conditions and the following disclaimer in the
#        documentation and/or other materials provided with the distribution.
#
#     3. Neither the name of Django nor the names of its contributors may be used
#        to endorse or promote products derived from this software without
#        specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
# ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
# ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

# Python's datetime strftime doesn't handle dates before 1900.
# These classes override date and datetime to support the formatting of a date
# through its full "proleptic Gregorian" date range.
#
# Based on code submitted to comp.lang.python by Andrew Dalke
#
# >>> datetime_safe.date(1850, 8, 2).strftime("%Y/%m/%d was a %A")
# '1850/08/02 was a Friday'

from datetime import date as real_date, datetime as real_datetime
import re
import time

class date(real_date):
    def strftime(self, fmt):
        return strftime(self, fmt)

class datetime(real_datetime):
    def strftime(self, fmt):
        return strftime(self, fmt)

    def combine(self, date, time):
        return datetime(date.year, date.month, date.day, time.hour, time.minute, time.microsecond, time.tzinfo)

    def date(self):
        return date(self.year, self.month, self.day)

def new_date(d):
    "Generate a safe date from a datetime.date object."
    return date(d.year, d.month, d.day)

def new_datetime(d):
    """
    Generate a safe datetime from a datetime.date or datetime.datetime object.
    """
    kw = [d.year, d.month, d.day]
    if isinstance(d, real_datetime):
        kw.extend([d.hour, d.minute, d.second, d.microsecond, d.tzinfo])
    return datetime(*kw)

# This library does not support strftime's "%s" or "%y" format strings.
# Allowed if there's an even number of "%"s because they are escaped.
_illegal_formatting = re.compile(r"((^|[^%])(%%)*%[sy])")

def _findall(text, substr):
    # Also finds overlaps
    sites = []
    i = 0
    while 1:
        j = text.find(substr, i)
        if j == -1:
            break
        sites.append(j)
        i=j+1
    return sites

def strftime(dt, fmt):
    if dt.year >= 1900:
        return super(type(dt), dt).strftime(fmt)
    illegal_formatting = _illegal_formatting.search(fmt)
    if illegal_formatting:
        raise TypeError("strftime of dates before 1900 does not handle" + illegal_formatting.group(0))

    year = dt.year
    # For every non-leap year century, advance by
    # 6 years to get into the 28-year repeat cycle
    delta = 2000 - year
    off = 6 * (delta // 100 + delta // 400)
    year = year + off

    # Move to around the year 2000
    year = year + ((2000 - year) // 28) * 28
    timetuple = dt.timetuple()
    s1 = time.strftime(fmt, (year,) + timetuple[1:])
    sites1 = _findall(s1, str(year))

    s2 = time.strftime(fmt, (year+28,) + timetuple[1:])
    sites2 = _findall(s2, str(year+28))

    sites = []
    for site in sites1:
        if site in sites2:
            sites.append(site)

    s = s1
    syear = "%04d" % (dt.year,)
    for site in sites:
        s = s[:site] + syear + s[site+4:]
    return s
