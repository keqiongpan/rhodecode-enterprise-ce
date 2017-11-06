## -*- coding: utf-8 -*-
<%namespace name="base" file="/base/base.mako"/>


<div class="panel panel-default">
    <div class="panel-heading">
      <h3 class="panel-title">${_('Repository Audit Logs')} -
      ${_ungettext('%s entry', '%s entries', c.audit_logs.item_count) % (c.audit_logs.item_count)}
      </h3>
    </div>
    <div class="panel-body">

        ${h.form(None, id_="filter_form", method="get")}
            <input class="q_filter_box ${'' if c.filter_term else 'initial'}" id="j_filter" size="15" type="text" name="filter" value="${c.filter_term or ''}" placeholder="${_('audit filter...')}"/>
            <input type='submit' value="${_('filter')}" class="btn" />
        ${h.end_form()}
        <p class="tooltip filterexample" style="position: inherit" title="${h.tooltip(h.journal_filter_help(c.pyramid_request))}">${_('Example Queries')}</p>

        <%include file="/admin/admin_log_base.mako" />

    </div>
</div>
