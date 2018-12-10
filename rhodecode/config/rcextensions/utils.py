# Copyright (C) 2016-2018 RhodeCode GmbH
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
import functools
import collections


class HookResponse(object):
    def __init__(self, status, output):
        self.status = status
        self.output = output

    def __add__(self, other):
        other_status = getattr(other, 'status', 0)
        new_status = max(self.status, other_status)
        other_output = getattr(other, 'output', '')
        new_output = self.output + other_output

        return HookResponse(new_status, new_output)

    def __bool__(self):
        return self.status == 0


class DotDict(dict):

    def __contains__(self, k):
        try:
            return dict.__contains__(self, k) or hasattr(self, k)
        except:
            return False

    # only called if k not found in normal places
    def __getattr__(self, k):
        try:
            return object.__getattribute__(self, k)
        except AttributeError:
            try:
                return self[k]
            except KeyError:
                raise AttributeError(k)

    def __setattr__(self, k, v):
        try:
            object.__getattribute__(self, k)
        except AttributeError:
            try:
                self[k] = v
            except:
                raise AttributeError(k)
        else:
            object.__setattr__(self, k, v)

    def __delattr__(self, k):
        try:
            object.__getattribute__(self, k)
        except AttributeError:
            try:
                del self[k]
            except KeyError:
                raise AttributeError(k)
        else:
            object.__delattr__(self, k)

    def toDict(self):
        return unserialize(self)

    def __repr__(self):
        keys = list(self.keys())
        keys.sort()
        args = ', '.join(['%s=%r' % (key, self[key]) for key in keys])
        return '%s(%s)' % (self.__class__.__name__, args)

    @staticmethod
    def fromDict(d):
        return serialize(d)


def serialize(x):
    if isinstance(x, dict):
        return DotDict((k, serialize(v)) for k, v in x.items())
    elif isinstance(x, (list, tuple)):
        return type(x)(serialize(v) for v in x)
    else:
        return x


def unserialize(x):
    if isinstance(x, dict):
        return dict((k, unserialize(v)) for k, v in x.items())
    elif isinstance(x, (list, tuple)):
        return type(x)(unserialize(v) for v in x)
    else:
        return x


def _verify_kwargs(func_name, expected_parameters, kwargs):
    """
    Verify that exactly `expected_parameters` are passed in as `kwargs`.
    """
    expected_parameters = set(expected_parameters)
    kwargs_keys = set(kwargs.keys())
    if kwargs_keys != expected_parameters:
        missing_kwargs = expected_parameters - kwargs_keys
        unexpected_kwargs = kwargs_keys - expected_parameters
        raise AssertionError(
            "func:%s: missing parameters: %r, unexpected parameters: %s" %
            (func_name, missing_kwargs, unexpected_kwargs))


def has_kwargs(required_args):
    """
    decorator to verify extension calls arguments.

    :param required_args:
    """
    def wrap(func):
        def wrapper(*args, **kwargs):
            _verify_kwargs(func.func_name, required_args.keys(), kwargs)
            # in case there's `calls` defined on module we store the data
            maybe_log_call(func.func_name, args, kwargs)
            return func(*args, **kwargs)
        return wrapper
    return wrap


def maybe_log_call(name, args, kwargs):
    from rhodecode.config import rcextensions
    if hasattr(rcextensions, 'calls'):
        calls = rcextensions.calls
        calls[name].append((args, kwargs))


def str2bool(_str):
    """
    returns True/False value from given string, it tries to translate the
    string into boolean

    :param _str: string value to translate into boolean
    :rtype: boolean
    :returns: boolean from given string
    """
    if _str is None:
        return False
    if _str in (True, False):
        return _str
    _str = str(_str).strip().lower()
    return _str in ('t', 'true', 'y', 'yes', 'on', '1')


def aslist(obj, sep=None, strip=True):
    """
    Returns given string separated by sep as list

    :param obj:
    :param sep:
    :param strip:
    """
    if isinstance(obj, (basestring,)):
        lst = obj.split(sep)
        if strip:
            lst = [v.strip() for v in lst]
        return lst
    elif isinstance(obj, (list, tuple)):
        return obj
    elif obj is None:
        return []
    else:
        return [obj]