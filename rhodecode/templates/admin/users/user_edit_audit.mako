## -*- coding: utf-8 -*-
<%namespace name="base" file="/base/base.mako"/>


<div class="panel panel-default">
    <div class="panel-heading">
      <h3 class="panel-title">
          ${base.gravatar_with_user(c.user.username, 16, tooltip=False, _class='pull-left')}
          &nbsp;- ${_('Audit Logs')}
          (${_ungettext('%s entry', '%s entries', c.audit_logs.item_count) % (c.audit_logs.item_count)})
      </h3>
      <a href="${h.route_path('edit_user_audit_logs_download', user_id=c.user.user_id)}" class="panel-edit">${_('Download as JSON')}</a>
    </div>
    <div class="panel-body">

        ${h.form(None, id_="filter_form", method="get")}
            <input class="q_filter_box ${'' if c.filter_term else 'initial'}" id="j_filter" size="15" type="text" name="filter" value="${c.filter_term or ''}" placeholder="${_('audit filter...')}"/>
            <input type='submit' value="${_('filter')}" class="btn" />
        ${h.end_form()}

        <p class="filterexample" style="position: inherit" onclick="$('#search-help').toggle()">${_('Example Queries')}</p>
        <pre id="search-help" style="display: none">${h.tooltip(h.journal_filter_help(request))}</pre>

        <%include file="/admin/admin_log_base.mako" />

    </div>
</div>
