## -*- coding: utf-8 -*-
<%inherit file="base.mako"/>


<%def name="subject()" filter="n,trim">
<%
data = {
    'user': h.person(user),
    'pr_title': pull_request.title,
    'pr_id': pull_request.pull_request_id,
    'status': status_change,
    'comment_file': comment_file,
    'comment_line': comment_line,
}
%>

${_('[mention]') if mention else ''} \

% if comment_file:
    ${_('%(user)s commented on pull request #%(pr_id)s "%(pr_title)s" (file: `%(comment_file)s`)') % data}
% else:
    % if status_change:
    ${_('%(user)s commented on pull request #%(pr_id)s "%(pr_title)s" (status: %(status)s)') % data}
    % else:
    ${_('%(user)s commented on pull request #%(pr_id)s "%(pr_title)s"') % data}
    % endif
% endif
</%def>

<%def name="body_plaintext()" filter="n,trim">
<%
data = {
    'user': h.person(user),
    'pr_title': pull_request.title,
    'pr_id': pull_request.pull_request_id,
    'status': status_change,
    'comment_file': comment_file,
    'comment_line': comment_line,
}
%>
${self.subject()}

* ${_('Comment link')}: ${pr_comment_url}

* ${_('Source repository')}: ${pr_source_repo_url}

%if comment_file:
* ${_('File: %(comment_file)s on line %(comment_line)s') % {'comment_file': comment_file, 'comment_line': comment_line}}
%endif

---

%if status_change and not closing_pr:
   ${_('%(user)s submitted pull request #%(pr_id)s status: *%(status)s*') % data}
%elif status_change and closing_pr:
   ${_('%(user)s submitted pull request #%(pr_id)s status: *%(status)s and closed*') % data}
%endif

${comment_body|n}

${self.plaintext_footer()}
</%def>


<%
data = {
    'user': h.person(user),
    'pr_title': pull_request.title,
    'pr_id': pull_request.pull_request_id,
    'status': status_change,
    'comment_file': comment_file,
    'comment_line': comment_line,
}
%>
<table style="text-align:left;vertical-align:middle;">
    <tr><td colspan="2" style="width:100%;padding-bottom:15px;border-bottom:1px solid #dbd9da;">
    <h4><a href="${pr_comment_url}" style="color:#427cc9;text-decoration:none;cursor:pointer">

    % if comment_file:
        ${_('%(user)s commented on pull request #%(pr_id)s "%(pr_title)s" (file:`%(comment_file)s`)') % data |n}
    % else:
        ${_('%(user)s commented on pull request #%(pr_id)s "%(pr_title)s"') % data |n}
    % endif
    </a>
    %if status_change and not closing_pr:
       , ${_('submitted pull request status: %(status)s') % data}
    %elif status_change and closing_pr:
       , ${_('submitted pull request status: %(status)s and closed') % data}
    %endif
    </h4>
    </td></tr>
    <tr><td style="padding-right:20px;padding-top:15px;">${_('Source')}</td><td style="padding-top:15px;"><a style="color:#427cc9;text-decoration:none;cursor:pointer" href="${pr_source_repo_url}">${pr_source_repo.repo_name}</a></td></tr>
    <tr><td style="padding-right:20px;">${(_('Comment on line: %(comment_line)s') if comment_file else _('Comment')) % data}</td><td style="line-height:1.2em;">${h.render(comment_body, renderer=renderer_type, mentions=True)}</td></tr>
</table>
