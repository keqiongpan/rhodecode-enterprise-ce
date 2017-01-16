
<div class="pull-request-wrap">

    <ul>
        % for pr_check_type, pr_check_msg in c.pr_merge_checks:
            <li>
                <span class="merge-message ${pr_check_type}" data-role="merge-message">
                    % if pr_check_type in ['success']:
                        <i class="icon-true"></i>
                    % else:
                        <i class="icon-false"></i>
                    % endif
                    ${pr_check_msg}
                </span>
            </li>
        % endfor
    </ul>

    <div class="pull-request-merge-actions">
        % if c.allowed_to_merge:
        <div class="pull-right">
          ${h.secure_form(url('pullrequest_merge', repo_name=c.repo_name, pull_request_id=c.pull_request.pull_request_id), id='merge_pull_request_form')}
          <% merge_disabled = ' disabled' if c.pr_merge_status is False else '' %>
          <a class="btn" href="#" onclick="refreshMergeChecks(); return false;">${_('refresh checks')}</a>
          <input type="submit" id="merge_pull_request" value="${_('Merge Pull Request')}" class="btn${merge_disabled}"${merge_disabled}>
          ${h.end_form()}
        </div>
        % elif c.rhodecode_user.username != h.DEFAULT_USER:
            <a class="btn" href="#" onclick="refreshMergeChecks(); return false;">${_('refresh checks')}</a>
            <input type="submit" value="${_('Merge Pull Request')}" class="btn disabled" disabled="disabled" title="${_('You are not allowed to merge this pull request.')}">
        % else:
          <input type="submit" value="${_('Login to Merge this Pull Request')}" class="btn disabled" disabled="disabled">
        % endif
    </div>

</div>

