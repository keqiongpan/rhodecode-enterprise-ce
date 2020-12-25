# -*- coding: utf-8 -*-

# Copyright (C) 2016-2020 RhodeCode GmbH
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


from rhodecode.apps._base import ADMIN_PREFIX


def includeme(config):
    from rhodecode.apps.login.views import LoginView
    
    config.add_route(
        name='login',
        pattern=ADMIN_PREFIX + '/login')
    config.add_view(
        LoginView,
        attr='login',
        route_name='login', request_method='GET',
        renderer='rhodecode:templates/login.mako')
    config.add_view(
        LoginView,
        attr='login_post',
        route_name='login', request_method='POST',
        renderer='rhodecode:templates/login.mako')

    config.add_route(
        name='logout',
        pattern=ADMIN_PREFIX + '/logout')
    config.add_view(
        LoginView,
        attr='logout',
        route_name='logout', request_method='POST')

    config.add_route(
        name='register',
        pattern=ADMIN_PREFIX + '/register')
    config.add_view(
        LoginView,
        attr='register',
        route_name='register', request_method='GET',
        renderer='rhodecode:templates/register.mako')
    config.add_view(
        LoginView,
        attr='register_post',
        route_name='register', request_method='POST',
        renderer='rhodecode:templates/register.mako')

    config.add_route(
        name='reset_password',
        pattern=ADMIN_PREFIX + '/password_reset')
    config.add_view(
        LoginView,
        attr='password_reset',
        route_name='reset_password', request_method=('GET', 'POST'),
        renderer='rhodecode:templates/password_reset.mako')

    config.add_route(
        name='reset_password_confirmation',
        pattern=ADMIN_PREFIX + '/password_reset_confirmation')
    config.add_view(
        LoginView,
        attr='password_reset_confirmation',
        route_name='reset_password_confirmation', request_method='GET')
