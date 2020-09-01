<%inherit file="/base/base.mako"/>
<%namespace name="base" file="/base/base.mako"/>
<%namespace name="dt" file="/data_table/_dt_elements.mako"/>

<%def name="title()">
    ${_('{} Pull Request !{}').format(c.repo_name, c.pull_request.pull_request_id)}
    %if c.rhodecode_name:
        &middot; ${h.branding(c.rhodecode_name)}
    %endif
</%def>

<%def name="breadcrumbs_links()">

</%def>

<%def name="menu_bar_nav()">
    ${self.menu_items(active='repositories')}
</%def>

<%def name="menu_bar_subnav()">
    ${self.repo_menu(active='showpullrequest')}
</%def>

<%def name="comments_table(comments, counter_num, todo_comments=False)">
    <%
        old_comments = False
        if todo_comments:
            cls_ = 'todos-content-table'
            def sorter(entry):
                user_id = entry.author.user_id
                resolved = '1' if entry.resolved else '0'
                if user_id == c.rhodecode_user.user_id:
                    # own comments first
                    user_id = 0
                return '{}'.format(str(entry.comment_id).zfill(10000))
        else:
            cls_ = 'comments-content-table'
            def sorter(entry):
                user_id = entry.author.user_id
                return '{}'.format(str(entry.comment_id).zfill(10000))



    %>
    <table class="todo-table ${cls_}" data-total-count="${len(comments)}" data-counter="${counter_num}">

     % for loop_obj, comment_obj in h.looper(reversed(sorted(comments, key=sorter))):
         <%
            display = ''
            _cls = ''
         %>
         <% comment_ver_index = comment_obj.get_index_version(getattr(c, 'versions', [])) %>
         <%
             prev_comment_ver_index = 0
             if loop_obj.previous:
                prev_comment_ver_index = loop_obj.previous.get_index_version(getattr(c, 'versions', []))
         %>
         <% hidden_at_ver = comment_obj.outdated_at_version_js(c.at_version_num) %>
         <% is_from_old_ver = comment_obj.older_than_version_js(c.at_version_num) %>
         <%
         if (prev_comment_ver_index > comment_ver_index) and old_comments is False:
           old_comments = True
         %>
          % if todo_comments:
              % if comment_obj.resolved:
                  <% _cls = 'resolved-todo' %>
                  <% display = 'none' %>
              % endif
          % else:
              ## SKIP TODOs we display them in other area
              % if comment_obj.is_todo:
                  <% display = 'none' %>
              % endif
              ## Skip outdated comments
              % if comment_obj.outdated:
                  <% display = 'none' %>
                  <% _cls = 'hidden-comment' %>
              % endif
          % endif

          % if not todo_comments and old_comments:
          <tr class="old-comments-marker">
              <td colspan="3"> <code>comments from older versions</code> </td>
          </tr>
          ## reset markers so we only show this marker once
          <% old_comments = None %>
          % endif

          <tr class="${_cls}" style="display: ${display};">
              <td class="td-todo-number">

                  <a class="${('todo-resolved' if comment_obj.resolved else '')} permalink"
                     href="#comment-${comment_obj.comment_id}"
                     onclick="return Rhodecode.comments.scrollToComment($('#comment-${comment_obj.comment_id}'), 0, ${hidden_at_ver})">

                  % if todo_comments:
                    % if comment_obj.is_inline:
                      <i class="tooltip icon-code" title="Inline TODO comment ${('made in older version (v{})'.format(comment_ver_index) if is_from_old_ver == 'true' else 'made in this version')}."></i>
                    % else:
                      <i class="tooltip icon-comment" title="General TODO comment ${('made in older version (v{})'.format(comment_ver_index) if is_from_old_ver == 'true' else 'made in this version')}."></i>
                    % endif
                  % else:
                    % if comment_obj.outdated:
                      <i class="tooltip icon-comment-toggle" title="Inline Outdated made in v${comment_ver_index}."></i>
                    % elif comment_obj.is_inline:
                      <i class="tooltip icon-code" title="Inline comment ${('made in older version (v{})'.format(comment_ver_index) if is_from_old_ver == 'true' else 'made in this version')}."></i>
                    % else:
                      <i class="tooltip icon-comment" title="General comment ${('made in older version (v{})'.format(comment_ver_index) if is_from_old_ver == 'true' else 'made in this version')}."></i>
                    % endif
                  % endif

                  #${comment_obj.comment_id}
                  </a>
              </td>

              <td class="td-todo-gravatar">
                  ${base.gravatar(comment_obj.author.email, 16, user=comment_obj.author, tooltip=True, extra_class=['no-margin'])}
              </td>
              <td class="todo-comment-text-wrapper">
                  <div class="tooltip todo-comment-text timeago" title="${h.format_date(comment_obj.created_on)}" datetime="${comment_obj.created_on}${h.get_timezone(comment_obj.created_on, time_is_local=True)}">
                    <code>${h.chop_at_smart(comment_obj.text, '\n', suffix_if_chopped='...')}</code>
                  </div>
              </td>
          </tr>
     % endfor

    </table>

</%def>


<%def name="main()">
## Container to gather extracted Tickets
<%
    c.referenced_commit_issues = []
    c.referenced_desc_issues = []
%>

<script type="text/javascript">
    // TODO: marcink switch this to pyroutes
    AJAX_COMMENT_DELETE_URL = "${h.route_path('pullrequest_comment_delete',repo_name=c.repo_name,pull_request_id=c.pull_request.pull_request_id,comment_id='__COMMENT_ID__')}";
    templateContext.pull_request_data.pull_request_id = ${c.pull_request.pull_request_id};
</script>

