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
import colander

from mako.template import Template

from rhodecode import events
from rhodecode.translation import _
from rhodecode.lib.celerylib import run_task
from rhodecode.lib.celerylib import tasks
from rhodecode.integrations.types.base import (
    IntegrationTypeBase, render_with_traceback)


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
                        % if data['push']['commits']:
                            % for commit in data['push']['commits']:
                            <a href="${commit['url']}">${commit['short_id']}</a> by ${commit['author']} at ${commit['date']} <br/>
                            ${commit['message_html']} <br/>
                            <br/>
                            % endfor
                        % else:
                            No commit data
                        % endif
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


class EmailSettingsSchema(colander.Schema):
    @colander.instantiate(validator=colander.Length(min=1))
    class recipients(colander.SequenceSchema):
        title = _('Recipients')
        description = _('Email addresses to send push events to')
        widget = deform.widget.SequenceWidget(min_len=1)

        recipient = colander.SchemaNode(
            colander.String(),
            title=_('Email address'),
            description=_('Email address'),
            default='',
            validator=colander.Email(),
            widget=deform.widget.TextInputWidget(
                placeholder='user@domain.com',
            ),
        )


class EmailIntegrationType(IntegrationTypeBase):
    key = 'email'
    display_name = _('Email')
    description = _('Send repo push summaries to a list of recipients via email')

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
   xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape"
   viewBox="0 -256 1850 1850"
   id="svg2989"
   version="1.1"
   inkscape:version="0.48.3.1 r9886"
   width="100%"
   height="100%"
   sodipodi:docname="envelope_font_awesome.svg">
  <metadata
     id="metadata2999">
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
     id="defs2997" />
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
     id="namedview2995"
     showgrid="false"
     inkscape:zoom="0.13169643"
     inkscape:cx="896"
     inkscape:cy="896"
     inkscape:window-x="0"
     inkscape:window-y="25"
     inkscape:window-maximized="0"
     inkscape:current-layer="svg2989" />
  <g
     transform="matrix(1,0,0,-1,37.966102,1282.678)"
     id="g2991">
    <path
       d="m 1664,32 v 768 q -32,-36 -69,-66 -268,-206 -426,-338 -51,-43 -83,-67 -32,-24 -86.5,-48.5 Q 945,256 897,256 h -1 -1 Q 847,256 792.5,280.5 738,305 706,329 674,353 623,396 465,528 197,734 160,764 128,800 V 32 Q 128,19 137.5,9.5 147,0 160,0 h 1472 q 13,0 22.5,9.5 9.5,9.5 9.5,22.5 z m 0,1051 v 11 13.5 q 0,0 -0.5,13 -0.5,13 -3,12.5 -2.5,-0.5 -5.5,9 -3,9.5 -9,7.5 -6,-2 -14,2.5 H 160 q -13,0 -22.5,-9.5 Q 128,1133 128,1120 128,952 275,836 468,684 676,519 682,514 711,489.5 740,465 757,452 774,439 801.5,420.5 829,402 852,393 q 23,-9 43,-9 h 1 1 q 20,0 43,9 23,9 50.5,27.5 27.5,18.5 44.5,31.5 17,13 46,37.5 29,24.5 35,29.5 208,165 401,317 54,43 100.5,115.5 46.5,72.5 46.5,131.5 z m 128,37 V 32 q 0,-66 -47,-113 -47,-47 -113,-47 H 160 Q 94,-128 47,-81 0,-34 0,32 v 1088 q 0,66 47,113 47,47 113,47 h 1472 q 66,0 113,-47 47,-47 47,-113 z"
       id="path2993"
       inkscape:connector-curvature="0"
       style="fill:currentColor" />
  </g>
</svg>
'''

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

    if commit_num == 1:
        if data['push']['branches']:
            _subject = '[{repo_name}] {author} pushed {commit_num} commit on branches: {branches}'
        else:
            _subject = '[{repo_name}] {author} pushed {commit_num} commit'
        subject = _subject.format(
            author=data['actor']['username'],
            repo_name=data['repo']['repo_name'],
            commit_num=commit_num,
            branches=', '.join(
                branch['name'] for branch in data['push']['branches'])
        )
    else:
        if data['push']['branches']:
            _subject = '[{repo_name}] {author} pushed {commit_num} commits on branches: {branches}'
        else:
            _subject = '[{repo_name}] {author} pushed {commit_num} commits'
        subject = _subject.format(
            author=data['actor']['username'],
            repo_name=data['repo']['repo_name'],
            commit_num=commit_num,
            branches=', '.join(
                branch['name'] for branch in data['push']['branches']))

    email_body_plaintext = render_with_traceback(
        repo_push_template_plaintext,
        data=data,
        subject=subject,
        instance_url=server_url)

    email_body_html = render_with_traceback(
        repo_push_template_html,
        data=data,
        subject=subject,
        instance_url=server_url)

    for email_address in settings['recipients']:
        run_task(
            tasks.send_email, email_address, subject,
            email_body_plaintext, email_body_html)
