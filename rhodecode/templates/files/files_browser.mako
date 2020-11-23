
<div id="codeblock" class="browserblock">
    <div class="browser-header">
        <div class="browser-nav">

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

            <div class="new-file">
                <div class="btn-group btn-group-actions">
                    <a class="btn btn-primary no-margin" href="${h.route_path('repo_files_add_file',repo_name=c.repo_name,commit_id=c.commit.raw_id,f_path=c.f_path)}">
                        ${_('Add File')}
                    </a>

                    <a class="tooltip btn btn-primary btn-more-option" data-toggle="dropdown" aria-pressed="false" role="button" title="${_('more options')}">
                        <i class="icon-down"></i>
                    </a>

                    <div class="btn-action-switcher-container right-align">
                        <ul class="btn-action-switcher" role="menu" style="min-width: 200px; width: max-content">
                            <li>
                                <a class="action_button" href="${h.route_path('repo_files_upload_file',repo_name=c.repo_name,commit_id=c.commit.raw_id,f_path=c.f_path)}">
                                    <i class="icon-upload"></i>
                                    ${_('Upload File')}
                                </a>
                            </li>
                        </ul>
                    </div>
                </div>
            </div>

            % endif

            % if c.enable_downloads:
              <%
                  at_path = '{}'.format(request.GET.get('at') or c.commit.raw_id[:6])
                  if c.f_path == '/':
                      label = _('Full tree as {}')
                      _query = {'with_hash': '1'}
                  else:
                      label = _('This tree as {}')
                      _query = {'at_path':c.f_path, 'with_hash': '1'}
              %>

                <div class="btn-group btn-group-actions new-file">
                    <a class="archive_link btn btn-default" data-ext=".zip" href="${h.route_path('repo_archivefile',repo_name=c.rhodecode_db_repo.repo_name, fname='{}{}'.format(c.commit.raw_id, '.zip'), _query=_query)}">
                        <i class="icon-download"></i>
                        ${label.format('.zip')}
                    </a>

                    <a class="tooltip btn btn-default btn-more-option" data-toggle="dropdown" aria-pressed="false" role="button" title="${_('more download options')}">
                        <i class="icon-down"></i>
                    </a>

                    <div class="btn-action-switcher-container left-align">
                        <ul class="btn-action-switcher" role="menu" style="min-width: 200px; width: max-content">
                            % for a_type, content_type, extension in h.ARCHIVE_SPECS:
                            % if extension not in ['.zip']:
                            <li>
                                <a class="archive_link" data-ext="${extension}" href="${h.route_path('repo_archivefile',repo_name=c.rhodecode_db_repo.repo_name, fname='{}{}'.format(c.commit.raw_id, extension), _query=_query)}">
                                    <i class="icon-download"></i>
                                    ${label.format(extension)}
                                </a>
                            </li>
                            % endif
                            % endfor
                        </ul>
                    </div>
                </div>
            % endif

            <div class="files-quick-filter">
                <ul class="files-filter-box">
                    <li class="files-filter-box-path">
                        <i class="icon-search"></i>
                    </li>
                    <li class="files-filter-box-input">
                        <input onkeydown="NodeFilter.initFilter(event)" class="init" type="text" placeholder="Quick filter" name="filter" size="25" id="node_filter" autocomplete="off">
                    </li>
                </ul>
            </div>
        </div>

    </div>

    ## file tree is computed from caches, and filled in
    <div id="file-tree">
    ${c.file_tree |n}
    </div>

    %if c.readme_data:
    <div id="readme" class="anchor">
    <div class="box">
        <div class="readme-title" title="${h.tooltip(_('Readme file from commit %s:%s') % (c.rhodecode_db_repo.landing_ref_type, c.rhodecode_db_repo.landing_ref_name))}">
            <div>
                <i class="icon-file-text"></i>
                <a href="${h.route_path('repo_files',repo_name=c.repo_name,commit_id=c.rhodecode_db_repo.landing_ref_name,f_path=c.readme_file)}">
                    ${c.readme_file}
                </a>
            </div>
        </div>
        <div class="readme codeblock">
          <div class="readme_box">
            ${c.readme_data|n}
          </div>
        </div>
    </div>
    </div>
    %endif

</div>
