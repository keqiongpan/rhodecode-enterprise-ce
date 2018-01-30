## -*- coding: utf-8 -*-
<%inherit file="/base/base.mako"/>
<%namespace name="base" file="/base/base.mako"/>

<%def name="title()">
    ${_('Admin audit log entry')}
    %if c.rhodecode_name:
        &middot; ${h.branding(c.rhodecode_name)}
    %endif
</%def>

<%def name="breadcrumbs_links()">
    ${_('Audit long entry')} ${c.audit_log_entry.entry_id}
</%def>

<%def name="menu_bar_nav()">
    ${self.menu_items(active='admin')}
</%def>
<%def name="main()">
<div class="box">
    <!-- box / title -->
    <div class="title">
        ${self.breadcrumbs()}
    </div>
    <!-- end box / title -->
    <div class="table">
        <div id="user_log">
            <table class="rctable audit-log">
                <tr>
                    <td>
                    ${_('User')}:
                    </td>
                    <td>
                        %if c.audit_log_entry.user is not None:
                          ${base.gravatar_with_user(c.audit_log_entry.user.email)}
                        %else:
                          ${c.audit_log_entry.username}
                        %endif
                    </td>
                </tr>
                <tr>
                    <td>
                    ${_('Date')}:
                    </td>
                    <td>
                        ${h.format_date(c.audit_log_entry.action_date)}
                    </td>
                </tr>
                <tr>
                    <td>
                    ${_('IP')}:
                    </td>
                    <td>
                        ${c.audit_log_entry.user_ip}
                    </td>
                </tr>

                <tr>
                    <td>
                    ${_('Action')}:
                    </td>
                    <td>
                        % if c.audit_log_entry.version == c.audit_log_entry.VERSION_1:
                            ${h.action_parser(request, l)[0]()}
                        % else:
                            ${h.literal(c.audit_log_entry.action)}
                        % endif

                        <div class="journal_action_params">
                            % if c.audit_log_entry.version == c.audit_log_entry.VERSION_1:
                                ${h.literal(h.action_parser(request, l)[1]())}
                            % endif
                        </div>
                    </td>
                </tr>
                <tr>
                    <td>
                    ${_('Action Data')}:
                    </td>
                    <td class="td-journalaction">
                        % if c.audit_log_entry.version == c.audit_log_entry.VERSION_2:
                            <div>
                                <pre>${h.json.dumps(c.audit_log_entry.action_data, indent=4, sort_keys=True)}</pre>
                            </div>
                        % else:
                            <pre title="${_('data not available for v1 entries type')}">-</pre>
                        % endif
                    </td>
                </tr>
                <tr>
                    <td>
                    ${_('Repository')}:
                    </td>
                    <td class="td-journalaction">
                        %if c.audit_log_entry.repository is not None:
                          ${h.link_to(c.audit_log_entry.repository.repo_name, h.route_path('repo_summary',repo_name=c.audit_log_entry.repository.repo_name))}
                        %else:
                          ${c.audit_log_entry.repository_name or '-'}
                        %endif
                    </td>
                </tr>

            </table>

        </div>
    </div>
</div>

<script>
$('#j_filter').autoGrowInput();
</script>
</%def>
