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
import string
from collections import OrderedDict

import deform
import deform.widget
import logging
import requests
import requests.adapters
import colander
from requests.packages.urllib3.util.retry import Retry

import rhodecode
from rhodecode import events
from rhodecode.translation import _
from rhodecode.integrations.types.base import (
    IntegrationTypeBase, get_auth, get_url_vars)
from rhodecode.lib.celerylib import run_task, async_task, RequestContextTask

log = logging.getLogger(__name__)


# updating this required to update the `common_vars` passed in url calling func
WEBHOOK_URL_VARS = [
    'repo_name',
    'repo_type',
    'repo_id',
    'repo_url',
    # extra repo fields
    'extra:<extra_key_name>',

    # special attrs below that we handle, using multi-call
    'branch',
    'commit_id',

    # pr events vars
    'pull_request_id',
    'pull_request_url',

    # user who triggers the call
    'username',
    'user_id',

]
URL_VARS = get_url_vars(WEBHOOK_URL_VARS)


class WebhookHandler(object):
    def __init__(self, template_url, secret_token, headers):
        self.template_url = template_url
        self.secret_token = secret_token
        self.headers = headers

    def get_base_parsed_template(self, data):
        """
        initially parses the passed in template with some common variables
        available on ALL calls
        """
        # note: make sure to update the `WEBHOOK_URL_VARS` if this changes
        common_vars = {
            'repo_name': data['repo']['repo_name'],
            'repo_type': data['repo']['repo_type'],
            'repo_id': data['repo']['repo_id'],
            'repo_url': data['repo']['url'],
            'username': data['actor']['username'],
            'user_id': data['actor']['user_id']
        }

        extra_vars = {}
        for extra_key, extra_val in data['repo']['extra_fields'].items():
            extra_vars['extra__{}'.format(extra_key)] = extra_val
        common_vars.update(extra_vars)

        template_url = self.template_url.replace('${extra:', '${extra__')
        return string.Template(template_url).safe_substitute(**common_vars)

    def repo_push_event_handler(self, event, data):
        url = self.get_base_parsed_template(data)
        url_cals = []
        branch_data = OrderedDict()
        for obj in data['push']['branches']:
            branch_data[obj['name']] = obj

        branches_commits = OrderedDict()
        for commit in data['push']['commits']:
            if commit.get('git_ref_change'):
                # special case for GIT that allows creating tags,
                # deleting branches without associated commit
                continue

            if commit['branch'] not in branches_commits:
                branch_commits = {'branch': branch_data[commit['branch']],
                                  'commits': []}
                branches_commits[commit['branch']] = branch_commits

            branch_commits = branches_commits[commit['branch']]
            branch_commits['commits'].append(commit)

        if '${branch}' in url:
            # call it multiple times, for each branch if used in variables
            for branch, commit_ids in branches_commits.items():
                branch_url = string.Template(url).safe_substitute(branch=branch)
                # call further down for each commit if used
                if '${commit_id}' in branch_url:
                    for commit_data in commit_ids['commits']:
                        commit_id = commit_data['raw_id']
                        commit_url = string.Template(branch_url).safe_substitute(
                            commit_id=commit_id)
                        # register per-commit call
                        log.debug(
                            'register webhook call(%s) to url %s', event, commit_url)
                        url_cals.append((commit_url, self.secret_token, self.headers, data))

                else:
                    # register per-branch call
                    log.debug(
                        'register webhook call(%s) to url %s', event, branch_url)
                    url_cals.append((branch_url, self.secret_token, self.headers, data))

        else:
            log.debug(
                'register webhook call(%s) to url %s', event, url)
            url_cals.append((url, self.secret_token, self.headers, data))

        return url_cals

    def repo_create_event_handler(self, event, data):
        url = self.get_base_parsed_template(data)
        log.debug(
            'register webhook call(%s) to url %s', event, url)
        return [(url, self.secret_token, self.headers, data)]

    def pull_request_event_handler(self, event, data):
        url = self.get_base_parsed_template(data)
        log.debug(
            'register webhook call(%s) to url %s', event, url)
        url = string.Template(url).safe_substitute(
            pull_request_id=data['pullrequest']['pull_request_id'],
            pull_request_url=data['pullrequest']['url'])
        return [(url, self.secret_token, self.headers, data)]

    def __call__(self, event, data):
        if isinstance(event, events.RepoPushEvent):
            return self.repo_push_event_handler(event, data)
        elif isinstance(event, events.RepoCreateEvent):
            return self.repo_create_event_handler(event, data)
        elif isinstance(event, events.PullRequestEvent):
            return self.pull_request_event_handler(event, data)
        else:
            raise ValueError('event type not supported: %s' % events)


