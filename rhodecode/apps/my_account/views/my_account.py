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
import datetime

import formencode
import formencode.htmlfill
from pyramid.httpexceptions import HTTPFound
from pyramid.view import view_config
from pyramid.renderers import render
from pyramid.response import Response

from rhodecode.apps._base import BaseAppView, DataGridAppView
from rhodecode import forms
from rhodecode.lib import helpers as h
from rhodecode.lib import audit_logger
from rhodecode.lib.ext_json import json
from rhodecode.lib.auth import LoginRequired, NotAnonymous, CSRFRequired
from rhodecode.lib.channelstream import (
    channelstream_request, ChannelstreamException)
from rhodecode.lib.utils2 import safe_int, md5, str2bool
from rhodecode.model.auth_token import AuthTokenModel
from rhodecode.model.comment import CommentsModel
from rhodecode.model.db import (
    Repository, UserEmailMap, UserApiKeys, UserFollowing, joinedload,
    PullRequest)
from rhodecode.model.forms import UserForm
from rhodecode.model.meta import Session
from rhodecode.model.pull_request import PullRequestModel
from rhodecode.model.scm import RepoList
from rhodecode.model.user import UserModel
from rhodecode.model.repo import RepoModel
from rhodecode.model.validation_schema.schemas import user_schema

log = logging.getLogger(__name__)


