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
from rhodecode.translation import _
from rhodecode.lib import helpers as h
from rhodecode.lib.celerylib import run_task
from rhodecode.lib.colander_utils import strip_whitespace
from rhodecode.integrations.types.base import IntegrationTypeBase

log = logging.getLogger(__name__)


class SlackSettingsSchema(colander.Schema):
    service = colander.SchemaNode(
        colander.String(),
        title=_('Slack service URL'),
        description=h.literal(_(
            'This can be setup at the '
            '<a href="https://my.slack.com/services/new/incoming-webhook/">'
            'slack app manager</a>')),
        default='',
        preparer=strip_whitespace,
        validator=colander.url,
        widget=deform.widget.TextInputWidget(
            placeholder='https://hooks.slack.com/services/...',
        ),
    )
    username = colander.SchemaNode(
        colander.String(),
        title=_('Username'),
        description=_('Username to show notifications coming from.'),
        missing='Rhodecode',
        preparer=strip_whitespace,
        widget=deform.widget.TextInputWidget(
            placeholder='Rhodecode'
        ),
    )
    channel = colander.SchemaNode(
        colander.String(),
        title=_('Channel'),
        description=_('Channel to send notifications to.'),
        missing='',
        preparer=strip_whitespace,
        widget=deform.widget.TextInputWidget(
            placeholder='#general'
        ),
    )
    icon_emoji = colander.SchemaNode(
        colander.String(),
        title=_('Emoji'),
        description=_('Emoji to use eg. :studio_microphone:'),
        missing='',
        preparer=strip_whitespace,
        widget=deform.widget.TextInputWidget(
            placeholder=':studio_microphone:'
        ),
    )


repo_push_template = Template(r'''
*${data['actor']['username']}* pushed to repo <${data['repo']['url']}|${data['repo']['repo_name']}>:
%for branch, branch_commits in branches_commits.items():
branch: <${branch_commits['branch']['url']}|${branch_commits['branch']['name']}>
    %for commit in branch_commits['commits']:
> <${commit['url']}|${commit['short_id']}> - ${commit['message_html']|html_to_slack_links}
    %endfor
%endfor
''')


