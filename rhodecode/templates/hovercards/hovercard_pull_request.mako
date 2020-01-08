<%namespace name="base" file="/base/base.mako"/>
<%namespace name="dt" file="/data_table/_dt_elements.mako"/>

% if c.can_view_pr:
<div class="pr-hovercard-header">
    <div class="pull-left tagtag">
        ${c.pull_request.status}
    </div>
    <div class="pr-hovercard-user">
        ${_('Created')}: ${h.format_date(c.pull_request.created_on)}
    </div>
</div>

<div class="pr-hovercard-title">
    <h3><a href="${h.route_path('pull_requests_global', pull_request_id=c.pull_request.pull_request_id)}">!${c.pull_request.pull_request_id}</a> - ${c.pull_request.title}</h3>
</div>

<div class="pr-hovercard-footer">
    ${_('repo')}: ${c.pull_request.target_repo.repo_name}
</div>
% else:
## user cannot view this PR we just show the generic info, without any exposed data
<div class="pr-hovercard-title">
    <h3>${_('Pull Request')} !${c.pull_request.pull_request_id}</h3>
</div>
% endif