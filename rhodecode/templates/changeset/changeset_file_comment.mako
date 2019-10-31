## -*- coding: utf-8 -*-
## usage:
## <%namespace name="comment" file="/changeset/changeset_file_comment.mako"/>
## ${comment.comment_block(comment)}
##
<%namespace name="base" file="/base/base.mako"/>

<%def name="comment_block(comment, inline=False)">
  <% pr_index_ver = comment.get_index_version(getattr(c, 'versions', [])) %>
  <% latest_ver = len(getattr(c, 'versions', [])) %>
  % if inline:
      <% outdated_at_ver = comment.outdated_at_version(getattr(c, 'at_version_num', None)) %>
  % else:
      <% outdated_at_ver = comment.older_than_version(getattr(c, 'at_version_num', None)) %>
  % endif


  <div class="comment
             ${'comment-inline' if inline else 'comment-general'}
             ${'comment-outdated' if outdated_at_ver else 'comment-current'}"
       id="comment-${comment.comment_id}"
       line="${comment.line_no}"
       data-comment-id="${comment.comment_id}"
       data-comment-type="${comment.comment_type}"
       data-comment-line-no="${comment.line_no}"
       data-comment-inline=${h.json.dumps(inline)}
       style="${'display: none;' if outdated_at_ver else ''}">

      <div class="meta">
          <div class="comment-type-label">
              <div class="comment-label ${comment.comment_type or 'note'}" id="comment-label-${comment.comment_id}" title="line: ${comment.line_no}">
              % if comment.comment_type == 'todo':
                  % if comment.resolved:
                      <div class="resolved tooltip" title="${_('Resolved by comment #{}').format(comment.resolved.comment_id)}">
                          <a href="#comment-${comment.resolved.comment_id}">${comment.comment_type}</a>
                      </div>
                  % else:
                      <div class="resolved tooltip" style="display: none">
                          <span>${comment.comment_type}</span>
                      </div>
                      <div class="resolve tooltip" onclick="return Rhodecode.comments.createResolutionComment(${comment.comment_id});" title="${_('Click to resolve this comment')}">
                        ${comment.comment_type}
                      </div>
                  % endif
              % else:
                  % if comment.resolved_comment:
                    fix
                    <a href="#comment-${comment.resolved_comment.comment_id}" onclick="Rhodecode.comments.scrollToComment($('#comment-${comment.resolved_comment.comment_id}'), 0, ${h.json.dumps(comment.resolved_comment.outdated)})">
                        <span style="text-decoration: line-through">#${comment.resolved_comment.comment_id}</span>
                    </a>
                  % else:
                    ${comment.comment_type or 'note'}
                  % endif
              % endif
              </div>
          </div>

          <div class="author ${'author-inline' if inline else 'author-general'}">
              ${base.gravatar_with_user(comment.author.email, 16, tooltip=True)}
          </div>
          <div class="date">
              ${h.age_component(comment.modified_at, time_is_local=True)}
          </div>
          % if inline:
              <span></span>
          % else:
              <div class="status-change">
                  % if comment.pull_request:
                      <a href="${h.route_path('pullrequest_show',repo_name=comment.pull_request.target_repo.repo_name,pull_request_id=comment.pull_request.pull_request_id)}">
                          % if comment.status_change:
                              ${_('pull request #%s') % comment.pull_request.pull_request_id}:
                          % else:
                              ${_('pull request #%s') % comment.pull_request.pull_request_id}
                          % endif
                      </a>
                  % else:
                      % if comment.status_change:
                          ${_('Status change on commit')}:
                      % endif
                  % endif
              </div>
          % endif

          % if comment.status_change:
            <i class="icon-circle review-status-${comment.status_change[0].status}"></i>
            <div title="${_('Commit status')}" class="changeset-status-lbl">
                 ${comment.status_change[0].status_lbl}
            </div>
          % endif

          <a class="permalink" href="#comment-${comment.comment_id}"> &para;</a>

          <div class="comment-links-block">
              % if comment.pull_request and comment.pull_request.author.user_id == comment.author.user_id:
                <span class="tag authortag tooltip" title="${_('Pull request author')}">
                ${_('author')}
                </span>
                |
              % endif
            % if inline:
                  <div class="pr-version-inline">
                    <a href="${request.current_route_path(_query=dict(version=comment.pull_request_version_id), _anchor='comment-{}'.format(comment.comment_id))}">
                    % if outdated_at_ver:
                        <code class="pr-version-num" title="${_('Outdated comment from pull request version v{0}, latest v{1}').format(pr_index_ver, latest_ver)}">
                            outdated ${'v{}'.format(pr_index_ver)} |
                        </code>
                    % elif pr_index_ver:
                        <code class="pr-version-num" title="${_('Comment from pull request version v{0}, latest v{1}').format(pr_index_ver, latest_ver)}">
                            ${'v{}'.format(pr_index_ver)} |
                        </code>
                    % endif
                    </a>
                  </div>
            % else:
                % if comment.pull_request_version_id and pr_index_ver:
                    |
                    <div class="pr-version">
                      % if comment.outdated:
                        <a href="?version=${comment.pull_request_version_id}#comment-${comment.comment_id}">
                            ${_('Outdated comment from pull request version v{0}, latest v{1}').format(pr_index_ver, latest_ver)}
                        </a>
                      % else:
                        <div title="${_('Comment from pull request version v{0}, latest v{1}').format(pr_index_ver, latest_ver)}">
                            <a href="${h.route_path('pullrequest_show',repo_name=comment.pull_request.target_repo.repo_name,pull_request_id=comment.pull_request.pull_request_id, version=comment.pull_request_version_id)}">
                            <code class="pr-version-num">
                                ${'v{}'.format(pr_index_ver)}
                            </code>
                            </a>
                        </div>
                      % endif
                    </div>
                % endif
            % endif

            ## show delete comment if it's not a PR (regular comments) or it's PR that is not closed
            ## only super-admin, repo admin OR comment owner can delete, also hide delete if currently viewed comment is outdated
            %if not outdated_at_ver and (not comment.pull_request or (comment.pull_request and not comment.pull_request.is_closed())):
               ## permissions to delete
               %if c.is_super_admin or h.HasRepoPermissionAny('repository.admin')(c.repo_name) or comment.author.user_id == c.rhodecode_user.user_id:
                  ## TODO: dan: add edit comment here
                  <a onclick="return Rhodecode.comments.deleteComment(this);" class="delete-comment"> ${_('Delete')}</a>
               %else:
                  <button class="btn-link" disabled="disabled"> ${_('Delete')}</button>
               %endif
            %else:
               <button class="btn-link" disabled="disabled"> ${_('Delete')}</button>
            %endif

            % if outdated_at_ver:
               | <a onclick="return Rhodecode.comments.prevOutdatedComment(this);" class="prev-comment"> ${_('Prev')}</a>
               | <a onclick="return Rhodecode.comments.nextOutdatedComment(this);" class="next-comment"> ${_('Next')}</a>
            % else:
               | <a onclick="return Rhodecode.comments.prevComment(this);" class="prev-comment"> ${_('Prev')}</a>
               | <a onclick="return Rhodecode.comments.nextComment(this);" class="next-comment"> ${_('Next')}</a>
            % endif

          </div>
      </div>
      <div class="text">
          ${h.render(comment.text, renderer=comment.renderer, mentions=True)}
      </div>

  </div>
