## -*- coding: utf-8 -*-
<%inherit file="base.mako"/>
<%namespace name="base" file="base.mako"/>

## EMAIL SUBJECT
<%def name="subject()" filter="n,trim,whitespace_filter">
<%
data = {
    'updating_user': '@'+h.person(updating_user),
    'pr_id': pull_request.pull_request_id,
    'pr_title': pull_request.title_safe,
}

subject_template = email_pr_update_subject_template or _('{updating_user} updated pull request. !{pr_id}: "{pr_title}"')
%>

${subject_template.format(**data) |n}
</%def>

## PLAINTEXT VERSION OF BODY
<%def name="body_plaintext()" filter="n,trim">
<%
data = {
    'updating_user': h.person(updating_user),
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

* Changed commits:

 - Added: ${len(added_commits)}
 - Removed: ${len(removed_commits)}

* Changed files:

%if not changed_files:
 No file changes found
%else:
%for file_name in added_files:
 - A `${file_name}`
%endfor
%for file_name in modified_files:
 - M `${file_name}`
%endfor
%for file_name in removed_files:
 - R `${file_name}`
%endfor
%endif

---
${self.plaintext_footer()}
</%def>
<%
data = {
    'updating_user': h.person(updating_user),
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
            <div class="clear-both" style="margin-bottom: 4px">
                <span style="color:#7E7F7F">@${h.person(updating_user.username)}</span>
                ${_('updated')}
                <a href="${pull_request_url}" style="${base.link_css()}">
                ${_('pull request.').format(**data) }
                </a>
            </div>
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
        <td style="padding-right:20px;">${_('Changes')}:</td>
        <td>
            <strong>Changed commits:</strong>
            <ul class="changes-ul">
                <li>- Added: ${len(added_commits)}</li>
                <li>- Removed: ${len(removed_commits)}</li>
            </ul>

            <strong>Changed files:</strong>
            <ul class="changes-ul">

            %if not changed_files:
                <li>No file changes found</li>
            %else:
                %for file_name in added_files:
                 <li>- A <a href="${pull_request_url + '#a_' + h.FID(ancestor_commit_id, file_name)}">${file_name}</a></li>
                %endfor
                %for file_name in modified_files:
                 <li>-  M <a href="${pull_request_url + '#a_' + h.FID(ancestor_commit_id, file_name)}">${file_name}</a></li>
                %endfor
                %for file_name in removed_files:
                 <li>-  R <a href="${pull_request_url + '#a_' + h.FID(ancestor_commit_id, file_name)}">${file_name}</a></li>
                %endfor
            %endif

            </ul>
        </td>
    </tr>

</table>
