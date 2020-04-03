<%namespace name="base" file="/base/base.mako"/>

<%
    if request.GET.get('at'):
        query={'at': request.GET.get('at')}
    else:
        query=None
%>
<div id="file-tree-wrapper" class="browser-body ${('full-load' if c.full_load else '')}">
    <table class="code-browser rctable repo_summary">
        <thead>
            <tr>
                <th>${_('Name')}</th>
                <th>${_('Size')}</th>
                <th>${_('Modified')}</th>
                <th>${_('Last Commit')}</th>
                <th>${_('Author')}</th>
            </tr>
        </thead>

        <tbody id="tbody">
        <tr>
            <td colspan="5">
                ${h.files_breadcrumbs(c.repo_name,c.commit.raw_id,c.file.path, request.GET.get('at'), limit_items=True)}
            </td>
        </tr>

        <% has_files = False %>
        % for cnt,node in enumerate(c.file):
        <% has_files = True %>
        <tr class="parity${(cnt % 2)}">
            <td class="td-componentname">
            % if node.is_submodule():
              <span class="submodule-dir">
                % if node.url.startswith('http://') or node.url.startswith('https://'):
                  <a href="${node.url}">
                      <i class="icon-directory browser-dir"></i>${node.name}
                  </a>
                % else:
                  <i class="icon-directory browser-dir"></i>${node.name}
                % endif
              </span>
            % else:
              <a href="${h.route_path('repo_files',repo_name=c.repo_name,commit_id=c.commit.raw_id,f_path=h.safe_unicode(node.path), _query=query)}">
                <i class="${('icon-file-text browser-file' if node.is_file() else 'icon-directory browser-dir')}"></i>${node.name}
              </a>
            % endif
            </td>
            %if node.is_file():
              <td class="td-size" data-attr-name="size">
                  % if c.full_load:
                    <span data-size="${node.size}">${h.format_byte_size_binary(node.size)}</span>
                  % else:
                    ${_('Loading ...')}
                  % endif
              </td>
              <td class="td-time" data-attr-name="modified_at">
                  % if c.full_load:
                    <span data-date="${node.last_commit.date}">${h.age_component(node.last_commit.date)}</span>
                  % endif
              </td>
              <td class="td-hash" data-attr-name="commit_id">
                  % if c.full_load:
                  <div class="tooltip-hovercard" data-hovercard-alt="${node.last_commit.message}" data-hovercard-url="${h.route_path('hovercard_repo_commit', repo_name=c.repo_name, commit_id=node.last_commit.raw_id)}">
                      <pre data-commit-id="${node.last_commit.raw_id}">r${node.last_commit.idx}:${node.last_commit.short_id}</pre>
                  </div>
                  % endif
              </td>
              <td class="td-user" data-attr-name="author">
                  % if c.full_load:
                  <span data-author="${node.last_commit.author}">${h.gravatar_with_user(request, node.last_commit.author, tooltip=True)|n}</span>
                  % endif
              </td>
            %else:
              <td></td>
              <td></td>
              <td></td>
              <td></td>
            %endif
          </tr>
        % endfor

        % if not has_files:
        <tr>
            <td colspan="5">
                ##empty-dir mostly SVN
                &nbsp;
            </td>
        </tr>
        % endif

        </tbody>
        <tbody id="tbody_filtered"></tbody>
    </table>
</div>
