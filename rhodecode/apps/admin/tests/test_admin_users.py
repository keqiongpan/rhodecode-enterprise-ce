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

import pytest
from sqlalchemy.orm.exc import NoResultFound

from rhodecode.lib import auth
from rhodecode.lib import helpers as h
from rhodecode.model.db import User, UserApiKeys, UserEmailMap, Repository
from rhodecode.model.meta import Session
from rhodecode.model.user import UserModel

from rhodecode.tests import (
    TestController, TEST_USER_REGULAR_LOGIN, assert_session_flash)
from rhodecode.tests.fixture import Fixture

fixture = Fixture()


def route_path(name, params=None, **kwargs):
    import urllib
    from rhodecode.apps._base import ADMIN_PREFIX

    base_url = {
        'users':
            ADMIN_PREFIX + '/users',
        'users_data':
            ADMIN_PREFIX + '/users_data',
        'users_create':
            ADMIN_PREFIX + '/users/create',
        'users_new':
            ADMIN_PREFIX + '/users/new',
        'user_edit':
            ADMIN_PREFIX + '/users/{user_id}/edit',
        'user_edit_advanced':
            ADMIN_PREFIX + '/users/{user_id}/edit/advanced',
        'user_edit_global_perms':
            ADMIN_PREFIX + '/users/{user_id}/edit/global_permissions',
        'user_edit_global_perms_update':
            ADMIN_PREFIX + '/users/{user_id}/edit/global_permissions/update',
        'user_update':
            ADMIN_PREFIX + '/users/{user_id}/update',
        'user_delete':
            ADMIN_PREFIX + '/users/{user_id}/delete',
        'user_force_password_reset':
            ADMIN_PREFIX + '/users/{user_id}/password_reset',
        'user_create_personal_repo_group':
            ADMIN_PREFIX + '/users/{user_id}/create_repo_group',

        'edit_user_auth_tokens':
            ADMIN_PREFIX + '/users/{user_id}/edit/auth_tokens',
        'edit_user_auth_tokens_add':
            ADMIN_PREFIX + '/users/{user_id}/edit/auth_tokens/new',
        'edit_user_auth_tokens_delete':
            ADMIN_PREFIX + '/users/{user_id}/edit/auth_tokens/delete',

        'edit_user_emails':
            ADMIN_PREFIX + '/users/{user_id}/edit/emails',
        'edit_user_emails_add':
            ADMIN_PREFIX + '/users/{user_id}/edit/emails/new',
        'edit_user_emails_delete':
            ADMIN_PREFIX + '/users/{user_id}/edit/emails/delete',

        'edit_user_ips':
            ADMIN_PREFIX + '/users/{user_id}/edit/ips',
        'edit_user_ips_add':
            ADMIN_PREFIX + '/users/{user_id}/edit/ips/new',
        'edit_user_ips_delete':
            ADMIN_PREFIX + '/users/{user_id}/edit/ips/delete',

        'edit_user_perms_summary':
            ADMIN_PREFIX + '/users/{user_id}/edit/permissions_summary',
        'edit_user_perms_summary_json':
            ADMIN_PREFIX + '/users/{user_id}/edit/permissions_summary/json',

        'edit_user_audit_logs':
            ADMIN_PREFIX + '/users/{user_id}/edit/audit',

    }[name].format(**kwargs)

    if params:
        base_url = '{}?{}'.format(base_url, urllib.urlencode(params))
    return base_url


