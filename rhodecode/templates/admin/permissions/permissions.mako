## -*- coding: utf-8 -*-
<%inherit file="/base/base.mako"/>

<%def name="title()">
    ${_('Permissions Administration')}
    %if c.rhodecode_name:
        &middot; ${h.branding(c.rhodecode_name)}
    %endif
</%def>

<%def name="breadcrumbs_links()">
    ${h.link_to(_('Admin'),h.route_path('admin_home'))}
    &raquo;
    ${_('Permissions')}
</%def>

<%def name="menu_bar_nav()">
    ${self.menu_items(active='admin')}
</%def>

<%def name="menu_bar_subnav()">
    ${self.admin_menu(active='permissions')}
</%def>

<%def name="main()">
<div class="box">

  <div class="sidebar-col-wrapper scw-small">
    ##main
    <div class="sidebar">
        <ul class="nav nav-pills nav-stacked">
          <li class="${h.is_active('application', c.active)}">
            <a href="${h.route_path('admin_permissions_application')}">${_('Application')}</a>
          </li>
          <li class="${h.is_active('global', c.active)}">
            <a href="${h.route_path('admin_permissions_global')}">${_('Global')}</a>
          </li>
          <li class="${h.is_active('objects', c.active)}">
            <a href="${h.route_path('admin_permissions_object')}">${_('Object')}</a>
          </li>
          <li class="${h.is_active('branch', c.active)}">
            <a href="${h.route_path('admin_permissions_branch')}">${_('Branch')}</a>
          </li>
          <li class="${h.is_active('ips', c.active)}">
            <a href="${h.route_path('admin_permissions_ips')}">${_('IP Whitelist')}</a>
          </li>
          <li class="${h.is_active('auth_token_access', c.active)}">
            <a href="${h.route_path('admin_permissions_auth_token_access')}">${_('AuthToken Access')}</a>
          </li>
          <li class="${h.is_active('ssh_keys', c.active)}">
            <a href="${h.route_path('admin_permissions_ssh_keys')}">${_('SSH Keys')}</a>
          </li>
          <li class="${h.is_active('perms', c.active)}">
            <a href="${h.route_path('admin_permissions_overview')}">${_('Overview')}</a>
          </li>
        </ul>
    </div>

    <div class="main-content-full-width">
        <%include file="/admin/permissions/permissions_${c.active}.mako"/>
    </div>
  </div>
</div>

</%def>
