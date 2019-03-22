## -*- coding: utf-8 -*-
<%inherit file="/base/base.mako"/>

<%def name="title()">
    ${_('Repositories defaults')}
    %if c.rhodecode_name:
        &middot; ${h.branding(c.rhodecode_name)}
    %endif
</%def>

<%def name="breadcrumbs_links()">
    ${h.link_to(_('Admin'),h.route_path('admin_home'))}
    &raquo;
    ${_('Repositories defaults')}
</%def>

<%def name="menu_bar_nav()">
    ${self.menu_items(active='admin')}
</%def>

<%def name="menu_bar_subnav()">
    ${self.admin_menu(active='defaults')}
</%def>

<%def name="main()">
<div class="box">

    ##main
    <div class="sidebar-col-wrapper">
        <div class="sidebar">
            <ul class="nav nav-pills nav-stacked">
              <li class="${'active' if c.active=='repositories' else ''}"><a href="${h.route_path('admin_defaults_repositories')}">${_('Repository')}</a></li>
            </ul>
        </div>

        <div class="main-content-full-width">
            <%include file="/admin/defaults/defaults_${c.active}.mako"/>
        </div>

    </div>
</div>

</%def>
