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


log = logging.getLogger(__name__)

repo_push_template_plaintext = Template('''
Commits:

% for commit in data['push']['commits']:
${commit['url']} by ${commit['author']} at ${commit['date']}
${commit['message']}
----

% endfor
''')

## TODO (marcink): think about putting this into a file, or use base.mako email template

repo_push_template_html = Template('''
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
    <meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
    <title>${subject}</title>
    <style type="text/css">
        /* Based on The MailChimp Reset INLINE: Yes. */
        #outlook a {padding:0;} /* Force Outlook to provide a "view in browser" menu link. */
        body{width:100% !important; -webkit-text-size-adjust:100%; -ms-text-size-adjust:100%; margin:0; padding:0;}
        /* Prevent Webkit and Windows Mobile platforms from changing default font sizes.*/
        .ExternalClass {width:100%;} /* Force Hotmail to display emails at full width */
        .ExternalClass, .ExternalClass p, .ExternalClass span, .ExternalClass font, .ExternalClass td, .ExternalClass div {line-height: 100%;}
        /* Forces Hotmail to display normal line spacing.  More on that: http://www.emailonacid.com/forum/viewthread/43/ */
        #backgroundTable {margin:0; padding:0; line-height: 100% !important;}
        /* End reset */

        /* defaults for images*/
        img {outline:none; text-decoration:none; -ms-interpolation-mode: bicubic;}
        a img {border:none;}
        .image_fix {display:block;}

        body {line-height:1.2em;}
        p {margin: 0 0 20px;}
        h1, h2, h3, h4, h5, h6 {color:#323232!important;}
        a {color:#427cc9;text-decoration:none;outline:none;cursor:pointer;}
        a:focus {outline:none;}
        a:hover {color: #305b91;}
        h1 a, h2 a, h3 a, h4 a, h5 a, h6 a {color:#427cc9!important;text-decoration:none!important;}
        h1 a:active, h2 a:active,  h3 a:active, h4 a:active, h5 a:active, h6 a:active {color: #305b91!important;}
        h1 a:visited, h2 a:visited,  h3 a:visited, h4 a:visited, h5 a:visited, h6 a:visited {color: #305b91!important;}
        table {font-size:13px;border-collapse:collapse;mso-table-lspace:0pt;mso-table-rspace:0pt;}
        table td {padding:.65em 1em .65em 0;border-collapse:collapse;vertical-align:top;text-align:left;}
        input {display:inline;border-radius:2px;border-style:solid;border: 1px solid #dbd9da;padding:.5em;}
        input:focus {outline: 1px solid #979797}
        @media only screen and (-webkit-min-device-pixel-ratio: 2) {
        /* Put your iPhone 4g styles in here */
        }

        /* Android targeting */
        @media only screen and (-webkit-device-pixel-ratio:.75){
        /* Put CSS for low density (ldpi) Android layouts in here */
        }
        @media only screen and (-webkit-device-pixel-ratio:1){
        /* Put CSS for medium density (mdpi) Android layouts in here */
        }
        @media only screen and (-webkit-device-pixel-ratio:1.5){
        /* Put CSS for high density (hdpi) Android layouts in here */
        }
        /* end Android targeting */

    </style>

    <!-- Targeting Windows Mobile -->
    <!--[if IEMobile 7]>
    <style type="text/css">

    </style>
    <![endif]-->

    <!--[if gte mso 9]>
        <style>
        /* Target Outlook 2007 and 2010 */
        </style>
    <![endif]-->
</head>
<body>
<!-- Wrapper/Container Table: Use a wrapper table to control the width and the background color consistently of your email. Use this approach instead of setting attributes on the body tag. -->
<table cellpadding="0" cellspacing="0" border="0" id="backgroundTable" align="left" style="margin:1%;width:97%;padding:0;font-family:sans-serif;font-weight:100;border:1px solid #dbd9da">
    <tr>
        <td valign="top" style="padding:0;">
            <table cellpadding="0" cellspacing="0" border="0" align="left" width="100%">
                <tr><td style="width:100%;padding:7px;background-color:#202020" valign="top">
                    <a style="color:#eeeeee;text-decoration:none;" href="${instance_url}">
                        ${'RhodeCode'}
                    </a>
                </td></tr>
                <tr>
                    <td style="padding:15px;" valign="top">
                        % for commit in data['push']['commits']:
                        <a href="${commit['url']}">${commit['short_id']}</a> by ${commit['author']} at ${commit['date']} <br/>
                        ${commit['message_html']} <br/>
                        <br/>
                        % endfor
                    </td>
                </tr>
            </table>
        </td>
    </tr>
</table>
<!-- End of wrapper table -->
<p><a style="margin-top:15px;margin-left:1%;font-family:sans-serif;font-weight:100;font-size:11px;color:#666666;text-decoration:none;" href="${instance_url}">
    ${'This is a notification from RhodeCode. %(instance_url)s' % {'instance_url': instance_url}}
</a></p>
</body>
</html>
''')


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
    commit_num = len(data['push']['commits'])
    server_url = data['server_url']

    if commit_num == 0:
        subject = '[{repo_name}] {author} pushed {commit_num} commit on branches: {branches}'.format(
            author=data['actor']['username'],
            repo_name=data['repo']['repo_name'],
            commit_num=commit_num,
            branches=', '.join(
                branch['name'] for branch in data['push']['branches'])
        )
    else:
        subject = '[{repo_name}] {author} pushed {commit_num} commits on branches: {branches}'.format(
            author=data['actor']['username'],
            repo_name=data['repo']['repo_name'],
            commit_num=commit_num,
            branches=', '.join(
                branch['name'] for branch in data['push']['branches']))

    email_body_plaintext = repo_push_template_plaintext.render(
        data=data,
        subject=subject,
        instance_url=server_url)

    email_body_html = repo_push_template_html.render(
        data=data,
        subject=subject,
        instance_url=server_url)

    for email_address in settings['recipients']:
        run_task(
            tasks.send_email, email_address, subject,
            email_body_plaintext, email_body_html)
