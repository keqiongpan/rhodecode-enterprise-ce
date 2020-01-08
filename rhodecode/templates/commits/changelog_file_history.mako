<%namespace name="base" file="/base/base.mako"/>
<div class="table">

    <table class="table rctable file_history">
    %for cnt,cs in enumerate(c.pagination):
        <tr id="chg_${cnt+1}" class="${('tablerow%s' % (cnt%2))}">
            <td class="td-user">
                ${base.gravatar_with_user(cs.author, 16, tooltip=True)}
            </td>
            <td class="td-time">
                <div class="date">
                    ${h.age_component(cs.date)}
                </div>
            </td>
            <td class="td-message">
                <div class="log-container">
                    <div class="message_history" title="${h.tooltip(cs.message)}">
                        <a href="${h.route_path('repo_commit',repo_name=c.repo_name,commit_id=cs.raw_id)}">
                            ${h.shorter(cs.message, 75)}
                        </a>
                    </div>
                </div>
            </td>
            <td class="td-hash">
                <code>
                    <a href="${h.route_path('repo_commit',repo_name=c.repo_name,commit_id=cs.raw_id)}">
                        <span>${h.show_id(cs)}</span>
                    </a>
                </code>
            </td>
            <td class="td-actions">
                <a href="${h.route_path('repo_files',repo_name=c.repo_name,commit_id=cs.raw_id,f_path=c.changelog_for_path)}">
                    ${_('Show File')}
                </a>
            </td>
            <td class="td-actions">
                <a href="${h.route_path('repo_compare',repo_name=c.repo_name, source_ref_type="rev", source_ref=cs.raw_id,target_ref_type="rev", target_ref=c.commit_id,_query=dict(merge='1',f_path=c.changelog_for_path))}">
                    <span title="${'Diff {} vs {}'.format(cs.raw_id[:8],c.commit_id[:8])}">${_('Diff File')}</span>
                </a>
            </td>
        </tr>
    %endfor
        <tr>
            <td colspan="6">
                <a id="file_history_overview_full" href="${h.route_path('repo_commits_file',repo_name=c.repo_name, commit_id=c.commit_id, f_path=c.f_path)}">
               ${_('Show Full History')}
                </a>
            </td>
        </tr>
    </table>
</div>
