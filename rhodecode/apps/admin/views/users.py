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

import logging
import datetime
import formencode
import formencode.htmlfill

from pyramid.httpexceptions import HTTPFound
from pyramid.renderers import render
from pyramid.response import Response

from rhodecode import events
from rhodecode.apps._base import BaseAppView, DataGridAppView, UserAppView
from rhodecode.apps.ssh_support import SshKeyFileChangeEvent
from rhodecode.authentication.base import get_authn_registry, RhodeCodeExternalAuthPlugin
from rhodecode.authentication.plugins import auth_rhodecode
from rhodecode.events import trigger
from rhodecode.model.db import true, UserNotice

from rhodecode.lib import audit_logger, rc_cache, auth
from rhodecode.lib.exceptions import (
    UserCreationError, UserOwnsReposException, UserOwnsRepoGroupsException,
    UserOwnsUserGroupsException, UserOwnsPullRequestsException,
    UserOwnsArtifactsException, DefaultUserException)
from rhodecode.lib.ext_json import json
from rhodecode.lib.auth import (
    LoginRequired, HasPermissionAllDecorator, CSRFRequired)
from rhodecode.lib import helpers as h
from rhodecode.lib.helpers import SqlPage
from rhodecode.lib.utils2 import safe_int, safe_unicode, AttributeDict
from rhodecode.model.auth_token import AuthTokenModel
from rhodecode.model.forms import (
    UserForm, UserIndividualPermissionsForm, UserPermissionsForm,
    UserExtraEmailForm, UserExtraIpForm)
from rhodecode.model.permission import PermissionModel
from rhodecode.model.repo_group import RepoGroupModel
from rhodecode.model.ssh_key import SshKeyModel
from rhodecode.model.user import UserModel
from rhodecode.model.user_group import UserGroupModel
from rhodecode.model.db import (
    or_, coalesce,IntegrityError, User, UserGroup, UserIpMap, UserEmailMap,
    UserApiKeys, UserSshKeys, RepoGroup)
from rhodecode.model.meta import Session

log = logging.getLogger(__name__)


class AdminUsersView(BaseAppView, DataGridAppView):

    def load_default_context(self):
        c = self._get_local_tmpl_context()
        return c

    @LoginRequired()
    @HasPermissionAllDecorator('hg.admin')
    def users_list(self):
        c = self.load_default_context()
        return self._get_template_context(c)

    @LoginRequired()
    @HasPermissionAllDecorator('hg.admin')
    def users_list_data(self):
        self.load_default_context()
        column_map = {
            'first_name': 'name',
            'last_name': 'lastname',
        }
        draw, start, limit = self._extract_chunk(self.request)
        search_q, order_by, order_dir = self._extract_ordering(
            self.request, column_map=column_map)
        _render = self.request.get_partial_renderer(
            'rhodecode:templates/data_table/_dt_elements.mako')

        def user_actions(user_id, username):
            return _render("user_actions", user_id, username)

        users_data_total_count = User.query()\
            .filter(User.username != User.DEFAULT_USER) \
            .count()

        users_data_total_inactive_count = User.query()\
            .filter(User.username != User.DEFAULT_USER) \
            .filter(User.active != true())\
            .count()

        # json generate
        base_q = User.query().filter(User.username != User.DEFAULT_USER)
        base_inactive_q = base_q.filter(User.active != true())

        if search_q:
            like_expression = u'%{}%'.format(safe_unicode(search_q))
            base_q = base_q.filter(or_(
                User.username.ilike(like_expression),
                User._email.ilike(like_expression),
                User.name.ilike(like_expression),
                User.lastname.ilike(like_expression),
            ))
            base_inactive_q = base_q.filter(User.active != true())

        users_data_total_filtered_count = base_q.count()
        users_data_total_filtered_inactive_count = base_inactive_q.count()

        sort_col = getattr(User, order_by, None)
        if sort_col:
            if order_dir == 'asc':
                # handle null values properly to order by NULL last
                if order_by in ['last_activity']:
                    sort_col = coalesce(sort_col, datetime.date.max)
                sort_col = sort_col.asc()
            else:
                # handle null values properly to order by NULL last
                if order_by in ['last_activity']:
                    sort_col = coalesce(sort_col, datetime.date.min)
                sort_col = sort_col.desc()

        base_q = base_q.order_by(sort_col)
        base_q = base_q.offset(start).limit(limit)

        users_list = base_q.all()

        users_data = []
        for user in users_list:
            users_data.append({
                "username": h.gravatar_with_user(self.request, user.username),
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "last_login": h.format_date(user.last_login),
                "last_activity": h.format_date(user.last_activity),
                "active": h.bool2icon(user.active),
                "active_raw": user.active,
                "admin": h.bool2icon(user.admin),
                "extern_type": user.extern_type,
                "extern_name": user.extern_name,
                "action": user_actions(user.user_id, user.username),
            })
        data = ({
            'draw': draw,
            'data': users_data,
            'recordsTotal': users_data_total_count,
            'recordsFiltered': users_data_total_filtered_count,
            'recordsTotalInactive': users_data_total_inactive_count,
            'recordsFilteredInactive': users_data_total_filtered_inactive_count
        })

        return data

    def _set_personal_repo_group_template_vars(self, c_obj):
        DummyUser = AttributeDict({
            'username': '${username}',
            'user_id': '${user_id}',
        })
        c_obj.default_create_repo_group = RepoGroupModel() \
            .get_default_create_personal_repo_group()
        c_obj.personal_repo_group_name = RepoGroupModel() \
            .get_personal_group_name(DummyUser)

    @LoginRequired()
    @HasPermissionAllDecorator('hg.admin')
    def users_new(self):
        _ = self.request.translate
        c = self.load_default_context()
        c.default_extern_type = auth_rhodecode.RhodeCodeAuthPlugin.uid
        self._set_personal_repo_group_template_vars(c)
        return self._get_template_context(c)

    @LoginRequired()
    @HasPermissionAllDecorator('hg.admin')
    @CSRFRequired()
    def users_create(self):
        _ = self.request.translate
        c = self.load_default_context()
        c.default_extern_type = auth_rhodecode.RhodeCodeAuthPlugin.uid
        user_model = UserModel()
        user_form = UserForm(self.request.translate)()
        try:
            form_result = user_form.to_python(dict(self.request.POST))
            user = user_model.create(form_result)
            Session().flush()
            creation_data = user.get_api_data()
            username = form_result['username']

            audit_logger.store_web(
                'user.create', action_data={'data': creation_data},
                user=c.rhodecode_user)

            user_link = h.link_to(
                h.escape(username),
                h.route_path('user_edit', user_id=user.user_id))
            h.flash(h.literal(_('Created user %(user_link)s')
                              % {'user_link': user_link}), category='success')
            Session().commit()
        except formencode.Invalid as errors:
            self._set_personal_repo_group_template_vars(c)
            data = render(
                'rhodecode:templates/admin/users/user_add.mako',
                self._get_template_context(c), self.request)
            html = formencode.htmlfill.render(
                data,
                defaults=errors.value,
                errors=errors.error_dict or {},
                prefix_error=False,
                encoding="UTF-8",
                force_defaults=False
            )
            return Response(html)
        except UserCreationError as e:
            h.flash(e, 'error')
        except Exception:
            log.exception("Exception creation of user")
            h.flash(_('Error occurred during creation of user %s')
                    % self.request.POST.get('username'), category='error')
        raise HTTPFound(h.route_path('users'))


