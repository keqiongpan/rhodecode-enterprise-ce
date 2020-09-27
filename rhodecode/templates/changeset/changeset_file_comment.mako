## -*- coding: utf-8 -*-
## usage:
## <%namespace name="comment" file="/changeset/changeset_file_comment.mako"/>
## ${comment.comment_block(comment)}
##

<%!
    from rhodecode.lib import html_filters
%>

<%namespace name="base" file="/base/base.mako"/>
<%def name="comment_block(comment, inline=False, active_pattern_entries=None)">

    <%
        from rhodecode.model.comment import CommentsModel
        comment_model = CommentsModel()
    %>
  <% comment_ver = comment.get_index_version(getattr(c, 'versions', [])) %>
  <% latest_ver = len(getattr(c, 'versions', [])) %>

  % if inline:
      <% outdated_at_ver = comment.outdated_at_version(c.at_version_num) %>
  % else:
      <% outdated_at_ver = comment.older_than_version(c.at_version_num) %>
  % endif

  <div class="comment
             ${'comment-inline' if inline else 'comment-general'}
             ${'comment-outdated' if outdated_at_ver else 'comment-current'}"
       id="comment-${comment.comment_id}"
       line="${comment.line_no}"
       data-comment-id="${comment.comment_id}"
       data-comment-type="${comment.comment_type}"
       data-comment-renderer="${comment.renderer}"
       data-comment-text="${comment.text | html_filters.base64,n}"
       data-comment-line-no="${comment.line_no}"
       data-comment-inline=${h.json.dumps(inline)}
       style="${'display: none;' if outdated_at_ver else ''}">

      <div class="meta">
          <div class="comment-type-label">
              <div class="comment-label ${comment.comment_type or 'note'}" id="comment-label-${comment.comment_id}">

              ## TODO COMMENT
              % if comment.comment_type == 'todo':
                  % if comment.resolved:
                      <div class="resolved tooltip" title="${_('Resolved by comment #{}').format(comment.resolved.comment_id)}">
                          <i class="icon-flag-filled"></i>
                          <a href="#comment-${comment.resolved.comment_id}">${comment.comment_type}</a>
                      </div>
                  % else:
                      <div class="resolved tooltip" style="display: none">
                          <span>${comment.comment_type}</span>
                      </div>
                      <div class="resolve tooltip" onclick="return Rhodecode.comments.createResolutionComment(${comment.comment_id});" title="${_('Click to create resolution comment.')}">
                        <i class="icon-flag-filled"></i>
                        ${comment.comment_type}
                      </div>
                  % endif
              ## NOTE COMMENT
              % else:
                  ## RESOLVED NOTE
                  % if comment.resolved_comment:
                    <div class="tooltip" title="${_('This comment resolves TODO #{}').format(comment.resolved_comment.comment_id)}">
                        fix
                        <a href="#comment-${comment.resolved_comment.comment_id}" onclick="Rhodecode.comments.scrollToComment($('#comment-${comment.resolved_comment.comment_id}'), 0, ${h.json.dumps(comment.resolved_comment.outdated)})">
                            <span style="text-decoration: line-through">#${comment.resolved_comment.comment_id}</span>
                        </a>
                    </div>
                  ## STATUS CHANGE NOTE
                  % elif not comment.is_inline and comment.status_change:
                    <%
                        if comment.pull_request:
                            status_change_title = 'Status of review for pull request !{}'.format(comment.pull_request.pull_request_id)
                        else:
                            status_change_title = 'Status of review for commit {}'.format(h.short_id(comment.commit_id))
                    %>

                    <i class="icon-circle review-status-${comment.review_status}"></i>
                    <div class="changeset-status-lbl tooltip" title="${status_change_title}">
                         ${comment.review_status_lbl}
                    </div>
                  % else:
                    <div>
                        <i class="icon-comment"></i>
                        ${(comment.comment_type or 'note')}
                    </div>
                  % endif
              % endif

              </div>
          </div>

          % if 0 and comment.status_change:
          <div class="pull-left">
              <span  class="tag authortag tooltip" title="${_('Status from pull request.')}">
                  <a href="${h.route_path('pullrequest_show',repo_name=comment.pull_request.target_repo.repo_name,pull_request_id=comment.pull_request.pull_request_id)}">
                      ${'!{}'.format(comment.pull_request.pull_request_id)}
                  </a>
              </span>
          </div>
          % endif

          <div class="author ${'author-inline' if inline else 'author-general'}">
              ${base.gravatar_with_user(comment.author.email, 16, tooltip=True)}
          </div>

          <div class="date">
              ${h.age_component(comment.modified_at, time_is_local=True)}
          </div>

          % if comment.pull_request and comment.pull_request.author.user_id == comment.author.user_id:
            <span class="tag authortag tooltip" title="${_('Pull request author')}">
            ${_('author')}
            </span>
          % endif

          <%
          comment_version_selector = 'comment_versions_{}'.format(comment.comment_id)
          %>

          % if comment.history:
              <div class="date">

                 <input id="${comment_version_selector}" name="${comment_version_selector}"
                        type="hidden"
                        data-last-version="${comment.history[-1].version}">

                 <script type="text/javascript">

                    var preLoadVersionData = [
                       % for comment_history in comment.history:
                            {
                                id: ${comment_history.comment_history_id},
                                text: 'v${comment_history.version}',
                                action: function () {
                                    Rhodecode.comments.showVersion(
                                        "${comment.comment_id}",
                                        "${comment_history.comment_history_id}"
                                    )
                                },
                                comment_version: "${comment_history.version}",
                                comment_author_username: "${comment_history.author.username}",
                                comment_author_gravatar: "${h.gravatar_url(comment_history.author.email, 16)}",
                                comment_created_on: '${h.age_component(comment_history.created_on, time_is_local=True)}',
                            },
                       % endfor
                        ]
                    initVersionSelector("#${comment_version_selector}", {results: preLoadVersionData});

                  </script>

              </div>
          % else:
              <div class="date" style="display: none">
                <input id="${comment_version_selector}" name="${comment_version_selector}"
                       type="hidden"
                       data-last-version="0">
              </div>
          %endif

          <div class="comment-links-block">

            % if inline:
                    <a class="pr-version-inline" href="${request.current_route_path(_query=dict(version=comment.pull_request_version_id), _anchor='comment-{}'.format(comment.comment_id))}">
                    % if outdated_at_ver:
                        <code class="tooltip pr-version-num" title="${_('Outdated comment from pull request version v{0}, latest v{1}').format(comment_ver, latest_ver)}">outdated ${'v{}'.format(comment_ver)}</code>
                        <code class="action-divider">|</code>
                    % elif comment_ver:
                        <code class="tooltip pr-version-num" title="${_('Comment from pull request version v{0}, latest v{1}').format(comment_ver, latest_ver)}">${'v{}'.format(comment_ver)}</code>
                        <code class="action-divider">|</code>
                    % endif
                    </a>
            % else:
                % if comment_ver:

                      % if comment.outdated:
                        <a class="pr-version"
                           href="?version=${comment.pull_request_version_id}#comment-${comment.comment_id}"
                        >
                            ${_('Outdated comment from pull request version v{0}, latest v{1}').format(comment_ver, latest_ver)}
                        </a>
                        <code class="action-divider">|</code>
                      % else:
                        <a class="tooltip pr-version"
                           title="${_('Comment from pull request version v{0}, latest v{1}').format(comment_ver, latest_ver)}"
                           href="${h.route_path('pullrequest_show',repo_name=comment.pull_request.target_repo.repo_name,pull_request_id=comment.pull_request.pull_request_id, version=comment.pull_request_version_id)}"
                        >
                            <code class="pr-version-num">${'v{}'.format(comment_ver)}</code>
                        </a>
                        <code class="action-divider">|</code>
                      % endif

                % endif
            % endif

            <details class="details-reset details-inline-block">
              <summary class="noselect"><i class="icon-options cursor-pointer"></i></summary>
              <details-menu class="details-dropdown">

                <div class="dropdown-item">
                    ${_('Comment')} #${comment.comment_id}
                    <span class="pull-right icon-clipboard clipboard-action" data-clipboard-text="${comment_model.get_url(comment,request, permalink=True, anchor='comment-{}'.format(comment.comment_id))}" title="${_('Copy permalink')}"></span>
                </div>

                ## show delete comment if it's not a PR (regular comments) or it's PR that is not closed
                ## only super-admin, repo admin OR comment owner can delete, also hide delete if currently viewed comment is outdated
                %if not outdated_at_ver and (not comment.pull_request or (comment.pull_request and not comment.pull_request.is_closed())):
                   ## permissions to delete
                   %if comment.immutable is False and (c.is_super_admin or h.HasRepoPermissionAny('repository.admin')(c.repo_name) or comment.author.user_id == c.rhodecode_user.user_id):
                       <div class="dropdown-divider"></div>
                       <div class="dropdown-item">
                        <a onclick="return Rhodecode.comments.editComment(this);" class="btn btn-link btn-sm edit-comment">${_('Edit')}</a>
                       </div>
                       <div class="dropdown-item">
                        <a onclick="return Rhodecode.comments.deleteComment(this);" class="btn btn-link btn-sm btn-danger delete-comment">${_('Delete')}</a>
                       </div>
                   %else:
                      <div class="dropdown-divider"></div>
                      <div class="dropdown-item">
                        <a class="tooltip edit-comment link-disabled" disabled="disabled" title="${_('Action unavailable')}">${_('Edit')}</a>
                      </div>
                      <div class="dropdown-item">
                        <a class="tooltip edit-comment link-disabled" disabled="disabled" title="${_('Action unavailable')}">${_('Delete')}</a>
                      </div>
                   %endif
                %else:
                    <div class="dropdown-divider"></div>
                    <div class="dropdown-item">
                      <a class="tooltip edit-comment link-disabled" disabled="disabled" title="${_('Action unavailable')}">${_('Edit')}</a>
                    </div>
                    <div class="dropdown-item">
                      <a class="tooltip edit-comment link-disabled" disabled="disabled" title="${_('Action unavailable')}">${_('Delete')}</a>
                    </div>
                %endif
              </details-menu>
            </details>

            <code class="action-divider">|</code>
            % if outdated_at_ver:
                <a onclick="return Rhodecode.comments.prevOutdatedComment(this);" class="tooltip prev-comment" title="${_('Jump to the previous outdated comment')}"> <i class="icon-angle-left"></i> </a>
                <a onclick="return Rhodecode.comments.nextOutdatedComment(this);" class="tooltip next-comment" title="${_('Jump to the next outdated comment')}"> <i class="icon-angle-right"></i></a>
            % else:
                <a onclick="return Rhodecode.comments.prevComment(this);" class="tooltip prev-comment" title="${_('Jump to the previous comment')}"> <i class="icon-angle-left"></i></a>
                <a onclick="return Rhodecode.comments.nextComment(this);" class="tooltip next-comment" title="${_('Jump to the next comment')}"> <i class="icon-angle-right"></i></a>
            % endif

          </div>
      </div>
      <div class="text">
          ${h.render(comment.text, renderer=comment.renderer, mentions=True, repo_name=getattr(c, 'repo_name', None), active_pattern_entries=active_pattern_entries)}
      </div>

  </div>