<div class="box">

  <div class="box pr-summary">

    <div class="summary-details block-left">
        <div id="pr-title">
            % if c.pull_request.is_closed():
                <span class="pr-title-closed-tag tag">${_('Closed')}</span>
            % endif
            <input class="pr-title-input large disabled" disabled="disabled" name="pullrequest_title" type="text" value="${c.pull_request.title}">
        </div>
        <div id="pr-title-edit" class="input" style="display: none;">
            <input class="pr-title-input large" id="pr-title-input" name="pullrequest_title" type="text" value="${c.pull_request.title}">
        </div>

    <% summary = lambda n:{False:'summary-short'}.get(n) %>
    <div class="pr-details-title">
        <div class="pull-left">
            <a href="${h.route_path('pull_requests_global', pull_request_id=c.pull_request.pull_request_id)}">${_('Pull request !{}').format(c.pull_request.pull_request_id)}</a>
            ${_('Created on')}
            <span class="tooltip" title="${_('Last updated on')} ${h.format_date(c.pull_request.updated_on)}">${h.format_date(c.pull_request.created_on)},</span>
            <span class="pr-details-title-author-pref">${_('by')}</span>
        </div>

        <div class="pull-left">
            ${self.gravatar_with_user(c.pull_request.author.email, 16, tooltip=True)}
        </div>

        %if c.allowed_to_update:
          <div class="pull-right">
              <div id="edit_pull_request" class="action_button pr-save" style="display: none;">${_('Update title & description')}</div>
              <div id="delete_pullrequest" class="action_button pr-save ${('' if c.allowed_to_delete else 'disabled' )}" style="display: none;">
                  % if c.allowed_to_delete:
                      ${h.secure_form(h.route_path('pullrequest_delete', repo_name=c.pull_request.target_repo.repo_name, pull_request_id=c.pull_request.pull_request_id), request=request)}
                          <input class="btn btn-link btn-danger no-margin" id="remove_${c.pull_request.pull_request_id}" name="remove_${c.pull_request.pull_request_id}"
                                 onclick="submitConfirm(event, this, _gettext('Confirm to delete this pull request'), _gettext('Delete'), '${'!{}'.format(c.pull_request.pull_request_id)}')"
                                 type="submit" value="${_('Delete pull request')}">
                      ${h.end_form()}
                  % else:
                    <span class="tooltip" title="${_('Not allowed to delete this pull request')}">${_('Delete pull request')}</span>
                  % endif
              </div>
              <div id="open_edit_pullrequest" class="action_button">${_('Edit')}</div>
              <div id="close_edit_pullrequest" class="action_button" style="display: none;">${_('Cancel')}</div>
          </div>

        %endif
    </div>

    <div id="pr-desc" class="input" title="${_('Rendered using {} renderer').format(c.renderer)}">
        ${h.render(c.pull_request.description, renderer=c.renderer, repo_name=c.repo_name, issues_container=c.referenced_desc_issues)}
    </div>

    <div id="pr-desc-edit" class="input textarea" style="display: none;">
        <input id="pr-renderer-input" type="hidden" name="description_renderer" value="${c.visual.default_renderer}">
        ${dt.markup_form('pr-description-input', form_text=c.pull_request.description)}
    </div>

    <div id="summary" class="fields pr-details-content">

       ## source
       <div class="field">
        <div class="label-pr-detail">
            <label>${_('Commit flow')}:</label>
        </div>
        <div class="input">
            <div class="pr-commit-flow">
                ## Source
                %if c.pull_request.source_ref_parts.type == 'branch':
                    <a href="${h.route_path('repo_commits', repo_name=c.pull_request.source_repo.repo_name, _query=dict(branch=c.pull_request.source_ref_parts.name))}"><code class="pr-source-info">${c.pull_request.source_ref_parts.type}:${c.pull_request.source_ref_parts.name}</code></a>
                %else:
                    <code class="pr-source-info">${'{}:{}'.format(c.pull_request.source_ref_parts.type, c.pull_request.source_ref_parts.name)}</code>
                %endif
                ${_('of')} <a href="${h.route_path('repo_summary', repo_name=c.pull_request.source_repo.repo_name)}">${c.pull_request.source_repo.repo_name}</a>
                &rarr;
                ## Target
                %if c.pull_request.target_ref_parts.type == 'branch':
                    <a href="${h.route_path('repo_commits', repo_name=c.pull_request.target_repo.repo_name, _query=dict(branch=c.pull_request.target_ref_parts.name))}"><code class="pr-target-info">${c.pull_request.target_ref_parts.type}:${c.pull_request.target_ref_parts.name}</code></a>
                %else:
                    <code class="pr-target-info">${'{}:{}'.format(c.pull_request.target_ref_parts.type, c.pull_request.target_ref_parts.name)}</code>
                %endif

                ${_('of')} <a href="${h.route_path('repo_summary', repo_name=c.pull_request.target_repo.repo_name)}">${c.pull_request.target_repo.repo_name}</a>

                <a class="source-details-action" href="#expand-source-details" onclick="return versionController.toggleElement(this, '.source-details')" data-toggle-on='<i class="icon-angle-down">more details</i>' data-toggle-off='<i class="icon-angle-up">less details</i>'>
                    <i class="icon-angle-down">more details</i>
                </a>

            </div>

            <div class="source-details" style="display: none">

                <ul>

                    ## common ancestor
                    <li>
                        ${_('Common ancestor')}:
                        % if c.ancestor_commit:
                            <a href="${h.route_path('repo_commit', repo_name=c.target_repo.repo_name, commit_id=c.ancestor_commit.raw_id)}">${h.show_id(c.ancestor_commit)}</a>
                        % else:
                            ${_('not available')}
                        % endif
                    </li>

                    ## pull url
                    <li>
                        %if h.is_hg(c.pull_request.source_repo):
                            <% clone_url = 'hg pull -r {} {}'.format(h.short_id(c.source_ref), c.pull_request.source_repo.clone_url()) %>
                        %elif h.is_git(c.pull_request.source_repo):
                            <% clone_url = 'git pull {} {}'.format(c.pull_request.source_repo.clone_url(), c.pull_request.source_ref_parts.name) %>
                        %endif

                        <span>${_('Pull changes from source')}</span>: <input type="text" class="input-monospace pr-pullinfo" value="${clone_url}" readonly="readonly">
                        <i class="tooltip icon-clipboard clipboard-action pull-right pr-pullinfo-copy" data-clipboard-text="${clone_url}" title="${_('Copy the pull url')}"></i>
                    </li>

                    ## Shadow repo
                    <li>
                        % if not c.pull_request.is_closed() and c.pull_request.shadow_merge_ref:
                            %if h.is_hg(c.pull_request.target_repo):
                                <% clone_url = 'hg clone --update {} {} pull-request-{}'.format(c.pull_request.shadow_merge_ref.name, c.shadow_clone_url, c.pull_request.pull_request_id) %>
                            %elif h.is_git(c.pull_request.target_repo):
                                <% clone_url = 'git clone --branch {} {} pull-request-{}'.format(c.pull_request.shadow_merge_ref.name, c.shadow_clone_url, c.pull_request.pull_request_id) %>
                            %endif

                            <span class="tooltip" title="${_('Clone repository in its merged state using shadow repository')}">${_('Clone from shadow repository')}</span>: <input type="text" class="input-monospace pr-mergeinfo" value="${clone_url}" readonly="readonly">
                            <i class="tooltip icon-clipboard clipboard-action pull-right pr-mergeinfo-copy" data-clipboard-text="${clone_url}" title="${_('Copy the clone url')}"></i>

                        % else:
                            <div class="">
                                ${_('Shadow repository data not available')}.
                            </div>
                        % endif
                    </li>

                </ul>

            </div>

        </div>

       </div>

       ## versions
       <div class="field">
           <div class="label-pr-detail">
               <label>${_('Versions')}:</label>
           </div>

           <% outdated_comm_count_ver = len(c.inline_versions[None]['outdated']) %>
           <% general_outdated_comm_count_ver = len(c.comment_versions[None]['outdated']) %>

           <div class="pr-versions">
           % if c.show_version_changes:
               <% outdated_comm_count_ver = len(c.inline_versions[c.at_version_num]['outdated']) %>
               <% general_outdated_comm_count_ver = len(c.comment_versions[c.at_version_num]['outdated']) %>
               ${_ungettext('{} version available for this pull request, ', '{} versions available for this pull request, ', len(c.versions)).format(len(c.versions))}
               <a id="show-pr-versions" onclick="return versionController.toggleVersionView(this)" href="#show-pr-versions"
                    data-toggle-on="${_('show versions')}."
                    data-toggle-off="${_('hide versions')}.">
                    ${_('show versions')}.
               </a>
               <table>
                   ## SHOW ALL VERSIONS OF PR
                   <% ver_pr = None %>

                   % for data in reversed(list(enumerate(c.versions, 1))):
                       <% ver_pos = data[0] %>
                       <% ver = data[1] %>
                       <% ver_pr = ver.pull_request_version_id %>
                       <% display_row = '' if c.at_version and (c.at_version_num == ver_pr or c.from_version_num == ver_pr) else 'none' %>

                       <tr class="version-pr" style="display: ${display_row}">
                           <td>
                                <code>
                                    <a href="${request.current_route_path(_query=dict(version=ver_pr or 'latest'))}">v${ver_pos}</a>
                                </code>
                           </td>
                           <td>
                               <input ${('checked="checked"' if c.from_version_index == ver_pr else '')} class="compare-radio-button" type="radio" name="ver_source" value="${ver_pr or 'latest'}" data-ver-pos="${ver_pos}"/>
                               <input ${('checked="checked"' if c.at_version_num == ver_pr else '')} class="compare-radio-button" type="radio" name="ver_target" value="${ver_pr or 'latest'}" data-ver-pos="${ver_pos}"/>
                           </td>
                           <td>
                            <% review_status = c.review_versions[ver_pr].status if ver_pr in c.review_versions else 'not_reviewed' %>
                            <i class="tooltip icon-circle review-status-${review_status}" title="${_('Your review status at this version')}"></i>

                           </td>
                           <td>
                               % if c.at_version_num != ver_pr:
                                <i class="tooltip icon-comment" title="${_('Comments from pull request version v{0}').format(ver_pos)}"></i>
                                <code>
                                   General:${len(c.comment_versions[ver_pr]['at'])} / Inline:${len(c.inline_versions[ver_pr]['at'])}
                                </code>
                               % endif
                           </td>
                           <td>
                               ##<code>${ver.source_ref_parts.commit_id[:6]}</code>
                           </td>
                           <td>
                               <code>${h.age_component(ver.updated_on, time_is_local=True, tooltip=False)}</code>
                           </td>
                       </tr>
                   % endfor

                   <tr>
                       <td colspan="6">
                           <button id="show-version-diff" onclick="return versionController.showVersionDiff()" class="btn btn-sm" style="display: none"
                                   data-label-text-locked="${_('select versions to show changes')}"
                                   data-label-text-diff="${_('show changes between versions')}"
                                   data-label-text-show="${_('show pull request for this version')}"
                           >
                               ${_('select versions to show changes')}
                           </button>
                       </td>
                   </tr>
               </table>
           % else:
               <div>
               ${_('Pull request versions not available')}.
               </div>
           % endif
           </div>
       </div>

    </div>

  </div>


  </div>

