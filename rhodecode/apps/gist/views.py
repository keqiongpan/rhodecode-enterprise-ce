# -*- coding: utf-8 -*-

# Copyright (C) 2013-2018 RhodeCode GmbH
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

import time
import logging

import formencode
import formencode.htmlfill
import peppercorn

from pyramid.httpexceptions import HTTPNotFound, HTTPFound
from pyramid.view import view_config
from pyramid.renderers import render
from pyramid.response import Response

from rhodecode.apps._base import BaseAppView
from rhodecode.lib import helpers as h
from rhodecode.lib.auth import LoginRequired, NotAnonymous, CSRFRequired
from rhodecode.lib.utils2 import time_to_datetime
from rhodecode.lib.ext_json import json
from rhodecode.lib.vcs.exceptions import VCSError, NodeNotChangedError
from rhodecode.model.gist import GistModel
from rhodecode.model.meta import Session
from rhodecode.model.db import Gist, User, or_
from rhodecode.model import validation_schema
from rhodecode.model.validation_schema.schemas import gist_schema


log = logging.getLogger(__name__)


class GistView(BaseAppView):

    def load_default_context(self):
        _ = self.request.translate
        c = self._get_local_tmpl_context()
        c.user = c.auth_user.get_instance()

        c.lifetime_values = [
            (-1, _('forever')),
            (5, _('5 minutes')),
            (60, _('1 hour')),
            (60 * 24, _('1 day')),
            (60 * 24 * 30, _('1 month')),
        ]

        c.lifetime_options = [(c.lifetime_values, _("Lifetime"))]
        c.acl_options = [
            (Gist.ACL_LEVEL_PRIVATE, _("Requires registered account")),
            (Gist.ACL_LEVEL_PUBLIC, _("Can be accessed by anonymous users"))
        ]


        return c

    @LoginRequired()
    @view_config(
        route_name='gists_show', request_method='GET',
        renderer='rhodecode:templates/admin/gists/index.mako')
    def gist_show_all(self):
        c = self.load_default_context()

        not_default_user = self._rhodecode_user.username != User.DEFAULT_USER
        c.show_private = self.request.GET.get('private') and not_default_user
        c.show_public = self.request.GET.get('public') and not_default_user
        c.show_all = self.request.GET.get('all') and self._rhodecode_user.admin

        gists = _gists = Gist().query()\
            .filter(or_(Gist.gist_expires == -1, Gist.gist_expires >= time.time()))\
            .order_by(Gist.created_on.desc())

        c.active = 'public'
        # MY private
        if c.show_private and not c.show_public:
            gists = _gists.filter(Gist.gist_type == Gist.GIST_PRIVATE)\
                        .filter(Gist.gist_owner == self._rhodecode_user.user_id)
            c.active = 'my_private'
        # MY public
        elif c.show_public and not c.show_private:
            gists = _gists.filter(Gist.gist_type == Gist.GIST_PUBLIC)\
                        .filter(Gist.gist_owner == self._rhodecode_user.user_id)
            c.active = 'my_public'
        # MY public+private
        elif c.show_private and c.show_public:
            gists = _gists.filter(or_(Gist.gist_type == Gist.GIST_PUBLIC,
                                      Gist.gist_type == Gist.GIST_PRIVATE))\
                        .filter(Gist.gist_owner == self._rhodecode_user.user_id)
            c.active = 'my_all'
        # Show all by super-admin
        elif c.show_all:
            c.active = 'all'
            gists = _gists

        # default show ALL public gists
        if not c.show_public and not c.show_private and not c.show_all:
            gists = _gists.filter(Gist.gist_type == Gist.GIST_PUBLIC)
            c.active = 'public'

        _render = self.request.get_partial_renderer(
            'rhodecode:templates/data_table/_dt_elements.mako')

        data = []

        for gist in gists:
            data.append({
                'created_on': _render('gist_created', gist.created_on),
                'created_on_raw': gist.created_on,
                'type': _render('gist_type', gist.gist_type),
                'access_id': _render('gist_access_id', gist.gist_access_id, gist.owner.full_contact),
                'author': _render('gist_author', gist.owner.full_contact, gist.created_on, gist.gist_expires),
                'author_raw': h.escape(gist.owner.full_contact),
                'expires': _render('gist_expires', gist.gist_expires),
                'description': _render('gist_description', gist.gist_description)
            })
        c.data = json.dumps(data)

        return self._get_template_context(c)

    @LoginRequired()
    @NotAnonymous()
    @view_config(
        route_name='gists_new', request_method='GET',
        renderer='rhodecode:templates/admin/gists/new.mako')
    def gist_new(self):
        c = self.load_default_context()
        return self._get_template_context(c)

    @LoginRequired()
    @NotAnonymous()
    @CSRFRequired()
    @view_config(
        route_name='gists_create', request_method='POST',
        renderer='rhodecode:templates/admin/gists/new.mako')
    def gist_create(self):
        _ = self.request.translate
        c = self.load_default_context()

        data = dict(self.request.POST)
        data['filename'] = data.get('filename') or Gist.DEFAULT_FILENAME
        data['nodes'] = [{
            'filename': data['filename'],
            'content': data.get('content'),
            'mimetype': data.get('mimetype')  # None is autodetect
        }]

        data['gist_type'] = (
            Gist.GIST_PUBLIC if data.get('public') else Gist.GIST_PRIVATE)
        data['gist_acl_level'] = (
            data.get('gist_acl_level') or Gist.ACL_LEVEL_PRIVATE)

        schema = gist_schema.GistSchema().bind(
            lifetime_options=[x[0] for x in c.lifetime_values])

        try:

            schema_data = schema.deserialize(data)
            # convert to safer format with just KEYs so we sure no duplicates
            schema_data['nodes'] = gist_schema.sequence_to_nodes(
                schema_data['nodes'])

            gist = GistModel().create(
                gist_id=schema_data['gistid'],  # custom access id not real ID
                description=schema_data['description'],
                owner=self._rhodecode_user.user_id,
                gist_mapping=schema_data['nodes'],
                gist_type=schema_data['gist_type'],
                lifetime=schema_data['lifetime'],
                gist_acl_level=schema_data['gist_acl_level']
            )
            Session().commit()
            new_gist_id = gist.gist_access_id
        except validation_schema.Invalid as errors:
            defaults = data
            errors = errors.asdict()

            if 'nodes.0.content' in errors:
                errors['content'] = errors['nodes.0.content']
                del errors['nodes.0.content']
            if 'nodes.0.filename' in errors:
                errors['filename'] = errors['nodes.0.filename']
                del errors['nodes.0.filename']

            data = render('rhodecode:templates/admin/gists/new.mako',
                          self._get_template_context(c), self.request)
            html = formencode.htmlfill.render(
                data,
                defaults=defaults,
                errors=errors,
                prefix_error=False,
                encoding="UTF-8",
                force_defaults=False
            )
            return Response(html)

        except Exception:
            log.exception("Exception while trying to create a gist")
            h.flash(_('Error occurred during gist creation'), category='error')
            raise HTTPFound(h.route_url('gists_new'))
        raise HTTPFound(h.route_url('gist_show', gist_id=new_gist_id))

    @LoginRequired()
    @NotAnonymous()
    @CSRFRequired()
    @view_config(
        route_name='gist_delete', request_method='POST')
    def gist_delete(self):
        _ = self.request.translate
        gist_id = self.request.matchdict['gist_id']

        c = self.load_default_context()
        c.gist = Gist.get_or_404(gist_id)

        owner = c.gist.gist_owner == self._rhodecode_user.user_id
        if not (h.HasPermissionAny('hg.admin')() or owner):
            log.warning('Deletion of Gist was forbidden '
                        'by unauthorized user: `%s`', self._rhodecode_user)
            raise HTTPNotFound()

        GistModel().delete(c.gist)
        Session().commit()
        h.flash(_('Deleted gist %s') % c.gist.gist_access_id, category='success')

        raise HTTPFound(h.route_url('gists_show'))

    def _get_gist(self, gist_id):

        gist = Gist.get_or_404(gist_id)

        # Check if this gist is expired
        if gist.gist_expires != -1:
            if time.time() > gist.gist_expires:
                log.error(
                    'Gist expired at %s', time_to_datetime(gist.gist_expires))
                raise HTTPNotFound()

        # check if this gist requires a login
        is_default_user = self._rhodecode_user.username == User.DEFAULT_USER
        if gist.acl_level == Gist.ACL_LEVEL_PRIVATE and is_default_user:
            log.error("Anonymous user %s tried to access protected gist `%s`",
                      self._rhodecode_user, gist_id)
            raise HTTPNotFound()
        return gist

    @LoginRequired()
    @view_config(
        route_name='gist_show', request_method='GET',
        renderer='rhodecode:templates/admin/gists/show.mako')
    @view_config(
        route_name='gist_show_rev', request_method='GET',
        renderer='rhodecode:templates/admin/gists/show.mako')
    @view_config(
        route_name='gist_show_formatted', request_method='GET',
        renderer=None)
    @view_config(
        route_name='gist_show_formatted_path', request_method='GET',
        renderer=None)
    def gist_show(self):
        gist_id = self.request.matchdict['gist_id']

        # TODO(marcink): expose those via matching dict
        revision = self.request.matchdict.get('revision', 'tip')
        f_path = self.request.matchdict.get('f_path', None)
        return_format = self.request.matchdict.get('format')

        c = self.load_default_context()
        c.gist = self._get_gist(gist_id)
        c.render = not self.request.GET.get('no-render', False)

        try:
            c.file_last_commit, c.files = GistModel().get_gist_files(
                gist_id, revision=revision)
        except VCSError:
            log.exception("Exception in gist show")
            raise HTTPNotFound()

        if return_format == 'raw':
            content = '\n\n'.join([f.content for f in c.files
                                   if (f_path is None or f.path == f_path)])
            response = Response(content)
            response.content_type = 'text/plain'
            return response

        return self._get_template_context(c)

    @LoginRequired()
    @NotAnonymous()
    @view_config(
        route_name='gist_edit', request_method='GET',
        renderer='rhodecode:templates/admin/gists/edit.mako')
    def gist_edit(self):
        _ = self.request.translate
        gist_id = self.request.matchdict['gist_id']
        c = self.load_default_context()
        c.gist = self._get_gist(gist_id)

        owner = c.gist.gist_owner == self._rhodecode_user.user_id
        if not (h.HasPermissionAny('hg.admin')() or owner):
            raise HTTPNotFound()

        try:
            c.file_last_commit, c.files = GistModel().get_gist_files(gist_id)
        except VCSError:
            log.exception("Exception in gist edit")
            raise HTTPNotFound()

        if c.gist.gist_expires == -1:
            expiry = _('never')
        else:
            # this cannot use timeago, since it's used in select2 as a value
            expiry = h.age(h.time_to_datetime(c.gist.gist_expires))

        c.lifetime_values.append(
            (0, _('%(expiry)s - current value') % {'expiry': _(expiry)})
        )

        return self._get_template_context(c)

    @LoginRequired()
    @NotAnonymous()
    @CSRFRequired()
    @view_config(
        route_name='gist_update', request_method='POST',
        renderer='rhodecode:templates/admin/gists/edit.mako')
    def gist_update(self):
        _ = self.request.translate
        gist_id = self.request.matchdict['gist_id']
        c = self.load_default_context()
        c.gist = self._get_gist(gist_id)

        owner = c.gist.gist_owner == self._rhodecode_user.user_id
        if not (h.HasPermissionAny('hg.admin')() or owner):
            raise HTTPNotFound()

        data = peppercorn.parse(self.request.POST.items())

        schema = gist_schema.GistSchema()
        schema = schema.bind(
            # '0' is special value to leave lifetime untouched
            lifetime_options=[x[0] for x in c.lifetime_values] + [0],
        )

        try:
            schema_data = schema.deserialize(data)
            # convert to safer format with just KEYs so we sure no duplicates
            schema_data['nodes'] = gist_schema.sequence_to_nodes(
                schema_data['nodes'])

            GistModel().update(
                gist=c.gist,
                description=schema_data['description'],
                owner=c.gist.owner,
                gist_mapping=schema_data['nodes'],
                lifetime=schema_data['lifetime'],
                gist_acl_level=schema_data['gist_acl_level']
            )

            Session().commit()
            h.flash(_('Successfully updated gist content'), category='success')
        except NodeNotChangedError:
            # raised if nothing was changed in repo itself. We anyway then
            # store only DB stuff for gist
            Session().commit()
            h.flash(_('Successfully updated gist data'), category='success')
        except validation_schema.Invalid as errors:
            errors = h.escape(errors.asdict())
            h.flash(_('Error occurred during update of gist {}: {}').format(
                gist_id, errors), category='error')
        except Exception:
            log.exception("Exception in gist edit")
            h.flash(_('Error occurred during update of gist %s') % gist_id,
                    category='error')

        raise HTTPFound(h.route_url('gist_show', gist_id=gist_id))

    @LoginRequired()
    @NotAnonymous()
    @view_config(
        route_name='gist_edit_check_revision', request_method='GET',
        renderer='json_ext')
    def gist_edit_check_revision(self):
        _ = self.request.translate
        gist_id = self.request.matchdict['gist_id']
        c = self.load_default_context()
        c.gist = self._get_gist(gist_id)

        last_rev = c.gist.scm_instance().get_commit()
        success = True
        revision = self.request.GET.get('revision')

        if revision != last_rev.raw_id:
            log.error('Last revision %s is different then submitted %s'
                      % (revision, last_rev))
            # our gist has newer version than we
            success = False

        return {'success': success}
