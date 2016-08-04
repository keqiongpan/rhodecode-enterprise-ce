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
import re
import logging
import requests
import colander
import textwrap
from celery.task import task
from mako.template import Template

from rhodecode import events
from rhodecode.translation import lazy_ugettext
from rhodecode.lib import helpers as h
from rhodecode.lib.celerylib import run_task
from rhodecode.lib.colander_utils import strip_whitespace
from rhodecode.integrations.types.base import IntegrationTypeBase
from rhodecode.integrations.schema import IntegrationSettingsSchemaBase

log = logging.getLogger()


class HipchatSettingsSchema(IntegrationSettingsSchemaBase):
    color_choices = [
        ('yellow', lazy_ugettext('Yellow')),
        ('red', lazy_ugettext('Red')),
        ('green', lazy_ugettext('Green')),
        ('purple', lazy_ugettext('Purple')),
        ('gray', lazy_ugettext('Gray')),
    ]

    server_url = colander.SchemaNode(
        colander.String(),
        title=lazy_ugettext('Hipchat server URL'),
        description=lazy_ugettext('Hipchat integration url.'),
        default='',
        preparer=strip_whitespace,
        validator=colander.url,
        widget=deform.widget.TextInputWidget(
            placeholder='https://?.hipchat.com/v2/room/?/notification?auth_token=?',
        ),
    )
    notify = colander.SchemaNode(
        colander.Bool(),
        title=lazy_ugettext('Notify'),
        description=lazy_ugettext('Make a notification to the users in room.'),
        missing=False,
        default=False,
    )
    color = colander.SchemaNode(
        colander.String(),
        title=lazy_ugettext('Color'),
        description=lazy_ugettext('Background color of message.'),
        missing='',
        validator=colander.OneOf([x[0] for x in color_choices]),
        widget=deform.widget.Select2Widget(
            values=color_choices,
        ),
    )


repo_push_template = Template('''
<b>${data['actor']['username']}</b> pushed to
%if data['push']['branches']:
${len(data['push']['branches']) > 1 and 'branches' or 'branch'}
${', '.join('<a href="%s">%s</a>' % (branch['url'], branch['name']) for branch in data['push']['branches'])}
%else:
unknown branch
%endif
in <a href="${data['repo']['url']}">${data['repo']['repo_name']}</a>
<br>
<ul>
%for commit in data['push']['commits']:
    <li>
        <a href="${commit['url']}">${commit['short_id']}</a> - ${commit['message_html']}
    </li>
%endfor
</ul>
''')



class HipchatIntegrationType(IntegrationTypeBase):
    key = 'hipchat'
    display_name = lazy_ugettext('Hipchat')
    valid_events = [
        events.PullRequestCloseEvent,
        events.PullRequestMergeEvent,
        events.PullRequestUpdateEvent,
        events.PullRequestCommentEvent,
        events.PullRequestReviewEvent,
        events.PullRequestCreateEvent,
        events.RepoPushEvent,
        events.RepoCreateEvent,
    ]

    def send_event(self, event):
        if event.__class__ not in self.valid_events:
            log.debug('event not valid: %r' % event)
            return

        if event.name not in self.settings['events']:
            log.debug('event ignored: %r' % event)
            return

        data = event.as_dict()

        text = '<b>%s<b> caused a <b>%s</b> event' % (
            data['actor']['username'], event.name)

        log.debug('handling hipchat event for %s' % event.name)

        if isinstance(event, events.PullRequestCommentEvent):
            text = self.format_pull_request_comment_event(event, data)
        elif isinstance(event, events.PullRequestReviewEvent):
            text = self.format_pull_request_review_event(event, data)
        elif isinstance(event, events.PullRequestEvent):
            text = self.format_pull_request_event(event, data)
        elif isinstance(event, events.RepoPushEvent):
            text = self.format_repo_push_event(data)
        elif isinstance(event, events.RepoCreateEvent):
            text = self.format_repo_create_event(data)
        else:
            log.error('unhandled event type: %r' % event)

        run_task(post_text_to_hipchat, self.settings, text)

    def settings_schema(self):
        schema = HipchatSettingsSchema()
        schema.add(colander.SchemaNode(
            colander.Set(),
            widget=deform.widget.CheckboxChoiceWidget(
                values=sorted(
                    [(e.name, e.display_name) for e in self.valid_events]
                )
            ),
            description="Events activated for this integration",
            name='events'
        ))

        return schema

    def format_pull_request_comment_event(self, event, data):
        comment_text = data['comment']['text']
        if len(comment_text) > 200:
            comment_text = '{comment_text}<a href="{comment_url}">...<a/>'.format(
                comment_text=comment_text[:200],
                comment_url=data['comment']['url'],
            )

        comment_status = ''
        if data['comment']['status']:
            comment_status = '[{}]: '.format(data['comment']['status'])

        return (textwrap.dedent(
            '''
            {user} commented on pull request <a href="{pr_url}">{number}</a> - {pr_title}:
            >>> {comment_status}{comment_text}
            ''').format(
                comment_status=comment_status,
                user=data['actor']['username'],
                number=data['pullrequest']['pull_request_id'],
                pr_url=data['pullrequest']['url'],
                pr_status=data['pullrequest']['status'],
                pr_title=data['pullrequest']['title'],
                comment_text=comment_text
            )
        )

    def format_pull_request_review_event(self, event, data):
        return (textwrap.dedent(
            '''
            Status changed to {pr_status} for pull request <a href="{pr_url}">#{number}</a> - {pr_title}
            ''').format(
                user=data['actor']['username'],
                number=data['pullrequest']['pull_request_id'],
                pr_url=data['pullrequest']['url'],
                pr_status=data['pullrequest']['status'],
                pr_title=data['pullrequest']['title'],
            )
        )

    def format_pull_request_event(self, event, data):
        action = {
            events.PullRequestCloseEvent: 'closed',
            events.PullRequestMergeEvent: 'merged',
            events.PullRequestUpdateEvent: 'updated',
            events.PullRequestCreateEvent: 'created',
        }.get(event.__class__, str(event.__class__))

        return ('Pull request <a href="{url}">#{number}</a> - {title} '
                '{action} by {user}').format(
            user=data['actor']['username'],
            number=data['pullrequest']['pull_request_id'],
            url=data['pullrequest']['url'],
            title=data['pullrequest']['title'],
            action=action
        )

    def format_repo_push_event(self, data):
        result = repo_push_template.render(
            data=data,
        )
        return result

    def format_repo_create_event(self, data):
        return '<a href="{}">{}</a> ({}) repository created by <b>{}</b>'.format(
            data['repo']['url'],
            data['repo']['repo_name'],
            data['repo']['repo_type'],
            data['actor']['username'],
        )


@task(ignore_result=True)
def post_text_to_hipchat(settings, text):
    log.debug('sending %s to hipchat %s' % (text, settings['server_url']))
    resp = requests.post(settings['server_url'], json={
        "message": text,
        "color": settings.get('color', 'yellow'),
        "notify": settings.get('notify', False),
    })
    resp.raise_for_status()  # raise exception on a failed request