</div>

<div class="box">

  % if c.state_progressing:

    <h2 style="text-align: center">
        ${_('Cannot show diff when pull request state is changing. Current progress state')}: <span class="tag tag-merge-state-${c.pull_request.state}">${c.pull_request.state}</span>

        % if c.is_super_admin:
        <br/>
        If you think this is an error try <a href="${h.current_route_path(request, force_state='created')}">forced state reset</a> to <span class="tag tag-merge-state-created">created</span> state.
        % endif
    </h2>

  % else:

      ## Diffs rendered here
      <div class="table" >
          <div id="changeset_compare_view_content">
              ##CS
              % if c.missing_requirements:
                <div class="box">
                  <div class="alert alert-warning">
                    <div>
                      <strong>${_('Missing requirements:')}</strong>
                      ${_('These commits cannot be displayed, because this repository uses the Mercurial largefiles extension, which was not enabled.')}
                    </div>
                  </div>
                </div>
              % elif c.missing_commits:
                <div class="box">
                  <div class="alert alert-warning">
                    <div>
                      <strong>${_('Missing commits')}:</strong>
                        ${_('This pull request cannot be displayed, because one or more commits no longer exist in the source repository.')}<br/>
                        ${_('Please update this pull request, push the commits back into the source repository, or consider closing this pull request.')}<br/>
                        ${_('Consider doing a `force update commits` in case you think this is an error.')}
                    </div>
                  </div>
                </div>
              % elif c.pr_merge_source_commit.changed and not c.pull_request.is_closed():
                <div class="box">
                  <div class="alert alert-info">
                    <div>
                        <strong>${_('There are new changes for `{}:{}` in source repository, please consider updating this pull request.').format(c.pr_merge_source_commit.ref_spec.type, c.pr_merge_source_commit.ref_spec.name)}</strong>
                    </div>
                  </div>
                </div>
              % endif

              <div class="compare_view_commits_title">
                  % if not c.compare_mode:

                    % if c.at_version_index:
                        <h4>
                        ${_('Showing changes at v{}, commenting is disabled.').format(c.at_version_index)}
                        </h4>
                    % endif

                    <div class="pull-left">
                      <div class="btn-group">
                          <a class="${('collapsed' if c.collapse_all_commits else '')}" href="#expand-commits" onclick="toggleCommitExpand(this); return false" data-toggle-commits-cnt=${len(c.commit_ranges)} >
                              % if c.collapse_all_commits:
                                <i class="icon-plus-squared-alt icon-no-margin"></i>
                                ${_ungettext('Expand {} commit', 'Expand {} commits', len(c.commit_ranges)).format(len(c.commit_ranges))}
                              % else:
                                <i class="icon-minus-squared-alt icon-no-margin"></i>
                                ${_ungettext('Collapse {} commit', 'Collapse {} commits', len(c.commit_ranges)).format(len(c.commit_ranges))}
                              % endif
                          </a>
                      </div>
                    </div>

                    <div class="pull-right">
                        % if c.allowed_to_update and not c.pull_request.is_closed():

                            <div class="btn-group btn-group-actions">
                                <a id="update_commits" class="btn btn-primary no-margin" onclick="updateController.updateCommits(this); return false">
                                    ${_('Update commits')}
                                </a>

                                <a id="update_commits_switcher" class="tooltip btn btn-primary btn-more-option" data-toggle="dropdown" aria-pressed="false" role="button" title="${_('more update options')}">
                                    <i class="icon-down"></i>
                                </a>

                                <div class="btn-action-switcher-container right-align" id="update-commits-switcher">
                                    <ul class="btn-action-switcher" role="menu" style="min-width: 300px;">
                                        <li>
                                            <a href="#forceUpdate" onclick="updateController.forceUpdateCommits(this); return false">
                                                ${_('Force update commits')}
                                            </a>
                                            <div class="action-help-block">
                                               ${_('Update commits and force refresh this pull request.')}
                                            </div>
                                        </li>
                                    </ul>
                                </div>
                            </div>

                        % else:
                          <a class="tooltip btn disabled pull-right" disabled="disabled" title="${_('Update is disabled for current view')}">${_('Update commits')}</a>
                        % endif

                    </div>
                  % endif
              </div>

              % if not c.missing_commits:
                ## COMPARE RANGE DIFF MODE
                % if c.compare_mode:
                    % if c.at_version:
                    <h4>
                        ${_('Commits and changes between v{ver_from} and {ver_to} of this pull request, commenting is disabled').format(ver_from=c.from_version_index, ver_to=c.at_version_index if c.at_version_index else 'latest')}:
                    </h4>

                    <div class="subtitle-compare">
                        ${_('commits added: {}, removed: {}').format(len(c.commit_changes_summary.added), len(c.commit_changes_summary.removed))}
                    </div>

                    <div class="container">
                        <table class="rctable compare_view_commits">
                            <tr>
                                <th></th>
                                <th>${_('Time')}</th>
                                <th>${_('Author')}</th>
                                <th>${_('Commit')}</th>
                                <th></th>
                                <th>${_('Description')}</th>
                            </tr>

                            % for c_type, commit in c.commit_changes:
                              % if c_type in ['a', 'r']:
                                <%
                                    if c_type == 'a':
                                        cc_title = _('Commit added in displayed changes')
                                    elif c_type == 'r':
                                        cc_title = _('Commit removed in displayed changes')
                                    else:
                                        cc_title = ''
                                %>
                                <tr id="row-${commit.raw_id}" commit_id="${commit.raw_id}" class="compare_select">
                                <td>
                                    <div class="commit-change-indicator color-${c_type}-border">
                                      <div class="commit-change-content color-${c_type} tooltip" title="${h.tooltip(cc_title)}">
                                        ${c_type.upper()}
                                      </div>
                                    </div>
                                </td>
                                <td class="td-time">
                                    ${h.age_component(commit.date)}
                                </td>
                                <td class="td-user">
                                    ${base.gravatar_with_user(commit.author, 16, tooltip=True)}
                                </td>
                                <td class="td-hash">
                                    <code>
                                        <a href="${h.route_path('repo_commit', repo_name=c.target_repo.repo_name, commit_id=commit.raw_id)}">
                                            r${commit.idx}:${h.short_id(commit.raw_id)}
                                        </a>
                                        ${h.hidden('revisions', commit.raw_id)}
                                    </code>
                                </td>
                                <td class="td-message expand_commit" data-commit-id="${commit.raw_id}" title="${_( 'Expand commit message')}" onclick="commitsController.expandCommit(this); return false">
                                    <i class="icon-expand-linked"></i>
                                </td>
                                <td class="mid td-description">
                                    <div class="log-container truncate-wrap">
                                        <div class="message truncate" id="c-${commit.raw_id}" data-message-raw="${commit.message}">${h.urlify_commit_message(commit.message, c.repo_name, issues_container=c.referenced_commit_issues)}</div>
                                    </div>
                                </td>
                            </tr>
                              % endif
                            % endfor
                        </table>
                    </div>

                    % endif

                ## Regular DIFF
                % else:
                    <%include file="/compare/compare_commits.mako" />
                % endif

                <div class="cs_files">
                    <%namespace name="cbdiffs" file="/codeblocks/diffs.mako"/>

                    <%
                        pr_menu_data = {
                            'outdated_comm_count_ver': outdated_comm_count_ver,
                            'pull_request': c.pull_request
                        }
                    %>

                    ${cbdiffs.render_diffset_menu(c.diffset, range_diff_on=c.range_diff_on, pull_request_menu=pr_menu_data)}

                    % if c.range_diff_on:
                        % for commit in c.commit_ranges:
                            ${cbdiffs.render_diffset(
                              c.changes[commit.raw_id],
                              commit=commit, use_comments=True,
                              collapse_when_files_over=5,
                              disable_new_comments=True,
                              deleted_files_comments=c.deleted_files_comments,
                              inline_comments=c.inline_comments,
                              pull_request_menu=pr_menu_data, show_todos=False)}
                        % endfor
                    % else:
                        ${cbdiffs.render_diffset(
                          c.diffset, use_comments=True,
                          collapse_when_files_over=30,
                          disable_new_comments=not c.allowed_to_comment,
                          deleted_files_comments=c.deleted_files_comments,
                          inline_comments=c.inline_comments,
                          pull_request_menu=pr_menu_data, show_todos=False)}
                    % endif

                </div>
              % else:
                  ## skipping commits we need to clear the view for missing commits
                  <div style="clear:both;"></div>
              % endif

          </div>
      </div>

      ## template for inline comment form
      <%namespace name="comment" file="/changeset/changeset_file_comment.mako"/>

      ## comments heading with count
      <div class="comments-heading">
        <i class="icon-comment"></i>
        ${_('General Comments')} ${len(c.comments)}
      </div>

      ## render general comments
      <div id="comment-tr-show">
        % if general_outdated_comm_count_ver:
        <div class="info-box">
            % if general_outdated_comm_count_ver == 1:
                ${_('there is {num} general comment from older versions').format(num=general_outdated_comm_count_ver)},
                <a href="#show-hidden-comments" onclick="$('.comment-general.comment-outdated').show(); $(this).parent().hide(); return false;">${_('show it')}</a>
            % else:
                ${_('there are {num} general comments from older versions').format(num=general_outdated_comm_count_ver)},
                <a href="#show-hidden-comments" onclick="$('.comment-general.comment-outdated').show(); $(this).parent().hide(); return false;">${_('show them')}</a>
            % endif
        </div>
        % endif
      </div>

      ${comment.generate_comments(c.comments, include_pull_request=True, is_pull_request=True)}

      % if not c.pull_request.is_closed():
        ## main comment form and it status
        ${comment.comments(h.route_path('pullrequest_comment_create', repo_name=c.repo_name,
                                        pull_request_id=c.pull_request.pull_request_id),
                           c.pull_request_review_status,
                           is_pull_request=True, change_status=c.allowed_to_change_status)}

        ## merge status, and merge action
        <div class="pull-request-merge">
            <%include file="/pullrequests/pullrequest_merge_checks.mako"/>
        </div>

      %endif

   % endif
  </div>


