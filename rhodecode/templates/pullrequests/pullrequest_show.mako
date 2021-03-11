<%inherit file="/base/base.mako"/>
<%namespace name="base" file="/base/base.mako"/>
<%namespace name="dt" file="/data_table/_dt_elements.mako"/>
<%namespace name="sidebar" file="/base/sidebar.mako"/>


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


<%def name="main()">
## Container to gather extracted Tickets
<%
    c.referenced_commit_issues = h.IssuesRegistry()
    c.referenced_desc_issues = h.IssuesRegistry()
%>

<script type="text/javascript">
    templateContext.pull_request_data.pull_request_id = ${c.pull_request.pull_request_id};
    templateContext.pull_request_data.pull_request_version = '${request.GET.get('version', '')}';
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
        ${h.render(c.pull_request.description, renderer=c.renderer, repo_name=c.repo_name, issues_container_callback=c.referenced_desc_issues())}
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

                <a class="source-details-action" href="#expand-source-details" onclick="return toggleElement(this, '.source-details')" data-toggle-on='<i class="icon-angle-down">more details</i>' data-toggle-off='<i class="icon-angle-up">less details</i>'>
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
                                        <div class="message truncate" id="c-${commit.raw_id}" data-message-raw="${commit.message}">${h.urlify_commit_message(commit.message, c.repo_name, issues_container_callback=c.referenced_commit_issues(commit.serialize()))}</div>
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


