# -*- coding: utf-8 -*-

# Copyright (C) 2013-2017 RhodeCode GmbH
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
my account controller for RhodeCode admin
"""

import logging

import formencode
from formencode import htmlfill
from pylons import request, tmpl_context as c, url, session
from pylons.controllers.util import redirect
from pylons.i18n.translation import _
from sqlalchemy.orm import joinedload

from rhodecode import forms
from rhodecode.lib import helpers as h
from rhodecode.lib import auth
from rhodecode.lib.auth import (
    LoginRequired, NotAnonymous, AuthUser, generate_auth_token)
from rhodecode.lib.base import BaseController, render
from rhodecode.lib.utils import jsonify
from rhodecode.lib.utils2 import safe_int, md5, str2bool
from rhodecode.lib.ext_json import json

from rhodecode.model.validation_schema.schemas import user_schema
from rhodecode.model.db import (
    Repository, PullRequest, UserEmailMap, User, UserFollowing)
from rhodecode.model.forms import UserForm
from rhodecode.model.scm import RepoList
from rhodecode.model.user import UserModel
from rhodecode.model.repo import RepoModel
from rhodecode.model.auth_token import AuthTokenModel
from rhodecode.model.meta import Session
from rhodecode.model.pull_request import PullRequestModel
from rhodecode.model.comment import ChangesetCommentsModel

log = logging.getLogger(__name__)


class MyAccountController(BaseController):
    """REST Controller styled on the Atom Publishing Protocol"""
    # To properly map this controller, ensure your config/routing.py
    # file has a resource setup:
    #     map.resource('setting', 'settings', controller='admin/settings',
    #         path_prefix='/admin', name_prefix='admin_')

    @LoginRequired()
    @NotAnonymous()
    def __before__(self):
        super(MyAccountController, self).__before__()

    def __load_data(self):
        c.user = User.get(c.rhodecode_user.user_id)
        if c.user.username == User.DEFAULT_USER:
            h.flash(_("You can't edit this user since it's"
                      " crucial for entire application"), category='warning')
            return redirect(url('users'))

    def _load_my_repos_data(self, watched=False):
        if watched:
            admin = False
            follows_repos = Session().query(UserFollowing)\
                .filter(UserFollowing.user_id == c.rhodecode_user.user_id)\
                .options(joinedload(UserFollowing.follows_repository))\
                .all()
            repo_list = [x.follows_repository for x in follows_repos]
        else:
            admin = True
            repo_list = Repository.get_all_repos(
                user_id=c.rhodecode_user.user_id)
            repo_list = RepoList(repo_list, perm_set=[
                'repository.read', 'repository.write', 'repository.admin'])

        repos_data = RepoModel().get_repos_as_dict(
            repo_list=repo_list, admin=admin)
        # json used to render the grid
        return json.dumps(repos_data)

    @auth.CSRFRequired()
    def my_account_update(self):
        """
        POST /_admin/my_account Updates info of my account
        """
        # url('my_account')
        c.active = 'profile_edit'
        self.__load_data()
        c.perm_user = AuthUser(user_id=c.rhodecode_user.user_id,
                               ip_addr=self.ip_addr)
        c.extern_type = c.user.extern_type
        c.extern_name = c.user.extern_name

        defaults = c.user.get_dict()
        update = False
        _form = UserForm(edit=True,
                         old_data={'user_id': c.rhodecode_user.user_id,
                                   'email': c.rhodecode_user.email})()
        form_result = {}
        try:
            post_data = dict(request.POST)
            post_data['new_password'] = ''
            post_data['password_confirmation'] = ''
            form_result = _form.to_python(post_data)
            # skip updating those attrs for my account
            skip_attrs = ['admin', 'active', 'extern_type', 'extern_name',
                          'new_password', 'password_confirmation']
            # TODO: plugin should define if username can be updated
            if c.extern_type != "rhodecode":
                # forbid updating username for external accounts
                skip_attrs.append('username')

            UserModel().update_user(
                c.rhodecode_user.user_id, skip_attrs=skip_attrs, **form_result)
            h.flash(_('Your account was updated successfully'),
                    category='success')
            Session().commit()
            update = True

        except formencode.Invalid as errors:
            return htmlfill.render(
                render('admin/my_account/my_account.html'),
                defaults=errors.value,
                errors=errors.error_dict or {},
                prefix_error=False,
                encoding="UTF-8",
                force_defaults=False)
        except Exception:
            log.exception("Exception updating user")
            h.flash(_('Error occurred during update of user %s')
                    % form_result.get('username'), category='error')

        if update:
            return redirect('my_account')

        return htmlfill.render(
            render('admin/my_account/my_account.html'),
            defaults=defaults,
            encoding="UTF-8",
            force_defaults=False
        )

    def my_account(self):
        """
        GET /_admin/my_account Displays info about my account
        """
        # url('my_account')
        c.active = 'profile'
        self.__load_data()

        defaults = c.user.get_dict()
        return htmlfill.render(
            render('admin/my_account/my_account.html'),
            defaults=defaults, encoding="UTF-8", force_defaults=False)

    def my_account_edit(self):
        """
        GET /_admin/my_account/edit Displays edit form of my account
        """
        c.active = 'profile_edit'
        self.__load_data()
        c.perm_user = AuthUser(user_id=c.rhodecode_user.user_id,
                               ip_addr=self.ip_addr)
        c.extern_type = c.user.extern_type
        c.extern_name = c.user.extern_name

        defaults = c.user.get_dict()
        return htmlfill.render(
            render('admin/my_account/my_account.html'),
            defaults=defaults,
            encoding="UTF-8",
            force_defaults=False
        )

    @auth.CSRFRequired(except_methods=['GET'])
    def my_account_password(self):
        c.active = 'password'
        self.__load_data()

        schema = user_schema.ChangePasswordSchema().bind(
            username=c.rhodecode_user.username)

        form = forms.Form(schema,
            buttons=(forms.buttons.save, forms.buttons.reset))

        if request.method == 'POST':
            controls = request.POST.items()
            try:
                valid_data = form.validate(controls)
                UserModel().update_user(c.rhodecode_user.user_id, **valid_data)
                instance = c.rhodecode_user.get_instance()
                instance.update_userdata(force_password_change=False)
                Session().commit()
            except forms.ValidationFailure as e:
                request.session.flash(
                    _('Error occurred during update of user password'),
                    queue='error')
                form = e
            except Exception:
                log.exception("Exception updating password")
                request.session.flash(
                    _('Error occurred during update of user password'),
                    queue='error')
            else:
                session.setdefault('rhodecode_user', {}).update(
                    {'password': md5(instance.password)})
                session.save()
                request.session.flash(
                    _("Successfully updated password"), queue='success')
                return redirect(url('my_account_password'))

        c.form = form
        return render('admin/my_account/my_account.html')

    def my_account_repos(self):
        c.active = 'repos'
        self.__load_data()

        # json used to render the grid
        c.data = self._load_my_repos_data()
        return render('admin/my_account/my_account.html')

    def my_account_watched(self):
        c.active = 'watched'
        self.__load_data()

        # json used to render the grid
        c.data = self._load_my_repos_data(watched=True)
        return render('admin/my_account/my_account.html')

    def my_account_perms(self):
        c.active = 'perms'
        self.__load_data()
        c.perm_user = AuthUser(user_id=c.rhodecode_user.user_id,
                               ip_addr=self.ip_addr)

        return render('admin/my_account/my_account.html')

    def my_account_emails(self):
        c.active = 'emails'
        self.__load_data()

        c.user_email_map = UserEmailMap.query()\
            .filter(UserEmailMap.user == c.user).all()
        return render('admin/my_account/my_account.html')

    @auth.CSRFRequired()
    def my_account_emails_add(self):
        email = request.POST.get('new_email')

        try:
            UserModel().add_extra_email(c.rhodecode_user.user_id, email)
            Session().commit()
            h.flash(_("Added new email address `%s` for user account") % email,
                    category='success')
        except formencode.Invalid as error:
            msg = error.error_dict['email']
            h.flash(msg, category='error')
        except Exception:
            log.exception("Exception in my_account_emails")
            h.flash(_('An error occurred during email saving'),
                    category='error')
        return redirect(url('my_account_emails'))

    @auth.CSRFRequired()
    def my_account_emails_delete(self):
        email_id = request.POST.get('del_email_id')
        user_model = UserModel()
        user_model.delete_extra_email(c.rhodecode_user.user_id, email_id)
        Session().commit()
        h.flash(_("Removed email address from user account"),
                category='success')
        return redirect(url('my_account_emails'))

    def _extract_ordering(self, request):
        column_index = safe_int(request.GET.get('order[0][column]'))
        order_dir = request.GET.get('order[0][dir]', 'desc')
        order_by = request.GET.get(
            'columns[%s][data][sort]' % column_index, 'name_raw')
        return order_by, order_dir

    def _get_pull_requests_list(self, statuses):
        start = safe_int(request.GET.get('start'), 0)
        length = safe_int(request.GET.get('length'), c.visual.dashboard_items)
        order_by, order_dir = self._extract_ordering(request)

        pull_requests = PullRequestModel().get_im_participating_in(
            user_id=c.rhodecode_user.user_id,
            statuses=statuses,
            offset=start, length=length, order_by=order_by,
            order_dir=order_dir)

        pull_requests_total_count = PullRequestModel().count_im_participating_in(
            user_id=c.rhodecode_user.user_id, statuses=statuses)

        from rhodecode.lib.utils import PartialRenderer
        _render = PartialRenderer('data_table/_dt_elements.html')
        data = []
        for pr in pull_requests:
            repo_id = pr.target_repo_id
            comments = ChangesetCommentsModel().get_all_comments(
                repo_id, pull_request=pr)
            owned = pr.user_id == c.rhodecode_user.user_id
            status = pr.calculated_review_status()

            data.append({
                'target_repo': _render('pullrequest_target_repo',
                                       pr.target_repo.repo_name),
                'name': _render('pullrequest_name',
                                pr.pull_request_id, pr.target_repo.repo_name,
                                short=True),
                'name_raw': pr.pull_request_id,
                'status': _render('pullrequest_status', status),
                'title': _render(
                    'pullrequest_title', pr.title, pr.description),
                'description': h.escape(pr.description),
                'updated_on': _render('pullrequest_updated_on',
                                      h.datetime_to_time(pr.updated_on)),
                'updated_on_raw': h.datetime_to_time(pr.updated_on),
                'created_on': _render('pullrequest_updated_on',
                                      h.datetime_to_time(pr.created_on)),
                'created_on_raw': h.datetime_to_time(pr.created_on),
                'author': _render('pullrequest_author',
                                  pr.author.full_contact, ),
                'author_raw': pr.author.full_name,
                'comments': _render('pullrequest_comments', len(comments)),
                'comments_raw': len(comments),
                'closed': pr.is_closed(),
                'owned': owned
            })
        # json used to render the grid
        data = ({
            'data': data,
            'recordsTotal': pull_requests_total_count,
            'recordsFiltered': pull_requests_total_count,
        })
        return data

    def my_account_pullrequests(self):
        c.active = 'pullrequests'
        self.__load_data()
        c.show_closed = str2bool(request.GET.get('pr_show_closed'))

        statuses = [PullRequest.STATUS_NEW, PullRequest.STATUS_OPEN]
        if c.show_closed:
            statuses += [PullRequest.STATUS_CLOSED]
        data = self._get_pull_requests_list(statuses)
        if not request.is_xhr:
            c.data_participate = json.dumps(data['data'])
            c.records_total_participate = data['recordsTotal']
            return render('admin/my_account/my_account.html')
        else:
            return json.dumps(data)

    def my_account_auth_tokens(self):
        c.active = 'auth_tokens'
        self.__load_data()
        show_expired = True
        c.lifetime_values = [
            (str(-1), _('forever')),
            (str(5), _('5 minutes')),
            (str(60), _('1 hour')),
            (str(60 * 24), _('1 day')),
            (str(60 * 24 * 30), _('1 month')),
        ]
        c.lifetime_options = [(c.lifetime_values, _("Lifetime"))]
        c.role_values = [(x, AuthTokenModel.cls._get_role_name(x))
                         for x in AuthTokenModel.cls.ROLES]
        c.role_options = [(c.role_values, _("Role"))]
        c.user_auth_tokens = AuthTokenModel().get_auth_tokens(
            c.rhodecode_user.user_id, show_expired=show_expired)
        return render('admin/my_account/my_account.html')

    @auth.CSRFRequired()
    def my_account_auth_tokens_add(self):
        lifetime = safe_int(request.POST.get('lifetime'), -1)
        description = request.POST.get('description')
        role = request.POST.get('role')
        AuthTokenModel().create(c.rhodecode_user.user_id, description, lifetime,
                                role)
        Session().commit()
        h.flash(_("Auth token successfully created"), category='success')
        return redirect(url('my_account_auth_tokens'))

    @auth.CSRFRequired()
    def my_account_auth_tokens_delete(self):
        auth_token = request.POST.get('del_auth_token')
        user_id = c.rhodecode_user.user_id
        if request.POST.get('del_auth_token_builtin'):
            user = User.get(user_id)
            if user:
                user.api_key = generate_auth_token(user.username)
                Session().add(user)
                Session().commit()
                h.flash(_("Auth token successfully reset"), category='success')
        elif auth_token:
            AuthTokenModel().delete(auth_token, c.rhodecode_user.user_id)
            Session().commit()
            h.flash(_("Auth token successfully deleted"), category='success')

        return redirect(url('my_account_auth_tokens'))

    def my_notifications(self):
        c.active = 'notifications'
        return render('admin/my_account/my_account.html')

    @auth.CSRFRequired()
    @jsonify
    def my_notifications_toggle_visibility(self):
        user = c.rhodecode_user.get_instance()
        new_status = not user.user_data.get('notification_status', True)
        user.update_userdata(notification_status=new_status)
        Session().commit()
        return user.user_data['notification_status']
