## -*- coding: utf-8 -*-
<%inherit file="/base/base.mako"/>

<%def name="title()">
    ${_('Admin audit logs')}
    %if c.rhodecode_name:
        &middot; ${h.branding(c.rhodecode_name)}
    %endif
</%def>

<%def name="breadcrumbs_links()">
    ${h.form(None, id_="filter_form", method="get")}
        <input class="q_filter_box ${'' if c.search_term else 'initial'}" id="j_filter" size="15" type="text" name="filter" value="${c.search_term or ''}" placeholder="${_('filter...')}"/>
        <input type='submit' value="${_('filter')}" class="btn" />
        ${_('Audit logs')} - ${_ungettext('%s entry', '%s entries', c.audit_logs.item_count) % (c.audit_logs.item_count)}
    ${h.end_form()}
    <p class="tooltip filterexample" title="${h.tooltip(h.journal_filter_help(c.pyramid_request))}">${_('Example Queries')}</p>
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
            <%include file="/admin/admin_log_base.mako" />
        </div>
    </div>
</div>

<script>
$('#j_filter').autoGrowInput();
</script>
</%def>