### NAVBOG RIGHT
<style>

    .right-sidebar {
        position: fixed;
        top: 0px;
        bottom: 0;
        right: 0;

        background: #fafafa;
        z-index: 50;
    }

    .right-sidebar {
        border-left: 1px solid #dbdbdb;
    }

    .right-sidebar.right-sidebar-expanded {
        width: 320px;
        overflow: scroll;
    }

    .right-sidebar.right-sidebar-collapsed {
        width: 50px;
        padding: 0;
        display: block;
        overflow: hidden;
    }

    .sidenav {
        float: right;
        will-change: min-height;
        background: #fafafa;
        width: 100%;
        padding-top: 50px;
    }

    .sidebar-toggle {
        height: 30px;
        text-align: center;
        margin: 15px 0px 0 0;
    }
    .sidebar-toggle a {

    }

    .sidebar-content {
        margin-left: 15px;
        margin-right: 15px;
    }

    .sidebar-heading {
        font-size: 1.2em;
        font-weight: 700;
        margin-top: 10px;
    }

    .sidebar-element {
        margin-top: 20px;
    }
    .right-sidebar-collapsed-state {
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        padding: 0 10px;
        cursor: pointer;
        font-size: 1.3em;
        margin: 0 -15px;
    }

    .right-sidebar-collapsed-state:hover {
        background-color: #dbd9da;
    }

    .old-comments-marker {
        text-align: center;
    }

    .old-comments-marker td {
        padding-top: 15px;
        border-bottom: 1px solid #dbd9da;
    }

    #add_reviewer {
        padding-top: 10px;
    }