class WebhookSettingsSchema(colander.Schema):
    url = colander.SchemaNode(
        colander.String(),
        title=_('Webhook URL'),
        description=
            _('URL to which Webhook should submit data. Following variables '
              'are allowed to be used: {vars}. Some of the variables would '
              'trigger multiple calls, like ${{branch}} or ${{commit_id}}. '
              'Webhook will be called as many times as unique objects in '
              'data in such cases.').format(vars=URL_VARS),
        missing=colander.required,
        required=True,
        validator=colander.url,
        widget=deform.widget.TextInputWidget(
            placeholder='https://www.example.com/webhook'
        ),
    )
    secret_token = colander.SchemaNode(
        colander.String(),
        title=_('Secret Token'),
        description=_('Optional string used to validate received payloads. '
                      'It will be sent together with event data in JSON'),
        default='',
        missing='',
        widget=deform.widget.TextInputWidget(
            placeholder='e.g. secret_token'
        ),
    )
    username = colander.SchemaNode(
        colander.String(),
        title=_('Username'),
        description=_('Optional username to authenticate the call.'),
        default='',
        missing='',
        widget=deform.widget.TextInputWidget(
            placeholder='e.g. admin'
        ),
    )
    password = colander.SchemaNode(
        colander.String(),
        title=_('Password'),
        description=_('Optional password to authenticate the call.'),
        default='',
        missing='',
        widget=deform.widget.PasswordWidget(
            placeholder='e.g. secret.',
            redisplay=True,
        ),
    )
    custom_header_key = colander.SchemaNode(
        colander.String(),
        title=_('Custom Header Key'),
        description=_('Custom Header name to be set when calling endpoint.'),
        default='',
        missing='',
        widget=deform.widget.TextInputWidget(
            placeholder='e.g.Authorization'
        ),
    )
    custom_header_val = colander.SchemaNode(
        colander.String(),
        title=_('Custom Header Value'),
        description=_('Custom Header value to be set when calling endpoint.'),
        default='',
        missing='',
        widget=deform.widget.TextInputWidget(
            placeholder='e.g. RcLogin auth=xxxx'
        ),
    )
    method_type = colander.SchemaNode(
        colander.String(),
        title=_('Call Method'),
        description=_('Select if the Webhook call should be made '
                      'with POST or GET.'),
        default='post',
        missing='',
        widget=deform.widget.RadioChoiceWidget(
            values=[('get', 'GET'), ('post', 'POST')],
            inline=True
        ),
    )