class TestAdminUsersView(TestController):

    def test_show_users(self):
        self.log_user()
        self.app.get(route_path('users'))

    def test_show_users_data(self, xhr_header):
        self.log_user()
        response = self.app.get(route_path(
            'users_data'), extra_environ=xhr_header)

        all_users = User.query().filter(
            User.username != User.DEFAULT_USER).count()
        assert response.json['recordsTotal'] == all_users

    def test_show_users_data_filtered(self, xhr_header):
        self.log_user()
        response = self.app.get(route_path(
            'users_data', params={'search[value]': 'empty_search'}),
            extra_environ=xhr_header)

        all_users = User.query().filter(
            User.username != User.DEFAULT_USER).count()
        assert response.json['recordsTotal'] == all_users
        assert response.json['recordsFiltered'] == 0

    def test_auth_tokens_default_user(self):
        self.log_user()
        user = User.get_default_user()
        response = self.app.get(
            route_path('edit_user_auth_tokens', user_id=user.user_id),
            status=302)

    def test_auth_tokens(self):
        self.log_user()

        user = User.get_by_username(TEST_USER_REGULAR_LOGIN)
        user_id = user.user_id
        auth_tokens = user.auth_tokens
        response = self.app.get(
            route_path('edit_user_auth_tokens', user_id=user_id))
        for token in auth_tokens:
            response.mustcontain(token)
            response.mustcontain('never')

    @pytest.mark.parametrize("desc, lifetime", [
        ('forever', -1),
        ('5mins', 60*5),
        ('30days', 60*60*24*30),
    ])
    def test_add_auth_token(self, desc, lifetime, user_util):
        self.log_user()
        user = user_util.create_user()
        user_id = user.user_id

        response = self.app.post(
            route_path('edit_user_auth_tokens_add', user_id=user_id),
            {'description': desc, 'lifetime': lifetime,
             'csrf_token': self.csrf_token})
        assert_session_flash(response, 'Auth token successfully created')

        response = response.follow()
        user = User.get(user_id)
        for auth_token in user.auth_tokens:
            response.mustcontain(auth_token)

    def test_delete_auth_token(self, user_util):
        self.log_user()
        user = user_util.create_user()
        user_id = user.user_id
        keys = user.auth_tokens
        assert 2 == len(keys)

        response = self.app.post(
            route_path('edit_user_auth_tokens_add', user_id=user_id),
            {'description': 'desc', 'lifetime': -1,
             'csrf_token': self.csrf_token})
        assert_session_flash(response, 'Auth token successfully created')
        response.follow()

        # now delete our key
        keys = UserApiKeys.query().filter(UserApiKeys.user_id == user_id).all()
        assert 3 == len(keys)

        response = self.app.post(
            route_path('edit_user_auth_tokens_delete', user_id=user_id),
            {'del_auth_token': keys[0].user_api_key_id,
             'csrf_token': self.csrf_token})

        assert_session_flash(response, 'Auth token successfully deleted')
        keys = UserApiKeys.query().filter(UserApiKeys.user_id == user_id).all()
        assert 2 == len(keys)

    def test_ips(self):
        self.log_user()
        user = User.get_by_username(TEST_USER_REGULAR_LOGIN)
        response = self.app.get(route_path('edit_user_ips', user_id=user.user_id))
        response.mustcontain('All IP addresses are allowed')

    @pytest.mark.parametrize("test_name, ip, ip_range, failure", [
        ('127/24', '127.0.0.1/24', '127.0.0.0 - 127.0.0.255', False),
        ('10/32', '10.0.0.10/32', '10.0.0.10 - 10.0.0.10', False),
        ('0/16', '0.0.0.0/16', '0.0.0.0 - 0.0.255.255', False),
        ('0/8', '0.0.0.0/8', '0.0.0.0 - 0.255.255.255', False),
        ('127_bad_mask', '127.0.0.1/99', '127.0.0.1 - 127.0.0.1', True),
        ('127_bad_ip', 'foobar', 'foobar', True),
    ])
    def test_ips_add(self, user_util, test_name, ip, ip_range, failure):
        self.log_user()
        user = user_util.create_user(username=test_name)
        user_id = user.user_id

        response = self.app.post(
            route_path('edit_user_ips_add', user_id=user_id),
            params={'new_ip': ip, 'csrf_token': self.csrf_token})

        if failure:
            assert_session_flash(
                response, 'Please enter a valid IPv4 or IpV6 address')
            response = self.app.get(route_path('edit_user_ips', user_id=user_id))

            response.mustcontain(no=[ip])
            response.mustcontain(no=[ip_range])

        else:
            response = self.app.get(route_path('edit_user_ips', user_id=user_id))
            response.mustcontain(ip)
            response.mustcontain(ip_range)

    def test_ips_delete(self, user_util):
        self.log_user()
        user = user_util.create_user()
        user_id = user.user_id
        ip = '127.0.0.1/32'
        ip_range = '127.0.0.1 - 127.0.0.1'
        new_ip = UserModel().add_extra_ip(user_id, ip)
        Session().commit()
        new_ip_id = new_ip.ip_id

        response = self.app.get(route_path('edit_user_ips', user_id=user_id))
        response.mustcontain(ip)
        response.mustcontain(ip_range)

        self.app.post(
            route_path('edit_user_ips_delete', user_id=user_id),
            params={'del_ip_id': new_ip_id, 'csrf_token': self.csrf_token})

        response = self.app.get(route_path('edit_user_ips', user_id=user_id))
        response.mustcontain('All IP addresses are allowed')
        response.mustcontain(no=[ip])
        response.mustcontain(no=[ip_range])

    def test_emails(self):
        self.log_user()
        user = User.get_by_username(TEST_USER_REGULAR_LOGIN)
        response = self.app.get(
            route_path('edit_user_emails', user_id=user.user_id))
        response.mustcontain('No additional emails specified')

    def test_emails_add(self, user_util):
        self.log_user()
        user = user_util.create_user()
        user_id = user.user_id

        self.app.post(
            route_path('edit_user_emails_add', user_id=user_id),
            params={'new_email': 'example@rhodecode.com',
                    'csrf_token': self.csrf_token})

        response = self.app.get(
            route_path('edit_user_emails', user_id=user_id))
        response.mustcontain('example@rhodecode.com')

    def test_emails_add_existing_email(self, user_util, user_regular):
        existing_email = user_regular.email

        self.log_user()
        user = user_util.create_user()
        user_id = user.user_id

        response = self.app.post(
            route_path('edit_user_emails_add', user_id=user_id),
            params={'new_email': existing_email,
                    'csrf_token': self.csrf_token})
        assert_session_flash(
            response, 'This e-mail address is already taken')

        response = self.app.get(
            route_path('edit_user_emails', user_id=user_id))
        response.mustcontain(no=[existing_email])

    def test_emails_delete(self, user_util):
        self.log_user()
        user = user_util.create_user()
        user_id = user.user_id

        self.app.post(
            route_path('edit_user_emails_add', user_id=user_id),
            params={'new_email': 'example@rhodecode.com',
                    'csrf_token': self.csrf_token})

        response = self.app.get(
            route_path('edit_user_emails', user_id=user_id))
        response.mustcontain('example@rhodecode.com')

        user_email = UserEmailMap.query()\
            .filter(UserEmailMap.email == 'example@rhodecode.com') \
            .filter(UserEmailMap.user_id == user_id)\
            .one()

        del_email_id = user_email.email_id
        self.app.post(
            route_path('edit_user_emails_delete', user_id=user_id),
            params={'del_email_id': del_email_id,
                    'csrf_token': self.csrf_token})

        response = self.app.get(
            route_path('edit_user_emails', user_id=user_id))
        response.mustcontain(no=['example@rhodecode.com'])


    def test_create(self, request, xhr_header):
        self.log_user()
        username = 'newtestuser'
        password = 'test12'
        password_confirmation = password
        name = 'name'
        lastname = 'lastname'
        email = 'mail@mail.com'

        self.app.get(route_path('users_new'))

        response = self.app.post(route_path('users_create'), params={
            'username': username,
            'password': password,
            'password_confirmation': password_confirmation,
            'firstname': name,
            'active': True,
            'lastname': lastname,
            'extern_name': 'rhodecode',
            'extern_type': 'rhodecode',
            'email': email,
            'csrf_token': self.csrf_token,
        })
        user_link = h.link_to(
            username,
            route_path(
                'user_edit', user_id=User.get_by_username(username).user_id))
        assert_session_flash(response, 'Created user %s' % (user_link,))

        @request.addfinalizer
        def cleanup():
            fixture.destroy_user(username)
            Session().commit()

        new_user = User.query().filter(User.username == username).one()

        assert new_user.username == username
        assert auth.check_password(password, new_user.password)
        assert new_user.name == name
        assert new_user.lastname == lastname
        assert new_user.email == email

        response = self.app.get(route_path('users_data'),
                                extra_environ=xhr_header)
        response.mustcontain(username)

    def test_create_err(self):
        self.log_user()
        username = 'new_user'
        password = ''
        name = 'name'
        lastname = 'lastname'
        email = 'errmail.com'

        self.app.get(route_path('users_new'))

        response = self.app.post(route_path('users_create'), params={
            'username': username,
            'password': password,
            'name': name,
            'active': False,
            'lastname': lastname,
            'email': email,
            'csrf_token': self.csrf_token,
        })

        msg = u'Username "%(username)s" is forbidden'
        msg = h.html_escape(msg % {'username': 'new_user'})
        response.mustcontain('<span class="error-message">%s</span>' % msg)
        response.mustcontain(
            '<span class="error-message">Please enter a value</span>')
        response.mustcontain(
            '<span class="error-message">An email address must contain a'
            ' single @</span>')

        def get_user():
            Session().query(User).filter(User.username == username).one()

        with pytest.raises(NoResultFound):
            get_user()

    def test_new(self):
        self.log_user()
        self.app.get(route_path('users_new'))

    @pytest.mark.parametrize("name, attrs", [
        ('firstname', {'firstname': 'new_username'}),
        ('lastname', {'lastname': 'new_username'}),
        ('admin', {'admin': True}),
        ('admin', {'admin': False}),
        ('extern_type', {'extern_type': 'ldap'}),
        ('extern_type', {'extern_type': None}),
        ('extern_name', {'extern_name': 'test'}),
        ('extern_name', {'extern_name': None}),
        ('active', {'active': False}),
        ('active', {'active': True}),
        ('email', {'email': 'some@email.com'}),
        ('language', {'language': 'de'}),
        ('language', {'language': 'en'}),
        # ('new_password', {'new_password': 'foobar123',
        #                   'password_confirmation': 'foobar123'})
        ])
    def test_update(self, name, attrs, user_util):
        self.log_user()
        usr = user_util.create_user(
            password='qweqwe',
            email='testme@rhodecode.org',
            extern_type='rhodecode',
            extern_name='xxx',
        )
        user_id = usr.user_id
        Session().commit()

        params = usr.get_api_data()
        cur_lang = params['language'] or 'en'
        params.update({
            'password_confirmation': '',
            'new_password': '',
            'language': cur_lang,
            'csrf_token': self.csrf_token,
        })
        params.update({'new_password': ''})
        params.update(attrs)
        if name == 'email':
            params['emails'] = [attrs['email']]
        elif name == 'extern_type':
            # cannot update this via form, expected value is original one
            params['extern_type'] = "rhodecode"
        elif name == 'extern_name':
            # cannot update this via form, expected value is original one
            params['extern_name'] = 'xxx'
            # special case since this user is not
            # logged in yet his data is not filled
            # so we use creation data

        response = self.app.post(
            route_path('user_update', user_id=usr.user_id), params)
        assert response.status_int == 302
        assert_session_flash(response, 'User updated successfully')

        updated_user = User.get(user_id)
        updated_params = updated_user.get_api_data()
        updated_params.update({'password_confirmation': ''})
        updated_params.update({'new_password': ''})

        del params['csrf_token']
        assert params == updated_params

    def test_update_and_migrate_password(
            self, autologin_user, real_crypto_backend, user_util):

        user = user_util.create_user()
        temp_user = user.username
        user.password = auth._RhodeCodeCryptoSha256().hash_create(
            b'test123')
        Session().add(user)
        Session().commit()

        params = user.get_api_data()

        params.update({
            'password_confirmation': 'qweqwe123',
            'new_password': 'qweqwe123',
            'language': 'en',
            'csrf_token': autologin_user.csrf_token,
        })

        response = self.app.post(
            route_path('user_update', user_id=user.user_id), params)
        assert response.status_int == 302
        assert_session_flash(response, 'User updated successfully')

        # new password should be bcrypted, after log-in and transfer
        user = User.get_by_username(temp_user)
        assert user.password.startswith('$')

        updated_user = User.get_by_username(temp_user)
        updated_params = updated_user.get_api_data()
        updated_params.update({'password_confirmation': 'qweqwe123'})
        updated_params.update({'new_password': 'qweqwe123'})

        del params['csrf_token']
        assert params == updated_params

    def test_delete(self):
        self.log_user()
        username = 'newtestuserdeleteme'

        fixture.create_user(name=username)

        new_user = Session().query(User)\
            .filter(User.username == username).one()
        response = self.app.post(
            route_path('user_delete', user_id=new_user.user_id),
            params={'csrf_token': self.csrf_token})

        assert_session_flash(response, 'Successfully deleted user')

    def test_delete_owner_of_repository(self, request, user_util):
        self.log_user()
        obj_name = 'test_repo'
        usr = user_util.create_user()
        username = usr.username
        fixture.create_repo(obj_name, cur_user=usr.username)

        new_user = Session().query(User)\
            .filter(User.username == username).one()
        response = self.app.post(
            route_path('user_delete', user_id=new_user.user_id),
            params={'csrf_token': self.csrf_token})

        msg = 'user "%s" still owns 1 repositories and cannot be removed. ' \
              'Switch owners or remove those repositories:%s' % (username,
                                                                 obj_name)
        assert_session_flash(response, msg)
        fixture.destroy_repo(obj_name)

    def test_delete_owner_of_repository_detaching(self, request, user_util):
        self.log_user()
        obj_name = 'test_repo'
        usr = user_util.create_user(auto_cleanup=False)
        username = usr.username
        fixture.create_repo(obj_name, cur_user=usr.username)

        new_user = Session().query(User)\
            .filter(User.username == username).one()
        response = self.app.post(
            route_path('user_delete', user_id=new_user.user_id),
            params={'user_repos': 'detach', 'csrf_token': self.csrf_token})

        msg = 'Detached 1 repositories'
        assert_session_flash(response, msg)
        fixture.destroy_repo(obj_name)

    def test_delete_owner_of_repository_deleting(self, request, user_util):
        self.log_user()
        obj_name = 'test_repo'
        usr = user_util.create_user(auto_cleanup=False)
        username = usr.username
        fixture.create_repo(obj_name, cur_user=usr.username)

        new_user = Session().query(User)\
            .filter(User.username == username).one()
        response = self.app.post(
            route_path('user_delete', user_id=new_user.user_id),
            params={'user_repos': 'delete', 'csrf_token': self.csrf_token})

        msg = 'Deleted 1 repositories'
        assert_session_flash(response, msg)

    def test_delete_owner_of_repository_group(self, request, user_util):
        self.log_user()
        obj_name = 'test_group'
        usr = user_util.create_user()
        username = usr.username
        fixture.create_repo_group(obj_name, cur_user=usr.username)

        new_user = Session().query(User)\
            .filter(User.username == username).one()
        response = self.app.post(
            route_path('user_delete', user_id=new_user.user_id),
            params={'csrf_token': self.csrf_token})

        msg = 'user "%s" still owns 1 repository groups and cannot be removed. ' \
              'Switch owners or remove those repository groups:%s' % (username,
                                                                      obj_name)
        assert_session_flash(response, msg)
        fixture.destroy_repo_group(obj_name)

    def test_delete_owner_of_repository_group_detaching(self, request, user_util):
        self.log_user()
        obj_name = 'test_group'
        usr = user_util.create_user(auto_cleanup=False)
        username = usr.username
        fixture.create_repo_group(obj_name, cur_user=usr.username)

        new_user = Session().query(User)\
            .filter(User.username == username).one()
        response = self.app.post(
            route_path('user_delete', user_id=new_user.user_id),
            params={'user_repo_groups': 'delete', 'csrf_token': self.csrf_token})

        msg = 'Deleted 1 repository groups'
        assert_session_flash(response, msg)

    def test_delete_owner_of_repository_group_deleting(self, request, user_util):
        self.log_user()
        obj_name = 'test_group'
        usr = user_util.create_user(auto_cleanup=False)
        username = usr.username
        fixture.create_repo_group(obj_name, cur_user=usr.username)

        new_user = Session().query(User)\
            .filter(User.username == username).one()
        response = self.app.post(
            route_path('user_delete', user_id=new_user.user_id),
            params={'user_repo_groups': 'detach', 'csrf_token': self.csrf_token})

        msg = 'Detached 1 repository groups'
        assert_session_flash(response, msg)
        fixture.destroy_repo_group(obj_name)

    def test_delete_owner_of_user_group(self, request, user_util):
        self.log_user()
        obj_name = 'test_user_group'
        usr = user_util.create_user()
        username = usr.username
        fixture.create_user_group(obj_name, cur_user=usr.username)

        new_user = Session().query(User)\
            .filter(User.username == username).one()
        response = self.app.post(
            route_path('user_delete', user_id=new_user.user_id),
            params={'csrf_token': self.csrf_token})

        msg = 'user "%s" still owns 1 user groups and cannot be removed. ' \
              'Switch owners or remove those user groups:%s' % (username,
                                                                obj_name)
        assert_session_flash(response, msg)
        fixture.destroy_user_group(obj_name)

    def test_delete_owner_of_user_group_detaching(self, request, user_util):
        self.log_user()
        obj_name = 'test_user_group'
        usr = user_util.create_user(auto_cleanup=False)
        username = usr.username
        fixture.create_user_group(obj_name, cur_user=usr.username)

        new_user = Session().query(User)\
            .filter(User.username == username).one()
        try:
            response = self.app.post(
                route_path('user_delete', user_id=new_user.user_id),
                params={'user_user_groups': 'detach',
                        'csrf_token': self.csrf_token})

            msg = 'Detached 1 user groups'
            assert_session_flash(response, msg)
        finally:
            fixture.destroy_user_group(obj_name)

    def test_delete_owner_of_user_group_deleting(self, request, user_util):
        self.log_user()
        obj_name = 'test_user_group'
        usr = user_util.create_user(auto_cleanup=False)
        username = usr.username
        fixture.create_user_group(obj_name, cur_user=usr.username)

        new_user = Session().query(User)\
            .filter(User.username == username).one()
        response = self.app.post(
            route_path('user_delete', user_id=new_user.user_id),
            params={'user_user_groups': 'delete', 'csrf_token': self.csrf_token})

        msg = 'Deleted 1 user groups'
        assert_session_flash(response, msg)

    def test_edit(self, user_util):
        self.log_user()
        user = user_util.create_user()
        self.app.get(route_path('user_edit', user_id=user.user_id))

    def test_edit_default_user_redirect(self):
        self.log_user()
        user = User.get_default_user()
        self.app.get(route_path('user_edit', user_id=user.user_id), status=302)

    @pytest.mark.parametrize(
        'repo_create, repo_create_write, user_group_create, repo_group_create,'
        'fork_create, inherit_default_permissions, expect_error,'
        'expect_form_error', [
            ('hg.create.none', 'hg.create.write_on_repogroup.false',
             'hg.usergroup.create.false', 'hg.repogroup.create.false',
             'hg.fork.none', 'hg.inherit_default_perms.false', False, False),
            ('hg.create.repository', 'hg.create.write_on_repogroup.false',
             'hg.usergroup.create.false', 'hg.repogroup.create.false',
             'hg.fork.none', 'hg.inherit_default_perms.false', False, False),
            ('hg.create.repository', 'hg.create.write_on_repogroup.true',
             'hg.usergroup.create.true', 'hg.repogroup.create.true',
             'hg.fork.repository', 'hg.inherit_default_perms.false', False,
             False),
            ('hg.create.XXX', 'hg.create.write_on_repogroup.true',
             'hg.usergroup.create.true', 'hg.repogroup.create.true',
             'hg.fork.repository', 'hg.inherit_default_perms.false', False,
             True),
            ('', '', '', '', '', '', True, False),
        ])
    def test_global_perms_on_user(
            self, repo_create, repo_create_write, user_group_create,
            repo_group_create, fork_create, expect_error, expect_form_error,
            inherit_default_permissions, user_util):
        self.log_user()
        user = user_util.create_user()
        uid = user.user_id

        # ENABLE REPO CREATE ON A GROUP
        perm_params = {
            'inherit_default_permissions': False,
            'default_repo_create': repo_create,
            'default_repo_create_on_write': repo_create_write,
            'default_user_group_create': user_group_create,
            'default_repo_group_create': repo_group_create,
            'default_fork_create': fork_create,
            'default_inherit_default_permissions': inherit_default_permissions,
            'csrf_token': self.csrf_token,
        }
        response = self.app.post(
            route_path('user_edit_global_perms_update', user_id=uid),
            params=perm_params)

        if expect_form_error:
            assert response.status_int == 200
            response.mustcontain('Value must be one of')
        else:
            if expect_error:
                msg = 'An error occurred during permissions saving'
            else:
                msg = 'User global permissions updated successfully'
                ug = User.get(uid)
                del perm_params['inherit_default_permissions']
                del perm_params['csrf_token']
                assert perm_params == ug.get_default_perms()
            assert_session_flash(response, msg)

    def test_global_permissions_initial_values(self, user_util):
        self.log_user()
        user = user_util.create_user()
        uid = user.user_id
        response = self.app.get(
            route_path('user_edit_global_perms', user_id=uid))
        default_user = User.get_default_user()
        default_permissions = default_user.get_default_perms()
        assert_response = response.assert_response()
        expected_permissions = (
            'default_repo_create', 'default_repo_create_on_write',
            'default_fork_create', 'default_repo_group_create',
            'default_user_group_create', 'default_inherit_default_permissions')
        for permission in expected_permissions:
            css_selector = '[name={}][checked=checked]'.format(permission)
            element = assert_response.get_element(css_selector)
            assert element.value == default_permissions[permission]

    def test_perms_summary_page(self):
        user = self.log_user()
        response = self.app.get(
            route_path('edit_user_perms_summary', user_id=user['user_id']))
        for repo in Repository.query().all():
            response.mustcontain(repo.repo_name)

    def test_perms_summary_page_json(self):
        user = self.log_user()
        response = self.app.get(
            route_path('edit_user_perms_summary_json', user_id=user['user_id']))
        for repo in Repository.query().all():
            response.mustcontain(repo.repo_name)

    def test_audit_log_page(self):
        user = self.log_user()
        self.app.get(
            route_path('edit_user_audit_logs', user_id=user['user_id']))
