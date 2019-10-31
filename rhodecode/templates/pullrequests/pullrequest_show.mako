<%inherit file="/base/base.mako"/>
<%namespace name="base" file="/base/base.mako"/>
<%namespace name="dt" file="/data_table/_dt_elements.mako"/>

<%def name="title()">
    ${_('%s Pull Request #%s') % (c.repo_name, c.pull_request.pull_request_id)}
    %if c.rhodecode_name:
        &middot; ${h.branding(c.rhodecode_name)}
    %endif
</%def>

<%def name="breadcrumbs_links()">
    <span id="pr-title">
    ${c.pull_request.title}
    %if c.pull_request.is_closed():
        (${_('Closed')})
    %endif
    </span>
    <div id="pr-title-edit" class="input" style="display: none;">
        ${h.text('pullrequest_title', id_="pr-title-input", class_="large", value=c.pull_request.title)}
    </div>
</%def>

<%def name="menu_bar_nav()">
    ${self.menu_items(active='repositories')}
</%def>

<%def name="menu_bar_subnav()">
    ${self.repo_menu(active='showpullrequest')}
</%def>

<%def name="main()">

<script type="text/javascript">
    // TODO: marcink switch this to pyroutes
    AJAX_COMMENT_DELETE_URL = "${h.route_path('pullrequest_comment_delete',repo_name=c.repo_name,pull_request_id=c.pull_request.pull_request_id,comment_id='__COMMENT_ID__')}";
    templateContext.pull_request_data.pull_request_id = ${c.pull_request.pull_request_id};