</%def>

## generate main comments
<%def name="generate_comments(comments, include_pull_request=False, is_pull_request=False)">
  <%
    active_pattern_entries = h.get_active_pattern_entries(getattr(c, 'repo_name', None))
  %>

  <div class="general-comments" id="comments">
    %for comment in comments:
        <div id="comment-tr-${comment.comment_id}">
          ## only render comments that are not from pull request, or from
          ## pull request and a status change
          %if not comment.pull_request or (comment.pull_request and comment.status_change) or include_pull_request:
          ${comment_block(comment, active_pattern_entries=active_pattern_entries)}
          %endif
        </div>
    %endfor
    ## to anchor ajax comments
    <div id="injected_page_comments"></div>
  </div>
</%def>


<%def name="comments(post_url, cur_status, is_pull_request=False, is_compare=False, change_status=True, form_extras=None)">

<div class="comments">
    <%
      if is_pull_request:
        placeholder = _('Leave a comment on this Pull Request.')
      elif is_compare:
        placeholder = _('Leave a comment on {} commits in this range.').format(len(form_extras))
      else:
        placeholder = _('Leave a comment on this Commit.')
    %>

    % if c.rhodecode_user.username != h.DEFAULT_USER:
    <div class="js-template" id="cb-comment-general-form-template">
        ## template generated for injection
        ${comment_form(form_type='general', review_statuses=c.commit_statuses, form_extras=form_extras)}
    </div>

    <div id="cb-comment-general-form-placeholder" class="comment-form ac">
        ## inject form here
    </div>
    <script type="text/javascript">
        var lineNo = 'general';
        var resolvesCommentId = null;
        var generalCommentForm = Rhodecode.comments.createGeneralComment(
            lineNo, "${placeholder}", resolvesCommentId);

        // set custom success callback on rangeCommit
        % if is_compare:
            generalCommentForm.setHandleFormSubmit(function(o) {
                var self = generalCommentForm;

                var text = self.cm.getValue();
                var status = self.getCommentStatus();
                var commentType = self.getCommentType();

                if (text === "" && !status) {
                    return;
                }

                // we can pick which commits we want to make the comment by
                // selecting them via click on preview pane, this will alter the hidden inputs
                var cherryPicked = $('#changeset_compare_view_content .compare_select.hl').length > 0;

                var commitIds = [];
                $('#changeset_compare_view_content .compare_select').each(function(el) {
                    var commitId = this.id.replace('row-', '');
                    if ($(this).hasClass('hl') || !cherryPicked) {
                        $("input[data-commit-id='{0}']".format(commitId)).val(commitId);
                        commitIds.push(commitId);
                    } else {
                        $("input[data-commit-id='{0}']".format(commitId)).val('')
                    }
                });

                self.setActionButtonsDisabled(true);
                self.cm.setOption("readOnly", true);
                var postData = {
                    'text': text,
                    'changeset_status': status,
                    'comment_type': commentType,
                    'commit_ids': commitIds,
                    'csrf_token': CSRF_TOKEN
                };

                var submitSuccessCallback = function(o) {
                    location.reload(true);
                };
                var submitFailCallback = function(){
                    self.resetCommentFormState(text)
                };
                self.submitAjaxPOST(
                    self.submitUrl, postData, submitSuccessCallback, submitFailCallback);
            });
        % endif

    </script>
    % else:
    ## form state when not logged in
    <div class="comment-form ac">

        <div class="comment-area">
            <div class="comment-area-header">
                <ul class="nav-links clearfix">
                    <li class="active">
                        <a class="disabled" href="#edit-btn" disabled="disabled" onclick="return false">${_('Write')}</a>
                    </li>
                    <li class="">
                        <a class="disabled" href="#preview-btn" disabled="disabled" onclick="return false">${_('Preview')}</a>
                    </li>
                </ul>
            </div>

            <div class="comment-area-write" style="display: block;">
                <div id="edit-container">
                    <div style="padding: 40px 0">
                      ${_('You need to be logged in to leave comments.')}
                      <a href="${h.route_path('login', _query={'came_from': h.current_route_path(request)})}">${_('Login now')}</a>
                    </div>
                </div>
                <div id="preview-container" class="clearfix" style="display: none;">
                    <div id="preview-box" class="preview-box"></div>
                </div>
            </div>

            <div class="comment-area-footer">
                <div class="toolbar">
                    <div class="toolbar-text">
                    </div>
                </div>
            </div>
        </div>

        <div class="comment-footer">
        </div>

    </div>
    % endif

    <script type="text/javascript">
        bindToggleButtons();
    </script>
