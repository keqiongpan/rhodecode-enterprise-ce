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

import colander
import string
import collections
import logging
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

from mako import exceptions

from rhodecode.translation import _


log = logging.getLogger(__name__)


class IntegrationTypeBase(object):
    """ Base class for IntegrationType plugins """
    is_dummy = False
    description = ''

    @classmethod
    def icon(cls):
        return '''
        <?xml version="1.0" encoding="UTF-8" standalone="no"?>
        <svg
           xmlns:dc="http://purl.org/dc/elements/1.1/"
           xmlns:cc="http://creativecommons.org/ns#"
           xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
           xmlns:svg="http://www.w3.org/2000/svg"
           xmlns="http://www.w3.org/2000/svg"
           xmlns:sodipodi="http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd"
           xmlns:inkscape="http://setwww.inkscape.org/namespaces/inkscape"
           viewBox="0 -256 1792 1792"
           id="svg3025"
           version="1.1"
           inkscape:version="0.48.3.1 r9886"
           width="100%"
           height="100%"
           sodipodi:docname="cog_font_awesome.svg">
          <metadata
             id="metadata3035">
            <rdf:RDF>
              <cc:Work
                 rdf:about="">
                <dc:format>image/svg+xml</dc:format>
                <dc:type
                   rdf:resource="http://purl.org/dc/dcmitype/StillImage" />
              </cc:Work>
            </rdf:RDF>
          </metadata>
          <defs
             id="defs3033" />
          <sodipodi:namedview
             pagecolor="#ffffff"
             bordercolor="#666666"
             borderopacity="1"
             objecttolerance="10"
             gridtolerance="10"
             guidetolerance="10"
             inkscape:pageopacity="0"
             inkscape:pageshadow="2"
             inkscape:window-width="640"
             inkscape:window-height="480"
             id="namedview3031"
             showgrid="false"
             inkscape:zoom="0.13169643"
             inkscape:cx="896"
             inkscape:cy="896"
             inkscape:window-x="0"
             inkscape:window-y="25"
             inkscape:window-maximized="0"
             inkscape:current-layer="svg3025" />
          <g
             transform="matrix(1,0,0,-1,121.49153,1285.4237)"
             id="g3027">
            <path
               d="m 1024,640 q 0,106 -75,181 -75,75 -181,75 -106,0 -181,-75 -75,-75 -75,-181 0,-106 75,-181 75,-75 181,-75 106,0 181,75 75,75 75,181 z m 512,109 V 527 q 0,-12 -8,-23 -8,-11 -20,-13 l -185,-28 q -19,-54 -39,-91 35,-50 107,-138 10,-12 10,-25 0,-13 -9,-23 -27,-37 -99,-108 -72,-71 -94,-71 -12,0 -26,9 l -138,108 q -44,-23 -91,-38 -16,-136 -29,-186 -7,-28 -36,-28 H 657 q -14,0 -24.5,8.5 Q 622,-111 621,-98 L 593,86 q -49,16 -90,37 L 362,16 Q 352,7 337,7 323,7 312,18 186,132 147,186 q -7,10 -7,23 0,12 8,23 15,21 51,66.5 36,45.5 54,70.5 -27,50 -41,99 L 29,495 Q 16,497 8,507.5 0,518 0,531 v 222 q 0,12 8,23 8,11 19,13 l 186,28 q 14,46 39,92 -40,57 -107,138 -10,12 -10,24 0,10 9,23 26,36 98.5,107.5 72.5,71.5 94.5,71.5 13,0 26,-10 l 138,-107 q 44,23 91,38 16,136 29,186 7,28 36,28 h 222 q 14,0 24.5,-8.5 Q 914,1391 915,1378 l 28,-184 q 49,-16 90,-37 l 142,107 q 9,9 24,9 13,0 25,-10 129,-119 165,-170 7,-8 7,-22 0,-12 -8,-23 -15,-21 -51,-66.5 -36,-45.5 -54,-70.5 26,-50 41,-98 l 183,-28 q 13,-2 21,-12.5 8,-10.5 8,-23.5 z"
               id="path3029"
               inkscape:connector-curvature="0"
               style="fill:currentColor" />
          </g>
        </svg>
        '''

    def __init__(self, settings):
        """
        :param settings: dict of settings to be used for the integration
        """
        self.settings = settings

    def settings_schema(self):
        """
        A colander schema of settings for the integration type
        """
        return colander.Schema()


class EEIntegration(IntegrationTypeBase):
    description = 'Integration available in RhodeCode EE edition.'
    is_dummy = True

    def __init__(self, name, key, settings=None):
        self.display_name = name
        self.key = key
        super(EEIntegration, self).__init__(settings)


# Helpers #
# updating this required to update the `common_vars` as well.
WEBHOOK_URL_VARS = [
    ('event_name', 'Unique name of the event type, e.g pullrequest-update'),
    ('repo_name', 'Full name of the repository'),
    ('repo_type', 'VCS type of repository'),
    ('repo_id', 'Unique id of repository'),
    ('repo_url', 'Repository url'),
    # extra repo fields
    ('extra:<extra_key_name>', 'Extra repo variables, read from its settings.'),

    # special attrs below that we handle, using multi-call
    ('branch', 'Name of each branch submitted, if any.'),
    ('branch_head', 'Head ID of pushed branch (full sha of last commit), if any.'),
    ('commit_id', 'ID (full sha) of each commit submitted, if any.'),

    # pr events vars
    ('pull_request_id', 'Unique ID of the pull request.'),
    ('pull_request_title', 'Title of the pull request.'),
    ('pull_request_url', 'Pull request url.'),
    ('pull_request_shadow_url', 'Pull request shadow repo clone url.'),
    ('pull_request_commits_uid', 'Calculated UID of all commits inside the PR. '
                                 'Changes after PR update'),

    # user who triggers the call
    ('username', 'User who triggered the call.'),
    ('user_id', 'User id who triggered the call.'),
]