class MyAccountView(BaseAppView, DataGridAppView):
    ALLOW_SCOPED_TOKENS = False
    """
    This view has alternative version inside EE, if modified please take a look
    in there as well.
    """

    def load_default_context(self):
        c = self._get_local_tmpl_context()
        c.user = c.auth_user.get_instance()
        c.allow_scoped_tokens = self.ALLOW_SCOPED_TOKENS
        self._register_global_c(c)
        return c

    @LoginRequired()
    @NotAnonymous()
    @view_config(
        route_name='my_account_profile', request_method='GET',
        renderer='rhodecode:templates/admin/my_account/my_account.mako')
    def my_account_profile(self):
        c = self.load_default_context()
        c.active = 'profile'
        return self._get_template_context(c)

    @LoginRequired()
    @NotAnonymous()
    @view_config(
        route_name='my_account_password', request_method='GET',
        renderer='rhodecode:templates/admin/my_account/my_account.mako')
    def my_account_password(self):
        c = self.load_default_context()
        c.active = 'password'
        c.extern_type = c.user.extern_type

        schema = user_schema.ChangePasswordSchema().bind(
            username=c.user.username)

        form = forms.Form(
            schema,
            action=h.route_path('my_account_password_update'),
            buttons=(forms.buttons.save, forms.buttons.reset))

        c.form = form
        return self._get_template_context(c)

    @LoginRequired()
    @NotAnonymous()
    @CSRFRequired()
    @view_config(
        route_name='my_account_password_update', request_method='POST',
        renderer='rhodecode:templates/admin/my_account/my_account.mako')
    def my_account_password_update(self):
        _ = self.request.translate
        c = self.load_default_context()
        c.active = 'password'
        c.extern_type = c.user.extern_type

        schema = user_schema.ChangePasswordSchema().bind(
            username=c.user.username)

        form = forms.Form(
            schema, buttons=(forms.buttons.save, forms.buttons.reset))

        if c.extern_type != 'rhodecode':
            raise HTTPFound(self.request.route_path('my_account_password'))

        controls = self.request.POST.items()
        try:
            valid_data = form.validate(controls)
            UserModel().update_user(c.user.user_id, **valid_data)
            c.user.update_userdata(force_password_change=False)
            Session().commit()
        except forms.ValidationFailure as e:
            c.form = e
            return self._get_template_context(c)

        except Exception:
            log.exception("Exception updating password")
            h.flash(_('Error occurred during update of user password'),
                    category='error')
        else:
            instance = c.auth_user.get_instance()
            self.session.setdefault('rhodecode_user', {}).update(
                {'password': md5(instance.password)})
            self.session.save()
            h.flash(_("Successfully updated password"), category='success')

        raise HTTPFound(self.request.route_path('my_account_password'))

    @LoginRequired()
    @NotAnonymous()
    @view_config(
        route_name='my_account_auth_tokens', request_method='GET',
        renderer='rhodecode:templates/admin/my_account/my_account.mako')
    def my_account_auth_tokens(self):
        _ = self.request.translate

        c = self.load_default_context()
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

    def maybe_attach_token_scope(self, token):
        # implemented in EE edition
        pass

    @LoginRequired()
    @NotAnonymous()
    @CSRFRequired()
    @view_config(
        route_name='my_account_auth_tokens_add', request_method='POST',)
    def my_account_auth_tokens_add(self):
        _ = self.request.translate
        c = self.load_default_context()

        lifetime = safe_int(self.request.POST.get('lifetime'), -1)
        description = self.request.POST.get('description')
        role = self.request.POST.get('role')

        token = AuthTokenModel().create(
            c.user.user_id, description, lifetime, role)
        token_data = token.get_api_data()

        self.maybe_attach_token_scope(token)
        audit_logger.store_web(
            'user.edit.token.add', action_data={
                'data': {'token': token_data, 'user': 'self'}},
            user=self._rhodecode_user, )
        Session().commit()

        h.flash(_("Auth token successfully created"), category='success')
        return HTTPFound(h.route_path('my_account_auth_tokens'))

    @LoginRequired()
    @NotAnonymous()
    @CSRFRequired()
    @view_config(
        route_name='my_account_auth_tokens_delete', request_method='POST')
    def my_account_auth_tokens_delete(self):
        _ = self.request.translate
        c = self.load_default_context()

        del_auth_token = self.request.POST.get('del_auth_token')

        if del_auth_token:
            token = UserApiKeys.get_or_404(del_auth_token)
            token_data = token.get_api_data()

            AuthTokenModel().delete(del_auth_token, c.user.user_id)
            audit_logger.store_web(
                'user.edit.token.delete', action_data={
                    'data': {'token': token_data, 'user': 'self'}},
                user=self._rhodecode_user,)
            Session().commit()
            h.flash(_("Auth token successfully deleted"), category='success')

        return HTTPFound(h.route_path('my_account_auth_tokens'))

    @LoginRequired()
    @NotAnonymous()
    @view_config(
        route_name='my_account_emails', request_method='GET',
        renderer='rhodecode:templates/admin/my_account/my_account.mako')
    def my_account_emails(self):
        _ = self.request.translate

        c = self.load_default_context()
        c.active = 'emails'

        c.user_email_map = UserEmailMap.query()\
            .filter(UserEmailMap.user == c.user).all()
        return self._get_template_context(c)

    @LoginRequired()
    @NotAnonymous()
    @CSRFRequired()
    @view_config(
        route_name='my_account_emails_add', request_method='POST')
    def my_account_emails_add(self):
        _ = self.request.translate
        c = self.load_default_context()

        email = self.request.POST.get('new_email')

        try:
            UserModel().add_extra_email(c.user.user_id, email)
            audit_logger.store_web(
                'user.edit.email.add', action_data={
                    'data': {'email': email, 'user': 'self'}},
                user=self._rhodecode_user,)

            Session().commit()
            h.flash(_("Added new email address `%s` for user account") % email,
                    category='success')
        except formencode.Invalid as error:
            h.flash(h.escape(error.error_dict['email']), category='error')
        except Exception:
            log.exception("Exception in my_account_emails")
            h.flash(_('An error occurred during email saving'),
                    category='error')
        return HTTPFound(h.route_path('my_account_emails'))

    @LoginRequired()
    @NotAnonymous()
    @CSRFRequired()
    @view_config(
        route_name='my_account_emails_delete', request_method='POST')
    def my_account_emails_delete(self):
        _ = self.request.translate
        c = self.load_default_context()

        del_email_id = self.request.POST.get('del_email_id')
        if del_email_id:
            email = UserEmailMap.get_or_404(del_email_id).email
            UserModel().delete_extra_email(c.user.user_id, del_email_id)
            audit_logger.store_web(
                'user.edit.email.delete', action_data={
                    'data': {'email': email, 'user': 'self'}},
                user=self._rhodecode_user,)
            Session().commit()
            h.flash(_("Email successfully deleted"),
                    category='success')
        return HTTPFound(h.route_path('my_account_emails'))

    @LoginRequired()
    @NotAnonymous()
    @CSRFRequired()
    @view_config(
        route_name='my_account_notifications_test_channelstream',
        request_method='POST', renderer='json_ext')
    def my_account_notifications_test_channelstream(self):
        message = 'Test message sent via Channelstream by user: {}, on {}'.format(
            self._rhodecode_user.username, datetime.datetime.now())
        payload = {
            # 'channel': 'broadcast',
            'type': 'message',
            'timestamp': datetime.datetime.utcnow(),
            'user': 'system',
            'pm_users': [self._rhodecode_user.username],
            'message': {
                'message': message,
                'level': 'info',
                'topic': '/notifications'
            }
        }

        registry = self.request.registry
        rhodecode_plugins = getattr(registry, 'rhodecode_plugins', {})
        channelstream_config = rhodecode_plugins.get('channelstream', {})

        try:
            channelstream_request(channelstream_config, [payload], '/message')
        except ChannelstreamException as e:
            log.exception('Failed to send channelstream data')
            return {"response": 'ERROR: {}'.format(e.__class__.__name__)}
        return {"response": 'Channelstream data sent. '
                            'You should see a new live message now.'}

    def _load_my_repos_data(self, watched=False):
        if watched:
            admin = False
            follows_repos = Session().query(UserFollowing)\
                .filter(UserFollowing.user_id == self._rhodecode_user.user_id)\
                .options(joinedload(UserFollowing.follows_repository))\
                .all()
            repo_list = [x.follows_repository for x in follows_repos]
        else:
            admin = True
            repo_list = Repository.get_all_repos(
                user_id=self._rhodecode_user.user_id)
            repo_list = RepoList(repo_list, perm_set=[
                'repository.read', 'repository.write', 'repository.admin'])

        repos_data = RepoModel().get_repos_as_dict(
            repo_list=repo_list, admin=admin)
        # json used to render the grid
        return json.dumps(repos_data)

    @LoginRequired()
    @NotAnonymous()
    @view_config(
        route_name='my_account_repos', request_method='GET',
        renderer='rhodecode:templates/admin/my_account/my_account.mako')
    def my_account_repos(self):
        c = self.load_default_context()
        c.active = 'repos'

        # json used to render the grid
        c.data = self._load_my_repos_data()
        return self._get_template_context(c)

    @LoginRequired()
    @NotAnonymous()
    @view_config(
        route_name='my_account_watched', request_method='GET',
        renderer='rhodecode:templates/admin/my_account/my_account.mako')
    def my_account_watched(self):
        c = self.load_default_context()
        c.active = 'watched'

        # json used to render the grid
        c.data = self._load_my_repos_data(watched=True)
        return self._get_template_context(c)

    @LoginRequired()
    @NotAnonymous()
    @view_config(
        route_name='my_account_perms', request_method='GET',
        renderer='rhodecode:templates/admin/my_account/my_account.mako')
    def my_account_perms(self):
        c = self.load_default_context()
        c.active = 'perms'

        c.perm_user = c.auth_user
        return self._get_template_context(c)

    @LoginRequired()
    @NotAnonymous()
    @view_config(
        route_name='my_account_notifications', request_method='GET',
        renderer='rhodecode:templates/admin/my_account/my_account.mako')
    def my_notifications(self):
        c = self.load_default_context()
        c.active = 'notifications'

        return self._get_template_context(c)

    @LoginRequired()
    @NotAnonymous()
    @CSRFRequired()
    @view_config(
        route_name='my_account_notifications_toggle_visibility',
        request_method='POST', renderer='json_ext')
    def my_notifications_toggle_visibility(self):
        user = self._rhodecode_db_user
        new_status = not user.user_data.get('notification_status', True)
        user.update_userdata(notification_status=new_status)
        Session().commit()
        return user.user_data['notification_status']

    @LoginRequired()
    @NotAnonymous()
    @view_config(
        route_name='my_account_edit',
        request_method='GET',
        renderer='rhodecode:templates/admin/my_account/my_account.mako')
    def my_account_edit(self):
        c = self.load_default_context()
        c.active = 'profile_edit'

        c.perm_user = c.auth_user
        c.extern_type = c.user.extern_type
        c.extern_name = c.user.extern_name

        defaults = c.user.get_dict()

        data = render('rhodecode:templates/admin/my_account/my_account.mako',
                      self._get_template_context(c), self.request)
        html = formencode.htmlfill.render(
            data,
            defaults=defaults,
            encoding="UTF-8",
            force_defaults=False
        )
        return Response(html)

    @LoginRequired()
    @NotAnonymous()
    @CSRFRequired()
    @view_config(
        route_name='my_account_update',
        request_method='POST',
        renderer='rhodecode:templates/admin/my_account/my_account.mako')
    def my_account_update(self):
        _ = self.request.translate
        c = self.load_default_context()
        c.active = 'profile_edit'

        c.perm_user = c.auth_user
        c.extern_type = c.user.extern_type
        c.extern_name = c.user.extern_name

        _form = UserForm(edit=True,
                         old_data={'user_id': self._rhodecode_user.user_id,
                                   'email': self._rhodecode_user.email})()
        form_result = {}
        try:
            post_data = dict(self.request.POST)
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
                self._rhodecode_user.user_id, skip_attrs=skip_attrs,
                **form_result)
            h.flash(_('Your account was updated successfully'),
                    category='success')
            Session().commit()

        except formencode.Invalid as errors:
            data = render(
                'rhodecode:templates/admin/my_account/my_account.mako',
                self._get_template_context(c), self.request)

            html = formencode.htmlfill.render(
                data,
                defaults=errors.value,
                errors=errors.error_dict or {},
                prefix_error=False,
                encoding="UTF-8",
                force_defaults=False)
            return Response(html)

        except Exception:
            log.exception("Exception updating user")
            h.flash(_('Error occurred during update of user %s')
                    % form_result.get('username'), category='error')
            raise HTTPFound(h.route_path('my_account_profile'))

        raise HTTPFound(h.route_path('my_account_profile'))

    def _get_pull_requests_list(self, statuses):
        draw, start, limit = self._extract_chunk(self.request)
        search_q, order_by, order_dir = self._extract_ordering(self.request)
        _render = self.request.get_partial_renderer(
            'rhodecode:templates/data_table/_dt_elements.mako')

        pull_requests = PullRequestModel().get_im_participating_in(
            user_id=self._rhodecode_user.user_id,
            statuses=statuses,
            offset=start, length=limit, order_by=order_by,
            order_dir=order_dir)

        pull_requests_total_count = PullRequestModel().count_im_participating_in(
            user_id=self._rhodecode_user.user_id, statuses=statuses)

        data = []
        comments_model = CommentsModel()
        for pr in pull_requests:
            repo_id = pr.target_repo_id
            comments = comments_model.get_all_comments(
                repo_id, pull_request=pr)
            owned = pr.user_id == self._rhodecode_user.user_id

            data.append({
                'target_repo': _render('pullrequest_target_repo',
                                       pr.target_repo.repo_name),
                'name': _render('pullrequest_name',
                                pr.pull_request_id, pr.target_repo.repo_name,
                                short=True),
                'name_raw': pr.pull_request_id,
                'status': _render('pullrequest_status',
                                  pr.calculated_review_status()),
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
            'draw': draw,
            'data': data,
            'recordsTotal': pull_requests_total_count,
            'recordsFiltered': pull_requests_total_count,
        })
        return data

    @LoginRequired()
    @NotAnonymous()
    @view_config(
        route_name='my_account_pullrequests',
        request_method='GET',
        renderer='rhodecode:templates/admin/my_account/my_account.mako')
    def my_account_pullrequests(self):
        c = self.load_default_context()
        c.active = 'pullrequests'
        req_get = self.request.GET

        c.closed = str2bool(req_get.get('pr_show_closed'))

        return self._get_template_context(c)

    @LoginRequired()
    @NotAnonymous()
    @view_config(
        route_name='my_account_pullrequests_data',
        request_method='GET', renderer='json_ext')
    def my_account_pullrequests_data(self):
        req_get = self.request.GET
        closed = str2bool(req_get.get('closed'))

        statuses = [PullRequest.STATUS_NEW, PullRequest.STATUS_OPEN]
        if closed:
            statuses += [PullRequest.STATUS_CLOSED]

        data = self._get_pull_requests_list(statuses=statuses)
        return data