### NAV SIDEBAR
<aside class="right-sidebar right-sidebar-expanded" id="pr-nav-sticky" style="display: none">
    <div class="sidenav navbar__inner" >
        ## TOGGLE
        <div class="sidebar-toggle" onclick="toggleSidebar(); return false">
            <a href="#toggleSidebar" class="grey-link-action">

            </a>
        </div>

        ## CONTENT
        <div class="sidebar-content">

            ## Drafts
            % if c.rhodecode_edition_id == 'EE':
            <div id="draftsTable" class="sidebar-element clear-both" style="display: ${'block' if c.draft_comments else 'none'}">
                <div class="tooltip right-sidebar-collapsed-state" style="display: none;" onclick="toggleSidebar(); return false" title="${_('Drafts')}">
                    <i class="icon-comment icon-draft"></i>
                    <span id="drafts-count">${len(c.draft_comments)}</span>
                </div>

                <div class="right-sidebar-expanded-state pr-details-title">
                  <span style="padding-left: 2px">
                  <input name="select_all_drafts" type="checkbox" onclick="$('[name=submit_draft]').prop('checked', !$('[name=submit_draft]').prop('checked'))">
                  </span>
                  <span class="sidebar-heading noselect" onclick="refreshDraftComments(); return false">
                    <i class="icon-comment icon-draft"></i>
                    ${_('Drafts')}
                  </span>
                  <span class="block-right action_button last-item" onclick="submitDrafts(event)">${_('Submit')}</span>
                </div>

                <div id="drafts" class="right-sidebar-expanded-state pr-details-content reviewers">
                    % if c.draft_comments:
                        ${sidebar.comments_table(c.draft_comments, len(c.draft_comments), draft_comments=True)}
                    % else:
                        <table class="drafts-content-table">
                            <tr>
                                <td>
                                    ${_('No TODOs yet')}
                                </td>
                            </tr>
                        </table>
                    % endif
                </div>

            </div>
            % endif

            ## RULES SUMMARY/RULES
            <div class="sidebar-element clear-both">
                <% vote_title = _ungettext(
                        'Status calculated based on votes from {} reviewer',
                        'Status calculated based on votes from {} reviewers', c.reviewers_count).format(c.reviewers_count)
                %>

                <div class="tooltip right-sidebar-collapsed-state" style="display: none" onclick="toggleSidebar(); return false" title="${vote_title}">
                    <i class="icon-circle review-status-${c.pull_request_review_status}"></i>
                    ${c.reviewers_count}
                </div>

                ## REVIEWERS
                <div class="right-sidebar-expanded-state pr-details-title">
                    <span class="tooltip sidebar-heading" title="${vote_title}">
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

                    <div id="review_rules" style="display: none" class="">

                        <strong>${_('Reviewer rules')}</strong>
                        <div class="pr-reviewer-rules">
                            ## review rules will be appended here, by default reviewers logic
                        </div>
                        <input id="review_data" type="hidden" name="review_data" value="">
                    </div>

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
                                <div id="add_reviewer_input" class="reviewer_ac" style="width: 240px">
                                   <input class="ac-input" id="user" name="user" placeholder="${_('Add reviewer or reviewer group')}" type="text" autocomplete="off">
                                   <div id="reviewers_container"></div>
                                </div>
                            % endif
                            <div class="pull-right" style="margin-bottom: 15px">
                                <button data-role="reviewer" id="update_reviewers" class="btn btn-sm no-margin">${_('Save Changes')}</button>
                            </div>
                        %endif
                        </div>
                    %endif
                </div>
            </div>

            ## OBSERVERS
            % if c.rhodecode_edition_id == 'EE':
            <div class="sidebar-element clear-both">
                <% vote_title = _ungettext(
                        '{} observer without voting right.',
                        '{} observers without voting right.', c.observers_count).format(c.observers_count)
                %>

                <div class="tooltip right-sidebar-collapsed-state" style="display: none" onclick="toggleSidebar(); return false" title="${vote_title}">
                    <i class="icon-circle-thin"></i>
                    ${c.observers_count}
                </div>

                <div class="right-sidebar-expanded-state pr-details-title">
                  <span class="tooltip sidebar-heading" title="${vote_title}">
                    <i class="icon-circle-thin"></i>
                    ${_('Observers')}
                  </span>
                  %if c.allowed_to_update:
                      <span id="open_edit_observers" class="block-right action_button last-item">${_('Edit')}</span>
                      <span id="close_edit_observers" class="block-right action_button last-item" style="display: none;">${_('Close')}</span>
                  %endif
                </div>

                <div id="observers" class="right-sidebar-expanded-state pr-details-content reviewers">
                    ## members redering block
                    <input type="hidden" name="__start__" value="observer_members:sequence">

                    <table id="observer_members" class="group_members">
                    ## This content is loaded via JS and ReviewersPanel
                    </table>

                    <input type="hidden" name="__end__" value="observer_members:sequence">
                    ## end members redering block

                    %if not c.pull_request.is_closed():
                        <div id="add_observer" class="ac" style="display: none;">
                        %if c.allowed_to_update:
                            % if not c.forbid_adding_reviewers or 1:
                                <div id="add_reviewer_input" class="reviewer_ac" style="width: 240px" >
                                   <input class="ac-input" id="observer" name="observer" placeholder="${_('Add observer or observer group')}" type="text" autocomplete="off">
                                   <div id="observers_container"></div>
                                </div>
                            % endif
                            <div class="pull-right" style="margin-bottom: 15px">
                                <button data-role="observer" id="update_observers" class="btn btn-sm no-margin">${_('Save Changes')}</button>
                            </div>
                        %endif
                        </div>
                    %endif
                </div>
            </div>
            % endif

            ## TODOs
            <div id="todosTable" class="sidebar-element clear-both">
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
                              <span class="block-right action_button last-item noselect" onclick="$('.unresolved-todo-text').toggle(); return toggleElement(this, '.resolved-todo');" data-toggle-on="Show resolved" data-toggle-off="Hide resolved">Show resolved</span>
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
                      ${sidebar.comments_table(c.unresolved_comments + c.resolved_comments, len(c.unresolved_comments), todo_comments=True)}
                    % else:
                        <table class="todos-content-table">
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
            <div id="commentsTable" class="sidebar-element clear-both">
                <div class="tooltip right-sidebar-collapsed-state" style="display: none" onclick="toggleSidebar(); return false" title="${_('Comments')}">
                    <i class="icon-comment" style="color: #949494"></i>
                    <span id="comments-count">${len(c.inline_comments_flat+c.comments)}</span>
                    <span class="display-none" id="general-comments-count">${len(c.comments)}</span>
                    <span class="display-none" id="inline-comments-count">${len(c.inline_comments_flat)}</span>
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
                    <span class="block-right action_button last-item noselect" onclick="return toggleElement(this, '.hidden-comment');" data-toggle-on="Show outdated" data-toggle-off="Hide outdated">Show outdated</span>
                  % else:
                    <span class="block-right last-item noselect">Show hidden</span>
                  % endif

                </div>

                <div class="right-sidebar-expanded-state pr-details-content">
                % if c.inline_comments_flat + c.comments:
                    ${sidebar.comments_table(c.inline_comments_flat + c.comments, len(c.inline_comments_flat+c.comments))}
                % else:
                    <table class="comments-content-table">
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
                    ${(c.referenced_desc_issues.issues_unique_count + c.referenced_commit_issues.issues_unique_count)}
                </div>

                <div class="right-sidebar-expanded-state pr-details-title">
                  <span class="sidebar-heading">
                    <i class="icon-info-circled"></i>
                    ${_('Referenced Tickets')}
                  </span>
                </div>
                <div class="right-sidebar-expanded-state pr-details-content">
                    <table>

                        <tr><td><code>${_('In pull request description')}:</code></td></tr>
                        % if c.referenced_desc_issues.issues:

                            % for ticket_id, ticket_dict in c.referenced_desc_issues.unique_issues.items():
                            <tr>
                                <td>
                                    <a href="${ticket_dict[0].get('url')}">
                                    ${ticket_id}
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

                        <tr><td style="padding-top: 10px"><code>${_('In commit messages')}:</code></td></tr>
                        % if c.referenced_commit_issues.issues:
                            % for ticket_id, ticket_dict in c.referenced_commit_issues.unique_issues.items():
                            <tr>
                                <td>
                                    <a href="${ticket_dict[0].get('url')}">
                                    ${ticket_id}
                                    </a>
                                    - ${_ungettext('in %s commit', 'in %s commits', len(ticket_dict)) % (len(ticket_dict))}
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
commentsController = new CommentsController();

