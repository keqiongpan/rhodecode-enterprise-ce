# -*- coding: utf-8 -*-

# Copyright (C) 2010-2020 RhodeCode GmbH
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
Set of custom exceptions used in RhodeCode
"""

from webob.exc import HTTPClientError
from pyramid.httpexceptions import HTTPBadGateway


class LdapUsernameError(Exception):
    pass


class LdapPasswordError(Exception):
    pass


class LdapConnectionError(Exception):
    pass


class LdapImportError(Exception):
    pass


class DefaultUserException(Exception):
    pass


class UserOwnsReposException(Exception):
    pass


class UserOwnsRepoGroupsException(Exception):
    pass


class UserOwnsUserGroupsException(Exception):
    pass


class UserOwnsPullRequestsException(Exception):
    pass


class UserOwnsArtifactsException(Exception):
    pass


class UserGroupAssignedException(Exception):
    pass


class StatusChangeOnClosedPullRequestError(Exception):
    pass


class AttachedForksError(Exception):
    pass


class AttachedPullRequestsError(Exception):
    pass


class RepoGroupAssignmentError(Exception):
    pass


class NonRelativePathError(Exception):
    pass


class HTTPRequirementError(HTTPClientError):
    title = explanation = 'Repository Requirement Missing'
    reason = None

    def __init__(self, message, *args, **kwargs):
        self.title = self.explanation = message
        super(HTTPRequirementError, self).__init__(*args, **kwargs)
        self.args = (message, )


class HTTPLockedRC(HTTPClientError):
    """
    Special Exception For locked Repos in RhodeCode, the return code can
    be overwritten by _code keyword argument passed into constructors
    """
    code = 423
    title = explanation = 'Repository Locked'
    reason = None

    def __init__(self, message, *args, **kwargs):
        from rhodecode import CONFIG
        from rhodecode.lib.utils2 import safe_int
        _code = CONFIG.get('lock_ret_code')
        self.code = safe_int(_code, self.code)
        self.title = self.explanation = message
        super(HTTPLockedRC, self).__init__(*args, **kwargs)
        self.args = (message, )


class HTTPBranchProtected(HTTPClientError):
    """
    Special Exception For Indicating that branch is protected in RhodeCode, the
    return code can be overwritten by _code keyword argument passed into constructors
    """
    code = 403
    title = explanation = 'Branch Protected'
    reason = None

    def __init__(self, message, *args, **kwargs):
        self.title = self.explanation = message
        super(HTTPBranchProtected, self).__init__(*args, **kwargs)
        self.args = (message, )


class IMCCommitError(Exception):
    pass


class UserCreationError(Exception):
    pass


class NotAllowedToCreateUserError(Exception):
    pass


class RepositoryCreationError(Exception):
    pass


class VCSServerUnavailable(HTTPBadGateway):
    """ HTTP Exception class for VCS Server errors """
    code = 502
    title = 'VCS Server Error'
    causes = [
        'VCS Server is not running',
        'Incorrect vcs.server=host:port',
        'Incorrect vcs.server.protocol',
    ]

    def __init__(self, message=''):
        self.explanation = 'Could not connect to VCS Server'
        if message:
            self.explanation += ': ' + message
        super(VCSServerUnavailable, self).__init__()


class ArtifactMetadataDuplicate(ValueError):

    def __init__(self, *args, **kwargs):
        self.err_section = kwargs.pop('err_section', None)
        self.err_key = kwargs.pop('err_key', None)
        super(ArtifactMetadataDuplicate, self).__init__(*args, **kwargs)


class ArtifactMetadataBadValueType(ValueError):
    pass


class CommentVersionMismatch(ValueError):
    pass
