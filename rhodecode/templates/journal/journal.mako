## -*- coding: utf-8 -*-
<%inherit file="/base/base.mako"/>
<%def name="title()">
    ${_('Journal')}
    %if c.rhodecode_name:
        &middot; ${h.branding(c.rhodecode_name)}
    %endif
</%def>

<%def name="breadcrumbs_links()">
    ${h.form(None, id_="filter_form", method="get")}
        <input class="q_filter_box ${'' if c.search_term else 'initial'}" id="j_filter" size="15" type="text" name="filter" value="${c.search_term}" placeholder="${_('quick filter...')}"/>
        <input type='submit' value="${_('filter')}" class="btn" />
        ${_('Journal')} - ${_ungettext('%s entry', '%s entries', c.journal_pager.item_count) % (c.journal_pager.item_count)}
    ${h.end_form()}
    <p class="filterexample" style="position: inherit" onclick="$('#search-help').toggle()">${_('Example Queries')}</p>
    <pre id="search-help" style="display: none">${h.tooltip(h.journal_filter_help(request))}</pre>
</%def>

<%def name="menu_bar_nav()">
    ${self.menu_items(active='journal')}
</%def>

<%def name="head_extra()">
<link href="${h.route_path('journal_atom', _query=dict(auth_token=c.rhodecode_user.feed_token))}" rel="alternate" title="${_('ATOM journal feed')}" type="application/atom+xml" />
<link href="${h.route_path('journal_rss', _query=dict(auth_token=c.rhodecode_user.feed_token))}" rel="alternate" title="${_('RSS journal feed')}" type="application/rss+xml" />
</%def>

<%def name="main()">

<div class="box">
    <!-- box / title -->
    <div class="title journal">
     ${self.breadcrumbs()}
     <ul class="links icon-only-links block-right">
       <li>
         <span><a id="refresh" href="${h.route_path('journal')}"><i class="icon-refresh"></i></a></span>
       </li>
       <li>
         <span>
             <a href="${h.route_path('journal_atom', _query=dict(auth_token=c.rhodecode_user.feed_token))}" title="RSS Feed" class="btn btn-sm"><i class="icon-rss-sign"></i>RSS</a>
         </span>
       </li>
     </ul>
    </div>
    <div id="journal">${c.journal_data|n}</div>
</div>

<script type="text/javascript">
    $('#j_filter').autoGrowInput();
</script>
</%def>