updateController = new UpdatePrController();

window.reviewerRulesData = ${c.pull_request_default_reviewers_data_json | n};
window.setReviewersData = ${c.pull_request_set_reviewers_data_json | n};
window.setObserversData = ${c.pull_request_set_observers_data_json | n};

(function () {
    "use strict";

    // custom code mirror
    var codeMirrorInstance = $('#pr-description-input').get(0).MarkupForm.cm;

    PRDetails.init();
    ReviewersPanel.init(reviewersController, reviewerRulesData, setReviewersData);
    ObserversPanel.init(reviewersController, reviewerRulesData, setObserversData);

    window.showOutdated = function (self) {
        $('.comment-inline.comment-outdated').show();
        $('.filediff-outdated').show();
        $('.showOutdatedComments').hide();
        $('.hideOutdatedComments').show();
    };

    window.hideOutdated = function (self) {
        $('.comment-inline.comment-outdated').hide();
        $('.filediff-outdated').hide();
        $('.hideOutdatedComments').hide();
        $('.showOutdatedComments').show();
    };

    window.refreshMergeChecks = function () {
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

    window.submitDrafts = function (event) {
        var target = $(event.currentTarget);
        var callback = function (result) {
            target.removeAttr('onclick').html('saving...');
        }
        var draftIds = [];
        $.each($('[name=submit_draft]:checked'), function (idx, val) {
            draftIds.push(parseInt($(val).val()));
        })
        if (draftIds.length > 0) {
            Rhodecode.comments.finalizeDrafts(draftIds, callback);
        }
        else {

        }
    }

    window.closePullRequest = function (status) {
        if (!confirm(_gettext('Are you sure to close this pull request without merging?'))) {
            return false;
        }
        // inject closing flag
        $('.action-buttons-extra').append('<input type="hidden" class="close-pr-input" id="close_pull_request" value="1">');
        $(generalCommentForm.statusChange).select2("val", status).trigger('change');
        $(generalCommentForm.submitForm).submit();
    };

    //TODO this functionality is now missing
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

    var $updateButtons = $('#update_reviewers,#update_observers');
    $updateButtons.on('click', function (e) {
        var role = $(this).data('role');
        $updateButtons.attr('disabled', 'disabled');
        $updateButtons.addClass('disabled');
        $updateButtons.html(_gettext('Saving...'));
        reviewersController.updateReviewers(
                templateContext.repo_name,
                templateContext.pull_request_data.pull_request_id,
                role
        );
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

    // register submit callback on commentForm form to track TODOs, and refresh mergeChecks conditions
    window.commentFormGlobalSubmitSuccessCallback = function (comment) {
        if (!comment.draft) {
            refreshMergeChecks();
        }
    };

    ReviewerAutoComplete('#user', reviewersController);
    ObserverAutoComplete('#observer', reviewersController);

})();

$(document).ready(function () {

    var channel = '${c.pr_broadcast_channel}';
    new ReviewerPresenceController(channel)
    // register globally so inject comment logic can re-use it.
    window.commentsController = commentsController;
})
</script>

</%def>
