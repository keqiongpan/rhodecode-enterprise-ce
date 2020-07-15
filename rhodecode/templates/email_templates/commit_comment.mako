## -*- coding: utf-8 -*-
<%inherit file="base.mako"/>
<%namespace name="base" file="base.mako"/>

## EMAIL SUBJECT
<%def name="subject()" filter="n,trim,whitespace_filter">
<%
data = {
    'user': '@'+h.person(user),
    'repo_name': repo_name,
    'status': status_change,
    'comment_file': comment_file,
    'comment_line': comment_line,
    'comment_type': comment_type,
    'comment_id': comment_id,

    'commit_id': h.show_id(commit),
    'mention_prefix': '[mention] ' if mention else '',
}
%>


% if comment_file:
    ${_('{mention_prefix}{user} left a {comment_type} on file `{comment_file}` in commit `{commit_id}`').format(**data)} ${_('in the `{repo_name}` repository').format(**data) |n}
% else:
    % if status_change:
    ${_('{mention_prefix}[status: {status}] {user} left a {comment_type} on commit `{commit_id}`').format(**data) |n} ${_('in the `{repo_name}` repository').format(**data) |n}
    % else:
    ${_('{mention_prefix}{user} left a {comment_type} on commit `{commit_id}`').format(**data) |n} ${_('in the `{repo_name}` repository').format(**data) |n}
    % endif
% endif

</%def>

## PLAINTEXT VERSION OF BODY
<%def name="body_plaintext()" filter="n,trim">
<%
data = {
    'user': h.person(user),
    'repo_name': repo_name,
    'status': status_change,
    'comment_file': comment_file,
    'comment_line': comment_line,
    'comment_type': comment_type,
    'comment_id': comment_id,

    'commit_id': h.show_id(commit),
}
%>

* ${_('Comment link')}: ${commit_comment_url}

%if status_change:
* ${_('Commit status')}: ${_('Status was changed to')}: *${status_change}*

%endif
* ${_('Commit')}: ${h.show_id(commit)}

* ${_('Commit message')}: ${commit.message}

%if comment_file:
* ${_('File: {comment_file} on line {comment_line}').format(**data)}

%endif
% if comment_type == 'todo':
${('Inline' if comment_file else 'General')} ${_('`TODO` number')} ${comment_id}:
% else:
${('Inline' if comment_file else 'General')} ${_('`Note` number')} ${comment_id}:
% endif

${comment_body |n, trim}

---
${self.plaintext_footer()}
</%def>


<%
data = {
    'user': h.person(user),
    'comment_file': comment_file,
    'comment_line': comment_line,
    'comment_type': comment_type,
    'comment_id': comment_id,
    'renderer_type': renderer_type or 'plain',

    'repo': commit_target_repo_url,
    'repo_name': repo_name,
    'commit_id': h.show_id(commit),
}
%>

## header
<table style="text-align:left;vertical-align:middle;width: 100%">
    <tr>
    <td style="width:100%;border-bottom:1px solid #dbd9da;">

        <div style="margin: 0; font-weight: bold">
            <div class="clear-both" style="margin-bottom: 4px">
                <span style="color:#7E7F7F">@${h.person(user.username)}</span>
                ${_('left a')}
                <a href="${commit_comment_url}" style="${base.link_css()}">
                    % if comment_file:
                        ${_('{comment_type} on file `{comment_file}` in commit.').format(**data)}
                    % else:
                        ${_('{comment_type} on commit.').format(**data) |n}
                    % endif
                </a>
            </div>
            <div style="margin-top: 10px"></div>
            ${_('Commit')} <code>${data['commit_id']}</code> ${_('of repository')}: ${data['repo_name']}
        </div>

    </td>
    </tr>

</table>
<div class="clear-both"></div>
## main body
<table style="text-align:left;vertical-align:middle;width: 100%">

    ## spacing def
    <tr>
        <td style="width: 130px"></td>
        <td></td>
    </tr>

    % if status_change:
        <tr>
            <td style="padding-right:20px;">${_('Commit Status')}:</td>
            <td>
                ${_('Status was changed to')}: ${base.status_text(status_change, tag_type=status_change_type)}
            </td>
        </tr>
    % endif

    <tr>
        <td style="padding-right:20px;">${_('Commit')}:</td>
        <td>
            <a href="${commit_comment_url}" style="${base.link_css()}">${h.show_id(commit)}</a>
        </td>
    </tr>
    <tr>
        <td style="padding-right:20px;">${_('Commit message')}:</td>
        <td style="white-space:pre-wrap">${h.urlify_commit_message(commit.message, repo_name)}</td>
    </tr>

    % if comment_file:
        <tr>
            <td style="padding-right:20px;">${_('File')}:</td>
            <td><a href="${commit_comment_url}" style="${base.link_css()}">${_('`{comment_file}` on line {comment_line}').format(**data)}</a></td>
        </tr>
    % endif

    <tr style="border-bottom:1px solid #dbd9da;">
        <td colspan="2" style="padding-right:20px;">
            % if comment_type == 'todo':
                ${('Inline' if comment_file else 'General')} ${_('`TODO` number')} ${comment_id}:
            % else:
                ${('Inline' if comment_file else 'General')} ${_('`Note` number')} ${comment_id}:
            % endif
        </td>
    </tr>

    <tr>
        <td colspan="2" style="background: #F7F7F7">${h.render(comment_body, renderer=data['renderer_type'], mentions=True)}</td>
    </tr>

    <tr>
        <td><a href="${commit_comment_reply_url}">${_('Reply')}</a></td>
        <td></td>
    </tr>
</table>
