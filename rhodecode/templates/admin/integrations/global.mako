## -*- coding: utf-8 -*-
<%inherit file="/base/base.mako"/>

<%def name="title()">
    ${_('Integrations administration')}
    %if c.rhodecode_name:
        &middot; ${h.branding(c.rhodecode_name)}
    %endif
</%def>

<%def name="breadcrumbs_links()">
    ${h.link_to(_('Admin'),h.route_path('admin_home'))}
    &raquo;
    ${_('Integrations')}
</%def>

<%def name="menu_bar_nav()">
    ${self.menu_items(active='admin')}
</%def>

<%def name="menu_bar_subnav()">
    ${self.admin_menu(active='integrations')}
</%def>

<%def name="side_bar_nav()">
    <li class="active">
      <a href="${h.route_path('global_integrations_home')}">Global</a>
    </li>
</%def>

<%def name="main_content()">
  <%include file="/admin/settings/settings_${c.active}.mako"/>
</%def>

<%def name="main()">
<div class="box">

    ##main
    <div class='sidebar-col-wrapper'>
      <div class="sidebar">
          <ul class="nav nav-pills nav-stacked">
            ${self.side_bar_nav()}
          </ul>
      </div>

      <div class="main-content-auto-width">
        ${self.main_content()}
      </div>
    </div>
</div>

</%def>
