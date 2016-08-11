# -*- coding: utf-8 -*-

# Copyright (C) 2012-2016  RhodeCode GmbH
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

from __future__ import unicode_literals

import deform
import logging
import colander

from mako.template import Template

from rhodecode import events
from rhodecode.translation import _, lazy_ugettext
from rhodecode.lib.celerylib import run_task
from rhodecode.lib.celerylib import tasks
from rhodecode.integrations.types.base import IntegrationTypeBase
from rhodecode.integrations.schema import IntegrationSettingsSchemaBase


log = logging.getLogger()



class EmailSettingsSchema(IntegrationSettingsSchemaBase):
    @colander.instantiate(validator=colander.Length(min=1))
    class recipients(colander.SequenceSchema):
        title = lazy_ugettext('Recipients')
        description = lazy_ugettext('Email addresses to send push events to')
        widget = deform.widget.SequenceWidget(min_len=1)

        recipient = colander.SchemaNode(
            colander.String(),
            title=lazy_ugettext('Email address'),
            description=lazy_ugettext('Email address'),
            default='',
            validator=colander.Email(),
            widget=deform.widget.TextInputWidget(
                placeholder='user@domain.com',
            ),
        )


class EmailIntegrationType(IntegrationTypeBase):
    key = 'email'
    display_name = lazy_ugettext('Email')
    SettingsSchema = EmailSettingsSchema

    def settings_schema(self):
        schema = EmailSettingsSchema()
        return schema

    def send_event(self, event):
        data = event.as_dict()
        log.debug('got event: %r', event)

        if isinstance(event, events.RepoPushEvent):
            repo_push_handler(data, self.settings)
        else:
            log.debug('ignoring event: %r', event)


def repo_push_handler(data, settings):
    for commit in data['push']['commits']:
        email_body_plaintext = repo_push_template_plaintext.render(
            data=data,
            commit=commit,
            commit_msg=commit['message'],
        )
        email_body_html = repo_push_template_html.render(
            data=data,
            commit=commit,
            commit_msg=commit['message_html'],
        )

        subject = '[%(repo_name)s] %(commit_id)s: %(commit_msg)s' % {
            'repo_name': data['repo']['repo_name'],
            'commit_id': commit['short_id'],
            'commit_msg': commit['message'].split('\n')[0][:150]
        }
        for email_address in settings['recipients']:
            task = run_task(
                tasks.send_email, email_address, subject,
                email_body_plaintext, email_body_html)


# TODO: dan: add changed files, make html pretty
repo_push_template_plaintext = Template('''
User: ${data['actor']['username']}
Branches: ${', '.join(branch['name'] for branch in data['push']['branches'])}
Repository: ${data['repo']['url']}
Commit: ${commit['raw_id']}
URL: ${commit['url']}
Author: ${commit['author']}
Date:   ${commit['date']}
Commit Message:

${commit_msg}
''')

repo_push_template_html = Template('''
User: ${data['actor']['username']}<br>
Branches: ${', '.join(branch['name'] for branch in data['push']['branches'])}<br>
Repository: ${data['repo']['url']}<br>
Commit: ${commit['raw_id']}<br>
URL: ${commit['url']}<br>
Author: ${commit['author']}<br>
Date:   ${commit['date']}<br>
Commit Message:<br>
<p>${commit_msg}</p>
''')
