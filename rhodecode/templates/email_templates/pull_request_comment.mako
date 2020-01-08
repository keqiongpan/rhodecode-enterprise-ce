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

    'pr_title': pull_request.title,
    'pr_id': pull_request.pull_request_id,
}
%>


% if comment_file:
    ${(_('[mention]') if mention else '')} ${_('{user} left a {comment_type} on file `{comment_file}` in pull request !{pr_id}: "{pr_title}"').format(**data) |n}
% else:
    % if status_change:
    ${(_('[mention]') if mention else '')} ${_('[status: {status}] {user} left a {comment_type} on pull request !{pr_id}: "{pr_title}"').format(**data) |n}
    % else:
    ${(_('[mention]') if mention else '')} ${_('{user} left a {comment_type} on pull request !{pr_id}: "{pr_title}"').format(**data) |n}
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

    'pr_title': pull_request.title,
    'pr_id': pull_request.pull_request_id,
    'source_ref_type': pull_request.source_ref_parts.type,
    'source_ref_name': pull_request.source_ref_parts.name,
    'target_ref_type': pull_request.target_ref_parts.type,
    'target_ref_name': pull_request.target_ref_parts.name,
    'source_repo': pull_request_source_repo.repo_name,
    'target_repo': pull_request_target_repo.repo_name,
    'source_repo_url': pull_request_source_repo_url,
    'target_repo_url': pull_request_target_repo_url,
}
%>

* ${_('Comment link')}: ${pr_comment_url}

* ${_('Pull Request')}: !${pull_request.pull_request_id}

* ${h.literal(_('Commit flow: {source_ref_type}:{source_ref_name} of {source_repo_url} into {target_ref_type}:{target_ref_name} of {target_repo_url}').format(**data))}

%if status_change and not closing_pr:
* ${_('{user} submitted pull request !{pr_id} status: *{status}*').format(**data)}

%elif status_change and closing_pr:
* ${_('{user} submitted pull request !{pr_id} status: *{status} and closed*').format(**data)}

%endif
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

    'pr_title': pull_request.title,
    'pr_id': pull_request.pull_request_id,
    'status': status_change,
    'source_ref_type': pull_request.source_ref_parts.type,
    'source_ref_name': pull_request.source_ref_parts.name,
    'target_ref_type': pull_request.target_ref_parts.type,
    'target_ref_name': pull_request.target_ref_parts.name,
    'source_repo': pull_request_source_repo.repo_name,
    'target_repo': pull_request_target_repo.repo_name,
    'source_repo_url': h.link_to(pull_request_source_repo.repo_name, pull_request_source_repo_url),
    'target_repo_url': h.link_to(pull_request_target_repo.repo_name, pull_request_target_repo_url),
}
%>

<table style="text-align:left;vertical-align:middle;width: 100%">
    <tr>
    <td style="width:100%;border-bottom:1px solid #dbd9da;">

        <h4 style="margin: 0">
            <div style="margin-bottom: 4px">
                <span style="color:#7E7F7F">@${h.person(user.username)}</span>
                ${_('left a')}
                <a href="${pr_comment_url}" style="${base.link_css()}">
                    % if comment_file:
                        ${_('{comment_type} on file `{comment_file}` in pull request.').format(**data)}
                    % else:
                        ${_('{comment_type} on pull request.').format(**data) |n}
                    % endif
                </a>
            </div>
            <div style="margin-top: 10px"></div>
            ${_('Pull request')} <code>!${data['pr_id']}: ${data['pr_title']}</code>
        </h4>

    </td>
    </tr>

</table>

<table style="text-align:left;vertical-align:middle;width: 100%">

    ## spacing def
    <tr>
        <td style="width: 130px"></td>
        <td></td>
    </tr>

    % if status_change:
    <tr>
        <td style="padding-right:20px;">${_('Review Status')}:</td>
        <td>
            % if closing_pr:
               ${_('Closed pull request with status')}: ${base.status_text(status_change, tag_type=status_change_type)}
            % else:
               ${_('Submitted review status')}: ${base.status_text(status_change, tag_type=status_change_type)}
            % endif
        </td>
    </tr>
    % endif
    <tr>
        <td style="padding-right:20px;">${_('Pull request')}:</td>
        <td>
            <a href="${pull_request_url}" style="${base.link_css()}">
            !${pull_request.pull_request_id}
            </a>
        </td>
    </tr>

    <tr>
        <td style="padding-right:20px;line-height:20px;">${_('Commit Flow')}:</td>
        <td style="line-height:20px;">
            <code>${'{}:{}'.format(data['source_ref_type'], pull_request.source_ref_parts.name)}</code> ${_('of')} ${data['source_repo_url']}
            &rarr;
            <code>${'{}:{}'.format(data['target_ref_type'], pull_request.target_ref_parts.name)}</code> ${_('of')}  ${data['target_repo_url']}
        </td>
    </tr>

    % if comment_file:
        <tr>
            <td style="padding-right:20px;">${_('File')}:</td>
            <td><a href="${pr_comment_url}" style="${base.link_css()}">${_('`{comment_file}` on line {comment_line}').format(**data)}</a></td>
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
        <td><a href="${pr_comment_reply_url}">${_('Reply')}</a></td>
        <td></td>
    </tr>
</table>
