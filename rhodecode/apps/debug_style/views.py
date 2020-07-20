# -*- coding: utf-8 -*-

# Copyright (C) 2016-2020 RhodeCode GmbH
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

import os
import logging
import datetime

from pyramid.view import view_config
from pyramid.renderers import render_to_response
from rhodecode.apps._base import BaseAppView
from rhodecode.lib.celerylib import run_task, tasks
from rhodecode.lib.utils2 import AttributeDict
from rhodecode.model.db import User
from rhodecode.model.notification import EmailNotificationModel

log = logging.getLogger(__name__)


class DebugStyleView(BaseAppView):
    def load_default_context(self):
        c = self._get_local_tmpl_context()

        return c

    @view_config(
        route_name='debug_style_home', request_method='GET',
        renderer=None)
    def index(self):
        c = self.load_default_context()
        c.active = 'index'

        return render_to_response(
            'debug_style/index.html', self._get_template_context(c),
            request=self.request)

    @view_config(
        route_name='debug_style_email', request_method='GET',
        renderer=None)
    @view_config(
        route_name='debug_style_email_plain_rendered', request_method='GET',
        renderer=None)
    def render_email(self):
        c = self.load_default_context()
        email_id = self.request.matchdict['email_id']
        c.active = 'emails'

        pr = AttributeDict(
            pull_request_id=123,
            title='digital_ocean: fix redis, elastic search start on boot, '
                  'fix fd limits on supervisor, set postgres 11 version',
            description='''
Check if we should use full-topic or mini-topic.

- full topic produces some problems with merge states etc
- server-mini-topic needs probably tweeks.            
            ''',
            repo_name='foobar',
            source_ref_parts=AttributeDict(type='branch', name='fix-ticket-2000'),
            target_ref_parts=AttributeDict(type='branch', name='master'),
        )
        target_repo = AttributeDict(repo_name='repo_group/target_repo')
        source_repo = AttributeDict(repo_name='repo_group/source_repo')
        user = User.get_by_username(self.request.GET.get('user')) or self._rhodecode_db_user
        # file/commit changes for PR update
        commit_changes = AttributeDict({
            'added': ['aaaaaaabbbbb', 'cccccccddddddd'],
            'removed': ['eeeeeeeeeee'],
        })
        file_changes = AttributeDict({
            'added': ['a/file1.md', 'file2.py'],
            'modified': ['b/modified_file.rst'],
            'removed': ['.idea'],
        })

        exc_traceback = {
            'exc_utc_date': '2020-03-26T12:54:50.683281',
            'exc_id': 139638856342656,
            'exc_timestamp': '1585227290.683288',
            'version': 'v1',
            'exc_message': 'Traceback (most recent call last):\n  File "/nix/store/s43k2r9rysfbzmsjdqnxgzvvb7zjhkxb-python2.7-pyramid-1.10.4/lib/python2.7/site-packages/pyramid/tweens.py", line 41, in excview_tween\n    response = handler(request)\n  File "/nix/store/s43k2r9rysfbzmsjdqnxgzvvb7zjhkxb-python2.7-pyramid-1.10.4/lib/python2.7/site-packages/pyramid/router.py", line 148, in handle_request\n    registry, request, context, context_iface, view_name\n  File "/nix/store/s43k2r9rysfbzmsjdqnxgzvvb7zjhkxb-python2.7-pyramid-1.10.4/lib/python2.7/site-packages/pyramid/view.py", line 667, in _call_view\n    response = view_callable(context, request)\n  File "/nix/store/s43k2r9rysfbzmsjdqnxgzvvb7zjhkxb-python2.7-pyramid-1.10.4/lib/python2.7/site-packages/pyramid/config/views.py", line 188, in attr_view\n    return view(context, request)\n  File "/nix/store/s43k2r9rysfbzmsjdqnxgzvvb7zjhkxb-python2.7-pyramid-1.10.4/lib/python2.7/site-packages/pyramid/config/views.py", line 214, in predicate_wrapper\n    return view(context, request)\n  File "/nix/store/s43k2r9rysfbzmsjdqnxgzvvb7zjhkxb-python2.7-pyramid-1.10.4/lib/python2.7/site-packages/pyramid/viewderivers.py", line 401, in viewresult_to_response\n    result = view(context, request)\n  File "/nix/store/s43k2r9rysfbzmsjdqnxgzvvb7zjhkxb-python2.7-pyramid-1.10.4/lib/python2.7/site-packages/pyramid/viewderivers.py", line 132, in _class_view\n    response = getattr(inst, attr)()\n  File "/mnt/hgfs/marcink/workspace/rhodecode-enterprise-ce/rhodecode/apps/debug_style/views.py", line 355, in render_email\n    template_type, **email_kwargs.get(email_id, {}))\n  File "/mnt/hgfs/marcink/workspace/rhodecode-enterprise-ce/rhodecode/model/notification.py", line 402, in render_email\n    body = email_template.render(None, **_kwargs)\n  File "/mnt/hgfs/marcink/workspace/rhodecode-enterprise-ce/rhodecode/lib/partial_renderer.py", line 95, in render\n    return self._render_with_exc(tmpl, args, kwargs)\n  File "/mnt/hgfs/marcink/workspace/rhodecode-enterprise-ce/rhodecode/lib/partial_renderer.py", line 79, in _render_with_exc\n    return render_func.render(*args, **kwargs)\n  File "/nix/store/dakh34sxz4yfr435c0cwjz0sd6hnd5g3-python2.7-mako-1.1.0/lib/python2.7/site-packages/mako/template.py", line 476, in render\n    return runtime._render(self, self.callable_, args, data)\n  File "/nix/store/dakh34sxz4yfr435c0cwjz0sd6hnd5g3-python2.7-mako-1.1.0/lib/python2.7/site-packages/mako/runtime.py", line 883, in _render\n    **_kwargs_for_callable(callable_, data)\n  File "/nix/store/dakh34sxz4yfr435c0cwjz0sd6hnd5g3-python2.7-mako-1.1.0/lib/python2.7/site-packages/mako/runtime.py", line 920, in _render_context\n    _exec_template(inherit, lclcontext, args=args, kwargs=kwargs)\n  File "/nix/store/dakh34sxz4yfr435c0cwjz0sd6hnd5g3-python2.7-mako-1.1.0/lib/python2.7/site-packages/mako/runtime.py", line 947, in _exec_template\n    callable_(context, *args, **kwargs)\n  File "rhodecode_templates_email_templates_base_mako", line 63, in render_body\n  File "rhodecode_templates_email_templates_exception_tracker_mako", line 43, in render_body\nAttributeError: \'str\' object has no attribute \'get\'\n',
            'exc_type': 'AttributeError'
        }
        email_kwargs = {
            'test': {},
            'message': {
                'body': 'message body !'
            },
            'email_test': {
                'user': user,
                'date': datetime.datetime.now(),
            },
            'exception': {
                'email_prefix': '[RHODECODE ERROR]',
                'exc_id': exc_traceback['exc_id'],
                'exc_url': 'http://server-url/{}'.format(exc_traceback['exc_id']),
                'exc_type_name': 'NameError',
                'exc_traceback': exc_traceback,
            },
            'password_reset': {
                'password_reset_url': 'http://example.com/reset-rhodecode-password/token',

                'user': user,
                'date': datetime.datetime.now(),
                'email': 'test@rhodecode.com',
                'first_admin_email': User.get_first_super_admin().email
            },
            'password_reset_confirmation': {
                'new_password': 'new-password-example',
                'user': user,
                'date': datetime.datetime.now(),
                'email': 'test@rhodecode.com',
                'first_admin_email': User.get_first_super_admin().email
            },
            'registration': {
                'user': user,
                'date': datetime.datetime.now(),
            },

            'pull_request_comment': {
                'user': user,

                'status_change': None,
                'status_change_type': None,

                'pull_request': pr,
                'pull_request_commits': [],

                'pull_request_target_repo': target_repo,
                'pull_request_target_repo_url': 'http://target-repo/url',

                'pull_request_source_repo': source_repo,
                'pull_request_source_repo_url': 'http://source-repo/url',

                'pull_request_url': 'http://localhost/pr1',
                'pr_comment_url': 'http://comment-url',
                'pr_comment_reply_url': 'http://comment-url#reply',

                'comment_file': None,
                'comment_line': None,
                'comment_type': 'note',
                'comment_body': 'This is my comment body. *I like !*',
                'comment_id': 2048,
                'renderer_type': 'markdown',
                'mention': True,

            },
            'pull_request_comment+status': {
                'user': user,

                'status_change': 'approved',
                'status_change_type': 'approved',

                'pull_request': pr,
                'pull_request_commits': [],

                'pull_request_target_repo': target_repo,
                'pull_request_target_repo_url': 'http://target-repo/url',

                'pull_request_source_repo': source_repo,
                'pull_request_source_repo_url': 'http://source-repo/url',

                'pull_request_url': 'http://localhost/pr1',
                'pr_comment_url': 'http://comment-url',
                'pr_comment_reply_url': 'http://comment-url#reply',

                'comment_type': 'todo',
                'comment_file': None,
                'comment_line': None,
                'comment_body': '''
I think something like this would be better

```py
// markdown renderer

def db():
   global connection
   return connection

```
                
                ''',
                'comment_id': 2048,
                'renderer_type': 'markdown',
                'mention': True,

            },
            'pull_request_comment+file': {
                'user': user,

                'status_change': None,
                'status_change_type': None,

                'pull_request': pr,
                'pull_request_commits': [],

                'pull_request_target_repo': target_repo,
                'pull_request_target_repo_url': 'http://target-repo/url',

                'pull_request_source_repo': source_repo,
                'pull_request_source_repo_url': 'http://source-repo/url',

                'pull_request_url': 'http://localhost/pr1',

                'pr_comment_url': 'http://comment-url',
                'pr_comment_reply_url': 'http://comment-url#reply',

                'comment_file': 'rhodecode/model/get_flow_commits',
                'comment_line': 'o1210',
                'comment_type': 'todo',
                'comment_body': '''
I like this !

But please check this code

.. code-block:: javascript

  // THIS IS RST CODE

  this.createResolutionComment = function(commentId) {
    // hide the trigger text
    $('#resolve-comment-{0}'.format(commentId)).hide();

    var comment = $('#comment-'+commentId);
    var commentData = comment.data();
    if (commentData.commentInline) {
        this.createComment(comment, commentId)
    } else {
        Rhodecode.comments.createGeneralComment('general', "$placeholder", commentId)
    }

    return false;
  };

This should work better !
                ''',
                'comment_id': 2048,
                'renderer_type': 'rst',
                'mention': True,

            },

            'pull_request_update': {
                'updating_user': user,

                'status_change': None,
                'status_change_type': None,

                'pull_request': pr,
                'pull_request_commits': [],

                'pull_request_target_repo': target_repo,
                'pull_request_target_repo_url': 'http://target-repo/url',

                'pull_request_source_repo': source_repo,
                'pull_request_source_repo_url': 'http://source-repo/url',

                'pull_request_url': 'http://localhost/pr1',

                # update comment links
                'pr_comment_url': 'http://comment-url',
                'pr_comment_reply_url': 'http://comment-url#reply',
                'ancestor_commit_id': 'f39bd443',
                'added_commits': commit_changes.added,
                'removed_commits': commit_changes.removed,
                'changed_files': (file_changes.added + file_changes.modified + file_changes.removed),
                'added_files': file_changes.added,
                'modified_files': file_changes.modified,
                'removed_files': file_changes.removed,
            },

            'cs_comment': {
                'user': user,
                'commit': AttributeDict(idx=123, raw_id='a'*40, message='Commit message'),
                'status_change': None,
                'status_change_type': None,

                'commit_target_repo_url': 'http://foo.example.com/#comment1',
                'repo_name': 'test-repo',
                'comment_type': 'note',
                'comment_file': None,
                'comment_line': None,
                'commit_comment_url': 'http://comment-url',
                'commit_comment_reply_url': 'http://comment-url#reply',
                'comment_body': 'This is my comment body. *I like !*',
                'comment_id': 2048,
                'renderer_type': 'markdown',
                'mention': True,
            },
            'cs_comment+status': {
                'user': user,
                'commit': AttributeDict(idx=123, raw_id='a' * 40, message='Commit message'),
                'status_change': 'approved',
                'status_change_type': 'approved',

                'commit_target_repo_url': 'http://foo.example.com/#comment1',
                'repo_name': 'test-repo',
                'comment_type': 'note',
                'comment_file': None,
                'comment_line': None,
                'commit_comment_url': 'http://comment-url',
                'commit_comment_reply_url': 'http://comment-url#reply',
                'comment_body': '''
Hello **world**

This is a multiline comment :)

- list
- list2
                ''',
                'comment_id': 2048,
                'renderer_type': 'markdown',
                'mention': True,
            },
            'cs_comment+file': {
                'user': user,
                'commit': AttributeDict(idx=123, raw_id='a' * 40, message='Commit message'),
                'status_change': None,
                'status_change_type': None,

                'commit_target_repo_url': 'http://foo.example.com/#comment1',
                'repo_name': 'test-repo',

                'comment_type': 'note',
                'comment_file': 'test-file.py',
                'comment_line': 'n100',

                'commit_comment_url': 'http://comment-url',
                'commit_comment_reply_url': 'http://comment-url#reply',
                'comment_body': 'This is my comment body. *I like !*',
                'comment_id': 2048,
                'renderer_type': 'markdown',
                'mention': True,
            },
            
            'pull_request': {
                'user': user,
                'pull_request': pr,
                'pull_request_commits': [
                    ('472d1df03bf7206e278fcedc6ac92b46b01c4e21', '''\
my-account: moved email closer to profile as it's similar data just moved outside.                    
                    '''),
                    ('cbfa3061b6de2696c7161ed15ba5c6a0045f90a7', '''\
users: description edit fixes

- tests
- added metatags info                    
                    '''),
                ],

                'pull_request_target_repo': target_repo,
                'pull_request_target_repo_url': 'http://target-repo/url',

                'pull_request_source_repo': source_repo,
                'pull_request_source_repo_url': 'http://source-repo/url',

                'pull_request_url': 'http://code.rhodecode.com/_pull-request/123',
            }

        }

        template_type = email_id.split('+')[0]
        (c.subject, c.email_body, c.email_body_plaintext) = EmailNotificationModel().render_email(
            template_type, **email_kwargs.get(email_id, {}))

        test_email = self.request.GET.get('email')
        if test_email:
            recipients = [test_email]
            run_task(tasks.send_email, recipients, c.subject,
                     c.email_body_plaintext, c.email_body)

        if self.request.matched_route.name == 'debug_style_email_plain_rendered':
            template = 'debug_style/email_plain_rendered.mako'
        else:
            template = 'debug_style/email.mako'
        return render_to_response(
            template, self._get_template_context(c),
            request=self.request)

    @view_config(
        route_name='debug_style_template', request_method='GET',
        renderer=None)
    def template(self):
        t_path = self.request.matchdict['t_path']
        c = self.load_default_context()
        c.active = os.path.splitext(t_path)[0]
        c.came_from = ''
        c.email_types = {
            'cs_comment+file': {},
            'cs_comment+status': {},

            'pull_request_comment+file': {},
            'pull_request_comment+status': {},

            'pull_request_update': {},
        }
        c.email_types.update(EmailNotificationModel.email_types)

        return render_to_response(
            'debug_style/' + t_path, self._get_template_context(c),
            request=self.request)

