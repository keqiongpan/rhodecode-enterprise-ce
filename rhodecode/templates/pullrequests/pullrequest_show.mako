<%inherit file="/base/base.mako"/>

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
    AJAX_COMMENT_DELETE_URL = "${url('pullrequest_comment_delete',repo_name=c.repo_name,comment_id='__COMMENT_ID__')}";
    templateContext.pull_request_data.pull_request_id = ${c.pull_request.pull_request_id};
</script>
<div class="box">

  <div class="title">
    ${self.repo_page_title(c.rhodecode_db_repo)}
  </div>

  ${self.breadcrumbs()}

  <div class="box pr-summary">

      <div class="summary-details block-left">
        <% summary = lambda n:{False:'summary-short'}.get(n) %>
        <div class="pr-details-title">
            <a href="${h.url('pull_requests_global', pull_request_id=c.pull_request.pull_request_id)}">${_('Pull request #%s') % c.pull_request.pull_request_id}</a> ${_('From')} ${h.format_date(c.pull_request.created_on)}
            %if c.allowed_to_update:
              <div id="delete_pullrequest" class="pull-right action_button ${'' if c.allowed_to_delete else 'disabled' }" style="clear:inherit;padding: 0">
                  % if c.allowed_to_delete:
                      ${h.secure_form(url('pullrequest_delete', repo_name=c.pull_request.target_repo.repo_name, pull_request_id=c.pull_request.pull_request_id),method='delete')}
                          ${h.submit('remove_%s' % c.pull_request.pull_request_id, _('Delete'),
                        class_="btn btn-link btn-danger",onclick="return confirm('"+_('Confirm to delete this pull request')+"');")}
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
                <label>${_('Origin')}:</label>
            </div>
            <div class="input">
                <div class="pr-origininfo">
                    ## branch link is only valid if it is a branch
                    <span class="tag">
                      %if c.pull_request.source_ref_parts.type == 'branch':
                        <a href="${h.url('changelog_home', repo_name=c.pull_request.source_repo.repo_name, branch=c.pull_request.source_ref_parts.name)}">${c.pull_request.source_ref_parts.type}: ${c.pull_request.source_ref_parts.name}</a>
                      %else:
                        ${c.pull_request.source_ref_parts.type}: ${c.pull_request.source_ref_parts.name}
                      %endif
                    </span>
                    <span class="clone-url">
                        <a href="${h.url('summary_home', repo_name=c.pull_request.source_repo.repo_name)}">${c.pull_request.source_repo.clone_url()}</a>
                    </span>
                </div>
                <div class="pr-pullinfo">
                     %if h.is_hg(c.pull_request.source_repo):
                        <input type="text"  value="hg pull -r ${h.short_id(c.source_ref)} ${c.pull_request.source_repo.clone_url()}" readonly="readonly">
                     %elif h.is_git(c.pull_request.source_repo):
                        <input type="text"  value="git pull ${c.pull_request.source_repo.clone_url()} ${c.pull_request.source_ref_parts.name}" readonly="readonly">
                     %endif
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
                        <a href="${h.url('changelog_home', repo_name=c.pull_request.target_repo.repo_name, branch=c.pull_request.target_ref_parts.name)}">${c.pull_request.target_ref_parts.type}: ${c.pull_request.target_ref_parts.name}</a>
                      %else:
                        ${c.pull_request.target_ref_parts.type}: ${c.pull_request.target_ref_parts.name}
                      %endif
                    </span>
                    <span class="clone-url">
                        <a href="${h.url('summary_home', repo_name=c.pull_request.target_repo.repo_name)}">${c.pull_request.target_repo.clone_url()}</a>
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
                    <div class="pr-mergeinfo">
                        %if h.is_hg(c.pull_request.target_repo):
                            <input type="text"  value="hg clone -u ${c.pull_request.shadow_merge_ref.name} ${c.shadow_clone_url} pull-request-${c.pull_request.pull_request_id}" readonly="readonly">
                        %elif h.is_git(c.pull_request.target_repo):
                            <input type="text"  value="git clone --branch ${c.pull_request.shadow_merge_ref.name} ${c.shadow_clone_url} pull-request-${c.pull_request.pull_request_id}" readonly="readonly">
                        %endif
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
                <div class="${'flag_status %s' % c.pull_request_review_status} tooltip pull-left"></div>
                <span class="changeset-status-lbl tooltip">
                  %if c.pull_request.is_closed():
                      ${_('Closed')},
                  %endif
                  ${h.commit_status_lbl(c.pull_request_review_status)}
                </span>
                - ${ungettext('calculated based on %s reviewer vote', 'calculated based on %s reviewers votes', len(c.pull_request_reviewers)) % len(c.pull_request_reviewers)}
              %endif
            </div>
           </div>
           <div class="field">
            <div class="pr-description-label label-summary">
                <label>${_('Description')}:</label>
            </div>
            <div id="pr-desc" class="input">
                <div class="pr-description">${h.urlify_commit_message(c.pull_request.description, c.repo_name)}</div>
            </div>
            <div id="pr-desc-edit" class="input textarea editor" style="display: none;">
                <textarea id="pr-description-input" size="30">${c.pull_request.description}</textarea>
            </div>
           </div>

           <div class="field">
                <div class="label-summary">
                    <label>${_('Versions')} (${len(c.versions)+1}):</label>
                </div>

               <div class="pr-versions">
               % if c.show_version_changes:
                   <table>
                       ## CURRENTLY SELECT PR VERSION
                       <tr class="version-pr" style="display: ${'' if c.at_version_num is None else 'none'}">
                           <td>
                               % if c.at_version_num is None:
                                <i class="icon-ok link"></i>
                               % else:
                                <i class="icon-comment"></i>
                                   <code>
                                   ${len(c.comment_versions[None]['at'])}/${len(c.inline_versions[None]['at'])}
                                   </code>
                               % endif
                           </td>
                           <td>
                               <code>
                               % if c.versions:
                                <a href="${h.url.current(version='latest')}">${_('latest')}</a>
                               % else:
                                ${_('initial')}
                               % endif
                               </code>
                           </td>
                           <td>
                               <code>${c.pull_request_latest.source_ref_parts.commit_id[:6]}</code>
                           </td>
                           <td>
                               ${_('created')} ${h.age_component(c.pull_request_latest.updated_on)}
                           </td>
                           <td align="right">
                               % if c.versions and c.at_version_num in [None, 'latest']:
                               <span id="show-pr-versions" class="btn btn-link" onclick="$('.version-pr').show(); $(this).hide(); return false">${_('Show all versions')}</span>
                               % endif
                           </td>
                       </tr>

                       ## SHOW ALL VERSIONS OF PR
                       <% ver_pr = None %>

                       % for data in reversed(list(enumerate(c.versions, 1))):
                           <% ver_pos = data[0] %>
                           <% ver = data[1] %>
                           <% ver_pr = ver.pull_request_version_id %>

                           <tr class="version-pr" style="display: ${'' if c.at_version_num == ver_pr else 'none'}">
                               <td>
                                   % if c.at_version_num == ver_pr:
                                    <i class="icon-ok link"></i>
                                   % else:
                                    <i class="icon-comment"></i>
                                       <code class="tooltip" title="${_('Comment from pull request version {0}, general:{1} inline{2}').format(ver_pos, len(c.comment_versions[ver_pr]['at']), len(c.inline_versions[ver_pr]['at']))}">
                                           ${len(c.comment_versions[ver_pr]['at'])}/${len(c.inline_versions[ver_pr]['at'])}
                                       </code>
                                   % endif
                               </td>
                               <td>
                                    <code>
                                        <a href="${h.url.current(version=ver_pr)}">v${ver_pos}</a>
                                    </code>
                               </td>
                               <td>
                                   <code>${ver.source_ref_parts.commit_id[:6]}</code>
                               </td>
                               <td>
                                   ${_('created')} ${h.age_component(ver.updated_on)}
                               </td>
                               <td align="right">
                                   % if c.at_version_num == ver_pr:
                                   <span id="show-pr-versions" class="btn btn-link" onclick="$('.version-pr').show(); $(this).hide(); return false">${_('Show all versions')}</span>
                                   % endif
                               </td>
                           </tr>
                       % endfor

                       ## show comment/inline comments summary
                       <tr>
                           <td>
                           </td>

                           <td colspan="4" style="border-top: 1px dashed #dbd9da">
                            <% outdated_comm_count_ver = len(c.inline_versions[c.at_version_num]['outdated']) %>
                            <% general_outdated_comm_count_ver = len(c.comment_versions[c.at_version_num]['outdated']) %>


                            % if c.at_version:
                                <% inline_comm_count_ver = len(c.inline_versions[c.at_version_num]['display']) %>
                                <% general_comm_count_ver = len(c.comment_versions[c.at_version_num]['display']) %>
                                ${_('Comments at this version')}:
                            % else:
                                <% inline_comm_count_ver = len(c.inline_versions[c.at_version_num]['until']) %>
                                <% general_comm_count_ver = len(c.comment_versions[c.at_version_num]['until']) %>
                                ${_('Comments for this pull request')}:
                            % endif

                            %if general_comm_count_ver:
                                <a href="#comments">${_("%d General ") % general_comm_count_ver}</a>
                            %else:
                                ${_("%d General ") % general_comm_count_ver}
                            %endif

                            %if inline_comm_count_ver:
                               , <a href="#" onclick="return Rhodecode.comments.nextComment();" id="inline-comments-counter">${_("%d Inline") % inline_comm_count_ver}</a>
                            %else:
                               , ${_("%d Inline") % inline_comm_count_ver}
                            %endif

                            %if outdated_comm_count_ver:
                              , <a href="#" onclick="showOutdated(); Rhodecode.comments.nextOutdatedComment(); return false;">${_("%d Outdated") % outdated_comm_count_ver}</a>
                                <a href="#" class="showOutdatedComments" onclick="showOutdated(this); return false;"> | ${_('show outdated comments')}</a>
                                <a href="#" class="hideOutdatedComments" style="display: none" onclick="hideOutdated(this); return false;"> | ${_('hide outdated comments')}</a>
                            %else:
                              , ${_("%d Outdated") % outdated_comm_count_ver}
                            %endif
                           </td>
                       </tr>

                       <tr>
                           <td></td>
                           <td colspan="4">
                           % if c.at_version:
<pre>
Changed commits:
 * added: ${len(c.changes.added)}
 * removed: ${len(c.changes.removed)}

% if not (c.file_changes.added+c.file_changes.modified+c.file_changes.removed):
No file changes found
% else:
Changed files:
 %for file_name in c.file_changes.added:
 * A <a href="#${'a_' + h.FID('', file_name)}">${file_name}</a>
 %endfor
 %for file_name in c.file_changes.modified:
 * M <a href="#${'a_' + h.FID('', file_name)}">${file_name}</a>
 %endfor
 %for file_name in c.file_changes.removed:
 * R ${file_name}
 %endfor
% endif
</pre>
                           % endif
                           </td>
                       </tr>
                   </table>
               % else:
                   ${_('Pull request versions not available')}.
               % endif
               </div>
           </div>

           <div id="pr-save" class="field" style="display: none;">
            <div class="label-summary"></div>
            <div class="input">
              <span id="edit_pull_request" class="btn btn-small">${_('Save Changes')}</span>
            </div>
           </div>
        </div>
      </div>
      <div>
        ## AUTHOR
        <div class="reviewers-title block-right">
          <div class="pr-details-title">
              ${_('Author')}
          </div>
        </div>
        <div class="block-right pr-details-content reviewers">
            <ul class="group_members">
              <li>
                ${self.gravatar_with_user(c.pull_request.author.email, 16)}
              </li>
            </ul>
        </div>
        ## REVIEWERS
        <div class="reviewers-title block-right">
          <div class="pr-details-title">
              ${_('Pull request reviewers')}
              %if c.allowed_to_update:
                <span id="open_edit_reviewers" class="block-right action_button">${_('Edit')}</span>
                <span id="close_edit_reviewers" class="block-right action_button" style="display: none;">${_('Close')}</span>
              %endif
          </div>
        </div>
        <div id="reviewers" class="block-right pr-details-content reviewers">
          ## members goes here !
            <input type="hidden" name="__start__" value="review_members:sequence">
            <ul id="review_members" class="group_members">
            %for member,reasons,status in c.pull_request_reviewers:
              <li id="reviewer_${member.user_id}">
                <div class="reviewers_member">
                    <div class="reviewer_status tooltip" title="${h.tooltip(h.commit_status_lbl(status[0][1].status if status else 'not_reviewed'))}">
                      <div class="${'flag_status %s' % (status[0][1].status if status else 'not_reviewed')} pull-left reviewer_member_status"></div>
                    </div>
                  <div id="reviewer_${member.user_id}_name" class="reviewer_name">
                    ${self.gravatar_with_user(member.email, 16)}
                  </div>
                  <input type="hidden" name="__start__" value="reviewer:mapping">
                  <input type="hidden" name="__start__" value="reasons:sequence">
                  %for reason in reasons:
                  <div class="reviewer_reason">- ${reason}</div>
                  <input type="hidden" name="reason" value="${reason}">

                  %endfor
                  <input type="hidden" name="__end__" value="reasons:sequence">
                  <input id="reviewer_${member.user_id}_input" type="hidden" value="${member.user_id}" name="user_id" />
                  <input type="hidden" name="__end__" value="reviewer:mapping">
                  %if c.allowed_to_update:
                  <div class="reviewer_member_remove action_button" onclick="removeReviewMember(${member.user_id}, true)" style="visibility: hidden;">
                      <i class="icon-remove-sign" ></i>
                  </div>
                  %endif
                </div>
              </li>
            %endfor
            </ul>
            <input type="hidden" name="__end__" value="review_members:sequence">
          %if not c.pull_request.is_closed():
          <div id="add_reviewer_input" class='ac' style="display: none;">
            %if c.allowed_to_update:
            <div class="reviewer_ac">
               ${h.text('user', class_='ac-input', placeholder=_('Add reviewer'))}
               <div id="reviewers_container"></div>
            </div>
            <div>
             <span id="update_pull_request" class="btn btn-small">${_('Save Changes')}</span>
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
                    </div>
                  </div>
                </div>
              % endif
                <div class="compare_view_commits_title">

                    <div class="pull-left">
                      <div class="btn-group">
                          <a
                              class="btn"
                              href="#"
                              onclick="$('.compare_select').show();$('.compare_select_hidden').hide(); return false">
                              ${ungettext('Expand %s commit','Expand %s commits', len(c.commit_ranges)) % len(c.commit_ranges)}
                          </a>
                          <a
                              class="btn"
                              href="#"
                              onclick="$('.compare_select').hide();$('.compare_select_hidden').show(); return false">
                              ${ungettext('Collapse %s commit','Collapse %s commits', len(c.commit_ranges)) % len(c.commit_ranges)}
                          </a>
                      </div>
                    </div>

                    <div class="pull-right">
                        % if c.allowed_to_update and not c.pull_request.is_closed():
                          <a id="update_commits" class="btn btn-primary pull-right">${_('Update commits')}</a>
                        % else:
                          <a class="tooltip btn disabled pull-right" disabled="disabled" title="${_('Update is disabled for current view')}">${_('Update commits')}</a>
                        % endif

                    </div>

                </div>

              % if not c.missing_commits:
                <%include file="/compare/compare_commits.mako" />
                <div class="cs_files">
                    <%namespace name="cbdiffs" file="/codeblocks/diffs.mako"/>
                    ${cbdiffs.render_diffset_menu()}
                    ${cbdiffs.render_diffset(
                      c.diffset, use_comments=True,
                      collapse_when_files_over=30,
                      disable_new_comments=not c.allowed_to_comment,
                      deleted_files_comments=c.deleted_files_comments)}
                </div>
              % else:
                  ## skipping commits we need to clear the view for missing commits
                  <div style="clear:both;"></div>
              % endif

          </div>
      </div>

      ## template for inline comment form
      <%namespace name="comment" file="/changeset/changeset_file_comment.mako"/>

      ## render general comments

      <div id="comment-tr-show">
          <div class="comment">
            % if general_outdated_comm_count_ver:
            <div class="meta">
                % if general_outdated_comm_count_ver == 1:
                    ${_('there is {num} general comment from older versions').format(num=general_outdated_comm_count_ver)},
                    <a href="#" onclick="$('.comment-general.comment-outdated').show(); $(this).parent().hide(); return false;">${_('show it')}</a>
                % else:
                    ${_('there are {num} general comments from older versions').format(num=general_outdated_comm_count_ver)},
                    <a href="#" onclick="$('.comment-general.comment-outdated').show(); $(this).parent().hide(); return false;">${_('show them')}</a>
                % endif
            </div>
            % endif
          </div>
      </div>

      ${comment.generate_comments(c.comments, include_pull_request=True, is_pull_request=True)}

      % if not c.pull_request.is_closed():
        ## merge status, and merge action
        <div class="pull-request-merge">
            <%include file="/pullrequests/pullrequest_merge_checks.mako"/>
        </div>

        ## main comment form and it status
        ${comment.comments(h.url('pullrequest_comment', repo_name=c.repo_name,
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

        $(function(){
            ReviewerAutoComplete('user');
            // custom code mirror
            var codeMirrorInstance = initPullRequestsCodeMirror('#pr-description-input');

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
              addButton: $('#add_reviewer_input'),
              removeButtons: $('.reviewer_member_remove'),

              init: function() {
                var that = this;
                this.editButton.on('click', function(e) { that.edit(); });
                this.closeButton.on('click', function(e) { that.close(); });
              },

              edit: function(event) {
                this.editButton.hide();
                this.closeButton.show();
                this.addButton.show();
                this.removeButtons.css('visibility', 'visible');
              },

              close: function(event) {
                this.editButton.show();
                this.closeButton.hide();
                this.addButton.hide();
                this.removeButtons.css('visibility', 'hidden');
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
                var loadUrl = "${h.url.current(merge_checks=1)}";
                $('.pull-request-merge').css('opacity', 0.3);
                $('.pull-request-merge').load(
                    loadUrl,function() {
                        $('.pull-request-merge').css('opacity', 1);
                    }
                );
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
                editPullRequest(
                    "${c.repo_name}", "${c.pull_request.pull_request_id}",
                    title, description);
            });

            $('#update_pull_request').on('click', function(e){
                updateReviewers(undefined, "${c.repo_name}", "${c.pull_request.pull_request_id}");
            });

            $('#update_commits').on('click', function(e){
                var isDisabled = !$(e.currentTarget).attr('disabled');
                $(e.currentTarget).text(_gettext('Updating...'));
                $(e.currentTarget).attr('disabled', 'disabled');
                if(isDisabled){
                    updateCommits("${c.repo_name}", "${c.pull_request.pull_request_id}");
                }

            });
            // fixing issue with caches on firefox
            $('#update_commits').removeAttr("disabled");

            $('#close_pull_request').on('click', function(e){
                closePullRequest("${c.repo_name}", "${c.pull_request.pull_request_id}");
            });

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

        })
      </script>

  </div>
</div>

</%def>
