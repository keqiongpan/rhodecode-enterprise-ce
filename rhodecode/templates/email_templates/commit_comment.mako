## -*- coding: utf-8 -*-
<%inherit file="base.mako"/>


<%def name="subject()" filter="n,trim">
<%
data = {
    'user': h.person(user),
    'repo_name': repo_name,
    'commit_id': h.show_id(commit),
    'status': status_change,
    'comment_file': comment_file,
    'comment_line': comment_line,
}
%>
${_('[mention]') if mention else ''} \

% if comment_file:
    ${_('%(user)s commented on commit `%(commit_id)s` (file: `%(comment_file)s`)') % data} ${_('in the %(repo_name)s repository') % data |n}
% else:
    % if status_change:
    ${_('%(user)s commented on commit `%(commit_id)s` (status: %(status)s)') % data |n} ${_('in the %(repo_name)s repository') % data |n}
    % else:
    ${_('%(user)s commented on commit `%(commit_id)s`') % data |n} ${_('in the %(repo_name)s repository') % data |n}
    % endif
% endif

</%def>

<%def name="body_plaintext()" filter="n,trim">
<%
data = {
    'user': h.person(user),
    'repo_name': repo_name,
    'commit_id': h.show_id(commit),
    'status': status_change,
    'comment_file': comment_file,
    'comment_line': comment_line,
}
%>
${self.subject()}

* ${_('Comment link')}: ${commit_comment_url}

* ${_('Commit')}: ${h.show_id(commit)}

%if comment_file:
* ${_('File: %(comment_file)s on line %(comment_line)s') % {'comment_file': comment_file, 'comment_line': comment_line}}
%endif

---

%if status_change:
    ${_('Commit status was changed to')}: *${status_change}*
%endif

${comment_body|n}

${self.plaintext_footer()}
</%def>


<%
data = {
    'user': h.person(user),
    'comment_file': comment_file,
    'comment_line': comment_line,
    'repo': commit_target_repo,
    'repo_name': repo_name,
    'commit_id': h.show_id(commit),
}
%>
<table style="text-align:left;vertical-align:middle;">
    <tr><td colspan="2" style="width:100%;padding-bottom:15px;border-bottom:1px solid #dbd9da;">
    % if comment_file:
        <h4><a href="${commit_comment_url}" style="color:#427cc9;text-decoration:none;cursor:pointer">${_('%(user)s commented on commit `%(commit_id)s` (file:`%(comment_file)s`)') % data}</a> ${_('in the %(repo)s repository') % data |n}</h4>
    % else:
        <h4><a href="${commit_comment_url}" style="color:#427cc9;text-decoration:none;cursor:pointer">${_('%(user)s commented on commit `%(commit_id)s`') % data |n}</a> ${_('in the %(repo)s repository') % data |n}</h4>
    % endif
    </td></tr>
    <tr><td style="padding-right:20px;padding-top:15px;">${_('Commit')}</td><td style="padding-top:15px;"><a href="${commit_comment_url}" style="color:#427cc9;text-decoration:none;cursor:pointer">${h.show_id(commit)}</a></td></tr>
    <tr><td style="padding-right:20px;">${_('Description')}</td><td>${h.urlify_commit_message(commit.message, repo_name)}</td></tr>

    % if status_change:
        <tr><td style="padding-right:20px;">${_('Status')}</td><td>${_('The commit status was changed to')}: ${status_change}.</td></tr>
    % endif
    <tr><td style="padding-right:20px;">${(_('Comment on line: %(comment_line)s') if comment_file else _('Comment')) % data}</td><td style="line-height:1.2em;">${h.render(comment_body, renderer=renderer_type, mentions=True)}</td></tr>
</table>
