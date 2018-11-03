## -*- coding: utf-8 -*-
<%inherit file="base.mako"/>
<%namespace name="base" file="base.mako"/>

## EMAIL SUBJECT
<%def name="subject()" filter="n,trim,whitespace_filter">
<%
data = {
    'user': h.person(user),
    'repo_name': repo_name,
    'commit_id': h.show_id(commit),
    'status': status_change,
    'comment_file': comment_file,
    'comment_line': comment_line,
    'comment_type': comment_type,
}
%>
${_('[mention]') if mention else ''} \

% if comment_file:
    ${_('{user} left a {comment_type} on file `{comment_file}` in commit `{commit_id}`').format(**data)} ${_('in the {repo_name} repository').format(**data) |n}
% else:
    % if status_change:
    ${_('[status: {status}] {user} left a {comment_type} on commit `{commit_id}`').format(**data) |n} ${_('in the {repo_name} repository').format(**data) |n}
    % else:
    ${_('{user} left a {comment_type} on commit `{commit_id}`').format(**data) |n} ${_('in the {repo_name} repository').format(**data) |n}
    % endif
% endif

</%def>

## PLAINTEXT VERSION OF BODY
<%def name="body_plaintext()" filter="n,trim">
<%
data = {
    'user': h.person(user),
    'repo_name': repo_name,
    'commit_id': h.show_id(commit),
    'status': status_change,
    'comment_file': comment_file,
    'comment_line': comment_line,
    'comment_type': comment_type,
}
%>
${self.subject()}

* ${_('Comment link')}: ${commit_comment_url}

* ${_('Commit')}: ${h.show_id(commit)}

%if comment_file:
* ${_('File: {comment_file} on line {comment_line}').format(**data)}
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
    'repo': commit_target_repo,
    'repo_name': repo_name,
    'commit_id': h.show_id(commit),
    'comment_file': comment_file,
    'comment_line': comment_line,
    'comment_type': comment_type,
}
%>
<table style="text-align:left;vertical-align:middle;">
    <tr><td colspan="2" style="width:100%;padding-bottom:15px;border-bottom:1px solid #dbd9da;">

    % if comment_file:
        <h4><a href="${commit_comment_url}" style="color:#427cc9;text-decoration:none;cursor:pointer">${_('{user} left a {comment_type} on file `{comment_file}` in commit `{commit_id}`').format(**data)}</a> ${_('in the {repo} repository').format(**data) |n}</h4>
    % else:
        <h4><a href="${commit_comment_url}" style="color:#427cc9;text-decoration:none;cursor:pointer">${_('{user} left a {comment_type} on commit `{commit_id}`').format(**data) |n}</a> ${_('in the {repo} repository').format(**data) |n}</h4>
    % endif
    </td></tr>

    <tr><td style="padding-right:20px;padding-top:15px;">${_('Commit')}</td><td style="padding-top:15px;"><a href="${commit_comment_url}" style="color:#427cc9;text-decoration:none;cursor:pointer">${h.show_id(commit)}</a></td></tr>
    <tr><td style="padding-right:20px;">${_('Description')}</td><td style="white-space:pre-wrap">${h.urlify_commit_message(commit.message, repo_name)}</td></tr>

    % if status_change:
        <tr>
            <td style="padding-right:20px;">${_('Status')}</td>
            <td>
                ${_('The commit status was changed to')}: ${base.status_text(status_change, tag_type=status_change_type)}
            </td>
        </tr>
    % endif
    <tr>
        <td style="padding-right:20px;">
            % if comment_type == 'todo':
                ${(_('TODO comment on line: {comment_line}') if comment_file else _('TODO comment')).format(**data)}
            % else:
                ${(_('Note comment on line: {comment_line}') if comment_file else _('Note comment')).format(**data)}
            % endif
        </td>
        <td style="line-height:1.2em;white-space:pre-wrap">${h.render(comment_body, renderer=renderer_type, mentions=True)}</td></tr>
</table>