</script>
<div class="box">

  ${self.breadcrumbs()}

  <div class="box pr-summary">

      <div class="summary-details block-left">
        <% summary = lambda n:{False:'summary-short'}.get(n) %>
        <div class="pr-details-title">
            <a href="${h.route_path('pull_requests_global', pull_request_id=c.pull_request.pull_request_id)}">${_('Pull request #%s') % c.pull_request.pull_request_id}</a> ${_('From')} ${h.format_date(c.pull_request.created_on)}
            %if c.allowed_to_update:
              <div id="delete_pullrequest" class="pull-right action_button ${'' if c.allowed_to_delete else 'disabled' }" style="clear:inherit;padding: 0">
                  % if c.allowed_to_delete:
                      ${h.secure_form(h.route_path('pullrequest_delete', repo_name=c.pull_request.target_repo.repo_name, pull_request_id=c.pull_request.pull_request_id), request=request)}
                          ${h.submit('remove_%s' % c.pull_request.pull_request_id, _('Delete'),
                        class_="btn btn-link btn-danger no-margin",onclick="return confirm('"+_('Confirm to delete this pull request')+"');")}
                      ${h.end_form()}
                  % else:
                    ${_('Delete')}
                  % endif
              </div>
              <div id="open_edit_pullrequest" class="pull-right action_button">${_('Edit')}</div>
              <div id="close_edit_pullrequest" class="pull-right action_button" style="display: none;padding: 0">${_('Cancel')}</div>
            %endif
        </div>

        <div id="summary" class="fields pr-details-content">
           <div class="field">
            <div class="label-summary">
                <label>${_('Source')}:</label>
            </div>
            <div class="input">
                <div class="pr-origininfo">
                    ## branch link is only valid if it is a branch
                    <span class="tag">
                      %if c.pull_request.source_ref_parts.type == 'branch':
                        <a href="${h.route_path('repo_commits', repo_name=c.pull_request.source_repo.repo_name, _query=dict(branch=c.pull_request.source_ref_parts.name))}">${c.pull_request.source_ref_parts.type}: ${c.pull_request.source_ref_parts.name}</a>
                      %else:
                        ${c.pull_request.source_ref_parts.type}: ${c.pull_request.source_ref_parts.name}
                      %endif
                    </span>
                    <span class="clone-url">
                        <a href="${h.route_path('repo_summary', repo_name=c.pull_request.source_repo.repo_name)}">${c.pull_request.source_repo.clone_url()}</a>
                    </span>
                    <br/>
                    % if c.ancestor_commit:
                        ${_('Common ancestor')}:
                        <code><a href="${h.route_path('repo_commit', repo_name=c.target_repo.repo_name, commit_id=c.ancestor_commit.raw_id)}">${h.show_id(c.ancestor_commit)}</a></code>
                    % endif
                </div>
                %if h.is_hg(c.pull_request.source_repo):
                    <% clone_url = 'hg pull -r {} {}'.format(h.short_id(c.source_ref), c.pull_request.source_repo.clone_url()) %>
                %elif h.is_git(c.pull_request.source_repo):
                    <% clone_url = 'git pull {} {}'.format(c.pull_request.source_repo.clone_url(), c.pull_request.source_ref_parts.name) %>
                %endif

                <div class="">
                    <input type="text" class="input-monospace pr-pullinfo" value="${clone_url}" readonly="readonly">
                    <i class="tooltip icon-clipboard clipboard-action pull-right pr-pullinfo-copy" data-clipboard-text="${clone_url}" title="${_('Copy the pull url')}"></i>
                </div>

            </div>
           </div>
           <div class="field">
            <div class="label-summary">
                <label>${_('Target')}:</label>
            </div>
            <div class="input">
                <div class="pr-targetinfo">
                    ## branch link is only valid if it is a branch
                    <span class="tag">
                      %if c.pull_request.target_ref_parts.type == 'branch':
                        <a href="${h.route_path('repo_commits', repo_name=c.pull_request.target_repo.repo_name, _query=dict(branch=c.pull_request.target_ref_parts.name))}">${c.pull_request.target_ref_parts.type}: ${c.pull_request.target_ref_parts.name}</a>
                      %else:
                        ${c.pull_request.target_ref_parts.type}: ${c.pull_request.target_ref_parts.name}
                      %endif
                    </span>
                    <span class="clone-url">
                        <a href="${h.route_path('repo_summary', repo_name=c.pull_request.target_repo.repo_name)}">${c.pull_request.target_repo.clone_url()}</a>
                    </span>
                </div>
            </div>
           </div>

            ## Link to the shadow repository.
            <div class="field">
                <div class="label-summary">
                    <label>${_('Merge')}:</label>
                </div>
                <div class="input">
                    % if not c.pull_request.is_closed() and c.pull_request.shadow_merge_ref:
                        %if h.is_hg(c.pull_request.target_repo):
                            <% clone_url = 'hg clone --update {} {} pull-request-{}'.format(c.pull_request.shadow_merge_ref.name, c.shadow_clone_url, c.pull_request.pull_request_id) %>
                        %elif h.is_git(c.pull_request.target_repo):
                            <% clone_url = 'git clone --branch {} {} pull-request-{}'.format(c.pull_request.shadow_merge_ref.name, c.shadow_clone_url, c.pull_request.pull_request_id) %>
                        %endif
                        <div class="">
                            <input type="text" class="input-monospace pr-mergeinfo" value="${clone_url}" readonly="readonly">
                            <i class="tooltip icon-clipboard clipboard-action pull-right pr-mergeinfo-copy" data-clipboard-text="${clone_url}" title="${_('Copy the clone url')}"></i>
                        </div>
                    % else:
                        <div class="">
                            ${_('Shadow repository data not available')}.
                        </div>
                    % endif
                </div>
            </div>

           <div class="field">
            <div class="label-summary">
                <label>${_('Review')}:</label>
            </div>
            <div class="input">
              %if c.pull_request_review_status:
                <i class="icon-circle review-status-${c.pull_request_review_status}"></i>
                <span class="changeset-status-lbl tooltip">
                  %if c.pull_request.is_closed():
                      ${_('Closed')},
                  %endif
                  ${h.commit_status_lbl(c.pull_request_review_status)}
                </span>
                - ${_ungettext('calculated based on %s reviewer vote', 'calculated based on %s reviewers votes', len(c.pull_request_reviewers)) % len(c.pull_request_reviewers)}
              %endif
            </div>
           </div>
           <div class="field">
            <div class="pr-description-label label-summary" title="${_('Rendered using {} renderer').format(c.renderer)}">
                <label>${_('Description')}:</label>
            </div>
            <div id="pr-desc" class="input">
                <div class="pr-description">${h.render(c.pull_request.description, renderer=c.renderer)}</div>
            </div>
            <div id="pr-desc-edit" class="input textarea editor" style="display: none;">
                <input id="pr-renderer-input" type="hidden" name="description_renderer" value="${c.visual.default_renderer}">
                ${dt.markup_form('pr-description-input', form_text=c.pull_request.description)}
            </div>
           </div>

           <div class="field">
               <div class="label-summary">
                   <label>${_('Versions')}:</label>
               </div>

               <% outdated_comm_count_ver = len(c.inline_versions[None]['outdated']) %>
               <% general_outdated_comm_count_ver = len(c.comment_versions[None]['outdated']) %>

               <div class="pr-versions">
               % if c.show_version_changes:
                   <% outdated_comm_count_ver = len(c.inline_versions[c.at_version_num]['outdated']) %>
                   <% general_outdated_comm_count_ver = len(c.comment_versions[c.at_version_num]['outdated']) %>
                   <a id="show-pr-versions" class="input" onclick="return versionController.toggleVersionView(this)" href="#show-pr-versions"
                        data-toggle-on="${_ungettext('{} version available for this pull request, show it.', '{} versions available for this pull request, show them.', len(c.versions)).format(len(c.versions))}"
                        data-toggle-off="${_('Hide all versions of this pull request')}">
                       ${_ungettext('{} version available for this pull request, show it.', '{} versions available for this pull request, show them.', len(c.versions)).format(len(c.versions))}
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
                                   <input ${'checked="checked"' if c.from_version_num == ver_pr else ''} class="compare-radio-button" type="radio" name="ver_source" value="${ver_pr or 'latest'}" data-ver-pos="${ver_pos}"/>
                                   <input ${'checked="checked"' if c.at_version_num == ver_pr else ''} class="compare-radio-button" type="radio" name="ver_target" value="${ver_pr or 'latest'}" data-ver-pos="${ver_pos}"/>
                               </td>
                               <td>
                                <% review_status = c.review_versions[ver_pr].status if ver_pr in c.review_versions else 'not_reviewed' %>
                                <i class="tooltip icon-circle review-status-${review_status}" title="${_('Your review status at this version')}"></i>
                                </div>
                               </td>
                               <td>
                                   % if c.at_version_num != ver_pr:
                                    <i class="icon-comment"></i>
                                       <code class="tooltip" title="${_('Comment from pull request version v{0}, general:{1} inline:{2}').format(ver_pos, len(c.comment_versions[ver_pr]['at']), len(c.inline_versions[ver_pr]['at']))}">
                                           G:${len(c.comment_versions[ver_pr]['at'])} / I:${len(c.inline_versions[ver_pr]['at'])}
                                       </code>
                                   % endif
                               </td>
                               <td>
                                   ##<code>${ver.source_ref_parts.commit_id[:6]}</code>
                               </td>
                               <td>
                                   ${h.age_component(ver.updated_on, time_is_local=True)}
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
                   <div class="input">
                   ${_('Pull request versions not available')}.
                   </div>
               % endif
               </div>
           </div>

           <div id="pr-save" class="field" style="display: none;">
            <div class="label-summary"></div>
            <div class="input">
              <span id="edit_pull_request" class="btn btn-small no-margin">${_('Save Changes')}</span>
            </div>
           </div>
        </div>
      </div>
      <div>
        ## AUTHOR
        <div class="reviewers-title block-right">
          <div class="pr-details-title">
              ${_('Author of this pull request')}
          </div>
        </div>
        <div class="block-right pr-details-content reviewers">
            <ul class="group_members">
              <li>
                ${self.gravatar_with_user(c.pull_request.author.email, 16, tooltip=True)}
              </li>
            </ul>
        </div>

        ## REVIEW RULES
        <div id="review_rules" style="display: none" class="reviewers-title block-right">
            <div class="pr-details-title">
                ${_('Reviewer rules')}
              %if c.allowed_to_update:
                <span id="close_edit_reviewers" class="block-right action_button last-item" style="display: none;">${_('Close')}</span>
              %endif
            </div>
            <div class="pr-reviewer-rules">
                ## review rules will be appended here, by default reviewers logic
            </div>
            <input id="review_data" type="hidden" name="review_data" value="">
        </div>

        ## REVIEWERS
        <div class="reviewers-title block-right">
          <div class="pr-details-title">
              ${_('Pull request reviewers')}
              %if c.allowed_to_update:
                <span id="open_edit_reviewers" class="block-right action_button last-item">${_('Edit')}</span>
              %endif
          </div>
        </div>
        <div id="reviewers" class="block-right pr-details-content reviewers">

            ## members redering block
            <input type="hidden" name="__start__" value="review_members:sequence">
            <ul id="review_members" class="group_members">

            % for review_obj, member, reasons, mandatory, status in c.pull_request_reviewers:
                <script>
                    var member = ${h.json.dumps(h.reviewer_as_json(member, reasons=reasons, mandatory=mandatory, user_group=review_obj.rule_user_group_data()))|n};
                    var status = "${(status[0][1].status if status else 'not_reviewed')}";
                    var status_lbl = "${h.commit_status_lbl(status[0][1].status if status else 'not_reviewed')}";
                    var allowed_to_update = ${h.json.dumps(c.allowed_to_update)};

                    var entry = renderTemplate('reviewMemberEntry', {
                        'member': member,
                        'mandatory': member.mandatory,
                        'reasons': member.reasons,
                        'allowed_to_update': allowed_to_update,
                        'review_status': status,
                        'review_status_label': status_lbl,
                        'user_group': member.user_group,
                        'create': false
                    });
                    $('#review_members').append(entry)
                </script>

            % endfor

            </ul>

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
  </div>
  <div class="box">
      ##DIFF
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
                        ${_('This pull request cannot be displayed, because one or more commits no longer exist in the source repository.')}
                        ${_('Please update this pull request, push the commits back into the source repository, or consider closing this pull request.')}
                        ${_('Consider doing a {force_refresh_url} in case you think this is an error.').format(force_refresh_url=h.link_to('force refresh', h.current_route_path(request, force_refresh='1')))|n}
                    </div>
                  </div>
                </div>
              % endif

              <div class="compare_view_commits_title">
                  % if not c.compare_mode:

                    % if c.at_version_pos:
                        <h4>
                        ${_('Showing changes at v%d, commenting is disabled.') % c.at_version_pos}
                        </h4>
                    % endif

                    <div class="pull-left">
                      <div class="btn-group">
                          <a
                              class="btn"
                              href="#"
                              onclick="$('.compare_select').show();$('.compare_select_hidden').hide(); return false">
                              ${_ungettext('Expand %s commit','Expand %s commits', len(c.commit_ranges)) % len(c.commit_ranges)}
                          </a>
                          <a
                              class="btn"
                              href="#"
                              onclick="$('.compare_select').hide();$('.compare_select_hidden').show(); return false">
                              ${_ungettext('Collapse %s commit','Collapse %s commits', len(c.commit_ranges)) % len(c.commit_ranges)}
                          </a>
                      </div>
                    </div>

                    <div class="pull-right">
                        % if c.allowed_to_update and not c.pull_request.is_closed():
                          <a id="update_commits" class="btn btn-primary no-margin pull-right">${_('Update commits')}</a>
                        % else:
                          <a class="tooltip btn disabled pull-right" disabled="disabled" title="${_('Update is disabled for current view')}">${_('Update commits')}</a>
                        % endif

                    </div>
                  % endif
              </div>

              % if not c.missing_commits:
                % if c.compare_mode:
                    % if c.at_version:
                    <h4>
                        ${_('Commits and changes between v{ver_from} and {ver_to} of this pull request, commenting is disabled').format(ver_from=c.from_version_pos, ver_to=c.at_version_pos if c.at_version_pos else 'latest')}:
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
                                        <div class="message truncate" id="c-${commit.raw_id}" data-message-raw="${commit.message}">${h.urlify_commit_message(commit.message, c.repo_name)}</div>
                                    </div>
                                </td>
                            </tr>
                              % endif
                            % endfor
                        </table>
                    </div>

                    % endif

                % else:
                    <%include file="/compare/compare_commits.mako" />
                % endif

                <div class="cs_files">
                    <%namespace name="cbdiffs" file="/codeblocks/diffs.mako"/>
                    % if c.at_version:
                        <% c.inline_cnt = len(c.inline_versions[c.at_version_num]['display']) %>
                        <% c.comments = c.comment_versions[c.at_version_num]['display'] %>
                    % else:
                        <% c.inline_cnt = len(c.inline_versions[c.at_version_num]['until']) %>
                        <% c.comments = c.comment_versions[c.at_version_num]['until'] %>
                    % endif

                    <%
                        pr_menu_data = {
                            'outdated_comm_count_ver': outdated_comm_count_ver
                        }
                    %>

                    ${cbdiffs.render_diffset_menu(c.diffset, range_diff_on=c.range_diff_on)}

                    % if c.range_diff_on:
                        % for commit in c.commit_ranges:
                            ${cbdiffs.render_diffset(
                              c.changes[commit.raw_id],
                              commit=commit, use_comments=True,
                              collapse_when_files_over=5,
                              disable_new_comments=True,
                              deleted_files_comments=c.deleted_files_comments,
                              inline_comments=c.inline_comments,
                              pull_request_menu=pr_menu_data)}
                        % endfor
                    % else:
                        ${cbdiffs.render_diffset(
                          c.diffset, use_comments=True,
                          collapse_when_files_over=30,
                          disable_new_comments=not c.allowed_to_comment,
                          deleted_files_comments=c.deleted_files_comments,
                          inline_comments=c.inline_comments,
                          pull_request_menu=pr_menu_data)}
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
        ${_('Comments')} ${len(c.comments)}
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
        ## merge status, and merge action
        <div class="pull-request-merge">
            <%include file="/pullrequests/pullrequest_merge_checks.mako"/>
        </div>

        ## main comment form and it status
        ${comment.comments(h.route_path('pullrequest_comment_create', repo_name=c.repo_name,
                                        pull_request_id=c.pull_request.pull_request_id),
                           c.pull_request_review_status,
                           is_pull_request=True, change_status=c.allowed_to_change_status)}
      %endif

      <script type="text/javascript">
        if (location.hash) {
          var result = splitDelimitedHash(location.hash);
            var line = $('html').find(result.loc);
            // show hidden comments if we use location.hash
            if (line.hasClass('comment-general')) {
                $(line).show();
            } else if (line.hasClass('comment-inline')) {
                $(line).show();
                var $cb = $(line).closest('.cb');
                $cb.removeClass('cb-collapsed')
            }
            if (line.length > 0){
                offsetScroll(line, 70);
            }
        }

        versionController = new VersionController();
        versionController.init();

        reviewersController = new ReviewersController();
        commitsController = new CommitsController();

        $(function(){

            // custom code mirror
            var codeMirrorInstance = $('#pr-description-input').get(0).MarkupForm.cm;

            var PRDetails = {
              editButton: $('#open_edit_pullrequest'),
              closeButton: $('#close_edit_pullrequest'),
              deleteButton: $('#delete_pullrequest'),
              viewFields: $('#pr-desc, #pr-title'),
              editFields: $('#pr-desc-edit, #pr-title-edit, #pr-save'),

              init: function() {
                var that = this;
                this.editButton.on('click', function(e) { that.edit(); });
                this.closeButton.on('click', function(e) { that.view(); });
              },

              edit: function(event) {
                this.viewFields.hide();
                this.editButton.hide();
                this.deleteButton.hide();
                this.closeButton.show();
                this.editFields.show();
                codeMirrorInstance.refresh();
              },

              view: function(event) {
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

              init: function() {
                var self = this;
                this.editButton.on('click', function(e) { self.edit(); });
                this.closeButton.on('click', function(e) { self.close(); });
              },

              edit: function(event) {
                this.editButton.hide();
                this.closeButton.show();
                this.addButton.show();
                this.removeButtons.css('visibility', 'visible');
                // review rules
                reviewersController.loadReviewRules(
                    ${c.pull_request.reviewer_data_json | n});
              },

              close: function(event) {
                this.editButton.show();
                this.closeButton.hide();
                this.addButton.hide();
                this.removeButtons.css('visibility', 'hidden');
                // hide review rules
                reviewersController.hideReviewRules()
              }
            };

            PRDetails.init();
            ReviewersPanel.init();

            showOutdated = function(self){
                $('.comment-inline.comment-outdated').show();
                $('.filediff-outdated').show();
                $('.showOutdatedComments').hide();
                $('.hideOutdatedComments').show();
            };

            hideOutdated = function(self){
                $('.comment-inline.comment-outdated').hide();
                $('.filediff-outdated').hide();
                $('.hideOutdatedComments').hide();
                $('.showOutdatedComments').show();
            };

            refreshMergeChecks = function(){
                var loadUrl = "${request.current_route_path(_query=dict(merge_checks=1))}";
                $('.pull-request-merge').css('opacity', 0.3);
                $('.action-buttons-extra').css('opacity', 0.3);

                $('.pull-request-merge').load(
                    loadUrl, function() {
                        $('.pull-request-merge').css('opacity', 1);

                        $('.action-buttons-extra').css('opacity', 1);
                    }
                );
            };

            closePullRequest = function (status) {
                // inject closing flag
                $('.action-buttons-extra').append('<input type="hidden" class="close-pr-input" id="close_pull_request" value="1">');
                $(generalCommentForm.statusChange).select2("val", status).trigger('change');
                $(generalCommentForm.submitForm).submit();
            };

            $('#show-outdated-comments').on('click', function(e){
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

            $('.show-inline-comments').on('change', function(e){
                var show = 'none';
                var target = e.currentTarget;
                if(target.checked){
                    show = ''
                }
                var boxid = $(target).attr('id_for');
                var comments = $('#{0} .inline-comments'.format(boxid));
                var fn_display = function(idx){
                   $(this).css('display', show);
                };
                $(comments).each(fn_display);
                var btns = $('#{0} .inline-comments-button'.format(boxid));
                $(btns).each(fn_display);
            });

            $('#merge_pull_request_form').submit(function() {
                if (!$('#merge_pull_request').attr('disabled')) {
                    $('#merge_pull_request').attr('disabled', 'disabled');
                }
                return true;
            });

            $('#edit_pull_request').on('click', function(e){
                var title = $('#pr-title-input').val();
                var description = codeMirrorInstance.getValue();
                var renderer = $('#pr-renderer-input').val();
                editPullRequest(
                    "${c.repo_name}", "${c.pull_request.pull_request_id}",
                    title, description, renderer);
            });

            $('#update_pull_request').on('click', function(e){
                $(this).attr('disabled', 'disabled');
                $(this).addClass('disabled');
                $(this).html(_gettext('Saving...'));
                reviewersController.updateReviewers(
                    "${c.repo_name}", "${c.pull_request.pull_request_id}");
            });

            $('#update_commits').on('click', function(e){
                var isDisabled = !$(e.currentTarget).attr('disabled');
                $(e.currentTarget).attr('disabled', 'disabled');
                $(e.currentTarget).addClass('disabled');
                $(e.currentTarget).removeClass('btn-primary');
                $(e.currentTarget).text(_gettext('Updating...'));
                if(isDisabled){
                    updateCommits(
                        "${c.repo_name}", "${c.pull_request.pull_request_id}");
                }
            });
            // fixing issue with caches on firefox
            $('#update_commits').removeAttr("disabled");

            $('.show-inline-comments').on('click', function(e){
                var boxid = $(this).attr('data-comment-id');
                var button = $(this);

                if(button.hasClass("comments-visible")) {
                  $('#{0} .inline-comments'.format(boxid)).each(function(index){
                    $(this).hide();
                  });
                  button.removeClass("comments-visible");
                } else {
                  $('#{0} .inline-comments'.format(boxid)).each(function(index){
                    $(this).show();
                  });
                  button.addClass("comments-visible");
                }
            });

            // register submit callback on commentForm form to track TODOs
            window.commentFormGlobalSubmitSuccessCallback = function(){
                refreshMergeChecks();
            };

            ReviewerAutoComplete('#user');

        })
      </script>

  </div>
</div>

</%def>