class WebhookIntegrationType(IntegrationTypeBase):
    key = 'webhook'
    display_name = _('Webhook')
    description = _('Post json events to a Webhook endpoint')

    @classmethod
    def icon(cls):
        return '''<?xml version="1.0" encoding="UTF-8" standalone="no"?><svg viewBox="0 0 256 239" version="1.1" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" preserveAspectRatio="xMidYMid"><g><path d="M119.540432,100.502743 C108.930124,118.338815 98.7646301,135.611455 88.3876025,152.753617 C85.7226696,157.154315 84.4040417,160.738531 86.5332204,166.333309 C92.4107024,181.787152 84.1193605,196.825836 68.5350381,200.908244 C53.8383677,204.759349 39.5192953,195.099955 36.6032893,179.365384 C34.0194114,165.437749 44.8274148,151.78491 60.1824106,149.608284 C61.4694072,149.424428 62.7821041,149.402681 64.944891,149.240571 C72.469175,136.623655 80.1773157,123.700312 88.3025935,110.073173 C73.611854,95.4654658 64.8677898,78.3885437 66.803227,57.2292132 C68.1712787,42.2715849 74.0527146,29.3462646 84.8033863,18.7517722 C105.393354,-1.53572199 136.805164,-4.82141828 161.048542,10.7510424 C184.333097,25.7086706 194.996783,54.8450075 185.906752,79.7822957 C179.052655,77.9239597 172.151111,76.049808 164.563565,73.9917997 C167.418285,60.1274266 165.306899,47.6765751 155.95591,37.0109123 C149.777932,29.9690049 141.850349,26.2780332 132.835442,24.9178894 C114.764113,22.1877169 97.0209573,33.7983633 91.7563309,51.5355878 C85.7800012,71.6669027 94.8245623,88.1111998 119.540432,100.502743 L119.540432,100.502743 Z" fill="#C73A63"></path><path d="M149.841194,79.4106285 C157.316054,92.5969067 164.905578,105.982857 172.427885,119.246236 C210.44865,107.483365 239.114472,128.530009 249.398582,151.063322 C261.81978,178.282014 253.328765,210.520191 228.933162,227.312431 C203.893073,244.551464 172.226236,241.605803 150.040866,219.46195 C155.694953,214.729124 161.376716,209.974552 167.44794,204.895759 C189.360489,219.088306 208.525074,218.420096 222.753207,201.614016 C234.885769,187.277151 234.622834,165.900356 222.138374,151.863988 C207.730339,135.66681 188.431321,135.172572 165.103273,150.721309 C155.426087,133.553447 145.58086,116.521995 136.210101,99.2295848 C133.05093,93.4015266 129.561608,90.0209366 122.440622,88.7873178 C110.547271,86.7253555 102.868785,76.5124151 102.408155,65.0698097 C101.955433,53.7537294 108.621719,43.5249733 119.04224,39.5394355 C129.363912,35.5914599 141.476705,38.7783085 148.419765,47.554004 C154.093621,54.7244134 155.896602,62.7943365 152.911402,71.6372484 C152.081082,74.1025091 151.00562,76.4886916 149.841194,79.4106285 L149.841194,79.4106285 Z" fill="#4B4B4B"></path><path d="M167.706921,187.209935 L121.936499,187.209935 C117.54964,205.253587 108.074103,219.821756 91.7464461,229.085759 C79.0544063,236.285822 65.3738898,238.72736 50.8136292,236.376762 C24.0061432,232.053165 2.08568567,207.920497 0.156179306,180.745298 C-2.02835403,149.962159 19.1309765,122.599149 47.3341915,116.452801 C49.2814904,123.524363 51.2485589,130.663141 53.1958579,137.716911 C27.3195169,150.919004 18.3639187,167.553089 25.6054984,188.352614 C31.9811726,206.657224 50.0900643,216.690262 69.7528413,212.809503 C89.8327554,208.847688 99.9567329,192.160226 98.7211371,165.37844 C117.75722,165.37844 136.809118,165.180745 155.847178,165.475311 C163.280522,165.591951 169.019617,164.820939 174.620326,158.267339 C183.840836,147.48306 200.811003,148.455721 210.741239,158.640984 C220.88894,169.049642 220.402609,185.79839 209.663799,195.768166 C199.302587,205.38802 182.933414,204.874012 173.240413,194.508846 C171.247644,192.37176 169.677943,189.835329 167.706921,187.209935 L167.706921,187.209935 Z" fill="#4A4A4A"></path></g></svg>'''

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

    def settings_schema(self):
        schema = WebhookSettingsSchema()
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

    def send_event(self, event):
        log.debug('handling event %s with Webhook integration %s',
            event.name, self)

        if event.__class__ not in self.valid_events:
            log.debug('event not valid: %r' % event)
            return

        if event.name not in self.settings['events']:
            log.debug('event ignored: %r' % event)
            return

        data = event.as_dict()
        template_url = self.settings['url']

        headers = {}
        head_key = self.settings.get('custom_header_key')
        head_val = self.settings.get('custom_header_val')
        if head_key and head_val:
            headers = {head_key: head_val}

        handler = WebhookHandler(
            template_url, self.settings['secret_token'], headers)

        url_calls = handler(event, data)
        log.debug('webhook: calling following urls: %s',
                  [x[0] for x in url_calls])

        run_task(post_to_webhook, url_calls, self.settings)


