<%namespace name="base" file="/base/base.mako"/>

%if c.audit_logs:
<table class="rctable admin_log">
    <tr>
        <th>${_('Uid')}</th>
        <th>${_('Username')}</th>
        <th>${_('Action')}</th>
        <th>${_('Action Data')}</th>
        <th>${_('Repository')}</th>
        <th>${_('Date')}</th>
        <th>${_('IP')}</th>
    </tr>

    %for cnt,l in enumerate(c.audit_logs):
    <tr class="parity${cnt%2}">
        <td class="td-col">
            <a href="${h.route_path('admin_audit_log_entry', audit_log_id=l.entry_id)}">${l.entry_id}</a>
        </td>
        <td class="td-user">
            %if l.user is not None:
              ${base.gravatar_with_user(l.user.email)}
            %else:
              ${l.username}
            %endif
        </td>
        <td class="td-journalaction">
            % if l.version == l.VERSION_1:
                ${h.action_parser(request, l)[0]()}
            % else:
                ${h.literal(l.action)}
            % endif

            <div class="journal_action_params">
                % if l.version == l.VERSION_1:
                    ${h.literal(h.action_parser(request, l)[1]())}
                % endif
            </div>
        </td>
        <td>
            % if l.version == l.VERSION_2:
                <a href="#" onclick="$('#entry-'+${l.user_log_id}).toggle();return false">${_('toggle')}</a>
                <div id="entry-${l.user_log_id}" style="display: none">
                    <pre>${h.json.dumps(l.action_data, indent=4, sort_keys=True)}</pre>
                </div>
            % else:
                <pre title="${_('data not available for v1 entries type')}">-</pre>
            % endif
        </td>
        <td class="td-componentname">
            %if l.repository is not None:
              ${h.link_to(l.repository.repo_name, h.route_path('repo_summary',repo_name=l.repository.repo_name))}
            %else:
              ${l.repository_name}
            %endif
        </td>

        <td class="td-time">${h.format_date(l.action_date)}</td>
        <td class="td-ip">${l.user_ip}</td>
    </tr>
    %endfor
</table>

<div class="pagination-wh pagination-left">
${c.audit_logs.render()}
</div>
%else:
    ${_('No actions yet')}
%endif