# common vars for url template used for CI plugins. Shared with webhook
CI_URL_VARS = WEBHOOK_URL_VARS


class CommitParsingDataHandler(object):

    def aggregate_branch_data(self, branches, commits):
        branch_data = collections.OrderedDict()
        for obj in branches:
            branch_data[obj['name']] = obj

        branches_commits = collections.OrderedDict()
        for commit in commits:
            if commit.get('git_ref_change'):
                # special case for GIT that allows creating tags,
                # deleting branches without associated commit
                continue
            commit_branch = commit['branch']

            if commit_branch not in branches_commits:
                _branch = branch_data[commit_branch] \
                    if commit_branch else commit_branch
                branch_commits = {'branch': _branch,
                                  'branch_head': '',
                                  'commits': []}
                branches_commits[commit_branch] = branch_commits

            branch_commits = branches_commits[commit_branch]
            branch_commits['commits'].append(commit)
            branch_commits['branch_head'] = commit['raw_id']
        return branches_commits


class WebhookDataHandler(CommitParsingDataHandler):
    name = 'webhook'

    def __init__(self, template_url, headers):
        self.template_url = template_url
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
            'user_id': data['actor']['user_id'],
            'event_name': data['name']
        }

        extra_vars = {}
        for extra_key, extra_val in data['repo']['extra_fields'].items():
            extra_vars['extra__{}'.format(extra_key)] = extra_val
        common_vars.update(extra_vars)

        template_url = self.template_url.replace('${extra:', '${extra__')
        return string.Template(template_url).safe_substitute(**common_vars)

    def repo_push_event_handler(self, event, data):
        url = self.get_base_parsed_template(data)
        url_calls = []

        branches_commits = self.aggregate_branch_data(
            data['push']['branches'], data['push']['commits'])
        if '${branch}' in url or '${branch_head}' in url or '${commit_id}' in url:
            # call it multiple times, for each branch if used in variables
            for branch, commit_ids in branches_commits.items():
                branch_url = string.Template(url).safe_substitute(branch=branch)

                if '${branch_head}' in branch_url:
                    # last commit in the aggregate is the head of the branch
                    branch_head = commit_ids['branch_head']
                    branch_url = string.Template(branch_url).safe_substitute(
                        branch_head=branch_head)

                # call further down for each commit if used
                if '${commit_id}' in branch_url:
                    for commit_data in commit_ids['commits']:
                        commit_id = commit_data['raw_id']
                        commit_url = string.Template(branch_url).safe_substitute(
                            commit_id=commit_id)
                        # register per-commit call
                        log.debug(
                            'register %s call(%s) to url %s',
                            self.name, event, commit_url)
                        url_calls.append(
                            (commit_url, self.headers, data))

                else:
                    # register per-branch call
                    log.debug(
                        'register %s call(%s) to url %s',
                        self.name, event, branch_url)
                    url_calls.append(
                        (branch_url, self.headers, data))

        else:
            log.debug(
                'register %s call(%s) to url %s', self.name, event, url)
            url_calls.append((url, self.headers, data))

        return url_calls

    def repo_create_event_handler(self, event, data):
        url = self.get_base_parsed_template(data)
        log.debug(
            'register %s call(%s) to url %s', self.name, event, url)
        return [(url, self.headers, data)]

    def pull_request_event_handler(self, event, data):
        url = self.get_base_parsed_template(data)
        log.debug(
            'register %s call(%s) to url %s', self.name, event, url)
        url = string.Template(url).safe_substitute(
            pull_request_id=data['pullrequest']['pull_request_id'],
            pull_request_title=data['pullrequest']['title'],
            pull_request_url=data['pullrequest']['url'],
            pull_request_shadow_url=data['pullrequest']['shadow_url'],
            pull_request_commits_uid=data['pullrequest']['commits_uid'],
        )
        return [(url, self.headers, data)]

    def __call__(self, event, data):
        from rhodecode import events

        if isinstance(event, events.RepoPushEvent):
            return self.repo_push_event_handler(event, data)
        elif isinstance(event, events.RepoCreateEvent):
            return self.repo_create_event_handler(event, data)
        elif isinstance(event, events.PullRequestEvent):
            return self.pull_request_event_handler(event, data)
        else:
            raise ValueError(
                'event type `%s` not in supported list: %s' % (
                    event.__class__, events))


def get_auth(settings):
    from requests.auth import HTTPBasicAuth
    username = settings.get('username')
    password = settings.get('password')
    if username and password:
        return HTTPBasicAuth(username, password)
    return None


def get_web_token(settings):
    return settings['secret_token']


def get_url_vars(url_vars):
    return '\n'.join(
        '{} - {}'.format('${' + key + '}', explanation)
        for key, explanation in url_vars)


def render_with_traceback(template, *args, **kwargs):
    try:
        return template.render(*args, **kwargs)
    except Exception:
        log.error(exceptions.text_error_template().render())
        raise


STATUS_400 = (400, 401, 403)
STATUS_500 = (500, 502, 504)


def requests_retry_call(
        retries=3, backoff_factor=0.3, status_forcelist=STATUS_400+STATUS_500,
        session=None):
    """
    session = requests_retry_session()
    response = session.get('http://example.com')

    :param retries:
    :param backoff_factor:
    :param status_forcelist:
    :param session:
    """
    session = session or requests.Session()
    retry = Retry(
        total=retries,
        read=retries,
        connect=retries,
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session
