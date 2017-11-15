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


import logging
import collections

import datetime
import formencode
import formencode.htmlfill

import rhodecode
from pyramid.view import view_config
from pyramid.httpexceptions import HTTPFound, HTTPNotFound
from pyramid.renderers import render
from pyramid.response import Response

from rhodecode.apps._base import BaseAppView
from rhodecode.apps.admin.navigation import navigation_list
from rhodecode.apps.svn_support.config_keys import generate_config
from rhodecode.lib import helpers as h
from rhodecode.lib.auth import (
    LoginRequired, HasPermissionAllDecorator, CSRFRequired)
from rhodecode.lib.celerylib import tasks, run_task
from rhodecode.lib.utils import repo2db_mapper
from rhodecode.lib.utils2 import str2bool, safe_unicode, AttributeDict
from rhodecode.lib.index import searcher_from_config

from rhodecode.model.db import RhodeCodeUi, Repository
from rhodecode.model.forms import (ApplicationSettingsForm,
    ApplicationUiSettingsForm, ApplicationVisualisationForm,
    LabsSettingsForm, IssueTrackerPatternsForm)
from rhodecode.model.repo_group import RepoGroupModel

from rhodecode.model.scm import ScmModel
from rhodecode.model.notification import EmailNotificationModel
from rhodecode.model.meta import Session
from rhodecode.model.settings import (
    IssueTrackerSettingsModel, VcsSettingsModel, SettingNotFound,
    SettingsModel)


log = logging.getLogger(__name__)


