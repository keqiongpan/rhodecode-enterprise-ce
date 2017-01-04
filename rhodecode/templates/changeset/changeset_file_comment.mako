## -*- coding: utf-8 -*-
## usage:
## <%namespace name="comment" file="/changeset/changeset_file_comment.mako"/>
## ${comment.comment_block(comment)}
##
<%namespace name="base" file="/base/base.mako"/>

<%def name="comment_block(comment, inline=False)">
  <% outdated_at_ver = comment.outdated_at_version(getattr(c, 'at_version', None)) %>

  <div class="comment
             ${'comment-inline' if inline else ''}
             ${'comment-outdated' if outdated_at_ver else 'comment-current'}"
       id="comment-${comment.comment_id}"
       line="${comment.line_no}"
       data-comment-id="${comment.comment_id}"
       style="${'display: none;' if outdated_at_ver else ''}">

      <div class="meta">
          <div class="author">
              ${base.gravatar_with_user(comment.author.email, 16)}
          </div>
          <div class="date">
              ${h.age_component(comment.modified_at, time_is_local=True)}
          </div>
          <div class="status-change">
              % if comment.pull_request:
                  % if comment.outdated:
                      <a href="?version=${comment.pull_request_version_id}#comment-${comment.comment_id}">
                        ${_('Outdated comment from pull request version {}').format(comment.pull_request_version_id)}
                      </a>
                  % else:
                      <a href="${h.url('pullrequest_show',repo_name=comment.pull_request.target_repo.repo_name,pull_request_id=comment.pull_request.pull_request_id)}">
                          %if comment.status_change:
                              ${_('Vote on pull request #%s') % comment.pull_request.pull_request_id}:
                          %else:
                              ${_('Comment on pull request #%s') % comment.pull_request.pull_request_id}
                          %endif
                      </a>
                  % endif
              % else:
                  % if comment.status_change:
                      ${_('Status change on commit')}:
                  % else:
                      ${_('Comment on commit')}
                  % endif
              % endif
          </div>
          %if comment.status_change:
            <div class="${'flag_status %s' % comment.status_change[0].status}"></div>
            <div title="${_('Commit status')}" class="changeset-status-lbl">
                 ${comment.status_change[0].status_lbl}
            </div>
          %endif
          <a class="permalink" href="#comment-${comment.comment_id}"> &para;</a>

          <div class="comment-links-block">
            ## show delete comment if it's not a PR (regular comments) or it's PR that is not closed
            ## only super-admin, repo admin OR comment owner can delete, also hide delete if currently viewed comment is outdated
            %if not outdated_at_ver and (not comment.pull_request or (comment.pull_request and not comment.pull_request.is_closed())):
               ## permissions to delete
               %if h.HasPermissionAny('hg.admin')() or h.HasRepoPermissionAny('repository.admin')(c.repo_name) or comment.author.user_id == c.rhodecode_user.user_id:
                  ## TODO: dan: add edit comment here
                  <a onclick="return Rhodecode.comments.deleteComment(this);" class="delete-comment"> ${_('Delete')}</a>
               %else:
                  <button class="btn-link" disabled="disabled"> ${_('Delete')}</button>
               %endif
            %else:
               <button class="btn-link" disabled="disabled"> ${_('Delete')}</button>
            %endif

            %if not outdated_at_ver:
               | <a onclick="return Rhodecode.comments.prevComment(this);" class="prev-comment"> ${_('Prev')}</a>
               | <a onclick="return Rhodecode.comments.nextComment(this);" class="next-comment"> ${_('Next')}</a>
            %endif

          </div>
      </div>
      <div class="text">
          ${comment.render(mentions=True)|n}
      </div>

  </div>
</%def>
## generate main comments
<%def name="generate_comments(include_pull_request=False, is_pull_request=False)">
  <div id="comments">
    %for comment in c.comments:
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

## MAIN COMMENT FORM
<%def name="comments(post_url, cur_status, is_pull_request=False, is_compare=False, change_status=True, form_extras=None)">

%if is_compare:
  <% form_id = "comments_form_compare" %>
%else:
  <% form_id = "comments_form" %>
%endif


