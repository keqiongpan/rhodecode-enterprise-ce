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
    from rhodecode.apps.my_account.views.my_account import MyAccountView
    from rhodecode.apps.my_account.views.my_account_notifications import MyAccountNotificationsView
    from rhodecode.apps.my_account.views.my_account_ssh_keys import MyAccountSshKeysView

    config.add_route(
        name='my_account_profile',
        pattern=ADMIN_PREFIX + '/my_account/profile')
    config.add_view(
        MyAccountView,
        attr='my_account_profile',
        route_name='my_account_profile', request_method='GET',
        renderer='rhodecode:templates/admin/my_account/my_account.mako')

    # my account edit details
    config.add_route(
        name='my_account_edit',
        pattern=ADMIN_PREFIX + '/my_account/edit')
    config.add_view(
        MyAccountView,
        attr='my_account_edit',
        route_name='my_account_edit',
        request_method='GET',
        renderer='rhodecode:templates/admin/my_account/my_account.mako')

    config.add_route(
        name='my_account_update',
        pattern=ADMIN_PREFIX + '/my_account/update')
    config.add_view(
        MyAccountView,
        attr='my_account_update',
        route_name='my_account_update',
        request_method='POST',
        renderer='rhodecode:templates/admin/my_account/my_account.mako')

    # my account password
    config.add_route(
        name='my_account_password',
        pattern=ADMIN_PREFIX + '/my_account/password')
    config.add_view(
        MyAccountView,
        attr='my_account_password',
        route_name='my_account_password', request_method='GET',
        renderer='rhodecode:templates/admin/my_account/my_account.mako')

    config.add_route(
        name='my_account_password_update',
        pattern=ADMIN_PREFIX + '/my_account/password/update')
    config.add_view(
        MyAccountView,
        attr='my_account_password_update',
        route_name='my_account_password_update', request_method='POST',
        renderer='rhodecode:templates/admin/my_account/my_account.mako')

    # my account tokens
    config.add_route(
        name='my_account_auth_tokens',
        pattern=ADMIN_PREFIX + '/my_account/auth_tokens')
    config.add_view(
        MyAccountView,
        attr='my_account_auth_tokens',
        route_name='my_account_auth_tokens', request_method='GET',
        renderer='rhodecode:templates/admin/my_account/my_account.mako')

    config.add_route(
        name='my_account_auth_tokens_view',
        pattern=ADMIN_PREFIX + '/my_account/auth_tokens/view')
    config.add_view(
        MyAccountView,
        attr='my_account_auth_tokens_view',
        route_name='my_account_auth_tokens_view', request_method='POST', xhr=True,
        renderer='json_ext')

    config.add_route(
        name='my_account_auth_tokens_add',
        pattern=ADMIN_PREFIX + '/my_account/auth_tokens/new')
    config.add_view(
        MyAccountView,
        attr='my_account_auth_tokens_add',
        route_name='my_account_auth_tokens_add', request_method='POST')

    config.add_route(
        name='my_account_auth_tokens_delete',
        pattern=ADMIN_PREFIX + '/my_account/auth_tokens/delete')
    config.add_view(
        MyAccountView,
        attr='my_account_auth_tokens_delete',
        route_name='my_account_auth_tokens_delete', request_method='POST')

    # my account ssh keys
    config.add_route(
        name='my_account_ssh_keys',
        pattern=ADMIN_PREFIX + '/my_account/ssh_keys')
    config.add_view(
        MyAccountSshKeysView,
        attr='my_account_ssh_keys',
        route_name='my_account_ssh_keys', request_method='GET',
        renderer='rhodecode:templates/admin/my_account/my_account.mako')

    config.add_route(
        name='my_account_ssh_keys_generate',
        pattern=ADMIN_PREFIX + '/my_account/ssh_keys/generate')
    config.add_view(
        MyAccountSshKeysView,
        attr='ssh_keys_generate_keypair',
        route_name='my_account_ssh_keys_generate', request_method='GET',
        renderer='rhodecode:templates/admin/my_account/my_account.mako')

    config.add_route(
        name='my_account_ssh_keys_add',
        pattern=ADMIN_PREFIX + '/my_account/ssh_keys/new')
    config.add_view(
        MyAccountSshKeysView,
        attr='my_account_ssh_keys_add',
        route_name='my_account_ssh_keys_add', request_method='POST',)

    config.add_route(
        name='my_account_ssh_keys_delete',
        pattern=ADMIN_PREFIX + '/my_account/ssh_keys/delete')
    config.add_view(
        MyAccountSshKeysView,
        attr='my_account_ssh_keys_delete',
        route_name='my_account_ssh_keys_delete', request_method='POST')

    # my account user group membership
    config.add_route(
        name='my_account_user_group_membership',
        pattern=ADMIN_PREFIX + '/my_account/user_group_membership')
    config.add_view(
        MyAccountView,
        attr='my_account_user_group_membership',
        route_name='my_account_user_group_membership',
        request_method='GET',
        renderer='rhodecode:templates/admin/my_account/my_account.mako')

    # my account emails
    config.add_route(
        name='my_account_emails',
        pattern=ADMIN_PREFIX + '/my_account/emails')
    config.add_view(
        MyAccountView,
        attr='my_account_emails',
        route_name='my_account_emails', request_method='GET',
        renderer='rhodecode:templates/admin/my_account/my_account.mako')

    config.add_route(
        name='my_account_emails_add',
        pattern=ADMIN_PREFIX + '/my_account/emails/new')
    config.add_view(
        MyAccountView,
        attr='my_account_emails_add',
        route_name='my_account_emails_add', request_method='POST',
        renderer='rhodecode:templates/admin/my_account/my_account.mako')

    config.add_route(
        name='my_account_emails_delete',
        pattern=ADMIN_PREFIX + '/my_account/emails/delete')
    config.add_view(
        MyAccountView,
        attr='my_account_emails_delete',
        route_name='my_account_emails_delete', request_method='POST')

    config.add_route(
        name='my_account_repos',
        pattern=ADMIN_PREFIX + '/my_account/repos')
    config.add_view(
        MyAccountView,
        attr='my_account_repos',
        route_name='my_account_repos', request_method='GET',
        renderer='rhodecode:templates/admin/my_account/my_account.mako')

    config.add_route(
        name='my_account_watched',
        pattern=ADMIN_PREFIX + '/my_account/watched')
    config.add_view(
        MyAccountView,
        attr='my_account_watched',
        route_name='my_account_watched', request_method='GET',
        renderer='rhodecode:templates/admin/my_account/my_account.mako')

    config.add_route(
        name='my_account_bookmarks',
        pattern=ADMIN_PREFIX + '/my_account/bookmarks')
    config.add_view(
        MyAccountView,
        attr='my_account_bookmarks',
        route_name='my_account_bookmarks', request_method='GET',
        renderer='rhodecode:templates/admin/my_account/my_account.mako')

    config.add_route(
        name='my_account_bookmarks_update',
        pattern=ADMIN_PREFIX + '/my_account/bookmarks/update')
    config.add_view(
        MyAccountView,
        attr='my_account_bookmarks_update',
        route_name='my_account_bookmarks_update', request_method='POST')

    config.add_route(
        name='my_account_goto_bookmark',
        pattern=ADMIN_PREFIX + '/my_account/bookmark/{bookmark_id}')
    config.add_view(
        MyAccountView,
        attr='my_account_goto_bookmark',
        route_name='my_account_goto_bookmark', request_method='GET',
        renderer='rhodecode:templates/admin/my_account/my_account.mako')

    config.add_route(
        name='my_account_perms',
        pattern=ADMIN_PREFIX + '/my_account/perms')
    config.add_view(
        MyAccountView,
        attr='my_account_perms',
        route_name='my_account_perms', request_method='GET',
        renderer='rhodecode:templates/admin/my_account/my_account.mako')

    config.add_route(
        name='my_account_notifications',
        pattern=ADMIN_PREFIX + '/my_account/notifications')
    config.add_view(
        MyAccountView,
        attr='my_notifications',
        route_name='my_account_notifications', request_method='GET',
        renderer='rhodecode:templates/admin/my_account/my_account.mako')

    config.add_route(
        name='my_account_notifications_toggle_visibility',
        pattern=ADMIN_PREFIX + '/my_account/toggle_visibility')
    config.add_view(
        MyAccountView,
        attr='my_notifications_toggle_visibility',
        route_name='my_account_notifications_toggle_visibility',
        request_method='POST', renderer='json_ext')

    # my account pull requests
    config.add_route(
        name='my_account_pullrequests',
        pattern=ADMIN_PREFIX + '/my_account/pull_requests')
    config.add_view(
        MyAccountView,
        attr='my_account_pullrequests',
        route_name='my_account_pullrequests',
        request_method='GET',
        renderer='rhodecode:templates/admin/my_account/my_account.mako')

    config.add_route(
        name='my_account_pullrequests_data',
        pattern=ADMIN_PREFIX + '/my_account/pull_requests/data')
    config.add_view(
        MyAccountView,
        attr='my_account_pullrequests_data',
        route_name='my_account_pullrequests_data',
        request_method='GET', renderer='json_ext')

    # channelstream test
    config.add_route(
        name='my_account_notifications_test_channelstream',
        pattern=ADMIN_PREFIX + '/my_account/test_channelstream')
    config.add_view(
        MyAccountView,
        attr='my_account_notifications_test_channelstream',
        route_name='my_account_notifications_test_channelstream',
        request_method='POST', renderer='json_ext')

    # notifications
    config.add_route(
        name='notifications_show_all',
        pattern=ADMIN_PREFIX + '/notifications')
    config.add_view(
        MyAccountNotificationsView,
        attr='notifications_show_all',
        route_name='notifications_show_all', request_method='GET',
        renderer='rhodecode:templates/admin/notifications/notifications_show_all.mako')

    # notifications
    config.add_route(
        name='notifications_mark_all_read',
        pattern=ADMIN_PREFIX + '/notifications_mark_all_read')
    config.add_view(
        MyAccountNotificationsView,
        attr='notifications_mark_all_read',
        route_name='notifications_mark_all_read', request_method='POST',
        renderer='rhodecode:templates/admin/notifications/notifications_show_all.mako')

    config.add_route(
        name='notifications_show',
        pattern=ADMIN_PREFIX + '/notifications/{notification_id}')
    config.add_view(
        MyAccountNotificationsView,
        attr='notifications_show',
        route_name='notifications_show', request_method='GET',
        renderer='rhodecode:templates/admin/notifications/notifications_show.mako')

    config.add_route(
        name='notifications_update',
        pattern=ADMIN_PREFIX + '/notifications/{notification_id}/update')
    config.add_view(
        MyAccountNotificationsView,
        attr='notification_update',
        route_name='notifications_update', request_method='POST',
        renderer='json_ext')

    config.add_route(
        name='notifications_delete',
        pattern=ADMIN_PREFIX + '/notifications/{notification_id}/delete')
    config.add_view(
        MyAccountNotificationsView,
        attr='notification_delete',
        route_name='notifications_delete', request_method='POST',
        renderer='json_ext')