class AdminSettingsView(BaseAppView):

    def load_default_context(self):
        c = self._get_local_tmpl_context()
        c.labs_active = str2bool(
            rhodecode.CONFIG.get('labs_settings_active', 'true'))
        c.navlist = navigation_list(self.request)

        return c

    @classmethod
    def _get_ui_settings(cls):
        ret = RhodeCodeUi.query().all()

        if not ret:
            raise Exception('Could not get application ui settings !')
        settings = {}
        for each in ret:
            k = each.ui_key
            v = each.ui_value
            if k == '/':
                k = 'root_path'

            if k in ['push_ssl', 'publish', 'enabled']:
                v = str2bool(v)

            if k.find('.') != -1:
                k = k.replace('.', '_')

            if each.ui_section in ['hooks', 'extensions']:
                v = each.ui_active

            settings[each.ui_section + '_' + k] = v
        return settings

    @classmethod
    def _form_defaults(cls):
        defaults = SettingsModel().get_all_settings()
        defaults.update(cls._get_ui_settings())

        defaults.update({
            'new_svn_branch': '',
            'new_svn_tag': '',
        })
        return defaults

    @LoginRequired()
    @HasPermissionAllDecorator('hg.admin')
    @view_config(
        route_name='admin_settings_vcs', request_method='GET',
        renderer='rhodecode:templates/admin/settings/settings.mako')
    def settings_vcs(self):
        c = self.load_default_context()
        c.active = 'vcs'
        model = VcsSettingsModel()
        c.svn_branch_patterns = model.get_global_svn_branch_patterns()
        c.svn_tag_patterns = model.get_global_svn_tag_patterns()

        settings = self.request.registry.settings
        c.svn_proxy_generate_config = settings[generate_config]

        defaults = self._form_defaults()

        model.create_largeobjects_dirs_if_needed(defaults['paths_root_path'])

        data = render('rhodecode:templates/admin/settings/settings.mako',
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
    @view_config(
        route_name='admin_settings_vcs_update', request_method='POST',
        renderer='rhodecode:templates/admin/settings/settings.mako')
    def settings_vcs_update(self):
        _ = self.request.translate
        c = self.load_default_context()
        c.active = 'vcs'

        model = VcsSettingsModel()
        c.svn_branch_patterns = model.get_global_svn_branch_patterns()
        c.svn_tag_patterns = model.get_global_svn_tag_patterns()

        settings = self.request.registry.settings
        c.svn_proxy_generate_config = settings[generate_config]

        application_form = ApplicationUiSettingsForm(self.request.translate)()

        try:
            form_result = application_form.to_python(dict(self.request.POST))
        except formencode.Invalid as errors:
            h.flash(
                _("Some form inputs contain invalid data."),
                category='error')
            data = render('rhodecode:templates/admin/settings/settings.mako',
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

        try:
            if c.visual.allow_repo_location_change:
                model.update_global_path_setting(
                    form_result['paths_root_path'])

            model.update_global_ssl_setting(form_result['web_push_ssl'])
            model.update_global_hook_settings(form_result)

            model.create_or_update_global_svn_settings(form_result)
            model.create_or_update_global_hg_settings(form_result)
            model.create_or_update_global_git_settings(form_result)
            model.create_or_update_global_pr_settings(form_result)
        except Exception:
            log.exception("Exception while updating settings")
            h.flash(_('Error occurred during updating '
                      'application settings'), category='error')
        else:
            Session().commit()
            h.flash(_('Updated VCS settings'), category='success')
            raise HTTPFound(h.route_path('admin_settings_vcs'))

        data = render('rhodecode:templates/admin/settings/settings.mako',
                      self._get_template_context(c), self.request)
        html = formencode.htmlfill.render(
            data,
            defaults=self._form_defaults(),
            encoding="UTF-8",
            force_defaults=False
        )
        return Response(html)

    @LoginRequired()
    @HasPermissionAllDecorator('hg.admin')
    @CSRFRequired()
    @view_config(
        route_name='admin_settings_vcs_svn_pattern_delete', request_method='POST',
        renderer='json_ext', xhr=True)
    def settings_vcs_delete_svn_pattern(self):
        delete_pattern_id = self.request.POST.get('delete_svn_pattern')
        model = VcsSettingsModel()
        try:
            model.delete_global_svn_pattern(delete_pattern_id)
        except SettingNotFound:
            log.exception(
                'Failed to delete svn_pattern with id %s', delete_pattern_id)
            raise HTTPNotFound()

        Session().commit()
        return True

    @LoginRequired()
    @HasPermissionAllDecorator('hg.admin')
    @view_config(
        route_name='admin_settings_mapping', request_method='GET',
        renderer='rhodecode:templates/admin/settings/settings.mako')
    def settings_mapping(self):
        c = self.load_default_context()
        c.active = 'mapping'

        data = render('rhodecode:templates/admin/settings/settings.mako',
                      self._get_template_context(c), self.request)
        html = formencode.htmlfill.render(
            data,
            defaults=self._form_defaults(),
            encoding="UTF-8",
            force_defaults=False
        )
        return Response(html)

    @LoginRequired()
    @HasPermissionAllDecorator('hg.admin')
    @CSRFRequired()
    @view_config(
        route_name='admin_settings_mapping_update', request_method='POST',
        renderer='rhodecode:templates/admin/settings/settings.mako')
    def settings_mapping_update(self):
        _ = self.request.translate
        c = self.load_default_context()
        c.active = 'mapping'
        rm_obsolete = self.request.POST.get('destroy', False)
        invalidate_cache = self.request.POST.get('invalidate', False)
        log.debug(
            'rescanning repo location with destroy obsolete=%s', rm_obsolete)

        if invalidate_cache:
            log.debug('invalidating all repositories cache')
            for repo in Repository.get_all():
                ScmModel().mark_for_invalidation(repo.repo_name, delete=True)

        filesystem_repos = ScmModel().repo_scan()
        added, removed = repo2db_mapper(filesystem_repos, rm_obsolete)
        _repr = lambda l: ', '.join(map(safe_unicode, l)) or '-'
        h.flash(_('Repositories successfully '
                  'rescanned added: %s ; removed: %s') %
                (_repr(added), _repr(removed)),
                category='success')
        raise HTTPFound(h.route_path('admin_settings_mapping'))

    @LoginRequired()
    @HasPermissionAllDecorator('hg.admin')
    @view_config(
        route_name='admin_settings', request_method='GET',
        renderer='rhodecode:templates/admin/settings/settings.mako')
    @view_config(
        route_name='admin_settings_global', request_method='GET',
        renderer='rhodecode:templates/admin/settings/settings.mako')
    def settings_global(self):
        c = self.load_default_context()
        c.active = 'global'
        c.personal_repo_group_default_pattern = RepoGroupModel()\
            .get_personal_group_name_pattern()

        data = render('rhodecode:templates/admin/settings/settings.mako',
                      self._get_template_context(c), self.request)
        html = formencode.htmlfill.render(
            data,
            defaults=self._form_defaults(),
            encoding="UTF-8",
            force_defaults=False
        )
        return Response(html)

    @LoginRequired()
    @HasPermissionAllDecorator('hg.admin')
    @CSRFRequired()
    @view_config(
        route_name='admin_settings_update', request_method='POST',
        renderer='rhodecode:templates/admin/settings/settings.mako')
    @view_config(
        route_name='admin_settings_global_update', request_method='POST',
        renderer='rhodecode:templates/admin/settings/settings.mako')
    def settings_global_update(self):
        _ = self.request.translate
        c = self.load_default_context()
        c.active = 'global'
        c.personal_repo_group_default_pattern = RepoGroupModel()\
            .get_personal_group_name_pattern()
        application_form = ApplicationSettingsForm(self.request.translate)()
        try:
            form_result = application_form.to_python(dict(self.request.POST))
        except formencode.Invalid as errors:
            data = render('rhodecode:templates/admin/settings/settings.mako',
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

        settings = [
            ('title', 'rhodecode_title', 'unicode'),
            ('realm', 'rhodecode_realm', 'unicode'),
            ('pre_code', 'rhodecode_pre_code', 'unicode'),
            ('post_code', 'rhodecode_post_code', 'unicode'),
            ('captcha_public_key', 'rhodecode_captcha_public_key', 'unicode'),
            ('captcha_private_key', 'rhodecode_captcha_private_key', 'unicode'),
            ('create_personal_repo_group', 'rhodecode_create_personal_repo_group', 'bool'),
            ('personal_repo_group_pattern', 'rhodecode_personal_repo_group_pattern', 'unicode'),
        ]
        try:
            for setting, form_key, type_ in settings:
                sett = SettingsModel().create_or_update_setting(
                    setting, form_result[form_key], type_)
                Session().add(sett)

            Session().commit()
            SettingsModel().invalidate_settings_cache()
            h.flash(_('Updated application settings'), category='success')
        except Exception:
            log.exception("Exception while updating application settings")
            h.flash(
                _('Error occurred during updating application settings'),
                category='error')

        raise HTTPFound(h.route_path('admin_settings_global'))

    @LoginRequired()
    @HasPermissionAllDecorator('hg.admin')
    @view_config(
        route_name='admin_settings_visual', request_method='GET',
        renderer='rhodecode:templates/admin/settings/settings.mako')
    def settings_visual(self):
        c = self.load_default_context()
        c.active = 'visual'

        data = render('rhodecode:templates/admin/settings/settings.mako',
                      self._get_template_context(c), self.request)
        html = formencode.htmlfill.render(
            data,
            defaults=self._form_defaults(),
            encoding="UTF-8",
            force_defaults=False
        )
        return Response(html)

    @LoginRequired()
    @HasPermissionAllDecorator('hg.admin')
    @CSRFRequired()
    @view_config(
        route_name='admin_settings_visual_update', request_method='POST',
        renderer='rhodecode:templates/admin/settings/settings.mako')
    def settings_visual_update(self):
        _ = self.request.translate
        c = self.load_default_context()
        c.active = 'visual'
        application_form = ApplicationVisualisationForm(self.request.translate)()
        try:
            form_result = application_form.to_python(dict(self.request.POST))
        except formencode.Invalid as errors:
            data = render('rhodecode:templates/admin/settings/settings.mako',
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

        try:
            settings = [
                ('show_public_icon', 'rhodecode_show_public_icon', 'bool'),
                ('show_private_icon', 'rhodecode_show_private_icon', 'bool'),
                ('stylify_metatags', 'rhodecode_stylify_metatags', 'bool'),
                ('repository_fields', 'rhodecode_repository_fields', 'bool'),
                ('dashboard_items', 'rhodecode_dashboard_items', 'int'),
                ('admin_grid_items', 'rhodecode_admin_grid_items', 'int'),
                ('show_version', 'rhodecode_show_version', 'bool'),
                ('use_gravatar', 'rhodecode_use_gravatar', 'bool'),
                ('markup_renderer', 'rhodecode_markup_renderer', 'unicode'),
                ('gravatar_url', 'rhodecode_gravatar_url', 'unicode'),
                ('clone_uri_tmpl', 'rhodecode_clone_uri_tmpl', 'unicode'),
                ('support_url', 'rhodecode_support_url', 'unicode'),
                ('show_revision_number', 'rhodecode_show_revision_number', 'bool'),
                ('show_sha_length', 'rhodecode_show_sha_length', 'int'),
            ]
            for setting, form_key, type_ in settings:
                sett = SettingsModel().create_or_update_setting(
                    setting, form_result[form_key], type_)
                Session().add(sett)

            Session().commit()
            SettingsModel().invalidate_settings_cache()
            h.flash(_('Updated visualisation settings'), category='success')
        except Exception:
            log.exception("Exception updating visualization settings")
            h.flash(_('Error occurred during updating '
                      'visualisation settings'),
                    category='error')

        raise HTTPFound(h.route_path('admin_settings_visual'))

    @LoginRequired()
    @HasPermissionAllDecorator('hg.admin')
    @view_config(
        route_name='admin_settings_issuetracker', request_method='GET',
        renderer='rhodecode:templates/admin/settings/settings.mako')
    def settings_issuetracker(self):
        c = self.load_default_context()
        c.active = 'issuetracker'
        defaults = SettingsModel().get_all_settings()

        entry_key = 'rhodecode_issuetracker_pat_'

        c.issuetracker_entries = {}
        for k, v in defaults.items():
            if k.startswith(entry_key):
                uid = k[len(entry_key):]
                c.issuetracker_entries[uid] = None

        for uid in c.issuetracker_entries:
            c.issuetracker_entries[uid] = AttributeDict({
                'pat': defaults.get('rhodecode_issuetracker_pat_' + uid),
                'url': defaults.get('rhodecode_issuetracker_url_' + uid),
                'pref': defaults.get('rhodecode_issuetracker_pref_' + uid),
                'desc': defaults.get('rhodecode_issuetracker_desc_' + uid),
            })

        return self._get_template_context(c)

    @LoginRequired()
    @HasPermissionAllDecorator('hg.admin')
    @CSRFRequired()
    @view_config(
        route_name='admin_settings_issuetracker_test', request_method='POST',
        renderer='string', xhr=True)
    def settings_issuetracker_test(self):
        return h.urlify_commit_message(
            self.request.POST.get('test_text', ''),
            'repo_group/test_repo1')

    @LoginRequired()
    @HasPermissionAllDecorator('hg.admin')
    @CSRFRequired()
    @view_config(
        route_name='admin_settings_issuetracker_update', request_method='POST',
        renderer='rhodecode:templates/admin/settings/settings.mako')
    def settings_issuetracker_update(self):
        _ = self.request.translate
        self.load_default_context()
        settings_model = IssueTrackerSettingsModel()

        try:
            form = IssueTrackerPatternsForm(self.request.translate)().to_python(self.request.POST)
        except formencode.Invalid as errors:
            log.exception('Failed to add new pattern')
            error = errors
            h.flash(_('Invalid issue tracker pattern: {}'.format(error)),
                    category='error')
            raise HTTPFound(h.route_path('admin_settings_issuetracker'))

        if form:
            for uid in form.get('delete_patterns', []):
                settings_model.delete_entries(uid)

            for pattern in form.get('patterns', []):
                for setting, value, type_ in pattern:
                    sett = settings_model.create_or_update_setting(
                        setting, value, type_)
                    Session().add(sett)

                Session().commit()

            SettingsModel().invalidate_settings_cache()
            h.flash(_('Updated issue tracker entries'), category='success')
        raise HTTPFound(h.route_path('admin_settings_issuetracker'))

    @LoginRequired()
    @HasPermissionAllDecorator('hg.admin')
    @CSRFRequired()
    @view_config(
        route_name='admin_settings_issuetracker_delete', request_method='POST',
        renderer='rhodecode:templates/admin/settings/settings.mako')
    def settings_issuetracker_delete(self):
        _ = self.request.translate
        self.load_default_context()
        uid = self.request.POST.get('uid')
        try:
            IssueTrackerSettingsModel().delete_entries(uid)
        except Exception:
            log.exception('Failed to delete issue tracker setting %s', uid)
            raise HTTPNotFound()
        h.flash(_('Removed issue tracker entry'), category='success')
        raise HTTPFound(h.route_path('admin_settings_issuetracker'))

    @LoginRequired()
    @HasPermissionAllDecorator('hg.admin')
    @view_config(
        route_name='admin_settings_email', request_method='GET',
        renderer='rhodecode:templates/admin/settings/settings.mako')
    def settings_email(self):
        c = self.load_default_context()
        c.active = 'email'
        c.rhodecode_ini = rhodecode.CONFIG

        data = render('rhodecode:templates/admin/settings/settings.mako',
                      self._get_template_context(c), self.request)
        html = formencode.htmlfill.render(
            data,
            defaults=self._form_defaults(),
            encoding="UTF-8",
            force_defaults=False
        )
        return Response(html)

    @LoginRequired()
    @HasPermissionAllDecorator('hg.admin')
    @CSRFRequired()
    @view_config(
        route_name='admin_settings_email_update', request_method='POST',
        renderer='rhodecode:templates/admin/settings/settings.mako')
    def settings_email_update(self):
        _ = self.request.translate
        c = self.load_default_context()
        c.active = 'email'

        test_email = self.request.POST.get('test_email')

        if not test_email:
            h.flash(_('Please enter email address'), category='error')
            raise HTTPFound(h.route_path('admin_settings_email'))

        email_kwargs = {
            'date': datetime.datetime.now(),
            'user': c.rhodecode_user,
            'rhodecode_version': c.rhodecode_version
        }

        (subject, headers, email_body,
         email_body_plaintext) = EmailNotificationModel().render_email(
            EmailNotificationModel.TYPE_EMAIL_TEST, **email_kwargs)

        recipients = [test_email] if test_email else None

        run_task(tasks.send_email, recipients, subject,
                 email_body_plaintext, email_body)

        h.flash(_('Send email task created'), category='success')
        raise HTTPFound(h.route_path('admin_settings_email'))

    @LoginRequired()
    @HasPermissionAllDecorator('hg.admin')
    @view_config(
        route_name='admin_settings_hooks', request_method='GET',
        renderer='rhodecode:templates/admin/settings/settings.mako')
    def settings_hooks(self):
        c = self.load_default_context()
        c.active = 'hooks'

        model = SettingsModel()
        c.hooks = model.get_builtin_hooks()
        c.custom_hooks = model.get_custom_hooks()

        data = render('rhodecode:templates/admin/settings/settings.mako',
                      self._get_template_context(c), self.request)
        html = formencode.htmlfill.render(
            data,
            defaults=self._form_defaults(),
            encoding="UTF-8",
            force_defaults=False
        )
        return Response(html)

    @LoginRequired()
    @HasPermissionAllDecorator('hg.admin')
    @CSRFRequired()
    @view_config(
        route_name='admin_settings_hooks_update', request_method='POST',
        renderer='rhodecode:templates/admin/settings/settings.mako')
    @view_config(
        route_name='admin_settings_hooks_delete', request_method='POST',
        renderer='rhodecode:templates/admin/settings/settings.mako')
    def settings_hooks_update(self):
        _ = self.request.translate
        c = self.load_default_context()
        c.active = 'hooks'
        if c.visual.allow_custom_hooks_settings:
            ui_key = self.request.POST.get('new_hook_ui_key')
            ui_value = self.request.POST.get('new_hook_ui_value')

            hook_id = self.request.POST.get('hook_id')
            new_hook = False

            model = SettingsModel()
            try:
                if ui_value and ui_key:
                    model.create_or_update_hook(ui_key, ui_value)
                    h.flash(_('Added new hook'), category='success')
                    new_hook = True
                elif hook_id:
                    RhodeCodeUi.delete(hook_id)
                    Session().commit()

                # check for edits
                update = False
                _d = self.request.POST.dict_of_lists()
                for k, v in zip(_d.get('hook_ui_key', []),
                                _d.get('hook_ui_value_new', [])):
                    model.create_or_update_hook(k, v)
                    update = True

                if update and not new_hook:
                    h.flash(_('Updated hooks'), category='success')
                Session().commit()
            except Exception:
                log.exception("Exception during hook creation")
                h.flash(_('Error occurred during hook creation'),
                        category='error')

        raise HTTPFound(h.route_path('admin_settings_hooks'))

    @LoginRequired()
    @HasPermissionAllDecorator('hg.admin')
    @view_config(
        route_name='admin_settings_search', request_method='GET',
        renderer='rhodecode:templates/admin/settings/settings.mako')
    def settings_search(self):
        c = self.load_default_context()
        c.active = 'search'

        searcher = searcher_from_config(self.request.registry.settings)
        c.statistics = searcher.statistics()

        return self._get_template_context(c)

    @LoginRequired()
    @HasPermissionAllDecorator('hg.admin')
    @view_config(
        route_name='admin_settings_labs', request_method='GET',
        renderer='rhodecode:templates/admin/settings/settings.mako')
    def settings_labs(self):
        c = self.load_default_context()
        if not c.labs_active:
            raise HTTPFound(h.route_path('admin_settings'))

        c.active = 'labs'
        c.lab_settings = _LAB_SETTINGS

        data = render('rhodecode:templates/admin/settings/settings.mako',
                      self._get_template_context(c), self.request)
        html = formencode.htmlfill.render(
            data,
            defaults=self._form_defaults(),
            encoding="UTF-8",
            force_defaults=False
        )
        return Response(html)

    @LoginRequired()
    @HasPermissionAllDecorator('hg.admin')
    @CSRFRequired()
    @view_config(
        route_name='admin_settings_labs_update', request_method='POST',
        renderer='rhodecode:templates/admin/settings/settings.mako')
    def settings_labs_update(self):
        _ = self.request.translate
        c = self.load_default_context()
        c.active = 'labs'

        application_form = LabsSettingsForm(self.request.translate)()
        try:
            form_result = application_form.to_python(dict(self.request.POST))
        except formencode.Invalid as errors:
            h.flash(
                _('Some form inputs contain invalid data.'),
                category='error')
            data = render('rhodecode:templates/admin/settings/settings.mako',
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

        try:
            session = Session()
            for setting in _LAB_SETTINGS:
                setting_name = setting.key[len('rhodecode_'):]
                sett = SettingsModel().create_or_update_setting(
                    setting_name, form_result[setting.key], setting.type)
                session.add(sett)

        except Exception:
            log.exception('Exception while updating lab settings')
            h.flash(_('Error occurred during updating labs settings'),
                    category='error')
        else:
            Session().commit()
            SettingsModel().invalidate_settings_cache()
            h.flash(_('Updated Labs settings'), category='success')
            raise HTTPFound(h.route_path('admin_settings_labs'))

        data = render('rhodecode:templates/admin/settings/settings.mako',
                      self._get_template_context(c), self.request)
        html = formencode.htmlfill.render(
            data,
            defaults=self._form_defaults(),
            encoding="UTF-8",
            force_defaults=False
        )
        return Response(html)


# :param key: name of the setting including the 'rhodecode_' prefix
# :param type: the RhodeCodeSetting type to use.
# :param group: the i18ned group in which we should dispaly this setting
# :param label: the i18ned label we should display for this setting
# :param help: the i18ned help we should dispaly for this setting
LabSetting = collections.namedtuple(
    'LabSetting', ('key', 'type', 'group', 'label', 'help'))


# This list has to be kept in sync with the form
# rhodecode.model.forms.LabsSettingsForm.
_LAB_SETTINGS = [

]
