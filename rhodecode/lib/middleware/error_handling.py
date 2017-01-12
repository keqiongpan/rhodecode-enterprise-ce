# -*- coding: utf-8 -*-

# Copyright (C) 2016-2017 RhodeCode GmbH
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


import logging
from pyramid import httpexceptions
from pyramid.httpexceptions import HTTPError, HTTPInternalServerError
from pyramid.threadlocal import get_current_request

from rhodecode.lib.exceptions import VCSServerUnavailable
from rhodecode.lib.vcs.exceptions import VCSCommunicationError


log = logging.getLogger(__name__)


class PylonsErrorHandlingMiddleware(object):
    """
    This middleware is wrapped around the old pylons application to catch
    errors and invoke our error handling view to return a proper error page.
    """
    def __init__(self, app, error_view, reraise=False):
        self.app = app
        self.error_view = error_view
        self._reraise = reraise

    def __call__(self, environ, start_response):
        # We need to use the pyramid request here instead of creating a custom
        # instance from the environ because this request maybe passed to the
        # error handler view which is a pyramid view and expects a pyramid
        # request which has been processed by the pyramid router.
        request = get_current_request()

        response = self.handle_request(request)
        return response(environ, start_response)

    def is_http_error(self, response):
        # webob type error responses
        return (400 <= response.status_int <= 599)

    def reraise(self):
        return self._reraise

    def handle_request(self, request):
        """
        Calls the underlying WSGI app (typically the old RhodeCode pylons app)
        and returns the response if no error happened. In case of an error it
        invokes the error handling view to return a proper error page as
        response.

        - old webob type exceptions get converted to pyramid exceptions
        - pyramid exceptions are passed to the error handler view
        """
        try:
            response = request.get_response(self.app)
            if self.is_http_error(response):
                response = webob_to_pyramid_http_response(response)
                return self.error_view(response, request)
        except HTTPError as e:  # pyramid type exceptions
            return self.error_view(e, request)
        except Exception as e:

            if self.reraise():
                raise

            if isinstance(e, VCSCommunicationError):
                return self.error_view(VCSServerUnavailable(), request)

            return self.error_view(HTTPInternalServerError(), request)

        return response


def webob_to_pyramid_http_response(webob_response):
    ResponseClass = httpexceptions.status_map[webob_response.status_int]
    pyramid_response = ResponseClass(webob_response.status)
    pyramid_response.status = webob_response.status
    pyramid_response.headers.update(webob_response.headers)
    if pyramid_response.headers['content-type'] == 'text/html':
        pyramid_response.headers['content-type'] = 'text/html; charset=UTF-8'
    return pyramid_response
