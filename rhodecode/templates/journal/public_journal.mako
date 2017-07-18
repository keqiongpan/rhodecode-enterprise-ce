## -*- coding: utf-8 -*-
<%inherit file="/base/base.mako"/>
<%def name="title()">
    ${_('Public Journal')}
    %if c.rhodecode_name:
        &middot; ${h.branding(c.rhodecode_name)}
    %endif
</%def>

<%def name="breadcrumbs()">
    <h1 class="block-left">
        ${_('Public Journal')} - ${_ungettext('%s entry', '%s entries', c.journal_pager.item_count) % (c.journal_pager.item_count)}
    </h1>
</%def>

<%def name="menu_bar_nav()">
    ${self.menu_items(active='journal')}
</%def>

<%def name="head_extra()">
<link href="${h.route_path('journal_public_atom')}" rel="alternate" title="${_('ATOM public journal feed')}" type="application/atom+xml" />
<link href="${h.route_path('journal_public_rss')}" rel="alternate" title="${_('RSS public journal feed')}" type="application/rss+xml" />
</%def>

<%def name="main()">

<div class="box">
  <!-- box / title -->
  <div class="title journal">
   ${self.breadcrumbs()}

   <ul class="links icon-only-links block-right">
     <li>
       <span>
         <a href="${h.route_path('journal_public_atom')}"> <i class="icon-rss-sign" ></i></a>
       </span>
     </li>
   </ul>
  </div>
  <div id="journal">${c.journal_data|n}</div>
</div>

</%def>
