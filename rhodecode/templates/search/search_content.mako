<%namespace name="search" file="/search/search.mako"/>

<%def name="highlight_text_file(has_matched_content, file_content, lexer, html_formatter, matching_lines, shown_matching_lines, url, use_hl_filter)">
% if has_matched_content:
    ${h.code_highlight(file_content, lexer, html_formatter, use_hl_filter=use_hl_filter)|n}
% else:
    ${_('No content matched')} <br/>
% endif

%if len(matching_lines) > shown_matching_lines:
<a href="${url}">
  ${len(matching_lines) - shown_matching_lines} ${_('more matches in this file')}
</a>
%endif
</%def>

<div class="search-results">
<% query_mark = c.searcher.query_to_mark(c.cur_query, 'content') %>

%for entry in c.formatted_results:

  <%
    file_content = entry['content_highlight'] or entry['content']
    mimetype = entry.get('mimetype')
    filepath = entry.get('path')
    max_lines = h.safe_int(request.GET.get('max_lines', '10'))
    line_context = h.safe_int(request.GET.get('line_contenxt', '3'))

    match_file_url=h.route_path('repo_files',repo_name=entry['repository'], commit_id=entry.get('commit_id', 'tip'),f_path=entry['f_path'], _query={"mark": query_mark})
    terms = c.cur_query

    if c.searcher.is_es_6:
        # use empty terms so we default to markers usage
        total_lines, matching_lines = h.get_matching_line_offsets(file_content, terms=None)
    else:
        total_lines, matching_lines = h.get_matching_line_offsets(file_content, terms)

    shown_matching_lines = 0
    lines_of_interest = set()
    for line_number in matching_lines:
        if len(lines_of_interest) < max_lines:
            lines_of_interest |= set(range(
                max(line_number - line_context, 0),
                min(line_number + line_context, total_lines + 1)))
            shown_matching_lines += 1
    lexer = h.get_lexer_safe(mimetype=mimetype, filepath=filepath)

    html_formatter = h.SearchContentCodeHtmlFormatter(
        linenos=True,
        cssclass="code-highlight",
        url=match_file_url,
        query_terms=terms,
        only_line_numbers=lines_of_interest
    )

    has_matched_content = len(lines_of_interest) >= 1

  %>
  ## search results are additionally filtered, and this check is just a safe gate
  % if c.rhodecode_user.is_admin or h.HasRepoPermissionAny('repository.write','repository.read','repository.admin')(entry['repository'], 'search results content check'):
      <div class="codeblock">
        <h1>
          <% repo_type = entry.get('repo_type') or h.get_repo_type_by_name(entry.get('repository')) %>
          ${search.repo_icon(repo_type)}
          ${h.link_to(entry['repository'], h.route_path('repo_summary', repo_name=entry['repository']))}
        </h1>

        <div class="codeblock-header">

            <div class="file-filename">
                <i class="icon-file"></i> ${entry['f_path'].split('/')[-1]}
            </div>

            <div class="file-stats">
                <div class="stats-info">
                    <span class="stats-first-item">
                        ${entry.get('lines', 0.)} ${_ungettext('line', 'lines', entry.get('lines', 0.))}
                        (${len(matching_lines)} ${_ungettext('matched', 'matched', len(matching_lines))})
                    </span>
                    <span>
                        % if entry.get('size'):
                          | ${h.format_byte_size_binary(entry['size'])}
                        % endif
                    </span>
                    <span>
                        % if entry.get('mimetype'):
                          | ${entry.get('mimetype', "unknown mimetype")}
                        % endif
                    </span>
                </div>
            </div>
        </div>

        <div class="path clear-fix">
            <div class="pull-left">
                ${h.files_breadcrumbs(entry['repository'], repo_type, entry.get('commit_id', 'tip'), entry['f_path'], linkify_last_item=True)}
            </div>

            <div class="pull-right stats">
##                     <a id="file_history_overview_full" href="${h.route_path('repo_commits_file',repo_name=entry.get('repository',''),commit_id=entry.get('commit_id', 'tip'),f_path=entry.get('f_path',''))}">
##                        ${_('Show Full History')}
##                     </a>
##                     | ${h.link_to(_('Annotation'), h.route_path('repo_files:annotated', repo_name=entry.get('repository',''),commit_id=entry.get('commit_id', 'tip'),f_path=entry.get('f_path','')))}
##                     | ${h.link_to(_('Raw'), h.route_path('repo_file_raw', repo_name=entry.get('repository',''),commit_id=entry.get('commit_id', 'tip'),f_path=entry.get('f_path','')))}
                <div class="search-tags">

                    <% repo_group = entry.get('repository_group')%>
                    ## hiden if in repo group view
                    % if repo_group and not c.repo_group_name:
                    <span class="tag tag8">
                        ${search.repo_group_icon()}
                        <a href="${h.route_path('search_repo_group', repo_group_name=repo_group, _query={'q': c.cur_query})}">${_('Narrow to this repository group')}</a>
                    </span>
                    % endif
                    ## hiden if in repo view
                    % if not c.repo_name:
                    <span class="tag tag8">
                        ${search.repo_icon(repo_type)}
                        <a href="${h.route_path('search_repo', repo_name=entry.get('repo_name'), _query={'q': c.cur_query})}">${_('Narrow to this repository')}</a>
                    </span>
                    % endif
                </div>

            </div>
            <div class="clear-fix"></div>
        </div>


        <div class="code-body search-code-body clear-fix">
            ${highlight_text_file(
                has_matched_content=has_matched_content,
                file_content=file_content,
                lexer=lexer,
                html_formatter=html_formatter,
                matching_lines=matching_lines,
                shown_matching_lines=shown_matching_lines,
                url=match_file_url,
                use_hl_filter=c.searcher.is_es_6
            )}
        </div>

      </div>
    % endif
%endfor
</div>
%if c.cur_query and c.formatted_results:
<div class="pagination-wh pagination-left" >
    ${c.formatted_results.render()}
</div>
%endif

%if c.cur_query:
<script type="text/javascript">
$(function(){
  $(".search-code-body").mark(
      "${query_mark}",
          {
              "className": 'match',
              "accuracy": "complementary",
              "ignorePunctuation": ":._(){}[]!'+=".split("")
          }
  );
})
</script>
%endif
