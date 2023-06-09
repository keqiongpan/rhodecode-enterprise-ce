<%namespace name="sourceblock" file="/codeblocks/source.mako"/>

<%
    at_ref = request.GET.get('at')
    if at_ref:
        query={'at': at_ref}
        default_commit_id = at_ref or c.rhodecode_db_repo.landing_ref_name
    else:
        query=None
        default_commit_id = c.commit.raw_id
%>

<div id="codeblock" class="browserblock">
    <div class="browser-header">
        <div class="browser-nav">
            <div class="pull-left">
                ## loads the history for a file
                ${h.hidden('file_refs_filter')}
            </div>

            <div class="pull-right">

            ## Download
            % if c.lf_node:
              <a class="btn btn-default" href="${h.route_path('repo_file_download',repo_name=c.repo_name,commit_id=c.commit.raw_id,f_path=c.f_path, _query=dict(lf=1))}">
              ${_('Download largefile')}
              </a>
            % else:
              <a  class="btn btn-default" href="${h.route_path('repo_file_download',repo_name=c.repo_name,commit_id=c.commit.raw_id,f_path=c.f_path)}">
              ${_('Download file')}
              </a>
            % endif

            %if h.HasRepoPermissionAny('repository.write','repository.admin')(c.repo_name):
              ## on branch head, can edit files
              %if c.on_branch_head and c.branch_or_raw_id:
                  ## binary files are delete only
                  % if c.file.is_binary:
                    ${h.link_to(_('Edit'), '#Edit', class_="btn btn-default disabled tooltip", title=_('Editing binary files not allowed'))}
                    ${h.link_to(_('Delete'), h.route_path('repo_files_remove_file',repo_name=c.repo_name,commit_id=c.branch_or_raw_id,f_path=c.f_path, _query=query),class_="btn btn-danger")}
                  % else:
                    <a  class="btn btn-default" href="${h.route_path('repo_files_edit_file',repo_name=c.repo_name,commit_id=c.branch_or_raw_id,f_path=c.f_path, _query=query)}">
                        ${_('Edit on branch: ')}<code>${c.branch_name}</code>
                    </a>

                    <a class="btn btn-danger" href="${h.route_path('repo_files_remove_file',repo_name=c.repo_name,commit_id=c.branch_or_raw_id,f_path=c.f_path, _query=query)}">
                        ${_('Delete')}
                    </a>
                  % endif
              ## not on head, forbid all
              % else:
               ${h.link_to(_('Edit'), '#Edit', class_="btn btn-default disabled tooltip", title=_('Editing files allowed only when on branch head commit'))}
               ${h.link_to(_('Delete'), '#Delete', class_="btn btn-default btn-danger disabled tooltip", title=_('Deleting files allowed only when on branch head commit'))}
              % endif
            %endif

          </div>
        </div>
        <div id="file_history_container"></div>

        </div>
    </div>

    <div class="codeblock">
      <div class=" codeblock-header">
        <div class="file-filename">
            <i class="icon-file"></i> ${c.file}
        </div>

        <div class="file-stats">

          <div class="stats-info">
            <span class="stats-first-item">
                % if c.file_size_too_big:
                    0 ${(_('lines'))}
                % else:
                    ${c.file.lines()[0]} ${_ungettext('line', 'lines', c.file.lines()[0])}
                % endif
            </span>

            <span> | ${h.format_byte_size_binary(c.file.size)}</span>
            % if c.lf_node:
            <span title="${_('This file is a pointer to large binary file')}"> | ${_('LargeFile')} ${h.format_byte_size_binary(c.lf_node.size)} </span>
            % endif
            <span>
                | ${c.file.mimetype}
            </span>

            % if not c.file_size_too_big:
            <span> |
                ${h.get_lexer_for_filenode(c.file).__class__.__name__}
            </span>
            % endif

          </div>
        </div>
      </div>

      <div class="path clear-fix">
          <div class="pull-left">
            ${h.files_breadcrumbs(c.repo_name, c.rhodecode_db_repo.repo_type, c.commit.raw_id, c.file.path, c.rhodecode_db_repo.landing_ref_name, request.GET.get('at'))}
          </div>

          <div class="pull-right stats">
                <a id="file_history_overview" href="#loadHistory">
                    ${_('History')}
                </a>
                 |
                %if c.annotate:
                  ${h.link_to(_('Source'), h.route_path('repo_files', repo_name=c.repo_name,commit_id=c.commit.raw_id,f_path=c.f_path))}
                %else:
                  ${h.link_to(_('Annotation'), h.route_path('repo_files:annotated',repo_name=c.repo_name,commit_id=c.commit.raw_id,f_path=c.f_path))}
                %endif
                 | ${h.link_to(_('Raw'), h.route_path('repo_file_raw',repo_name=c.repo_name,commit_id=c.commit.raw_id,f_path=c.f_path))}
                 % if not c.file.is_binary:
                 |<a href="#copySource" onclick="return false;" class="no-grey clipboard-action" data-clipboard-text="${c.file.content}">${_('Copy content')}</a>
                 |<a href="#copyPermaLink" onclick="return false;" class="no-grey clipboard-action" data-clipboard-text="${h.route_url('repo_files', repo_name=c.repo_name,commit_id=c.commit.raw_id,f_path=c.f_path)}">${_('Copy permalink')}</a>
                 % endif

          </div>
          <div class="clear-fix"></div>
      </div>

      <div class="code-body clear-fix ">
        %if c.file.is_binary:
             <% rendered_binary = h.render_binary(c.repo_name, c.file)%>
             % if rendered_binary:
                 <div class="text-center">
                 ${rendered_binary}
                 </div>
             % else:
                 <div>
                  ${_('Binary file ({})').format(c.file.mimetype)}
                 </div>
             % endif
        %else:
            % if c.file_size_too_big:
                ${_('File size {} is bigger then allowed limit {}. ').format(h.format_byte_size_binary(c.file.size), h.format_byte_size_binary(c.visual.cut_off_limit_file))} ${h.link_to(_('Show as raw'),
                h.route_path('repo_file_raw',repo_name=c.repo_name,commit_id=c.commit.raw_id,f_path=c.f_path))}
            % else:
                %if c.renderer and not c.annotate:
                    ## pick relative url based on renderer
                    <%
                        relative_urls = {
                            'raw': h.route_path('repo_file_raw',repo_name=c.repo_name,commit_id=c.commit.raw_id,f_path=c.f_path),
                            'standard': h.route_path('repo_files',repo_name=c.repo_name,commit_id=c.commit.raw_id,f_path=c.f_path),
                        }
                    %>
                    ${h.render(c.file.content, renderer=c.renderer, relative_urls=relative_urls)}
                %else:
                    <table class="cb codehilite">
                    %if c.annotate:
                      <% color_hasher = h.color_hasher() %>
                      %for annotation, lines in c.annotated_lines:
                        ${sourceblock.render_annotation_lines(annotation, lines, color_hasher)}
                      %endfor
                    %else:
                      %for line_num, tokens in enumerate(c.lines, 1):
                        ${sourceblock.render_line(line_num, tokens)}
                      %endfor
                    %endif
                    </table>
                %endif
            % endif
        %endif
    </div>

    </div>

<script type="text/javascript">
% if request.GET.get('mark'):

$(function(){
  $(".codehilite").mark(
      "${request.GET.get('mark')}",
          {
              "className": 'match',
              "accuracy": "complementary",
              "ignorePunctuation": ":._(){}[]!'+=".split(""),
              "each": function(el) {
                  // and also highlight lines !
                  $($(el).closest('tr')).find('td.cb-lineno').addClass('cb-line-selected');
              }
          }
  );

});
% endif
</script>
