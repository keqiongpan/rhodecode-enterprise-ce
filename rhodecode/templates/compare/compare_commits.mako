## Changesets table !
<%namespace name="base" file="/base/base.mako"/>

%if c.ancestor:
<div class="ancestor">${_('Common Ancestor Commit')}:
    <a href="${h.route_path('repo_commit', repo_name=c.repo_name, commit_id=c.ancestor)}">
        ${h.short_id(c.ancestor)}
    </a>. ${_('Compare was calculated based on this shared commit.')}
    <input id="common_ancestor" type="hidden" name="common_ancestor" value="${c.ancestor}">
</div>
%endif

<div class="container">
    <input type="hidden" name="__start__" value="revisions:sequence">
    <table class="rctable compare_view_commits">
        <tr>
            <th>${_('Time')}</th>
            <th>${_('Author')}</th>
            <th>${_('Commit')}</th>
            <th></th>
            <th>${_('Description')}</th>
        </tr>
    ## to speed up lookups cache some functions before the loop
    <%
        active_patterns = h.get_active_pattern_entries(c.repo_name)
        urlify_commit_message = h.partial(h.urlify_commit_message, active_pattern_entries=active_patterns)
    %>
    %for commit in c.commit_ranges:
        <tr id="row-${commit.raw_id}"
            commit_id="${commit.raw_id}"
            class="compare_select"
            style="${'display: none' if c.collapse_all_commits else ''}"
        >
            <td class="td-time">
                ${h.age_component(commit.date)}
            </td>
            <td class="td-user">
                ${base.gravatar_with_user(commit.author, 16)}
            </td>
            <td class="td-hash">
                <code>
                    <a href="${h.route_path('repo_commit', repo_name=c.target_repo.repo_name, commit_id=commit.raw_id)}">
                        r${commit.idx}:${h.short_id(commit.raw_id)}
                    </a>
                    ${h.hidden('revisions',commit.raw_id)}
                </code>
            </td>
            <td class="expand_commit"
                data-commit-id="${commit.raw_id}"
                title="${_( 'Expand commit message')}"
            >
                <div class="show_more_col">
                <i class="icon-expand-linked"></i>
                </div>
            </td>
            <td class="mid td-description">
                <div class="log-container truncate-wrap">
                    <div
                        id="c-${commit.raw_id}"
                        class="message truncate"
                        data-message-raw="${commit.message}"
                    >
                        ${urlify_commit_message(commit.message, c.repo_name)}
                    </div>
                </div>
            </td>
        </tr>
    %endfor
        <tr class="compare_select_hidden" style="${'' if c.collapse_all_commits else 'display: none'}">
            <td colspan="5">
                ${_ungettext('%s commit hidden','%s commits hidden', len(c.commit_ranges)) % len(c.commit_ranges)},
                <a href="#" onclick="$('.compare_select').show();$('.compare_select_hidden').hide(); return false">${_ungettext('show it','show them', len(c.commit_ranges))}</a>
            </td>
        </tr>
    % if not c.commit_ranges:
        <tr class="compare_select">
            <td colspan="5">
                ${_('No commits in this compare')}
            </td>
        </tr>
    % endif
    </table>
    <input type="hidden" name="__end__" value="revisions:sequence">

</div>

<script>
$('.expand_commit').on('click',function(e){
  var target_expand = $(this);
  var cid = target_expand.data('commitId');

  // ## TODO: dan: extract styles into css, and just toggleClass('open') here
  if (target_expand.hasClass('open')){
    $('#c-'+cid).css({
        'height': '1.5em',
        'white-space': 'nowrap',
        'text-overflow': 'ellipsis',
        'overflow':'hidden'
    });
    target_expand.removeClass('open');
  }
  else {
    $('#c-'+cid).css({
        'height': 'auto',
        'white-space': 'pre-line',
        'text-overflow': 'initial',
        'overflow':'visible'
    });
    target_expand.addClass('open');
  }
});

$('.compare_select').on('click',function(e){
    var cid = $(this).attr('commit_id');
    $('#row-'+cid).toggleClass('hl', !$('#row-'+cid).hasClass('hl'));
});
</script>