%if is_pull_request:
<div class="pull-request-merge">
    %if c.allowed_to_merge:
    <div class="pull-request-wrap">
        <div class="pull-right">
          ${h.secure_form(url('pullrequest_merge', repo_name=c.repo_name, pull_request_id=c.pull_request.pull_request_id), id='merge_pull_request_form')}
          <span data-role="merge-message">${c.pr_merge_msg} ${c.approval_msg if c.approval_msg else ''}</span>
          <% merge_disabled = ' disabled' if c.pr_merge_status is False else '' %>
          <input type="submit" id="merge_pull_request" value="${_('Merge Pull Request')}" class="btn${merge_disabled}"${merge_disabled}>
          ${h.end_form()}
        </div>
    </div>
    %else:
    <div class="pull-request-wrap">
        <div class="pull-right">
          <span>${c.pr_merge_msg} ${c.approval_msg if c.approval_msg else ''}</span>
        </div>
    </div>
    %endif
</div>
%endif
<div class="comments">
    <%
      if is_pull_request:
        placeholder = _('Leave a comment on this Pull Request.')
      elif is_compare:
        placeholder = _('Leave a comment on all commits in this range.')
      else:
        placeholder = _('Leave a comment on this Commit.')
    %>
    % if c.rhodecode_user.username != h.DEFAULT_USER:
    <div class="comment-form ac">
        ${h.secure_form(post_url, id_=form_id)}
        <div class="comment-area">
            <div class="comment-area-header">
                <ul class="nav-links clearfix">
                    <li class="active">
                        <a href="#edit-btn" tabindex="-1" id="edit-btn">${_('Write')}</a>
                    </li>
                    <li class="">
                        <a href="#preview-btn" tabindex="-1" id="preview-btn">${_('Preview')}</a>
                    </li>
                </ul>
            </div>

            <div class="comment-area-write" style="display: block;">
                <div id="edit-container">
                    <textarea id="text" name="text" class="comment-block-ta ac-input"></textarea>
                </div>
                <div id="preview-container" class="clearfix" style="display: none;">
                    <div id="preview-box" class="preview-box"></div>
                </div>
            </div>

            <div class="comment-area-footer">
                <div class="toolbar">
                    <div class="toolbar-text">
                      ${(_('Comments parsed using %s syntax with %s support.') % (
                             ('<a href="%s">%s</a>' % (h.url('%s_help' % c.visual.default_renderer), c.visual.default_renderer.upper())),
                               ('<span  class="tooltip" title="%s">@mention</span>' % _('Use @username inside this text to send notification to this RhodeCode user'))
                           )
                        )|n
                       }
                    </div>
                </div>
            </div>
        </div>

        <div id="comment_form_extras">
        %if form_extras and isinstance(form_extras, (list, tuple)):
            % for form_ex_el in form_extras:
                ${form_ex_el|n}
            % endfor
        %endif
        </div>
        <div class="comment-footer">
          %if change_status:
          <div class="status_box">
              <select id="change_status" name="changeset_status">
                  <option></option> # Placeholder
                  %for status,lbl in c.commit_statuses:
                  <option value="${status}" data-status="${status}">${lbl}</option>
                      %if is_pull_request and change_status and status in ('approved', 'rejected'):
                          <option value="${status}_closed" data-status="${status}">${lbl} & ${_('Closed')}</option>
                      %endif
                  %endfor
              </select>
          </div>
          %endif
          <div class="action-buttons">
              <div class="comment-button">${h.submit('save', _('Comment'), class_="btn btn-success comment-button-input")}</div>
          </div>
        </div>
          ${h.end_form()}
    </div>
    % else:
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
                      <a href="${h.route_path('login', _query={'came_from': h.url.current()})}">${_('Login now')}</a>
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

</div>

<script>
    // init active elements of commentForm
    var commitId = templateContext.commit_data.commit_id;
    var pullRequestId = templateContext.pull_request_data.pull_request_id;
    var lineNo;

    var mainCommentForm = new CommentForm(
            "#${form_id}", commitId, pullRequestId, lineNo, true);

    mainCommentForm.cm.setOption('placeholder', "${placeholder}");

    mainCommentForm.initStatusChangeSelector();
    bindToggleButtons();
</script>
</%def>
