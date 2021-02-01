## -*- coding: utf-8 -*-
<%inherit file="base.mako"/>
<%namespace name="base" file="base.mako"/>

## EMAIL SUBJECT
<%def name="subject()" filter="n,trim,whitespace_filter">
<%
data = {
    'user': '@'+h.person(user),
    'pr_id': pull_request.pull_request_id,
    'pr_title': pull_request.title_safe,
}

if user_role == 'observer':
    subject_template = email_pr_review_subject_template or _('{user} added you as observer to pull request. !{pr_id}: "{pr_title}"')
else:
    subject_template = email_pr_review_subject_template or _('{user} requested a pull request review. !{pr_id}: "{pr_title}"')
%>

${subject_template.format(**data) |n}
</%def>

## PLAINTEXT VERSION OF BODY
<%def name="body_plaintext()" filter="n,trim">
<%
data = {
    'user': h.person(user),
    'pr_id': pull_request.pull_request_id,
    'pr_title': pull_request.title_safe,
    'source_ref_type': pull_request.source_ref_parts.type,
    'source_ref_name': pull_request.source_ref_parts.name,
    'target_ref_type': pull_request.target_ref_parts.type,
    'target_ref_name': pull_request.target_ref_parts.name,
    'repo_url': pull_request_source_repo_url,
    'source_repo': pull_request_source_repo.repo_name,
    'target_repo': pull_request_target_repo.repo_name,
    'source_repo_url': pull_request_source_repo_url,
    'target_repo_url': pull_request_target_repo_url,
}

%>

* ${_('Pull Request link')}: ${pull_request_url}

* ${h.literal(_('Commit flow: {source_ref_type}:{source_ref_name} of {source_repo_url} into {target_ref_type}:{target_ref_name} of {target_repo_url}').format(**data))}

* ${_('Title')}: ${pull_request.title}

* ${_('Description')}:

${pull_request.description | trim}


* ${_ungettext('Commit (%(num)s)', 'Commits (%(num)s)', len(pull_request_commits) ) % {'num': len(pull_request_commits)}}:

% for commit_id, message in pull_request_commits:
    - ${h.short_id(commit_id)}
    ${h.chop_at_smart(message.lstrip(), '\n', suffix_if_chopped='...')}

% endfor

---
${self.plaintext_footer()}
</%def>
<%
data = {
    'user': h.person(user),
    'pr_id': pull_request.pull_request_id,
    'pr_title': pull_request.title_safe,
    'source_ref_type': pull_request.source_ref_parts.type,
    'source_ref_name': pull_request.source_ref_parts.name,
    'target_ref_type': pull_request.target_ref_parts.type,
    'target_ref_name': pull_request.target_ref_parts.name,
    'repo_url': pull_request_source_repo_url,
    'source_repo': pull_request_source_repo.repo_name,
    'target_repo': pull_request_target_repo.repo_name,
    'source_repo_url': h.link_to(pull_request_source_repo.repo_name, pull_request_source_repo_url),
    'target_repo_url': h.link_to(pull_request_target_repo.repo_name, pull_request_target_repo_url),
}
%>
## header
<table style="text-align:left;vertical-align:middle;width: 100%">
    <tr>
    <td style="width:100%;border-bottom:1px solid #dbd9da;">
        <div style="margin: 0; font-weight: bold">
            % if user_role == 'observer':
            <div class="clear-both" class="clear-both" style="margin-bottom: 4px">
                <span style="color:#7E7F7F">@${h.person(user.username)}</span>
                ${_('added you as observer to')}
                <a href="${pull_request_url}" style="${base.link_css()}">pull request</a>.
            </div>
            % else:
            <div class="clear-both" class="clear-both" style="margin-bottom: 4px">
                <span style="color:#7E7F7F">@${h.person(user.username)}</span>
                ${_('requested a')}
                <a href="${pull_request_url}" style="${base.link_css()}">pull request</a> review.
            </div>
            % endif
            <div style="margin-top: 10px"></div>
            ${_('Pull request')} <code>!${data['pr_id']}: ${data['pr_title']}</code>
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

    <tr>
        <td style="padding-right:20px;">${_('Description')}:</td>
        <td style="white-space:pre-wrap"><code>${pull_request.description | trim}</code></td>
    </tr>
    <tr>
        <td style="padding-right:20px;">${_ungettext('Commit (%(num)s)', 'Commits (%(num)s)', len(pull_request_commits)) % {'num': len(pull_request_commits)}}:</td>
        <td></td>
    </tr>

    <tr>
        <td colspan="2">
            <ol style="margin:0 0 0 1em;padding:0;text-align:left;">
                % for commit_id, message in pull_request_commits:
                    <li style="margin:0 0 1em;">
                        <pre style="margin:0 0 .5em"><a href="${h.route_path('repo_commit', repo_name=pull_request_source_repo.repo_name, commit_id=commit_id)}" style="${base.link_css()}">${h.short_id(commit_id)}</a></pre>
                        ${h.chop_at_smart(message, '\n', suffix_if_chopped='...')}
                    </li>
                % endfor
            </ol>
        </td>
    </tr>
</table>
