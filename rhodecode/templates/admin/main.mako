## -*- coding: utf-8 -*-
<%inherit file="/base/base.mako"/>

<%def name="title()">
    ${_('Settings administration')}
    %if c.rhodecode_name:
        &middot; ${h.branding(c.rhodecode_name)}
    %endif
</%def>

<%def name="breadcrumbs_links()">
    ${h.link_to(_('Admin'),h.route_path('admin_home'))}
    &raquo;
    ${_('Settings')}
</%def>

<%def name="menu_bar_nav()">
    ${self.menu_items(active='admin')}
</%def>

<%def name="side_bar_nav()">

</%def>

<%def name="main_content()">
  Hello Admin
</%def>

<%def name="main()">
<div class="box">
    <div class="title">
        ${self.breadcrumbs()}
    </div>

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