class UsersView(UserAppView):
    ALLOW_SCOPED_TOKENS = False
    """
    This view has alternative version inside EE, if modified please take a look
    in there as well.
    """

    def get_auth_plugins(self):
        valid_plugins = []
        authn_registry = get_authn_registry(self.request.registry)
        for plugin in authn_registry.get_plugins_for_authentication():
            if isinstance(plugin, RhodeCodeExternalAuthPlugin):
                valid_plugins.append(plugin)
            elif plugin.name == 'rhodecode':
                valid_plugins.append(plugin)

        # extend our choices if user has set a bound plugin which isn't enabled at the
        # moment
        extern_type = self.db_user.extern_type
        if extern_type not in [x.uid for x in valid_plugins]:
            try:
                plugin = authn_registry.get_plugin_by_uid(extern_type)
                if plugin:
                    valid_plugins.append(plugin)

            except Exception:
                log.exception(
                    'Could not extend user plugins with `{}`'.format(extern_type))
        return valid_plugins

    def load_default_context(self):
        req = self.request

        c = self._get_local_tmpl_context()
        c.allow_scoped_tokens = self.ALLOW_SCOPED_TOKENS
        c.allowed_languages = [
            ('en', 'English (en)'),
            ('de', 'German (de)'),
            ('fr', 'French (fr)'),
            ('it', 'Italian (it)'),
            ('ja', 'Japanese (ja)'),
            ('pl', 'Polish (pl)'),
            ('pt', 'Portuguese (pt)'),
            ('ru', 'Russian (ru)'),
            ('zh', 'Chinese (zh)'),
        ]

        c.allowed_extern_types = [
            (x.uid, x.get_display_name()) for x in self.get_auth_plugins()
        ]
        perms = req.registry.settings.get('available_permissions')
        if not perms:
            # inject info about available permissions
            auth.set_available_permissions(req.registry.settings)

        c.available_permissions = req.registry.settings['available_permissions']
        PermissionModel().set_global_permission_choices(
            c, gettext_translator=req.translate)

        return c

    @LoginRequired()
    @HasPermissionAllDecorator('hg.admin')
    @CSRFRequired()
    def user_update(self):
        _ = self.request.translate
        c = self.load_default_context()

        user_id = self.db_user_id
        c.user = self.db_user

        c.active = 'profile'
        c.extern_type = c.user.extern_type
        c.extern_name = c.user.extern_name
        c.perm_user = c.user.AuthUser(ip_addr=self.request.remote_addr)
        available_languages = [x[0] for x in c.allowed_languages]
        _form = UserForm(self.request.translate, edit=True,
                         available_languages=available_languages,
                         old_data={'user_id': user_id,
                                   'email': c.user.email})()

        c.edit_mode = self.request.POST.get('edit') == '1'
        form_result = {}
        old_values = c.user.get_api_data()
        try:
            form_result = _form.to_python(dict(self.request.POST))
            skip_attrs = ['extern_name']
            # TODO: plugin should define if username can be updated

            if c.extern_type != "rhodecode" and not c.edit_mode:
                # forbid updating username for external accounts
                skip_attrs.append('username')

            UserModel().update_user(
                user_id, skip_attrs=skip_attrs, **form_result)

            audit_logger.store_web(
                'user.edit', action_data={'old_data': old_values},
                user=c.rhodecode_user)

            Session().commit()
            h.flash(_('User updated successfully'), category='success')
        except formencode.Invalid as errors:
            data = render(
                'rhodecode:templates/admin/users/user_edit.mako',
                self._get_template_context(c), self.request)
            html = formencode.htmlfill.render(
                data,
                defaults=errors.value,
                errors=errors.error_dict or {},
                prefix_error=False,
                encoding="UTF-8",
                force_defaults=False
            )
            return Response(html)
        except UserCreationError as e:
            h.flash(e, 'error')
        except Exception:
            log.exception("Exception updating user")
            h.flash(_('Error occurred during update of user %s')
                    % form_result.get('username'), category='error')
        raise HTTPFound(h.route_path('user_edit', user_id=user_id))

    @LoginRequired()
    @HasPermissionAllDecorator('hg.admin')
    @CSRFRequired()
    def user_delete(self):
        _ = self.request.translate
        c = self.load_default_context()
        c.user = self.db_user

        _repos = c.user.repositories
        _repo_groups = c.user.repository_groups
        _user_groups = c.user.user_groups
        _pull_requests = c.user.user_pull_requests
        _artifacts = c.user.artifacts

        handle_repos = None
        handle_repo_groups = None
        handle_user_groups = None
        handle_pull_requests = None
        handle_artifacts = None

        # calls for flash of handle based on handle case detach or delete
        def set_handle_flash_repos():
            handle = handle_repos
            if handle == 'detach':
                h.flash(_('Detached %s repositories') % len(_repos),
                        category='success')
            elif handle == 'delete':
                h.flash(_('Deleted %s repositories') % len(_repos),
                        category='success')

        def set_handle_flash_repo_groups():
            handle = handle_repo_groups
            if handle == 'detach':
                h.flash(_('Detached %s repository groups') % len(_repo_groups),
                        category='success')
            elif handle == 'delete':
                h.flash(_('Deleted %s repository groups') % len(_repo_groups),
                        category='success')

        def set_handle_flash_user_groups():
            handle = handle_user_groups
            if handle == 'detach':
                h.flash(_('Detached %s user groups') % len(_user_groups),
                        category='success')
            elif handle == 'delete':
                h.flash(_('Deleted %s user groups') % len(_user_groups),
                        category='success')

        def set_handle_flash_pull_requests():
            handle = handle_pull_requests
            if handle == 'detach':
                h.flash(_('Detached %s pull requests') % len(_pull_requests),
                        category='success')
            elif handle == 'delete':
                h.flash(_('Deleted %s pull requests') % len(_pull_requests),
                        category='success')

        def set_handle_flash_artifacts():
            handle = handle_artifacts
            if handle == 'detach':
                h.flash(_('Detached %s artifacts') % len(_artifacts),
                        category='success')
            elif handle == 'delete':
                h.flash(_('Deleted %s artifacts') % len(_artifacts),
                        category='success')

        handle_user = User.get_first_super_admin()
        handle_user_id = safe_int(self.request.POST.get('detach_user_id'))
        if handle_user_id:
            # NOTE(marcink): we get new owner for objects...
            handle_user = User.get_or_404(handle_user_id)

        if _repos and self.request.POST.get('user_repos'):
            handle_repos = self.request.POST['user_repos']

        if _repo_groups and self.request.POST.get('user_repo_groups'):
            handle_repo_groups = self.request.POST['user_repo_groups']

        if _user_groups and self.request.POST.get('user_user_groups'):
            handle_user_groups = self.request.POST['user_user_groups']

        if _pull_requests and self.request.POST.get('user_pull_requests'):
            handle_pull_requests = self.request.POST['user_pull_requests']

        if _artifacts and self.request.POST.get('user_artifacts'):
            handle_artifacts = self.request.POST['user_artifacts']

        old_values = c.user.get_api_data()

        try:

            UserModel().delete(
                c.user,
                handle_repos=handle_repos,
                handle_repo_groups=handle_repo_groups,
                handle_user_groups=handle_user_groups,
                handle_pull_requests=handle_pull_requests,
                handle_artifacts=handle_artifacts,
                handle_new_owner=handle_user
            )

            audit_logger.store_web(
                'user.delete', action_data={'old_data': old_values},
                user=c.rhodecode_user)

            Session().commit()
            set_handle_flash_repos()
            set_handle_flash_repo_groups()
            set_handle_flash_user_groups()
            set_handle_flash_pull_requests()
            set_handle_flash_artifacts()
            username = h.escape(old_values['username'])
            h.flash(_('Successfully deleted user `{}`').format(username), category='success')
        except (UserOwnsReposException, UserOwnsRepoGroupsException,
                UserOwnsUserGroupsException, UserOwnsPullRequestsException,
                UserOwnsArtifactsException, DefaultUserException) as e:
            h.flash(e, category='warning')
        except Exception:
            log.exception("Exception during deletion of user")
            h.flash(_('An error occurred during deletion of user'),
                    category='error')
        raise HTTPFound(h.route_path('users'))

    @LoginRequired()
    @HasPermissionAllDecorator('hg.admin')
    def user_edit(self):
        _ = self.request.translate
        c = self.load_default_context()
        c.user = self.db_user

        c.active = 'profile'
        c.extern_type = c.user.extern_type
        c.extern_name = c.user.extern_name
        c.perm_user = c.user.AuthUser(ip_addr=self.request.remote_addr)
        c.edit_mode = self.request.GET.get('edit') == '1'

        defaults = c.user.get_dict()
        defaults.update({'language': c.user.user_data.get('language')})

        data = render(
            'rhodecode:templates/admin/users/user_edit.mako',
            self._get_template_context(c), self.request)
        html = formencode.htmlfill.render(
            data,
            defaults=defaults,
            encoding="UTF-8",
            force_defaults=False
        )
        return Response(html)

    @LoginRequired()
    @HasPermissionAllDecorator('hg.admin')
    def user_edit_advanced(self):
        _ = self.request.translate
        c = self.load_default_context()

        user_id = self.db_user_id
        c.user = self.db_user

        c.detach_user = User.get_first_super_admin()
        detach_user_id = safe_int(self.request.GET.get('detach_user_id'))
        if detach_user_id:
            c.detach_user = User.get_or_404(detach_user_id)

        c.active = 'advanced'
        c.personal_repo_group = RepoGroup.get_user_personal_repo_group(user_id)
        c.personal_repo_group_name = RepoGroupModel()\
            .get_personal_group_name(c.user)

        c.user_to_review_rules = sorted(
            (x.user for x in c.user.user_review_rules),
            key=lambda u: u.username.lower())

        defaults = c.user.get_dict()

        # Interim workaround if the user participated on any pull requests as a
        # reviewer.
        has_review = len(c.user.reviewer_pull_requests)
        c.can_delete_user = not has_review
        c.can_delete_user_message = ''
        inactive_link = h.link_to(
            'inactive', h.route_path('user_edit', user_id=user_id, _anchor='active'))
        if has_review == 1:
            c.can_delete_user_message = h.literal(_(
                'The user participates as reviewer in {} pull request and '
                'cannot be deleted. \nYou can set the user to '
                '"{}" instead of deleting it.').format(
                has_review, inactive_link))
        elif has_review:
            c.can_delete_user_message = h.literal(_(
                'The user participates as reviewer in {} pull requests and '
                'cannot be deleted. \nYou can set the user to '
                '"{}" instead of deleting it.').format(
                has_review, inactive_link))

        data = render(
            'rhodecode:templates/admin/users/user_edit.mako',
            self._get_template_context(c), self.request)
        html = formencode.htmlfill.render(
            data,
            defaults=defaults,
            encoding="UTF-8",
            force_defaults=False
        )
        return Response(html)

    @LoginRequired()
    @HasPermissionAllDecorator('hg.admin')
    def user_edit_global_perms(self):
        _ = self.request.translate
        c = self.load_default_context()
        c.user = self.db_user

        c.active = 'global_perms'

        c.default_user = User.get_default_user()
        defaults = c.user.get_dict()
        defaults.update(c.default_user.get_default_perms(suffix='_inherited'))
        defaults.update(c.default_user.get_default_perms())
        defaults.update(c.user.get_default_perms())

        data = render(
            'rhodecode:templates/admin/users/user_edit.mako',
            self._get_template_context(c), self.request)
        html = formencode.htmlfill.render(
            data,
            defaults=defaults,
            encoding="UTF-8",
            force_defaults=False
        )
        return Response(html)

    @LoginRequired()
    @HasPermissionAllDecorator('hg.admin')
    @CSRFRequired()
    def user_edit_global_perms_update(self):
        _ = self.request.translate
        c = self.load_default_context()

        user_id = self.db_user_id
        c.user = self.db_user

        c.active = 'global_perms'
        try:
            # first stage that verifies the checkbox
            _form = UserIndividualPermissionsForm(self.request.translate)
            form_result = _form.to_python(dict(self.request.POST))
            inherit_perms = form_result['inherit_default_permissions']
            c.user.inherit_default_permissions = inherit_perms
            Session().add(c.user)

            if not inherit_perms:
                # only update the individual ones if we un check the flag
                _form = UserPermissionsForm(
                    self.request.translate,
                    [x[0] for x in c.repo_create_choices],
                    [x[0] for x in c.repo_create_on_write_choices],
                    [x[0] for x in c.repo_group_create_choices],
                    [x[0] for x in c.user_group_create_choices],
                    [x[0] for x in c.fork_choices],
                    [x[0] for x in c.inherit_default_permission_choices])()

                form_result = _form.to_python(dict(self.request.POST))
                form_result.update({'perm_user_id': c.user.user_id})

                PermissionModel().update_user_permissions(form_result)

            # TODO(marcink): implement global permissions
            # audit_log.store_web('user.edit.permissions')

            Session().commit()

            h.flash(_('User global permissions updated successfully'),
                    category='success')

        except formencode.Invalid as errors:
            data = render(
                'rhodecode:templates/admin/users/user_edit.mako',
                self._get_template_context(c), self.request)
            html = formencode.htmlfill.render(
                data,
                defaults=errors.value,
                errors=errors.error_dict or {},
                prefix_error=False,
                encoding="UTF-8",
                force_defaults=False
            )
            return Response(html)
        except Exception:
            log.exception("Exception during permissions saving")
            h.flash(_('An error occurred during permissions saving'),
                    category='error')

        affected_user_ids = [user_id]
        PermissionModel().trigger_permission_flush(affected_user_ids)
        raise HTTPFound(h.route_path('user_edit_global_perms', user_id=user_id))

    @LoginRequired()
    @HasPermissionAllDecorator('hg.admin')
    @CSRFRequired()
    def user_enable_force_password_reset(self):
        _ = self.request.translate
        c = self.load_default_context()

        user_id = self.db_user_id
        c.user = self.db_user

        try:
            c.user.update_userdata(force_password_change=True)

            msg = _('Force password change enabled for user')
            audit_logger.store_web('user.edit.password_reset.enabled',
                                   user=c.rhodecode_user)

            Session().commit()
            h.flash(msg, category='success')
        except Exception:
            log.exception("Exception during password reset for user")
            h.flash(_('An error occurred during password reset for user'),
                    category='error')

        raise HTTPFound(h.route_path('user_edit_advanced', user_id=user_id))

    @LoginRequired()
    @HasPermissionAllDecorator('hg.admin')
    @CSRFRequired()
    def user_disable_force_password_reset(self):
        _ = self.request.translate
        c = self.load_default_context()

        user_id = self.db_user_id
        c.user = self.db_user

        try:
            c.user.update_userdata(force_password_change=False)

            msg = _('Force password change disabled for user')
            audit_logger.store_web(
                'user.edit.password_reset.disabled',
                user=c.rhodecode_user)

            Session().commit()
            h.flash(msg, category='success')
        except Exception:
            log.exception("Exception during password reset for user")
            h.flash(_('An error occurred during password reset for user'),
                    category='error')

        raise HTTPFound(h.route_path('user_edit_advanced', user_id=user_id))

    @LoginRequired()
    @HasPermissionAllDecorator('hg.admin')
    @CSRFRequired()
    def user_notice_dismiss(self):
        _ = self.request.translate
        c = self.load_default_context()

        user_id = self.db_user_id
        c.user = self.db_user
        user_notice_id = safe_int(self.request.POST.get('notice_id'))
        notice = UserNotice().query()\
            .filter(UserNotice.user_id == user_id)\
            .filter(UserNotice.user_notice_id == user_notice_id)\
            .scalar()
        read = False
        if notice:
            notice.notice_read = True
            Session().add(notice)
            Session().commit()
            read = True

        return {'notice': user_notice_id, 'read': read}

    @LoginRequired()
    @HasPermissionAllDecorator('hg.admin')
    @CSRFRequired()
    def user_create_personal_repo_group(self):
        """
        Create personal repository group for this user
        """
        from rhodecode.model.repo_group import RepoGroupModel

        _ = self.request.translate
        c = self.load_default_context()

        user_id = self.db_user_id
        c.user = self.db_user

        personal_repo_group = RepoGroup.get_user_personal_repo_group(
            c.user.user_id)
        if personal_repo_group:
            raise HTTPFound(h.route_path('user_edit_advanced', user_id=user_id))

        personal_repo_group_name = RepoGroupModel().get_personal_group_name(c.user)
        named_personal_group = RepoGroup.get_by_group_name(
            personal_repo_group_name)
        try:

            if named_personal_group and named_personal_group.user_id == c.user.user_id:
                # migrate the same named group, and mark it as personal
                named_personal_group.personal = True
                Session().add(named_personal_group)
                Session().commit()
                msg = _('Linked repository group `%s` as personal' % (
                    personal_repo_group_name,))
                h.flash(msg, category='success')
            elif not named_personal_group:
                RepoGroupModel().create_personal_repo_group(c.user)

                msg = _('Created repository group `%s`' % (
                    personal_repo_group_name,))
                h.flash(msg, category='success')
            else:
                msg = _('Repository group `%s` is already taken' % (
                    personal_repo_group_name,))
                h.flash(msg, category='warning')
        except Exception:
            log.exception("Exception during repository group creation")
            msg = _(
                'An error occurred during repository group creation for user')
            h.flash(msg, category='error')
            Session().rollback()

        raise HTTPFound(h.route_path('user_edit_advanced', user_id=user_id))

    @LoginRequired()
    @HasPermissionAllDecorator('hg.admin')
    def auth_tokens(self):
        _ = self.request.translate
        c = self.load_default_context()
        c.user = self.db_user

        c.active = 'auth_tokens'

        c.lifetime_values = AuthTokenModel.get_lifetime_values(translator=_)
        c.role_values = [
            (x, AuthTokenModel.cls._get_role_name(x))
            for x in AuthTokenModel.cls.ROLES]
        c.role_options = [(c.role_values, _("Role"))]
        c.user_auth_tokens = AuthTokenModel().get_auth_tokens(
            c.user.user_id, show_expired=True)
        c.role_vcs = AuthTokenModel.cls.ROLE_VCS
        return self._get_template_context(c)

    @LoginRequired()
    @HasPermissionAllDecorator('hg.admin')
    def auth_tokens_view(self):
        _ = self.request.translate
        c = self.load_default_context()
        c.user = self.db_user

        auth_token_id = self.request.POST.get('auth_token_id')

        if auth_token_id:
            token = UserApiKeys.get_or_404(auth_token_id)

            return {
                'auth_token': token.api_key
            }

    def maybe_attach_token_scope(self, token):
        # implemented in EE edition
        pass

    @LoginRequired()
    @HasPermissionAllDecorator('hg.admin')
    @CSRFRequired()
    def auth_tokens_add(self):
        _ = self.request.translate
        c = self.load_default_context()

        user_id = self.db_user_id
        c.user = self.db_user

        user_data = c.user.get_api_data()
        lifetime = safe_int(self.request.POST.get('lifetime'), -1)
        description = self.request.POST.get('description')
        role = self.request.POST.get('role')

        token = UserModel().add_auth_token(
            user=c.user.user_id,
            lifetime_minutes=lifetime, role=role, description=description,
            scope_callback=self.maybe_attach_token_scope)
        token_data = token.get_api_data()

        audit_logger.store_web(
            'user.edit.token.add', action_data={
                'data': {'token': token_data, 'user': user_data}},
            user=self._rhodecode_user, )
        Session().commit()

        h.flash(_("Auth token successfully created"), category='success')
        return HTTPFound(h.route_path('edit_user_auth_tokens', user_id=user_id))

    @LoginRequired()
    @HasPermissionAllDecorator('hg.admin')
    @CSRFRequired()
    def auth_tokens_delete(self):
        _ = self.request.translate
        c = self.load_default_context()

        user_id = self.db_user_id
        c.user = self.db_user

        user_data = c.user.get_api_data()

        del_auth_token = self.request.POST.get('del_auth_token')

        if del_auth_token:
            token = UserApiKeys.get_or_404(del_auth_token)
            token_data = token.get_api_data()

            AuthTokenModel().delete(del_auth_token, c.user.user_id)
            audit_logger.store_web(
                'user.edit.token.delete', action_data={
                    'data': {'token': token_data, 'user': user_data}},
                user=self._rhodecode_user,)
            Session().commit()
            h.flash(_("Auth token successfully deleted"), category='success')

        return HTTPFound(h.route_path('edit_user_auth_tokens', user_id=user_id))

    @LoginRequired()
    @HasPermissionAllDecorator('hg.admin')
    def ssh_keys(self):
        _ = self.request.translate
        c = self.load_default_context()
        c.user = self.db_user

        c.active = 'ssh_keys'
        c.default_key = self.request.GET.get('default_key')
        c.user_ssh_keys = SshKeyModel().get_ssh_keys(c.user.user_id)
        return self._get_template_context(c)

    @LoginRequired()
    @HasPermissionAllDecorator('hg.admin')
    def ssh_keys_generate_keypair(self):
        _ = self.request.translate
        c = self.load_default_context()

        c.user = self.db_user

        c.active = 'ssh_keys_generate'
        comment = 'RhodeCode-SSH {}'.format(c.user.email or '')
        private_format = self.request.GET.get('private_format') \
                         or SshKeyModel.DEFAULT_PRIVATE_KEY_FORMAT
        c.private, c.public = SshKeyModel().generate_keypair(
            comment=comment, private_format=private_format)

        return self._get_template_context(c)

    @LoginRequired()
    @HasPermissionAllDecorator('hg.admin')
    @CSRFRequired()
    def ssh_keys_add(self):
        _ = self.request.translate
        c = self.load_default_context()

        user_id = self.db_user_id
        c.user = self.db_user

        user_data = c.user.get_api_data()
        key_data = self.request.POST.get('key_data')
        description = self.request.POST.get('description')

        fingerprint = 'unknown'
        try:
            if not key_data:
                raise ValueError('Please add a valid public key')

            key = SshKeyModel().parse_key(key_data.strip())
            fingerprint = key.hash_md5()

            ssh_key = SshKeyModel().create(
                c.user.user_id, fingerprint, key.keydata, description)
            ssh_key_data = ssh_key.get_api_data()

            audit_logger.store_web(
                'user.edit.ssh_key.add', action_data={
                    'data': {'ssh_key': ssh_key_data, 'user': user_data}},
                user=self._rhodecode_user, )
            Session().commit()

            # Trigger an event on change of keys.
            trigger(SshKeyFileChangeEvent(), self.request.registry)

            h.flash(_("Ssh Key successfully created"), category='success')

        except IntegrityError:
            log.exception("Exception during ssh key saving")
            err = 'Such key with fingerprint `{}` already exists, ' \
                  'please use a different one'.format(fingerprint)
            h.flash(_('An error occurred during ssh key saving: {}').format(err),
                    category='error')
        except Exception as e:
            log.exception("Exception during ssh key saving")
            h.flash(_('An error occurred during ssh key saving: {}').format(e),
                    category='error')

        return HTTPFound(
            h.route_path('edit_user_ssh_keys', user_id=user_id))

    @LoginRequired()
    @HasPermissionAllDecorator('hg.admin')
    @CSRFRequired()
    def ssh_keys_delete(self):
        _ = self.request.translate
        c = self.load_default_context()

        user_id = self.db_user_id
        c.user = self.db_user

        user_data = c.user.get_api_data()

        del_ssh_key = self.request.POST.get('del_ssh_key')

        if del_ssh_key:
            ssh_key = UserSshKeys.get_or_404(del_ssh_key)
            ssh_key_data = ssh_key.get_api_data()

            SshKeyModel().delete(del_ssh_key, c.user.user_id)
            audit_logger.store_web(
                'user.edit.ssh_key.delete', action_data={
                    'data': {'ssh_key': ssh_key_data, 'user': user_data}},
                user=self._rhodecode_user,)
            Session().commit()
            # Trigger an event on change of keys.
            trigger(SshKeyFileChangeEvent(), self.request.registry)
            h.flash(_("Ssh key successfully deleted"), category='success')

        return HTTPFound(h.route_path('edit_user_ssh_keys', user_id=user_id))

    @LoginRequired()
    @HasPermissionAllDecorator('hg.admin')
    def emails(self):
        _ = self.request.translate
        c = self.load_default_context()
        c.user = self.db_user

        c.active = 'emails'
        c.user_email_map = UserEmailMap.query() \
            .filter(UserEmailMap.user == c.user).all()

        return self._get_template_context(c)

    @LoginRequired()
    @HasPermissionAllDecorator('hg.admin')
    @CSRFRequired()
    def emails_add(self):
        _ = self.request.translate
        c = self.load_default_context()

        user_id = self.db_user_id
        c.user = self.db_user

        email = self.request.POST.get('new_email')
        user_data = c.user.get_api_data()
        try:

            form = UserExtraEmailForm(self.request.translate)()
            data = form.to_python({'email': email})
            email = data['email']

            UserModel().add_extra_email(c.user.user_id, email)
            audit_logger.store_web(
                'user.edit.email.add',
                action_data={'email': email, 'user': user_data},
                user=self._rhodecode_user)
            Session().commit()
            h.flash(_("Added new email address `%s` for user account") % email,
                    category='success')
        except formencode.Invalid as error:
            h.flash(h.escape(error.error_dict['email']), category='error')
        except IntegrityError:
            log.warning("Email %s already exists", email)
            h.flash(_('Email `{}` is already registered for another user.').format(email),
                    category='error')
        except Exception:
            log.exception("Exception during email saving")
            h.flash(_('An error occurred during email saving'),
                    category='error')
        raise HTTPFound(h.route_path('edit_user_emails', user_id=user_id))

    @LoginRequired()
    @HasPermissionAllDecorator('hg.admin')
    @CSRFRequired()
    def emails_delete(self):
        _ = self.request.translate
        c = self.load_default_context()

        user_id = self.db_user_id
        c.user = self.db_user

        email_id = self.request.POST.get('del_email_id')
        user_model = UserModel()

        email = UserEmailMap.query().get(email_id).email
        user_data = c.user.get_api_data()
        user_model.delete_extra_email(c.user.user_id, email_id)
        audit_logger.store_web(
            'user.edit.email.delete',
            action_data={'email': email, 'user': user_data},
            user=self._rhodecode_user)
        Session().commit()
        h.flash(_("Removed email address from user account"),
                category='success')
        raise HTTPFound(h.route_path('edit_user_emails', user_id=user_id))

    @LoginRequired()
    @HasPermissionAllDecorator('hg.admin')
    def ips(self):
        _ = self.request.translate
        c = self.load_default_context()
        c.user = self.db_user

        c.active = 'ips'
        c.user_ip_map = UserIpMap.query() \
            .filter(UserIpMap.user == c.user).all()

        c.inherit_default_ips = c.user.inherit_default_permissions
        c.default_user_ip_map = UserIpMap.query() \
            .filter(UserIpMap.user == User.get_default_user()).all()

        return self._get_template_context(c)

    @LoginRequired()
    @HasPermissionAllDecorator('hg.admin')
    @CSRFRequired()
    # NOTE(marcink): this view is allowed for default users, as we can
    # edit their IP white list
    def ips_add(self):
        _ = self.request.translate
        c = self.load_default_context()

        user_id = self.db_user_id
        c.user = self.db_user

        user_model = UserModel()
        desc = self.request.POST.get('description')
        try:
            ip_list = user_model.parse_ip_range(
                self.request.POST.get('new_ip'))
        except Exception as e:
            ip_list = []
            log.exception("Exception during ip saving")
            h.flash(_('An error occurred during ip saving:%s' % (e,)),
                    category='error')
        added = []
        user_data = c.user.get_api_data()
        for ip in ip_list:
            try:
                form = UserExtraIpForm(self.request.translate)()
                data = form.to_python({'ip': ip})
                ip = data['ip']

                user_model.add_extra_ip(c.user.user_id, ip, desc)
                audit_logger.store_web(
                    'user.edit.ip.add',
                    action_data={'ip': ip, 'user': user_data},
                    user=self._rhodecode_user)
                Session().commit()
                added.append(ip)
            except formencode.Invalid as error:
                msg = error.error_dict['ip']
                h.flash(msg, category='error')
            except Exception:
                log.exception("Exception during ip saving")
                h.flash(_('An error occurred during ip saving'),
                        category='error')
        if added:
            h.flash(
                _("Added ips %s to user whitelist") % (', '.join(ip_list), ),
                category='success')
        if 'default_user' in self.request.POST:
            # case for editing global IP list we do it for 'DEFAULT' user
            raise HTTPFound(h.route_path('admin_permissions_ips'))
        raise HTTPFound(h.route_path('edit_user_ips', user_id=user_id))

    @LoginRequired()
    @HasPermissionAllDecorator('hg.admin')
    @CSRFRequired()
    # NOTE(marcink): this view is allowed for default users, as we can
    # edit their IP white list
    def ips_delete(self):
        _ = self.request.translate
        c = self.load_default_context()

        user_id = self.db_user_id
        c.user = self.db_user

        ip_id = self.request.POST.get('del_ip_id')
        user_model = UserModel()
        user_data = c.user.get_api_data()
        ip = UserIpMap.query().get(ip_id).ip_addr
        user_model.delete_extra_ip(c.user.user_id, ip_id)
        audit_logger.store_web(
            'user.edit.ip.delete', action_data={'ip': ip, 'user': user_data},
            user=self._rhodecode_user)
        Session().commit()
        h.flash(_("Removed ip address from user whitelist"), category='success')

        if 'default_user' in self.request.POST:
            # case for editing global IP list we do it for 'DEFAULT' user
            raise HTTPFound(h.route_path('admin_permissions_ips'))
        raise HTTPFound(h.route_path('edit_user_ips', user_id=user_id))

    @LoginRequired()
    @HasPermissionAllDecorator('hg.admin')
    def groups_management(self):
        c = self.load_default_context()
        c.user = self.db_user
        c.data = c.user.group_member

        groups = [UserGroupModel.get_user_groups_as_dict(group.users_group)
                  for group in c.user.group_member]
        c.groups = json.dumps(groups)
        c.active = 'groups'

        return self._get_template_context(c)

    @LoginRequired()
    @HasPermissionAllDecorator('hg.admin')
    @CSRFRequired()
    def groups_management_updates(self):
        _ = self.request.translate
        c = self.load_default_context()

        user_id = self.db_user_id
        c.user = self.db_user

        user_groups = set(self.request.POST.getall('users_group_id'))
        user_groups_objects = []

        for ugid in user_groups:
            user_groups_objects.append(
                UserGroupModel().get_group(safe_int(ugid)))
        user_group_model = UserGroupModel()
        added_to_groups, removed_from_groups = \
            user_group_model.change_groups(c.user, user_groups_objects)

        user_data = c.user.get_api_data()
        for user_group_id in added_to_groups:
            user_group = UserGroup.get(user_group_id)
            old_values = user_group.get_api_data()
            audit_logger.store_web(
                'user_group.edit.member.add',
                action_data={'user': user_data, 'old_data': old_values},
                user=self._rhodecode_user)

        for user_group_id in removed_from_groups:
            user_group = UserGroup.get(user_group_id)
            old_values = user_group.get_api_data()
            audit_logger.store_web(
                'user_group.edit.member.delete',
                action_data={'user': user_data, 'old_data': old_values},
                user=self._rhodecode_user)

        Session().commit()
        c.active = 'user_groups_management'
        h.flash(_("Groups successfully changed"), category='success')

        return HTTPFound(h.route_path(
            'edit_user_groups_management', user_id=user_id))

    @LoginRequired()
    @HasPermissionAllDecorator('hg.admin')
    def user_audit_logs(self):
        _ = self.request.translate
        c = self.load_default_context()
        c.user = self.db_user

        c.active = 'audit'

        p = safe_int(self.request.GET.get('page', 1), 1)

        filter_term = self.request.GET.get('filter')
        user_log = UserModel().get_user_log(c.user, filter_term)

        def url_generator(page_num):
            query_params = {
                'page': page_num
            }
            if filter_term:
                query_params['filter'] = filter_term
            return self.request.current_route_path(_query=query_params)

        c.audit_logs = SqlPage(
            user_log, page=p, items_per_page=10, url_maker=url_generator)
        c.filter_term = filter_term
        return self._get_template_context(c)

    @LoginRequired()
    @HasPermissionAllDecorator('hg.admin')
    def user_audit_logs_download(self):
        _ = self.request.translate
        c = self.load_default_context()
        c.user = self.db_user

        user_log = UserModel().get_user_log(c.user, filter_term=None)

        audit_log_data = {}
        for entry in user_log:
            audit_log_data[entry.user_log_id] = entry.get_dict()

        response = Response(json.dumps(audit_log_data, indent=4))
        response.content_disposition = str(
            'attachment; filename=%s' % 'user_{}_audit_logs.json'.format(c.user.user_id))
        response.content_type = 'application/json'

        return response

    @LoginRequired()
    @HasPermissionAllDecorator('hg.admin')
    def user_perms_summary(self):
        _ = self.request.translate
        c = self.load_default_context()
        c.user = self.db_user

        c.active = 'perms_summary'
        c.perm_user = c.user.AuthUser(ip_addr=self.request.remote_addr)

        return self._get_template_context(c)

    @LoginRequired()
    @HasPermissionAllDecorator('hg.admin')
    def user_perms_summary_json(self):
        self.load_default_context()
        perm_user = self.db_user.AuthUser(ip_addr=self.request.remote_addr)

        return perm_user.permissions

    @LoginRequired()
    @HasPermissionAllDecorator('hg.admin')
    def user_caches(self):
        _ = self.request.translate
        c = self.load_default_context()
        c.user = self.db_user

        c.active = 'caches'
        c.perm_user = c.user.AuthUser(ip_addr=self.request.remote_addr)

        cache_namespace_uid = 'cache_user_auth.{}'.format(self.db_user.user_id)
        c.region = rc_cache.get_or_create_region('cache_perms', cache_namespace_uid)
        c.backend = c.region.backend
        c.user_keys = sorted(c.region.backend.list_keys(prefix=cache_namespace_uid))

        return self._get_template_context(c)

    @LoginRequired()
    @HasPermissionAllDecorator('hg.admin')
    @CSRFRequired()
    def user_caches_update(self):
        _ = self.request.translate
        c = self.load_default_context()
        c.user = self.db_user

        c.active = 'caches'
        c.perm_user = c.user.AuthUser(ip_addr=self.request.remote_addr)

        cache_namespace_uid = 'cache_user_auth.{}'.format(self.db_user.user_id)
        del_keys = rc_cache.clear_cache_namespace('cache_perms', cache_namespace_uid)

        h.flash(_("Deleted {} cache keys").format(del_keys), category='success')

        return HTTPFound(h.route_path(
            'edit_user_caches', user_id=c.user.user_id))