</style>

<aside class="right-sidebar right-sidebar-expanded" id="pr-nav-sticky" style="display: none">
    <div class="sidenav navbar__inner" >
        ## TOGGLE
        <div class="sidebar-toggle" onclick="toggleSidebar(); return false">
            <a href="#toggleSidebar">

            </a>
        </div>

        ## CONTENT
        <div class="sidebar-content">

            ## RULES SUMMARY/RULES
            <div class="sidebar-element clear-both">

                <div class="tooltip right-sidebar-collapsed-state" style="display: none" onclick="toggleSidebar(); return false" title="${_('Reviewers')}">
                    <i class="icon-circle review-status-${c.pull_request_review_status}"></i>
                    ${len(c.allowed_reviewers)}
                </div>

                ## REVIEW RULES
                <div id="review_rules" style="display: none" class="">
                    <div class="right-sidebar-expanded-state pr-details-title">
                        <span class="sidebar-heading">
                            ${_('Reviewer rules')}
                        </span>

                    </div>
                    <div class="pr-reviewer-rules">
                        ## review rules will be appended here, by default reviewers logic
                    </div>
                    <input id="review_data" type="hidden" name="review_data" value="">
                </div>

                ## REVIEWERS
                <div class="right-sidebar-expanded-state pr-details-title">
                    <span class="tooltip sidebar-heading" title="${_ungettext('Review status calculated based on {} reviewer vote', 'Review status calculated based on {} reviewers votes', len(c.allowed_reviewers)).format(len(c.allowed_reviewers))}">
                        <i class="icon-circle review-status-${c.pull_request_review_status}"></i>
                        ${_('Reviewers')}
                    </span>
                    %if c.allowed_to_update:
                        <span id="open_edit_reviewers" class="block-right action_button last-item">${_('Edit')}</span>
                        <span id="close_edit_reviewers" class="block-right action_button last-item" style="display: none;">${_('Close')}</span>
                    %else:
                        <span id="open_edit_reviewers" class="block-right action_button last-item">${_('Show rules')}</span>
                        <span id="close_edit_reviewers" class="block-right action_button last-item" style="display: none;">${_('Close')}</span>
                    %endif
                </div>

                <div id="reviewers" class="right-sidebar-expanded-state pr-details-content reviewers">

                    ## members redering block
                    <input type="hidden" name="__start__" value="review_members:sequence">

                    <table id="review_members" class="group_members">
                    ## This content is loaded via JS and ReviewersPanel
                    </table>

                    <input type="hidden" name="__end__" value="review_members:sequence">
                    ## end members redering block

                    %if not c.pull_request.is_closed():
                        <div id="add_reviewer" class="ac" style="display: none;">
                        %if c.allowed_to_update:
                            % if not c.forbid_adding_reviewers:
                                <div id="add_reviewer_input" class="reviewer_ac">
                                   ${h.text('user', class_='ac-input', placeholder=_('Add reviewer or reviewer group'))}
                                   <div id="reviewers_container"></div>
                                </div>
                            % endif
                            <div class="pull-right">
                                <button id="update_pull_request" class="btn btn-small no-margin">${_('Save Changes')}</button>
                            </div>
                        %endif
                        </div>
                    %endif
                </div>
            </div>

