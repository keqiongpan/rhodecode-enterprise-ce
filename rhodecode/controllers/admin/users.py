# -*- coding: utf-8 -*-

# Copyright (C) 2010-2017 RhodeCode GmbH
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
Users crud controller for pylons
"""

import logging
import formencode

from formencode import htmlfill
from pylons import request, tmpl_context as c, url, config
from pylons.controllers.util import redirect
from pylons.i18n.translation import _

from rhodecode.authentication.plugins import auth_rhodecode

from rhodecode.lib import helpers as h
from rhodecode.lib import auth
from rhodecode.lib import audit_logger
from rhodecode.lib.auth import (
    LoginRequired, HasPermissionAllDecorator, AuthUser)
from rhodecode.lib.base import BaseController, render
from rhodecode.lib.exceptions import (
    DefaultUserException, UserOwnsReposException, UserOwnsRepoGroupsException,
    UserOwnsUserGroupsException, UserCreationError)
from rhodecode.lib.utils2 import safe_int, AttributeDict

from rhodecode.model.db import (
    PullRequestReviewers, User, UserEmailMap, UserIpMap, RepoGroup)
from rhodecode.model.forms import (
    UserForm, UserPermissionsForm, UserIndividualPermissionsForm)
from rhodecode.model.repo_group import RepoGroupModel
from rhodecode.model.user import UserModel
from rhodecode.model.meta import Session
from rhodecode.model.permission import PermissionModel

log = logging.getLogger(__name__)


class UsersController(BaseController):
    """REST Controller styled on the Atom Publishing Protocol"""

    @LoginRequired()
    def __before__(self):
        super(UsersController, self).__before__()
        c.available_permissions = config['available_permissions']
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
        PermissionModel().set_global_permission_choices(c, gettext_translator=_)

    def _get_personal_repo_group_template_vars(self):
        DummyUser = AttributeDict({
            'username': '${username}',
            'user_id': '${user_id}',
        })
        c.default_create_repo_group = RepoGroupModel() \
            .get_default_create_personal_repo_group()
        c.personal_repo_group_name = RepoGroupModel() \
            .get_personal_group_name(DummyUser)

    @HasPermissionAllDecorator('hg.admin')
    @auth.CSRFRequired()
    def create(self):
        c.default_extern_type = auth_rhodecode.RhodeCodeAuthPlugin.name
        user_model = UserModel()
        user_form = UserForm()()
        try:
            form_result = user_form.to_python(dict(request.POST))
            user = user_model.create(form_result)
            Session().flush()
            creation_data = user.get_api_data()
            username = form_result['username']

            audit_logger.store_web(
                'user.create', action_data={'data': creation_data},
                user=c.rhodecode_user)

            user_link = h.link_to(h.escape(username),
                                  url('edit_user',
                                      user_id=user.user_id))
            h.flash(h.literal(_('Created user %(user_link)s')
                              % {'user_link': user_link}), category='success')
            Session().commit()
        except formencode.Invalid as errors:
            self._get_personal_repo_group_template_vars()
            return htmlfill.render(
                render('admin/users/user_add.mako'),
                defaults=errors.value,
                errors=errors.error_dict or {},
                prefix_error=False,
                encoding="UTF-8",
                force_defaults=False)
        except UserCreationError as e:
            h.flash(e, 'error')
        except Exception:
            log.exception("Exception creation of user")
            h.flash(_('Error occurred during creation of user %s')
                    % request.POST.get('username'), category='error')
        return redirect(h.route_path('users'))

    @HasPermissionAllDecorator('hg.admin')
    def new(self):
        c.default_extern_type = auth_rhodecode.RhodeCodeAuthPlugin.name
        self._get_personal_repo_group_template_vars()
        return render('admin/users/user_add.mako')

    @HasPermissionAllDecorator('hg.admin')
    @auth.CSRFRequired()
    def update(self, user_id):

        user_id = safe_int(user_id)
        c.user = User.get_or_404(user_id)
        c.active = 'profile'
        c.extern_type = c.user.extern_type
        c.extern_name = c.user.extern_name
        c.perm_user = AuthUser(user_id=user_id, ip_addr=self.ip_addr)
        available_languages = [x[0] for x in c.allowed_languages]
        _form = UserForm(edit=True, available_languages=available_languages,
                         old_data={'user_id': user_id,
                                   'email': c.user.email})()
        form_result = {}
        old_values = c.user.get_api_data()
        try:
            form_result = _form.to_python(dict(request.POST))
            skip_attrs = ['extern_type', 'extern_name']
            # TODO: plugin should define if username can be updated
            if c.extern_type != "rhodecode":
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
            defaults = errors.value
            e = errors.error_dict or {}

            return htmlfill.render(
                render('admin/users/user_edit.mako'),
                defaults=defaults,
                errors=e,
                prefix_error=False,
                encoding="UTF-8",
                force_defaults=False)
        except UserCreationError as e:
            h.flash(e, 'error')
        except Exception:
            log.exception("Exception updating user")
            h.flash(_('Error occurred during update of user %s')
                    % form_result.get('username'), category='error')
        return redirect(url('edit_user', user_id=user_id))

    @HasPermissionAllDecorator('hg.admin')
    @auth.CSRFRequired()
    def delete(self, user_id):
        user_id = safe_int(user_id)
        c.user = User.get_or_404(user_id)

        _repos = c.user.repositories
        _repo_groups = c.user.repository_groups
        _user_groups = c.user.user_groups

        handle_repos = None
        handle_repo_groups = None
        handle_user_groups = None
        # dummy call for flash of handle
        set_handle_flash_repos = lambda: None
        set_handle_flash_repo_groups = lambda: None
        set_handle_flash_user_groups = lambda: None

        if _repos and request.POST.get('user_repos'):
            do = request.POST['user_repos']
            if do == 'detach':
                handle_repos = 'detach'
                set_handle_flash_repos = lambda: h.flash(
                    _('Detached %s repositories') % len(_repos),
                    category='success')
            elif do == 'delete':
                handle_repos = 'delete'
                set_handle_flash_repos = lambda: h.flash(
                    _('Deleted %s repositories') % len(_repos),
                    category='success')

        if _repo_groups and request.POST.get('user_repo_groups'):
            do = request.POST['user_repo_groups']
            if do == 'detach':
                handle_repo_groups = 'detach'
                set_handle_flash_repo_groups = lambda: h.flash(
                    _('Detached %s repository groups') % len(_repo_groups),
                    category='success')
            elif do == 'delete':
                handle_repo_groups = 'delete'
                set_handle_flash_repo_groups = lambda: h.flash(
                    _('Deleted %s repository groups') % len(_repo_groups),
                    category='success')

        if _user_groups and request.POST.get('user_user_groups'):
            do = request.POST['user_user_groups']
            if do == 'detach':
                handle_user_groups = 'detach'
                set_handle_flash_user_groups = lambda: h.flash(
                    _('Detached %s user groups') % len(_user_groups),
                    category='success')
            elif do == 'delete':
                handle_user_groups = 'delete'
                set_handle_flash_user_groups = lambda: h.flash(
                    _('Deleted %s user groups') % len(_user_groups),
                    category='success')

        old_values = c.user.get_api_data()
        try:
            UserModel().delete(c.user, handle_repos=handle_repos,
                               handle_repo_groups=handle_repo_groups,
                               handle_user_groups=handle_user_groups)

            audit_logger.store_web(
                'user.delete', action_data={'old_data': old_values},
                user=c.rhodecode_user)

            Session().commit()
            set_handle_flash_repos()
            set_handle_flash_repo_groups()
            set_handle_flash_user_groups()
            h.flash(_('Successfully deleted user'), category='success')
        except (UserOwnsReposException, UserOwnsRepoGroupsException,
                UserOwnsUserGroupsException, DefaultUserException) as e:
            h.flash(e, category='warning')
        except Exception:
            log.exception("Exception during deletion of user")
            h.flash(_('An error occurred during deletion of user'),
                    category='error')
        return redirect(h.route_path('users'))

    @HasPermissionAllDecorator('hg.admin')
    @auth.CSRFRequired()
    def reset_password(self, user_id):
        """
        toggle reset password flag for this user
        """
        user_id = safe_int(user_id)
        c.user = User.get_or_404(user_id)
        try:
            old_value = c.user.user_data.get('force_password_change')
            c.user.update_userdata(force_password_change=not old_value)

            if old_value:
                msg = _('Force password change disabled for user')
                audit_logger.store_web(
                    'user.edit.password_reset.disabled',
                    user=c.rhodecode_user)
            else:
                msg = _('Force password change enabled for user')
                audit_logger.store_web(
                    'user.edit.password_reset.enabled',
                    user=c.rhodecode_user)

            Session().commit()
            h.flash(msg, category='success')
        except Exception:
            log.exception("Exception during password reset for user")
            h.flash(_('An error occurred during password reset for user'),
                    category='error')

        return redirect(url('edit_user_advanced', user_id=user_id))

    @HasPermissionAllDecorator('hg.admin')
    @auth.CSRFRequired()
    def create_personal_repo_group(self, user_id):
        """
        Create personal repository group for this user
        """
        from rhodecode.model.repo_group import RepoGroupModel

        user_id = safe_int(user_id)
        c.user = User.get_or_404(user_id)
        personal_repo_group = RepoGroup.get_user_personal_repo_group(
            c.user.user_id)
        if personal_repo_group:
            return redirect(url('edit_user_advanced', user_id=user_id))

        personal_repo_group_name = RepoGroupModel().get_personal_group_name(
            c.user)
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

        return redirect(url('edit_user_advanced', user_id=user_id))

    @HasPermissionAllDecorator('hg.admin')
    def show(self, user_id):
        """GET /users/user_id: Show a specific item"""
        # url('user', user_id=ID)
        User.get_or_404(-1)

    @HasPermissionAllDecorator('hg.admin')
    def edit(self, user_id):
        """GET /users/user_id/edit: Form to edit an existing item"""
        # url('edit_user', user_id=ID)
        user_id = safe_int(user_id)
        c.user = User.get_or_404(user_id)
        if c.user.username == User.DEFAULT_USER:
            h.flash(_("You can't edit this user"), category='warning')
            return redirect(h.route_path('users'))

        c.active = 'profile'
        c.extern_type = c.user.extern_type
        c.extern_name = c.user.extern_name
        c.perm_user = AuthUser(user_id=user_id, ip_addr=self.ip_addr)

        defaults = c.user.get_dict()
        defaults.update({'language': c.user.user_data.get('language')})
        return htmlfill.render(
            render('admin/users/user_edit.mako'),
            defaults=defaults,
            encoding="UTF-8",
            force_defaults=False)

    @HasPermissionAllDecorator('hg.admin')
    def edit_advanced(self, user_id):
        user_id = safe_int(user_id)
        user = c.user = User.get_or_404(user_id)
        if user.username == User.DEFAULT_USER:
            h.flash(_("You can't edit this user"), category='warning')
            return redirect(h.route_path('users'))

        c.active = 'advanced'
        c.personal_repo_group = RepoGroup.get_user_personal_repo_group(user_id)
        c.personal_repo_group_name = RepoGroupModel()\
            .get_personal_group_name(user)
        c.first_admin = User.get_first_super_admin()
        defaults = user.get_dict()

        # Interim workaround if the user participated on any pull requests as a
        # reviewer.
        has_review = bool(PullRequestReviewers.query().filter(
            PullRequestReviewers.user_id == user_id).first())
        c.can_delete_user = not has_review
        c.can_delete_user_message = _(
            'The user participates as reviewer in pull requests and '
            'cannot be deleted. You can set the user to '
            '"inactive" instead of deleting it.') if has_review else ''

        return htmlfill.render(
            render('admin/users/user_edit.mako'),
            defaults=defaults,
            encoding="UTF-8",
            force_defaults=False)

    @HasPermissionAllDecorator('hg.admin')
    def edit_global_perms(self, user_id):
        user_id = safe_int(user_id)
        c.user = User.get_or_404(user_id)
        if c.user.username == User.DEFAULT_USER:
            h.flash(_("You can't edit this user"), category='warning')
            return redirect(h.route_path('users'))

        c.active = 'global_perms'

        c.default_user = User.get_default_user()
        defaults = c.user.get_dict()
        defaults.update(c.default_user.get_default_perms(suffix='_inherited'))
        defaults.update(c.default_user.get_default_perms())
        defaults.update(c.user.get_default_perms())

        return htmlfill.render(
            render('admin/users/user_edit.mako'),
            defaults=defaults,
            encoding="UTF-8",
            force_defaults=False)

    @HasPermissionAllDecorator('hg.admin')
    @auth.CSRFRequired()
    def update_global_perms(self, user_id):
        user_id = safe_int(user_id)
        user = User.get_or_404(user_id)
        c.active = 'global_perms'
        try:
            # first stage that verifies the checkbox
            _form = UserIndividualPermissionsForm()
            form_result = _form.to_python(dict(request.POST))
            inherit_perms = form_result['inherit_default_permissions']
            user.inherit_default_permissions = inherit_perms
            Session().add(user)

            if not inherit_perms:
                # only update the individual ones if we un check the flag
                _form = UserPermissionsForm(
                    [x[0] for x in c.repo_create_choices],
                    [x[0] for x in c.repo_create_on_write_choices],
                    [x[0] for x in c.repo_group_create_choices],
                    [x[0] for x in c.user_group_create_choices],
                    [x[0] for x in c.fork_choices],
                    [x[0] for x in c.inherit_default_permission_choices])()

                form_result = _form.to_python(dict(request.POST))
                form_result.update({'perm_user_id': user.user_id})

                PermissionModel().update_user_permissions(form_result)

            # TODO(marcink): implement global permissions
            # audit_log.store_web('user.edit.permissions')

            Session().commit()
            h.flash(_('User global permissions updated successfully'),
                    category='success')

        except formencode.Invalid as errors:
            defaults = errors.value
            c.user = user
            return htmlfill.render(
                render('admin/users/user_edit.mako'),
                defaults=defaults,
                errors=errors.error_dict or {},
                prefix_error=False,
                encoding="UTF-8",
                force_defaults=False)
        except Exception:
            log.exception("Exception during permissions saving")
            h.flash(_('An error occurred during permissions saving'),
                    category='error')
        return redirect(url('edit_user_global_perms', user_id=user_id))

    @HasPermissionAllDecorator('hg.admin')
    def edit_perms_summary(self, user_id):
        user_id = safe_int(user_id)
        c.user = User.get_or_404(user_id)
        if c.user.username == User.DEFAULT_USER:
            h.flash(_("You can't edit this user"), category='warning')
            return redirect(h.route_path('users'))

        c.active = 'perms_summary'
        c.perm_user = AuthUser(user_id=user_id, ip_addr=self.ip_addr)

        return render('admin/users/user_edit.mako')

    @HasPermissionAllDecorator('hg.admin')
    def edit_emails(self, user_id):
        user_id = safe_int(user_id)
        c.user = User.get_or_404(user_id)
        if c.user.username == User.DEFAULT_USER:
            h.flash(_("You can't edit this user"), category='warning')
            return redirect(h.route_path('users'))

        c.active = 'emails'
        c.user_email_map = UserEmailMap.query() \
            .filter(UserEmailMap.user == c.user).all()

        defaults = c.user.get_dict()
        return htmlfill.render(
            render('admin/users/user_edit.mako'),
            defaults=defaults,
            encoding="UTF-8",
            force_defaults=False)

    @HasPermissionAllDecorator('hg.admin')
    @auth.CSRFRequired()
    def add_email(self, user_id):
        user_id = safe_int(user_id)
        c.user = User.get_or_404(user_id)

        email = request.POST.get('new_email')
        user_model = UserModel()
        user_data = c.user.get_api_data()
        try:
            user_model.add_extra_email(user_id, email)
            audit_logger.store_web(
                'user.edit.email.add',
                action_data={'email': email, 'user': user_data},
                user=c.rhodecode_user)
            Session().commit()
            h.flash(_("Added new email address `%s` for user account") % email,
                    category='success')
        except formencode.Invalid as error:
            msg = error.error_dict['email']
            h.flash(msg, category='error')
        except Exception:
            log.exception("Exception during email saving")
            h.flash(_('An error occurred during email saving'),
                    category='error')
        return redirect(url('edit_user_emails', user_id=user_id))

    @HasPermissionAllDecorator('hg.admin')
    @auth.CSRFRequired()
    def delete_email(self, user_id):
        user_id = safe_int(user_id)
        c.user = User.get_or_404(user_id)
        email_id = request.POST.get('del_email_id')
        user_model = UserModel()

        email = UserEmailMap.query().get(email_id).email
        user_data = c.user.get_api_data()
        user_model.delete_extra_email(user_id, email_id)
        audit_logger.store_web(
            'user.edit.email.delete',
            action_data={'email': email, 'user': user_data},
            user=c.rhodecode_user)
        Session().commit()
        h.flash(_("Removed email address from user account"), category='success')
        return redirect(url('edit_user_emails', user_id=user_id))

    @HasPermissionAllDecorator('hg.admin')
    def edit_ips(self, user_id):
        user_id = safe_int(user_id)
        c.user = User.get_or_404(user_id)
        if c.user.username == User.DEFAULT_USER:
            h.flash(_("You can't edit this user"), category='warning')
            return redirect(h.route_path('users'))

        c.active = 'ips'
        c.user_ip_map = UserIpMap.query() \
            .filter(UserIpMap.user == c.user).all()

        c.inherit_default_ips = c.user.inherit_default_permissions
        c.default_user_ip_map = UserIpMap.query() \
            .filter(UserIpMap.user == User.get_default_user()).all()

        defaults = c.user.get_dict()
        return htmlfill.render(
            render('admin/users/user_edit.mako'),
            defaults=defaults,
            encoding="UTF-8",
            force_defaults=False)

    @HasPermissionAllDecorator('hg.admin')
    @auth.CSRFRequired()
    def add_ip(self, user_id):
        user_id = safe_int(user_id)
        c.user = User.get_or_404(user_id)
        user_model = UserModel()
        try:
            ip_list = user_model.parse_ip_range(request.POST.get('new_ip'))
        except Exception as e:
            ip_list = []
            log.exception("Exception during ip saving")
            h.flash(_('An error occurred during ip saving:%s' % (e,)),
                    category='error')

        desc = request.POST.get('description')
        added = []
        user_data = c.user.get_api_data()
        for ip in ip_list:
            try:
                user_model.add_extra_ip(user_id, ip, desc)
                audit_logger.store_web(
                    'user.edit.ip.add',
                    action_data={'ip': ip, 'user': user_data},
                    user=c.rhodecode_user)
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
        if 'default_user' in request.POST:
            return redirect(url('admin_permissions_ips'))
        return redirect(url('edit_user_ips', user_id=user_id))

    @HasPermissionAllDecorator('hg.admin')
    @auth.CSRFRequired()
    def delete_ip(self, user_id):
        user_id = safe_int(user_id)
        c.user = User.get_or_404(user_id)

        ip_id = request.POST.get('del_ip_id')
        user_model = UserModel()
        ip = UserIpMap.query().get(ip_id).ip_addr
        user_data = c.user.get_api_data()
        user_model.delete_extra_ip(user_id, ip_id)
        audit_logger.store_web(
            'user.edit.ip.delete',
            action_data={'ip': ip, 'user': user_data},
            user=c.rhodecode_user)
        Session().commit()
        h.flash(_("Removed ip address from user whitelist"), category='success')

        if 'default_user' in request.POST:
            return redirect(url('admin_permissions_ips'))
        return redirect(url('edit_user_ips', user_id=user_id))
