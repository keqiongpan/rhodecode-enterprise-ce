
<div class="pull-request-wrap">

    % if c.pr_merge_possible:
        <h2 class="merge-status">
            <span class="merge-icon success"><i class="icon-ok"></i></span>
            ${_('This pull request can be merged automatically.')}
        </h2>
    % else:
        <h2 class="merge-status">
            <span class="merge-icon warning"><i class="icon-false"></i></span>
            ${_('Merge is not currently possible because of below failed checks.')}
        </h2>
    % endif

    % if c.pr_merge_errors.items():
    <ul>
        % for pr_check_key, pr_check_details in c.pr_merge_errors.items():
            <% pr_check_type = pr_check_details['error_type'] %>
            <li>
                <span class="merge-message ${pr_check_type}" data-role="merge-message">
                    - ${pr_check_details['message']}
                    % if pr_check_key == 'todo':
                        % for co in pr_check_details['details']:
                            <a class="permalink" href="#comment-${co.comment_id}" onclick="Rhodecode.comments.scrollToComment($('#comment-${co.comment_id}'), 0, ${h.json.dumps(co.outdated)})"> #${co.comment_id}</a>${'' if loop.last else ','}
                        % endfor
                    % endif
                </span>
            </li>
        % endfor
        <li>
            Try <a href="${h.current_route_path(request, force_refresh=1)}">forced recheck</a> of the merge workspace in case current status seems wrong.
        </li>
    </ul>
    % endif

    <div class="pull-request-merge-actions">
        % if c.allowed_to_merge:
          ## Merge info, show only if all errors are taken care of
          % if not c.pr_merge_errors and c.pr_merge_info:
              <div class="pull-request-merge-info">
                  <ul>
                    % for pr_merge_key, pr_merge_details in c.pr_merge_info.items():
                    <li>
                        - ${pr_merge_details['message']}
                    </li>
                    % endfor
                  </ul>
              </div>
          % endif

        <div>
          ${h.secure_form(h.route_path('pullrequest_merge', repo_name=c.repo_name, pull_request_id=c.pull_request.pull_request_id), id='merge_pull_request_form', request=request)}
          <% merge_disabled = ' disabled' if c.pr_merge_possible is False else '' %>

          % if c.allowed_to_close:
            ## close PR action, injected later next to COMMENT button
            % if c.pull_request_review_status == c.REVIEW_STATUS_APPROVED:
            <a id="close-pull-request-action" class="btn btn-approved-status" href="#close-as-approved" onclick="closePullRequest('${c.REVIEW_STATUS_APPROVED}'); return false;">
                ${_('Close with status {}').format(h.commit_status_lbl(c.REVIEW_STATUS_APPROVED))}
            </a>
            % else:
            <a id="close-pull-request-action" class="btn btn-rejected-status" href="#close-as-rejected" onclick="closePullRequest('${c.REVIEW_STATUS_REJECTED}'); return false;">
                ${_('Close with status {}').format(h.commit_status_lbl(c.REVIEW_STATUS_REJECTED))}
            </a>
            % endif
          % endif

          <input type="submit" id="merge_pull_request" value="${_('Merge and close Pull Request')}" class="btn${merge_disabled}"${merge_disabled}>
          ${h.end_form()}

          <div class="pull-request-merge-refresh">
              <a href="#refreshChecks" onclick="refreshMergeChecks(); return false;">${_('refresh checks')}</a>
          </div>

        </div>
        % elif c.rhodecode_user.username != h.DEFAULT_USER:
            <a class="btn" href="#" onclick="refreshMergeChecks(); return false;">${_('refresh checks')}</a>
            <input type="submit" value="${_('Merge and close Pull Request')}" class="btn disabled" disabled="disabled" title="${_('You are not allowed to merge this pull request.')}">
        % else:
          <input type="submit" value="${_('Login to Merge this Pull Request')}" class="btn disabled" disabled="disabled">
        % endif
    </div>

</div>
