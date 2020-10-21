## snippet for sidebar elements
## usage:
##    <%namespace name="sidebar" file="/base/sidebar.mako"/>
##    ${sidebar.comments_table()}
<%namespace name="base" file="/base/base.mako"/>

<%def name="comments_table(comments, counter_num, todo_comments=False, existing_ids=None, is_pr=True)">
    <%
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

        existing_ids = existing_ids or []

    %>

    <table class="todo-table ${cls_}" data-total-count="${len(comments)}" data-counter="${counter_num}">

     % for loop_obj, comment_obj in h.looper(reversed(sorted(comments, key=sorter))):
         <%
            display = ''
            _cls = ''
            ## Extra precaution to not show drafts in the sidebar for todo/comments
            if comment_obj.draft:
                continue
         %>


         <%
             comment_ver_index = comment_obj.get_index_version(getattr(c, 'versions', []))
             prev_comment_ver_index = 0
             if loop_obj.previous:
                prev_comment_ver_index = loop_obj.previous.get_index_version(getattr(c, 'versions', []))

             ver_info = None
             if getattr(c, 'versions', []):
                ver_info = c.versions[comment_ver_index-1] if comment_ver_index else None
         %>
         <% hidden_at_ver = comment_obj.outdated_at_version_js(c.at_version_num) %>
         <% is_from_old_ver = comment_obj.older_than_version_js(c.at_version_num) %>
         <%
         if (prev_comment_ver_index > comment_ver_index):
           comments_ver_divider = comment_ver_index
         else:
            comments_ver_divider = None
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

          % if not todo_comments and comments_ver_divider:
          <tr class="old-comments-marker">
              <td colspan="3">
                  % if ver_info:
                    <code>v${comments_ver_divider} ${h.age_component(ver_info.created_on, time_is_local=True, tooltip=False)}</code>
                  % else:
                    <code>v${comments_ver_divider}</code>
                  % endif
              </td>
          </tr>

          % endif

          <tr class="${_cls}" style="display: ${display};" data-sidebar-comment-id="${comment_obj.comment_id}">
              <td class="td-todo-number">
                  <%
                    version_info = ''
                    if is_pr:
                        version_info = (' made in older version (v{})'.format(comment_ver_index) if is_from_old_ver == 'true' else ' made in this version')
                  %>
                  ## new comments, since refresh
                  % if existing_ids and comment_obj.comment_id not in existing_ids:
                      <div class="tooltip" style="position: absolute; left: 8px; color: #682668" title="New comment">
                          !
                      </div>
                  % endif

                  <%
                      data = h.json.dumps({
                            'comment_id': comment_obj.comment_id,
                            'version_info': version_info,
                            'file_name': comment_obj.f_path,
                            'line_no': comment_obj.line_no,
                            'outdated': comment_obj.outdated,
                            'inline': comment_obj.is_inline,
                            'is_todo': comment_obj.is_todo,
                            'created_on': h.format_date(comment_obj.created_on),
                            'datetime': '{}{}'.format(comment_obj.created_on, h.get_timezone(comment_obj.created_on, time_is_local=True)),
                            'review_status': (comment_obj.review_status or '')
                      })

                      if comment_obj.outdated:
                          icon = 'icon-comment-toggle'
                      elif comment_obj.is_inline:
                          icon = 'icon-code'
                      else:
                          icon = 'icon-comment'
                  %>

                  <i id="commentHovercard${comment_obj.comment_id}"
                     class="${icon} tooltip-hovercard"
                     data-hovercard-url="javascript:sidebarComment(${comment_obj.comment_id})"
                     data-comment-json-b64='${h.b64(data)}'>
                  </i>

              </td>

              <td class="td-todo-gravatar">
                  ${base.gravatar(comment_obj.author.email, 16, user=comment_obj.author, tooltip=True, extra_class=['no-margin'])}
              </td>
              <td class="todo-comment-text-wrapper">
                  <div class="todo-comment-text ${('todo-resolved' if comment_obj.resolved else '')}">
                      <a class="${('todo-resolved' if comment_obj.resolved else '')} permalink"
                         href="#comment-${comment_obj.comment_id}"
                         onclick="return Rhodecode.comments.scrollToComment($('#comment-${comment_obj.comment_id}'), 0, ${hidden_at_ver})">

                         ${h.chop_at_smart(comment_obj.text, '\n', suffix_if_chopped='...')}
                      </a>
                  </div>
              </td>
          </tr>
     % endfor

    </table>

</%def>