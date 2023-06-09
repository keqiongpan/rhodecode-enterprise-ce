<%namespace name="base" file="/base/base.mako"/>
<%namespace name="search" file="/search/search.mako"/>

% if c.formatted_results:

<table class="rctable search-results">
    <tr>
        <th>${_('Repository')}</th>
        <th>${_('Commit')}</th>
        <th></th>
        <th>
            <a href="${search.field_sort('message')}">${_('Commit message')}</a>
        </th>
        <th>
            <a href="${search.field_sort('date')}">${_('Commit date')}</a>
        </th>
        <th>
            <a href="${search.field_sort('author_email')}">${_('Author')}</a>
        </th>
    </tr>
    %for entry in c.formatted_results:
        ## search results are additionally filtered, and this check is just a safe gate
        % if c.rhodecode_user.is_admin or h.HasRepoPermissionAny('repository.write','repository.read','repository.admin')(entry['repository'], 'search results commit check'):
            <tr class="body">
                <td class="td-componentname">
                    <% repo_type = entry.get('repo_type') or h.get_repo_type_by_name(entry.get('repository')) %>
                    ${search.repo_icon(repo_type)}
                    ${h.link_to(entry['repository'], h.route_path('repo_summary',repo_name=entry['repository']))}
                </td>
                <td class="td-hash">
                    ${h.link_to(h._shorten_commit_id(entry['commit_id']),
                      h.route_path('repo_commit',repo_name=entry['repository'],commit_id=entry['commit_id']))}
                </td>
                <td class="td-message expand_commit search open" data-commit-id="${h.md5_safe(entry['repository'])+entry['commit_id']}" id="t-${h.md5_safe(entry['repository'])+entry['commit_id']}" title="${_('Expand commit message')}">
                    <div>
                    <i class="icon-expand-linked"></i>&nbsp;
                    </div>
                </td>
                <td data-commit-id="${h.md5_safe(entry['repository'])+entry['commit_id']}" id="c-${h.md5_safe(entry['repository'])+entry['commit_id']}" class="message td-description open">
                    %if entry.get('message_hl'):
                        ${h.literal(entry['message_hl'])}
                    %else:
                        ${h.urlify_commit_message(entry['message'], entry['repository'])}
                    %endif
                </td>
                <td class="td-time">
                    ${h.age_component(h.time_to_utcdatetime(entry['date']))}
                </td>

                <td class="td-user author">
                    <%
                    ## es6 stores this as object
                    author = entry['author']
                    if isinstance(author, dict):
                        author = author['email']
                    %>
                    ${base.gravatar_with_user(author, tooltip=True)}
                </td>
            </tr>
        % endif
    %endfor
</table>

%if c.cur_query:
<div class="pagination-wh pagination-left">
    ${c.formatted_results.render()}
</div>
%endif

<script>
    $('.expand_commit').on('click',function(e){
      var target_expand = $(this);
      var cid = target_expand.data('commit-id');

      if (target_expand.hasClass('open')){
        $('#c-'+cid).css({'height': '1.5em', 'white-space': 'nowrap', 'text-overflow': 'ellipsis', 'overflow':'hidden'});
        $('#t-'+cid).css({'height': 'auto', 'line-height': '.9em', 'text-overflow': 'ellipsis', 'overflow':'hidden'});
        target_expand.removeClass('open');
      }
      else {
        $('#c-'+cid).css({'height': 'auto', 'white-space': 'normal', 'text-overflow': 'initial', 'overflow':'visible'});
        $('#t-'+cid).css({'height': 'auto', 'max-height': 'none', 'text-overflow': 'initial', 'overflow':'visible'});
        target_expand.addClass('open');
      }
    });

    $(".message.td-description").mark(
        "${c.searcher.query_to_mark(c.cur_query, 'message')}",
        {
            "className": 'match',
            "accuracy": "complementary",
            "ignorePunctuation": ":._(){}[]!'+=".split("")
        }
    );

</script>

% endif
