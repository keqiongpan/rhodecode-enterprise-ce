
<div id="codeblock" class="browserblock">
    <div class="browser-header">
        <div class="browser-nav">

            <div class="files-quick-filter">

                <ul class="files-filter-box">

                    <li class="files-filter-box-path">
                        <span class="tag">
                        ${h.get_last_path_part(c.file)}
                        </span>
                    </li>

                    <li class="files-filter-box-input">
                        <input onkeydown="NodeFilter.initFilter(event)" class="init" type="text" name="filter" size="25" id="node_filter" autocomplete="off">
                    </li>

                </ul>

            </div>

            <div class="info_box">

              <div class="info_box_elem previous">
                  <a id="prev_commit_link" data-commit-id="${c.prev_commit.raw_id}" class=" ${('disabled' if c.url_prev == '#' else '')}" href="${c.url_prev}" title="${_('Previous commit')}"><i class="icon-left"></i></a>
              </div>

              ${h.hidden('refs_filter')}

              <div class="info_box_elem next">
                  <a id="next_commit_link" data-commit-id="${c.next_commit.raw_id}" class=" ${('disabled' if c.url_next == '#' else '')}" href="${c.url_next}" title="${_('Next commit')}"><i class="icon-right"></i></a>
              </div>
            </div>

            % if h.HasRepoPermissionAny('repository.write','repository.admin')(c.repo_name):
              <div title="${_('Add New File')}" class="btn btn-primary new-file">
                <a href="${h.route_path('repo_files_add_file',repo_name=c.repo_name,commit_id=c.commit.raw_id,f_path=c.f_path, _anchor='edit')}">
                    ${_('Add File')}</a>
              </div>
            % endif
            % if c.enable_downloads:
              <% at_path = '{}.zip'.format(request.GET.get('at') or c.commit.raw_id[:6]) %>
              <div title="${_('Download tree at {}').format(at_path)}" class="btn btn-default new-file">
                <a href="${h.route_path('repo_archivefile',repo_name=c.repo_name, fname='{}.zip'.format(c.commit.raw_id))}">
                    ${_('Download tree at {}').format(at_path)}
                </a>
              </div>
            % endif

        </div>

    </div>
    ## file tree is computed from caches, and filled in
    <div id="file-tree">
    ${c.file_tree |n}
    </div>

</div>
