# -*- coding: utf-8 -*-

# Copyright (C) 2014-2019 RhodeCode GmbH
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
Custom vcs exceptions module.
"""
import logging
import functools
import urllib2
import rhodecode
from pyramid import compat

log = logging.getLogger(__name__)


class VCSCommunicationError(Exception):
    pass


class HttpVCSCommunicationError(VCSCommunicationError):
    pass


class VCSError(Exception):
    pass


class RepositoryError(VCSError):
    pass


class RepositoryRequirementError(RepositoryError):
    pass


class UnresolvedFilesInRepo(RepositoryError):
    pass


class VCSBackendNotSupportedError(VCSError):
    """
    Exception raised when VCSServer does not support requested backend
    """


class EmptyRepositoryError(RepositoryError):
    pass


class TagAlreadyExistError(RepositoryError):
    pass


class TagDoesNotExistError(RepositoryError):
    pass


class BranchAlreadyExistError(RepositoryError):
    pass


class BranchDoesNotExistError(RepositoryError):
    pass


class CommitError(RepositoryError):
    """
    Exceptions related to an existing commit
    """


class CommitDoesNotExistError(CommitError):
    pass


class CommittingError(RepositoryError):
    """
    Exceptions happening while creating a new commit
    """


class NothingChangedError(CommittingError):
    pass


class NodeError(VCSError):
    pass


class RemovedFileNodeError(NodeError):
    pass


class NodeAlreadyExistsError(CommittingError):
    pass


class NodeAlreadyChangedError(CommittingError):
    pass


class NodeDoesNotExistError(CommittingError):
    pass


class NodeNotChangedError(CommittingError):
    pass


class NodeAlreadyAddedError(CommittingError):
    pass


class NodeAlreadyRemovedError(CommittingError):
    pass


class SubrepoMergeError(RepositoryError):
    """
    This happens if we try to merge a repository which contains subrepos and
    the subrepos cannot be merged. The subrepos are not merged itself but
    their references in the root repo are merged.
    """


class ImproperArchiveTypeError(VCSError):
    pass


class CommandError(VCSError):
    pass


class UnhandledException(VCSError):
    """
    Signals that something unexpected went wrong.

    This usually means we have a programming error on the side of the VCSServer
    and should inspect the logfile of the VCSServer to find more details.
    """


_EXCEPTION_MAP = {
    'abort': RepositoryError,
    'archive': ImproperArchiveTypeError,
    'error': RepositoryError,
    'lookup': CommitDoesNotExistError,
    'repo_locked': RepositoryError,
    'requirement': RepositoryRequirementError,
    'unhandled': UnhandledException,
    # TODO: johbo: Define our own exception for this and stop abusing
    # urllib's exception class.
    'url_error': urllib2.URLError,
    'subrepo_merge_error': SubrepoMergeError,
}


def map_vcs_exceptions(func):
    """
    Utility to decorate functions so that plain exceptions are translated.

    The translation is based on `exc_map` which maps a `str` indicating
    the error type into an exception class representing this error inside
    of the vcs layer.
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            from rhodecode.lib.utils2 import str2bool
            debug = str2bool(rhodecode.CONFIG.get('debug'))

            # The error middleware adds information if it finds
            # __traceback_info__ in a frame object. This way the remote
            # traceback information is made available in error reports.
            remote_tb = getattr(e, '_vcs_server_traceback', None)
            org_remote_tb = getattr(e, '_vcs_server_org_exc_tb', '')
            __traceback_info__ = None
            if remote_tb:
                if isinstance(remote_tb, compat.string_types):
                    remote_tb = [remote_tb]
                __traceback_info__ = (
                    'Found VCSServer remote traceback information:\n'
                    '{}\n'
                    '+++ BEG SOURCE EXCEPTION +++\n\n'
                    '{}\n'
                    '+++ END SOURCE EXCEPTION +++\n'
                    ''.format('\n'.join(remote_tb), org_remote_tb)
                )

                # Avoid that remote_tb also appears in the frame
                del remote_tb

            # Special vcs errors had an attribute "_vcs_kind" which is used
            # to translate them to the proper exception class in the vcs
            # client layer.
            kind = getattr(e, '_vcs_kind', None)

            if kind:
                if any(e.args):
                    args = e.args
                else:
                    args = [__traceback_info__ or 'unhandledException']
                if debug or __traceback_info__ and kind not in ['unhandled', 'lookup']:
                    # for other than unhandled errors also log the traceback
                    # can be useful for debugging
                    log.error(__traceback_info__)
                raise _EXCEPTION_MAP[kind](*args)
            else:
                raise
    return wrapper