</div>
</%def>


<%def name="comment_form(form_type, form_id='', lineno_id='{1}', review_statuses=None, form_extras=None)">

  ## comment injected based on assumption that user is logged in
  <form ${('id="{}"'.format(form_id) if form_id else '') |n} action="#" method="GET">

    <div class="comment-area">
        <div class="comment-area-header">
            <div class="pull-left">
                <ul class="nav-links clearfix">
                    <li class="active">
                        <a href="#edit-btn" tabindex="-1" id="edit-btn_${lineno_id}">${_('Write')}</a>
                    </li>
                    <li class="">
                        <a href="#preview-btn" tabindex="-1" id="preview-btn_${lineno_id}">${_('Preview')}</a>
                    </li>
                </ul>
            </div>
            <div class="pull-right">
                <span class="comment-area-text">${_('Mark as')}:</span>
                <select class="comment-type" id="comment_type_${lineno_id}" name="comment_type">
                    % for val in c.visual.comment_types:
                        <option value="${val}">${val.upper()}</option>
                    % endfor
                </select>
            </div>
        </div>

        <div class="comment-area-write" style="display: block;">
            <div id="edit-container_${lineno_id}">
                <textarea id="text_${lineno_id}" name="text" class="comment-block-ta ac-input"></textarea>
            </div>
            <div id="preview-container_${lineno_id}" class="clearfix" style="display: none;">
                <div id="preview-box_${lineno_id}" class="preview-box"></div>
            </div>
        </div>

        <div class="comment-area-footer comment-attachment-uploader">
            <div class="toolbar">

                <div class="comment-attachment-text">
                    <div class="dropzone-text">
                        ${_("Drag'n Drop files here or")} <span class="link pick-attachment">${_('Choose your files')}</span>.<br>
                    </div>
                    <div class="dropzone-upload" style="display:none">
                        <i class="icon-spin animate-spin"></i> ${_('uploading...')}
                    </div>
                </div>

                ## comments dropzone template, empty on purpose
                <div style="display: none" class="comment-attachment-uploader-template">
                    <div class="dz-file-preview" style="margin: 0">
                        <div class="dz-error-message"></div>
                    </div>
                </div>

            </div>
        </div>
    </div>

    <div class="comment-footer">

        ## inject extra inputs into the form
        % if form_extras and isinstance(form_extras, (list, tuple)):
            <div id="comment_form_extras">
                % for form_ex_el in form_extras:
                    ${form_ex_el|n}
                % endfor
            </div>
        % endif

        <div class="action-buttons">
            % if form_type != 'inline':
                <div class="action-buttons-extra"></div>
            % endif

            <input class="btn btn-success comment-button-input" id="save_${lineno_id}" name="save" type="submit" value="${_('Comment')}">

            ## inline for has a file, and line-number together with cancel hide button.
            % if form_type == 'inline':
                <input type="hidden" name="f_path" value="{0}">
                <input type="hidden" name="line" value="${lineno_id}">
                <button type="button" class="cb-comment-cancel" onclick="return Rhodecode.comments.cancelComment(this);">
                ${_('Cancel')}
                </button>
            % endif
        </div>

        % if review_statuses:
        <div class="status_box">
          <select id="change_status_${lineno_id}" name="changeset_status">
              <option></option> ## Placeholder
              % for status, lbl in review_statuses:
              <option value="${status}" data-status="${status}">${lbl}</option>
                  %if is_pull_request and change_status and status in ('approved', 'rejected'):
                      <option value="${status}_closed" data-status="${status}">${lbl} & ${_('Closed')}</option>
                  %endif
              % endfor
          </select>
        </div>
        % endif

        <div class="toolbar-text">
            <% renderer_url = '<a href="%s">%s</a>' % (h.route_url('%s_help' % c.visual.default_renderer), c.visual.default_renderer.upper()) %>
            ${_('Comments parsed using {} syntax.').format(renderer_url)|n} <br/>
            <span class="tooltip" title="${_('Use @username inside this text to send notification to this RhodeCode user')}">@mention</span>
            ${_('and')}
            <span class="tooltip" title="${_('Start typing with / for certain actions to be triggered via text box.')}">`/` autocomplete</span>
            ${_('actions supported.')}
        </div>
    </div>

  </form>

</%def>