##             ## OBSERVERS
##             <div class="sidebar-element clear-both">
##                 <div class="tooltip right-sidebar-collapsed-state" style="display: none" onclick="toggleSidebar(); return false" title="${_('Observers')}">
##                     <i class="icon-eye"></i>
##                     0
##                 </div>
##
##                 <div class="right-sidebar-expanded-state pr-details-title">
##                   <span class="sidebar-heading">
##                     <i class="icon-eye"></i>
##                     ${_('Observers')}
##                   </span>
##                 </div>
##                 <div class="right-sidebar-expanded-state pr-details-content">
##                     No observers
##                 </div>
##             </div>

            ## TODOs
            <div class="sidebar-element clear-both">
                <div class="tooltip right-sidebar-collapsed-state" style="display: none" onclick="toggleSidebar(); return false" title="TODOs">
                  <i class="icon-flag-filled"></i>
                  <span id="todos-count">${len(c.unresolved_comments)}</span>
                </div>

                <div class="right-sidebar-expanded-state pr-details-title">
                      ## Only show unresolved, that is only what matters
                      <span class="sidebar-heading noselect" onclick="refreshTODOs(); return false">
                      <i class="icon-flag-filled"></i>
                      TODOs
                      </span>

                      % if not c.at_version:
                          % if c.resolved_comments:
                              <span class="block-right action_button last-item noselect" onclick="$('.unresolved-todo-text').toggle(); return versionController.toggleElement(this, '.resolved-todo');" data-toggle-on="Show resolved" data-toggle-off="Hide resolved">Show resolved</span>
                          % else:
                              <span class="block-right last-item noselect">Show resolved</span>
                          % endif
                      % endif
                  </div>

                <div class="right-sidebar-expanded-state pr-details-content">

                  % if c.at_version:
                      <table>
                          <tr>
                            <td class="unresolved-todo-text">${_('TODOs unavailable when browsing versions')}.</td>
                          </tr>
                      </table>
                  % else:
                    % if c.unresolved_comments + c.resolved_comments:
                      ${comments_table(c.unresolved_comments + c.resolved_comments, len(c.unresolved_comments), todo_comments=True)}
                    % else:
                        <table>
                            <tr>
                                <td>
                                    ${_('No TODOs yet')}
                                </td>
                            </tr>
                        </table>
                    % endif
                  % endif
                </div>
            </div>

            ## COMMENTS
            <div class="sidebar-element clear-both">
                <div class="tooltip right-sidebar-collapsed-state" style="display: none" onclick="toggleSidebar(); return false" title="${_('Comments')}">
                    <i class="icon-comment" style="color: #949494"></i>
                    <span id="comments-count">${len(c.inline_comments_flat+c.comments)}</span>
                </div>

                <div class="right-sidebar-expanded-state pr-details-title">
                  <span class="sidebar-heading noselect" onclick="refreshComments(); return false">
                    <i class="icon-comment" style="color: #949494"></i>
                    ${_('Comments')}

##                    % if outdated_comm_count_ver:
##                         <a href="#" onclick="showOutdated(); Rhodecode.comments.nextOutdatedComment(); return false;">
##                             (${_("{} Outdated").format(outdated_comm_count_ver)})
##                         </a>
##                         <a href="#" class="showOutdatedComments" onclick="showOutdated(this); return false;"> | ${_('show outdated')}</a>
##                         <a href="#" class="hideOutdatedComments" style="display: none" onclick="hideOutdated(this); return false;"> | ${_('hide outdated')}</a>

##                         % else:
##                             (${_("{} Outdated").format(outdated_comm_count_ver)})
##                    % endif

                  </span>

                  % if outdated_comm_count_ver:
                    <span class="block-right action_button last-item noselect" onclick="return versionController.toggleElement(this, '.hidden-comment');" data-toggle-on="Show outdated" data-toggle-off="Hide outdated">Show outdated</span>
                  % else:
                    <span class="block-right last-item noselect">Show hidden</span>
                  % endif

                </div>

                <div class="right-sidebar-expanded-state pr-details-content">
                % if c.inline_comments_flat + c.comments:
                    ${comments_table(c.inline_comments_flat + c.comments, len(c.inline_comments_flat+c.comments))}
                % else:
                    <table>
                        <tr>
                            <td>
                                ${_('No Comments yet')}
                            </td>
                        </tr>
                    </table>
                % endif
                </div>

            </div>

            ## Referenced Tickets
            <div class="sidebar-element clear-both">
                <div class="tooltip right-sidebar-collapsed-state" style="display: none" onclick="toggleSidebar(); return false" title="${_('Referenced Tickets')}">
                    <i class="icon-info-circled"></i>
                    ${(len(c.referenced_desc_issues) + len(c.referenced_commit_issues))}
                </div>

                <div class="right-sidebar-expanded-state pr-details-title">
                  <span class="sidebar-heading">
                    <i class="icon-info-circled"></i>
                    ${_('Referenced Tickets')}
                  </span>
                </div>
                <div class="right-sidebar-expanded-state pr-details-content">
                    <table>

                        <tr><td><code>${_('Pull Request Description')}</code></td></tr>
                        % if c.referenced_desc_issues:
                            % for ticket_dict in c.referenced_desc_issues:
                            <tr>
                                <td>
                                    <a href="${ticket_dict.get('url')}">
                                    ${ticket_dict.get('id')}
                                    </a>
                                </td>
                            </tr>
                            % endfor
                        % else:
                            <tr>
                                <td>
                                    ${_('No Ticket data found.')}
                                </td>
                            </tr>
                        % endif

                        <tr><td style="padding-top: 10px"><code>${_('Commit Messages')}</code></td></tr>
                        % if c.referenced_commit_issues:
                            % for ticket_dict in c.referenced_commit_issues:
                            <tr>
                                <td>
                                    <a href="${ticket_dict.get('url')}">
                                    ${ticket_dict.get('id')}
                                    </a>
                                </td>
                            </tr>
                            % endfor
                        % else:
                            <tr>
                                <td>
                                    ${_('No Ticket data found.')}
                                </td>
                            </tr>
                        % endif
                    </table>

                </div>
            </div>

        </div>

    </div>
</aside>

## This JS needs to be at the end
<script type="text/javascript">

      versionController = new VersionController();
      versionController.init();

      reviewersController = new ReviewersController();
      commitsController = new CommitsController();

      updateController = new UpdatePrController();

/** leak object to top level scope **/
window.PullRequestPresenceController;

