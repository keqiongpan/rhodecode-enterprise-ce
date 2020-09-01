## Changesets table !
<%namespace name="base" file="/base/base.mako"/>

%if c.ancestor:
<div class="ancestor">${_('Compare was calculated based on this common ancestor commit')}:
    <a href="${h.route_path('repo_commit', repo_name=c.repo_name, commit_id=c.ancestor)}">${h.short_id(c.ancestor)}</a>
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
        urlify_commit_message = h.partial(h.urlify_commit_message, active_pattern_entries=active_patterns, issues_container=getattr(c, 'referenced_commit_issues', None))
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
                ${base.gravatar_with_user(commit.author, 16, tooltip=True)}
            </td>
            <td class="td-hash">
                <code>
                    <a href="${h.route_path('repo_commit', repo_name=c.target_repo.repo_name, commit_id=commit.raw_id)}">
                        r${commit.idx}:${h.short_id(commit.raw_id)}
                    </a>
                    ${h.hidden('revisions',commit.raw_id)}
                </code>
            </td>
            <td class="td-message expand_commit" data-commit-id="${commit.raw_id}" title="${_('Expand commit message')}" onclick="commitsController.expandCommit(this); return false">
                <i class="icon-expand-linked"></i>
            </td>
            <td class="mid td-description">
                <div class="log-container truncate-wrap">
                    <div class="message truncate" id="c-${commit.raw_id}" data-message-raw="${commit.message}">${urlify_commit_message(commit.message, c.repo_name)}</div>
                </div>
            </td>
        </tr>
    %endfor
        <tr class="compare_select_hidden" style="${('' if c.collapse_all_commits else 'display: none')}">
            <td colspan="5">
                ${_ungettext('{} commit hidden, click expand to show them.', '{} commits hidden, click expand to show them.', len(c.commit_ranges)).format(len(c.commit_ranges))}
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
commitsController = new CommitsController();
$('.compare_select').on('click',function(e){
    var cid = $(this).attr('commit_id');
    $('#row-'+cid).toggleClass('hl', !$('#row-'+cid).hasClass('hl'));
});
</script>
