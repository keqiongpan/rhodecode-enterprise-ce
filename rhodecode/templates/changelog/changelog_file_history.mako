<%namespace name="base" file="/base/base.mako"/>
<div class="table">

    <table class="table rctable file_history">
    %for cnt,cs in enumerate(c.pagination):
        <tr id="chg_${cnt+1}" class="${'tablerow%s' % (cnt%2)}">
            <td class="td-user">
                ${base.gravatar_with_user(cs.author, 16)}
            </td>
            <td class="td-time">
                <div class="date">
                    ${h.age_component(cs.date)}
                </div>
            </td>
            <td class="td-message">
                <div class="log-container">
                    <div class="message_history" title="${h.tooltip(cs.message)}">
                        <a href="${h.url('changeset_home',repo_name=c.repo_name,revision=cs.raw_id)}">
                            ${h.shorter(cs.message, 75)}
                        </a>
                    </div>
                </div>
            </td>
            <td class="td-hash">
                <code>
                    <a href="${h.url('changeset_home',repo_name=c.repo_name,revision=cs.raw_id)}">
                        <span>${h.show_id(cs)}</span>
                    </a>
                </code>
            </td>
            <td class="td-actions">
                <a href="${h.route_path('repo_files',repo_name=c.repo_name,commit_id=cs.raw_id,f_path=c.changelog_for_path)}">
                    ${_('Show File')}
                </a>
            </td>
        </tr>
    %endfor
    </table>
</div>