(function () {
    "use strict";

    window.PullRequestPresenceController = function (channel) {
        var self = this;
        this.channel = channel;
        this.users = {};

        this.storeUsers = function (users) {
            self.users = {}
            $.each(users, function(index, value) {
                var userId = value.state.id;
                self.users[userId] = value.state;
            })
        }

        this.render = function () {
            $.each($('.reviewer_entry'), function(index, value) {
                var userData = $(value).data();
                if(self.users[userData.reviewerUserId] !== undefined){
                    $(value).find('.presence-state').show();
                } else {
                    $(value).find('.presence-state').hide();
                }
            })
        };

        this.handlePresence = function (data) {

            if (data.type == 'presence' && data.channel === self.channel) {
                this.storeUsers(data.users);
                this.render()
            }
        };

        this.handleChannelUpdate = function (data) {

            if (data.channel === this.channel) {
                this.storeUsers(data.state.users);
                this.render()
            }

        };

        /* subscribe our chat to topics that are interesting to it */
        $.Topic('/connection_controller/channel_update').subscribe(this.handleChannelUpdate.bind(this));
        $.Topic('/connection_controller/presence').subscribe(this.handlePresence.bind(this));
    };

})();


      $(function () {

          // custom code mirror
          var codeMirrorInstance = $('#pr-description-input').get(0).MarkupForm.cm;

          var PRDetails = {
              editButton: $('#open_edit_pullrequest'),
              closeButton: $('#close_edit_pullrequest'),
              deleteButton: $('#delete_pullrequest'),
              viewFields: $('#pr-desc, #pr-title'),
              editFields: $('#pr-desc-edit, #pr-title-edit, .pr-save'),

              init: function () {
                  var that = this;
                  this.editButton.on('click', function (e) {
                      that.edit();
                  });
                  this.closeButton.on('click', function (e) {
                      that.view();
                  });
              },

              edit: function (event) {
                  this.viewFields.hide();
                  this.editButton.hide();
                  this.deleteButton.hide();
                  this.closeButton.show();
                  this.editFields.show();
                  codeMirrorInstance.refresh();
              },

              view: function (event) {
                  this.editButton.show();
                  this.deleteButton.show();
                  this.editFields.hide();
                  this.closeButton.hide();
                  this.viewFields.show();
              }
          };

          var ReviewersPanel = {
              editButton: $('#open_edit_reviewers'),
              closeButton: $('#close_edit_reviewers'),
              addButton: $('#add_reviewer'),
              removeButtons: $('.reviewer_member_remove,.reviewer_member_mandatory_remove'),
              reviewRules: ${c.pull_request_default_reviewers_data_json | n},
              setReviewers: ${c.pull_request_set_reviewers_data_json | n},

              init: function () {
                  var self = this;
                  this.editButton.on('click', function (e) {
                      self.edit();
                  });
                  this.closeButton.on('click', function (e) {
                      self.close();
                      self.renderReviewers();
                  });

                  self.renderReviewers();

              },

              renderReviewers: function () {

                $('#review_members').html('')
                $.each(this.setReviewers.reviewers, function (key, val) {
                    var member = val;

                    var entry = renderTemplate('reviewMemberEntry', {
                        'member': member,
                        'mandatory': member.mandatory,
                        'reasons': member.reasons,
                        'allowed_to_update': member.allowed_to_update,
                        'review_status': member.review_status,
                        'review_status_label': member.review_status_label,
                        'user_group': member.user_group,
                        'create': false
                    });

                    $('#review_members').append(entry)
                });
                tooltipActivate();

              },

              edit: function (event) {
                  this.editButton.hide();
                  this.closeButton.show();
                  this.addButton.show();
                  $(this.removeButtons.selector).css('visibility', 'visible');
                  // review rules
                  reviewersController.loadReviewRules(this.reviewRules);
              },

              close: function (event) {
                  this.editButton.show();
                  this.closeButton.hide();
                  this.addButton.hide();
                  $(this.removeButtons.selector).css('visibility', 'hidden');
                  // hide review rules
                  reviewersController.hideReviewRules()
              }
          };

          PRDetails.init();
          ReviewersPanel.init();

          showOutdated = function (self) {
              $('.comment-inline.comment-outdated').show();
              $('.filediff-outdated').show();
              $('.showOutdatedComments').hide();
              $('.hideOutdatedComments').show();
          };

          hideOutdated = function (self) {
              $('.comment-inline.comment-outdated').hide();
              $('.filediff-outdated').hide();
              $('.hideOutdatedComments').hide();
              $('.showOutdatedComments').show();
          };

          refreshMergeChecks = function () {
              var loadUrl = "${request.current_route_path(_query=dict(merge_checks=1))}";
              $('.pull-request-merge').css('opacity', 0.3);
              $('.action-buttons-extra').css('opacity', 0.3);

              $('.pull-request-merge').load(
                  loadUrl, function () {
                      $('.pull-request-merge').css('opacity', 1);

                      $('.action-buttons-extra').css('opacity', 1);
                  }
              );
          };

          refreshComments = function () {
            var params = {
                'pull_request_id': templateContext.pull_request_data.pull_request_id,
                'repo_name': templateContext.repo_name,
                'version': '${request.GET.get('version', '')}',
            };
            var data = {"comments[]": ["1"]};
            var loadUrl = pyroutes.url('pullrequest_comments', params);
            var $targetElem = $('.comments-content-table');
            $targetElem.css('opacity', 0.3);
            $targetElem.load(
                  loadUrl, data, function (responseText, textStatus, jqXHR) {
                    if (jqXHR.status !== 200) {
                        return false;
                    }
                    var $counterElem = $('#comments-count');
                    var newCount = $(responseText).data('counter');
                    if (newCount !== undefined) {
                        var callback = function () {
                            $counterElem.animate({'opacity': 1.00}, 200)
                            $counterElem.html(newCount);
                        };
                        $counterElem.animate({'opacity': 0.15}, 200, callback);
                    }


                    $targetElem.css('opacity', 1);
                    tooltipActivate();
                  }
            );
          }

          refreshTODOs = function () {
            var params = {
                'pull_request_id': templateContext.pull_request_data.pull_request_id,
                'repo_name': templateContext.repo_name,
                'version': '${request.GET.get('version', '')}',
            };
            var data = {"comments[]": ["1"]};
            var loadUrl = pyroutes.url('pullrequest_todos', params);
            var $targetElem = $('.todos-content-table');
            $targetElem.css('opacity', 0.3);
            $targetElem.load(
                  loadUrl, data, function (responseText, textStatus, jqXHR) {
                    if (jqXHR.status !== 200) {
                        return false;
                    }
                    var $counterElem = $('#todos-count')
                    var newCount = $(responseText).data('counter');
                    if (newCount !== undefined) {
                        var callback = function () {
                            $counterElem.animate({'opacity': 1.00}, 200)
                            $counterElem.html(newCount);
                        };
                        $counterElem.animate({'opacity': 0.15}, 200, callback);
                    }

                    $targetElem.css('opacity', 1);
                    tooltipActivate();
                  }
            );

          }

          refreshAllComments = function() {
              refreshComments();
              refreshTODOs();
          }

          closePullRequest = function (status) {
              if (!confirm(_gettext('Are you sure to close this pull request without merging?'))) {
                  return false;
              }
              // inject closing flag
              $('.action-buttons-extra').append('<input type="hidden" class="close-pr-input" id="close_pull_request" value="1">');
              $(generalCommentForm.statusChange).select2("val", status).trigger('change');
              $(generalCommentForm.submitForm).submit();
          };

          $('#show-outdated-comments').on('click', function (e) {
              var button = $(this);
              var outdated = $('.comment-outdated');

              if (button.html() === "(Show)") {
                  button.html("(Hide)");
                  outdated.show();
              } else {
                  button.html("(Show)");
                  outdated.hide();
              }
          });

          $('.show-inline-comments').on('change', function (e) {
              var show = 'none';
              var target = e.currentTarget;
              if (target.checked) {
                  show = ''
              }
              var boxid = $(target).attr('id_for');
              var comments = $('#{0} .inline-comments'.format(boxid));
              var fn_display = function (idx) {
                  $(this).css('display', show);
              };
              $(comments).each(fn_display);
              var btns = $('#{0} .inline-comments-button'.format(boxid));
              $(btns).each(fn_display);
          });

          $('#merge_pull_request_form').submit(function () {
              if (!$('#merge_pull_request').attr('disabled')) {
                  $('#merge_pull_request').attr('disabled', 'disabled');
              }
              return true;
          });

          $('#edit_pull_request').on('click', function (e) {
              var title = $('#pr-title-input').val();
              var description = codeMirrorInstance.getValue();
              var renderer = $('#pr-renderer-input').val();
              editPullRequest(
                      "${c.repo_name}", "${c.pull_request.pull_request_id}",
                      title, description, renderer);
          });

          $('#update_pull_request').on('click', function (e) {
              $(this).attr('disabled', 'disabled');
              $(this).addClass('disabled');
              $(this).html(_gettext('Saving...'));
              reviewersController.updateReviewers(
                      "${c.repo_name}", "${c.pull_request.pull_request_id}");
          });


          // fixing issue with caches on firefox
          $('#update_commits').removeAttr("disabled");

          $('.show-inline-comments').on('click', function (e) {
              var boxid = $(this).attr('data-comment-id');
              var button = $(this);

              if (button.hasClass("comments-visible")) {
                  $('#{0} .inline-comments'.format(boxid)).each(function (index) {
                      $(this).hide();
                  });
                  button.removeClass("comments-visible");
              } else {
                  $('#{0} .inline-comments'.format(boxid)).each(function (index) {
                      $(this).show();
                  });
                  button.addClass("comments-visible");
              }
          });

          // register submit callback on commentForm form to track TODOs
          window.commentFormGlobalSubmitSuccessCallback = function () {
              refreshMergeChecks();
          };

          ReviewerAutoComplete('#user');

      })

      $(document).ready(function () {

        var $sideBar = $('.right-sidebar');
        var marginExpVal = '320'
        var marginColVal = '50'
        var marginExpanded = {'margin': '0 {0}px 0 0'.format(marginExpVal)};
        var marginCollapsed = {'margin': '0 {0}px 0 0'.format(marginColVal)};
        var marginExpandedHeader = {'margin': '0 -{0}px 0 0'.format(marginExpVal), 'z-index': 10000};
        var marginCollapsedHeader = {'margin': '0 -{0}px 0 0'.format(marginColVal), 'z-index': 10000};

        var updateStickyHeader = function() {
          if (window.updateSticky !== undefined) {
              // potentially our comments change the active window size, so we
              // notify sticky elements
              updateSticky()
          }
        }

        var expandSidebar = function() {
            var $sideBar = $('.right-sidebar');
            $('.outerwrapper').css(marginExpanded);
            $('.header').css(marginExpandedHeader);
            $('.sidebar-toggle a').html('<i class="icon-right" style="margin-right: -10px"></i><i class="icon-right"></i>');
            $('.right-sidebar-collapsed-state').hide();
            $('.right-sidebar-expanded-state').show();

            $sideBar.addClass('right-sidebar-expanded')
            $sideBar.removeClass('right-sidebar-collapsed')
        }

        var collapseSidebar = function() {
            var $sideBar = $('.right-sidebar');
            $('.outerwrapper').css(marginCollapsed);
            $('.header').css(marginCollapsedHeader);
            $('.sidebar-toggle a').html('<i class="icon-left" style="margin-right: -10px"></i><i class="icon-left"></i>');
            $('.right-sidebar-collapsed-state').show();
            $('.right-sidebar-expanded-state').hide();

            $sideBar.removeClass('right-sidebar-expanded')
            $sideBar.addClass('right-sidebar-collapsed')
        }

        toggleSidebar = function () {
            var $sideBar = $('.right-sidebar');

            if ($sideBar.hasClass('right-sidebar-expanded')) {
                // expanded -> collapsed transition
                collapseSidebar();
                var sidebarState = 'collapsed';

            } else {
                // collapsed -> expanded
                expandSidebar();
                var sidebarState = 'expanded';
            }

            // update our other sticky header in same context
            updateStickyHeader();
            storeUserSessionAttr('rc_user_session_attr.sidebarState', sidebarState);
        }

        var expanded = $sideBar.hasClass('right-sidebar-expanded');

        if (templateContext.session_attrs.sidebarState === 'expanded') {
            expanded = true
        } else if (templateContext.session_attrs.sidebarState === 'collapsed') {
            expanded = false
        }

        // show sidebar since it's hidden on load
        $('.right-sidebar').show();

        // init based on set initial class, or if defined user session attrs
        if (expanded) {
             expandSidebar();
             updateStickyHeader();

        } else {
             collapseSidebar();
             updateStickyHeader();
        }
        var channel = '${c.pr_broadcast_channel}';
        new PullRequestPresenceController(channel)

    })
  </script>

</%def>