class SlackIntegrationType(IntegrationTypeBase):
    key = 'slack'
    display_name = _('Slack')
    description = _('Send events such as repo pushes and pull requests to '
                    'your slack channel.')
    icon = '''<?xml version="1.0" encoding="UTF-8" standalone="no"?><svg viewBox="0 0 256 256" version="1.1" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" preserveAspectRatio="xMidYMid"><g><path d="M165.963541,15.8384262 C162.07318,3.86308197 149.212328,-2.69009836 137.239082,1.20236066 C125.263738,5.09272131 118.710557,17.9535738 122.603016,29.9268197 L181.550164,211.292328 C185.597902,222.478689 197.682361,228.765377 209.282098,225.426885 C221.381246,221.943607 228.756984,209.093246 224.896,197.21023 C224.749115,196.756984 165.963541,15.8384262 165.963541,15.8384262" fill="#DFA22F"></path><path d="M74.6260984,45.515541 C70.7336393,33.5422951 57.8727869,26.9891148 45.899541,30.8794754 C33.9241967,34.7698361 27.3710164,47.6306885 31.2634754,59.6060328 L90.210623,240.971541 C94.2583607,252.157902 106.34282,258.44459 117.942557,255.104 C130.041705,251.62282 137.417443,238.772459 133.556459,226.887344 C133.409574,226.436197 74.6260984,45.515541 74.6260984,45.515541" fill="#3CB187"></path><path d="M240.161574,166.045377 C252.136918,162.155016 258.688,149.294164 254.797639,137.31882 C250.907279,125.345574 238.046426,118.792393 226.07318,122.682754 L44.7076721,181.632 C33.5213115,185.677639 27.234623,197.762098 30.5731148,209.361836 C34.0563934,221.460984 46.9067541,228.836721 58.7897705,224.975738 C59.2430164,224.828852 240.161574,166.045377 240.161574,166.045377" fill="#CE1E5B"></path><path d="M82.507541,217.270557 C94.312918,213.434754 109.528131,208.491016 125.855475,203.186361 C122.019672,191.380984 117.075934,176.163672 111.76918,159.83423 L68.4191475,173.924721 L82.507541,217.270557" fill="#392538"></path><path d="M173.847082,187.591344 C190.235279,182.267803 205.467279,177.31777 217.195016,173.507148 C213.359213,161.70177 208.413377,146.480262 203.106623,130.146623 L159.75659,144.237115 L173.847082,187.591344" fill="#BB242A"></path><path d="M210.484459,74.7058361 C222.457705,70.8154754 229.010885,57.954623 225.120525,45.9792787 C221.230164,34.0060328 208.369311,27.4528525 196.393967,31.3432131 L15.028459,90.292459 C3.84209836,94.3380984 -2.44459016,106.422557 0.896,118.022295 C4.37718033,130.121443 17.227541,137.49718 29.1126557,133.636197 C29.5638033,133.489311 210.484459,74.7058361 210.484459,74.7058361" fill="#72C5CD"></path><path d="M52.8220328,125.933115 C64.6274098,122.097311 79.8468197,117.151475 96.1762623,111.84682 C90.8527213,95.4565246 85.9026885,80.2245246 82.0920656,68.4946885 L38.731541,82.5872787 L52.8220328,125.933115" fill="#248C73"></path><path d="M144.159475,96.256 C160.551869,90.9303607 175.785967,85.9803279 187.515803,82.1676066 C182.190164,65.7752131 177.240131,50.5390164 173.42741,38.807082 L130.068984,52.8996721 L144.159475,96.256" fill="#62803A"></path></g></svg>'''
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

        text = '*%s* caused a *%s* event' % (
            data['actor']['username'], event.name)

        log.debug('handling slack event for %s' % event.name)

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

        run_task(post_text_to_slack, self.settings, text)

    def settings_schema(self):
        schema = SlackSettingsSchema()
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
            comment_text = '<{comment_url}|{comment_text}...>'.format(
                comment_text=comment_text[:200],
                comment_url=data['comment']['url'],
            )

        comment_status = ''
        if data['comment']['status']:
            comment_status = '[{}]: '.format(data['comment']['status'])

        return (textwrap.dedent(
            '''
            {user} commented on pull request <{pr_url}|#{number}> - {pr_title}:
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
            Status changed to {pr_status} for pull request <{pr_url}|#{number}> - {pr_title}
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

        return ('Pull request <{url}|#{number}> - {title} '
                '{action} by {user}').format(
            user=data['actor']['username'],
            number=data['pullrequest']['pull_request_id'],
            url=data['pullrequest']['url'],
            title=data['pullrequest']['title'],
            action=action
        )

    def format_repo_push_event(self, data):
        branch_data = {branch['name']: branch
                      for branch in data['push']['branches']}

        branches_commits = {}
        for commit in data['push']['commits']:
            log.critical(commit)
            if commit['branch'] not in branches_commits:
                branch_commits = {'branch': branch_data[commit['branch']],
                                  'commits': []}
                branches_commits[commit['branch']] = branch_commits

            branch_commits = branches_commits[commit['branch']]
            branch_commits['commits'].append(commit)

        result = repo_push_template.render(
            data=data,
            branches_commits=branches_commits,
            html_to_slack_links=html_to_slack_links,
        )
        return result

    def format_repo_create_event(self, data):
        return '<{}|{}> ({}) repository created by *{}*'.format(
            data['repo']['url'],
            data['repo']['repo_name'],
            data['repo']['repo_type'],
            data['actor']['username'],
        )


def html_to_slack_links(message):
    return re.compile(r'<a .*?href=["\'](.+?)".*?>(.+?)</a>').sub(
        r'<\1|\2>', message)


@task(ignore_result=True)
def post_text_to_slack(settings, text):
    log.debug('sending %s to slack %s' % (text, settings['service']))
    resp = requests.post(settings['service'], json={
        "channel": settings.get('channel', ''),
        "username": settings.get('username', 'Rhodecode'),
        "text": text,
        "icon_emoji": settings.get('icon_emoji', ':studio_microphone:')
    })
    resp.raise_for_status()  # raise exception on a failed request