@async_task(ignore_result=True, base=RequestContextTask)
def post_to_webhook(url_calls, settings):
    """
    Example data::

        {'actor': {'user_id': 2, 'username': u'admin'},
         'actor_ip': u'192.168.157.1',
         'name': 'repo-push',
         'push': {'branches': [{'name': u'default',
            'url': 'http://rc.local:8080/hg-repo/changelog?branch=default'}],
          'commits': [{'author': u'Marcin Kuzminski <marcin@rhodecode.com>',
            'branch': u'default',
            'date': datetime.datetime(2017, 11, 30, 12, 59, 48),
            'issues': [],
            'mentions': [],
            'message': u'commit Thu 30 Nov 2017 13:59:48 CET',
            'message_html': u'commit Thu 30 Nov 2017 13:59:48 CET',
            'message_html_title': u'commit Thu 30 Nov 2017 13:59:48 CET',
            'parents': [{'raw_id': '431b772a5353dad9974b810dd3707d79e3a7f6e0'}],
            'permalink_url': u'http://rc.local:8080/_7/changeset/a815cc738b9651eb5ffbcfb1ce6ccd7c701a5ddf',
            'raw_id': 'a815cc738b9651eb5ffbcfb1ce6ccd7c701a5ddf',
            'refs': {'bookmarks': [], 'branches': [u'default'], 'tags': [u'tip']},
            'reviewers': [],
            'revision': 9L,
            'short_id': 'a815cc738b96',
            'url': u'http://rc.local:8080/hg-repo/changeset/a815cc738b9651eb5ffbcfb1ce6ccd7c701a5ddf'}],
          'issues': {}},
         'repo': {'extra_fields': '',
          'permalink_url': u'http://rc.local:8080/_7',
          'repo_id': 7,
          'repo_name': u'hg-repo',
          'repo_type': u'hg',
          'url': u'http://rc.local:8080/hg-repo'},
         'server_url': u'http://rc.local:8080',
         'utc_timestamp': datetime.datetime(2017, 11, 30, 13, 0, 1, 569276)

    """
    max_retries = 3
    retries = Retry(
        total=max_retries,
        backoff_factor=0.15,
        status_forcelist=[500, 502, 503, 504])
    call_headers = {
        'User-Agent': 'RhodeCode-webhook-caller/{}'.format(
            rhodecode.__version__)
    }  # updated below with custom ones, allows override

    for url, token, headers, data in url_calls:
        req_session = requests.Session()
        req_session.mount(  # retry max N times
            'http://', requests.adapters.HTTPAdapter(max_retries=retries))

        method = settings.get('method_type') or 'post'
        call_method = getattr(req_session, method)

        headers = headers or {}
        call_headers.update(headers)
        auth = get_auth(settings)

        log.debug('calling Webhook with method: %s, and auth:%s',
                  call_method, auth)
        if settings.get('log_data'):
            log.debug('calling webhook with data: %s', data)
        resp = call_method(url, json={
            'token': token,
            'event': data
        }, headers=call_headers, auth=auth)
        log.debug('Got Webhook response: %s', resp)

        resp.raise_for_status()  # raise exception on a failed request
