# -*- coding: utf-8 -*-

# Copyright (C) 2012-2018 RhodeCode GmbH
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
import requests
import colander
import textwrap
from mako.template import Template
from rhodecode import events
from rhodecode.translation import _
from rhodecode.lib import helpers as h
from rhodecode.lib.celerylib import run_task, async_task, RequestContextTask
from rhodecode.lib.colander_utils import strip_whitespace
from rhodecode.integrations.types.base import (
    IntegrationTypeBase, CommitParsingDataHandler, render_with_traceback)

log = logging.getLogger(__name__)


class HipchatSettingsSchema(colander.Schema):
    color_choices = [
        ('yellow', _('Yellow')),
        ('red', _('Red')),
        ('green', _('Green')),
        ('purple', _('Purple')),
        ('gray', _('Gray')),
    ]

    server_url = colander.SchemaNode(
        colander.String(),
        title=_('Hipchat server URL'),
        description=_('Hipchat integration url.'),
        default='',
        preparer=strip_whitespace,
        validator=colander.url,
        widget=deform.widget.TextInputWidget(
            placeholder='https://?.hipchat.com/v2/room/?/notification?auth_token=?',
        ),
    )
    notify = colander.SchemaNode(
        colander.Bool(),
        title=_('Notify'),
        description=_('Make a notification to the users in room.'),
        missing=False,
        default=False,
    )
    color = colander.SchemaNode(
        colander.String(),
        title=_('Color'),
        description=_('Background color of message.'),
        missing='',
        validator=colander.OneOf([x[0] for x in color_choices]),
        widget=deform.widget.Select2Widget(
            values=color_choices,
        ),
    )


repo_push_template = Template('''
<b>${data['actor']['username']}</b> pushed to repo <a href="${data['repo']['url']}">${data['repo']['repo_name']}</a>:
<br>
<ul>
%for branch, branch_commits in branches_commits.items():
    <li>
        % if branch:
        <a href="${branch_commits['branch']['url']}">branch: ${branch_commits['branch']['name']}</a>
        % else:
        to trunk
        % endif
        <ul>
        % for commit in branch_commits['commits']:
            <li><a href="${commit['url']}">${commit['short_id']}</a> - ${commit['message_html']}</li>
        % endfor
        </ul>
    </li>
%endfor
''')


class HipchatIntegrationType(IntegrationTypeBase, CommitParsingDataHandler):
    key = 'hipchat'
    display_name = _('Hipchat')
    description = _('Send events such as repo pushes and pull requests to '
                    'your hipchat channel.')

    @classmethod
    def icon(cls):
        return '''<?xml version="1.0" encoding="utf-8"?><!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN" "http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd"><svg version="1.1" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" x="0px" y="0px" viewBox="0 0 1000 1000" enable-background="new 0 0 1000 1000" xml:space="preserve"><g><g transform="translate(0.000000,511.000000) scale(0.100000,-0.100000)"><path fill="#205281" d="M4197.1,4662.4c-1661.5-260.4-3018-1171.6-3682.6-2473.3C219.9,1613.6,100,1120.3,100,462.6c0-1014,376.8-1918.4,1127-2699.4C2326.7-3377.6,3878.5-3898.3,5701-3730.5l486.5,44.5l208.9-123.3c637.2-373.4,1551.8-640.6,2240.4-650.9c304.9-6.9,335.7,0,417.9,75.4c185,174.7,147.3,411.1-89.1,548.1c-315.2,181.6-620,544.7-733.1,870.1l-51.4,157.6l472.7,472.7c349.4,349.4,520.7,551.5,657.7,774.2c784.5,1281.2,784.5,2788.5,0,4052.6c-236.4,376.8-794.8,966-1178.4,1236.7c-572.1,407.7-1264.1,709.1-1993.7,870.1c-267.2,58.2-479.6,75.4-1038,82.2C4714.4,4686.4,4310.2,4679.6,4197.1,4662.4z M5947.6,3740.9c1856.7-380.3,3127.6-1709.4,3127.6-3275c0-1000.3-534.4-1949.2-1466.2-2600.1c-188.4-133.6-287.8-226.1-301.5-284.4c-41.1-157.6,263.8-938.6,397.4-1020.8c20.5-10.3,34.3-44.5,34.3-75.4c0-167.8-811.9,195.3-1363.4,609.8l-181.6,137l-332.3-58.2c-445.3-78.8-1281.2-78.8-1702.6,0C2796-2569.2,1734.1-1832.6,1220.2-801.5C983.8-318.5,905,51.5,929,613.3c27.4,640.6,243.2,1192.1,685.1,1740.3c620,770.8,1661.5,1305.2,2822.8,1452.5C4806.9,3854,5553.7,3819.7,5947.6,3740.9z"/><path fill="#205281" d="M2381.5-345.9c-75.4-106.2-68.5-167.8,34.3-322c332.3-500.2,1010.6-928.4,1760.8-1120.2c417.9-106.2,1226.4-106.2,1644.3,0c712.5,181.6,1270.9,517.3,1685.4,1014C7681-561.7,7715.3-424.7,7616-325.4c-89.1,89.1-167.9,65.1-431.7-133.6c-835.8-630.3-2028-856.4-3086.5-585.8C3683.3-938.6,3142-685,2830.3-448.7C2576.8-253.4,2463.7-229.4,2381.5-345.9z"/></g></g><!-- Svg Vector Icons : http://www.onlinewebfonts.com/icon --></svg>'''

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
                comment_text=h.html_escape(comment_text[:200]),
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
                pr_title=h.html_escape(data['pullrequest']['title']),
                comment_text=h.html_escape(comment_text)
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
                pr_title=h.html_escape(data['pullrequest']['title']),
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
                '{action} by <b>{user}</b>').format(
            user=data['actor']['username'],
            number=data['pullrequest']['pull_request_id'],
            url=data['pullrequest']['url'],
            title=h.html_escape(data['pullrequest']['title']),
            action=action
        )

    def format_repo_push_event(self, data):
        branches_commits = self.aggregate_branch_data(
            data['push']['branches'], data['push']['commits'])

        result = render_with_traceback(
            repo_push_template,
            data=data,
            branches_commits=branches_commits,
        )
        return result

    def format_repo_create_event(self, data):
        return '<a href="{}">{}</a> ({}) repository created by <b>{}</b>'.format(
            data['repo']['url'],
            h.html_escape(data['repo']['repo_name']),
            data['repo']['repo_type'],
            data['actor']['username'],
        )


@async_task(ignore_result=True, base=RequestContextTask)
def post_text_to_hipchat(settings, text):
    log.debug('sending %s to hipchat %s' % (text, settings['server_url']))
    json_message = {
        "message": text,
        "color": settings.get('color', 'yellow'),
        "notify": settings.get('notify', False),
    }

    resp = requests.post(settings['server_url'], json=json_message, timeout=60)
    resp.raise_for_status()  # raise exception on a failed request