</%def>

## generate main comments
<%def name="generate_comments(comments, include_pull_request=False, is_pull_request=False)">
  <div class="general-comments" id="comments">
    %for comment in comments:
        <div id="comment-tr-${comment.comment_id}">
          ## only render comments that are not from pull request, or from
          ## pull request and a status change
          %if not comment.pull_request or (comment.pull_request and comment.status_change) or include_pull_request:
          ${comment_block(comment)}
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
  <form ${'id="{}"'.format(form_id) if form_id else '' |n} action="#" method="GET">

    <div class="comment-area">
        <div class="comment-area-header">
            <ul class="nav-links clearfix">
                <li class="active">
                    <a href="#edit-btn" tabindex="-1" id="edit-btn_${lineno_id}">${_('Write')}</a>
                </li>
                <li class="">
                    <a href="#preview-btn" tabindex="-1" id="preview-btn_${lineno_id}">${_('Preview')}</a>
                </li>
                <li class="pull-right">
                    <select class="comment-type" id="comment_type_${lineno_id}" name="comment_type">
                        % for val in c.visual.comment_types:
                            <option value="${val}">${val.upper()}</option>
                        % endfor
                    </select>
                </li>
            </ul>
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
                <div class="toolbar-text">
                  ${(_('Comments parsed using %s syntax with %s, and %s actions support.') % (
                           ('<a href="%s">%s</a>' % (h.route_url('%s_help' % c.visual.default_renderer), c.visual.default_renderer.upper())),
                           ('<span class="tooltip" title="%s">@mention</span>' % _('Use @username inside this text to send notification to this RhodeCode user')),
                           ('<span class="tooltip" title="%s">`/`</span>' % _('Start typing with / for certain actions to be triggered via text box.'))
                       )
                    )|n}
                </div>

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

        ## inject extra inputs into the form
        % if form_extras and isinstance(form_extras, (list, tuple)):
            <div id="comment_form_extras">
                % for form_ex_el in form_extras:
                    ${form_ex_el|n}
                % endfor
            </div>
        % endif

        <div class="action-buttons">
            ## inline for has a file, and line-number together with cancel hide button.
            % if form_type == 'inline':
                <input type="hidden" name="f_path" value="{0}">
                <input type="hidden" name="line" value="${lineno_id}">
                <button type="button" class="cb-comment-cancel" onclick="return Rhodecode.comments.cancelComment(this);">
                ${_('Cancel')}
                </button>
            % endif

            % if form_type != 'inline':
                <div class="action-buttons-extra"></div>
            % endif

            ${h.submit('save', _('Comment'), class_='btn btn-success comment-button-input')}

        </div>
    </div>

  </form>

</%def>