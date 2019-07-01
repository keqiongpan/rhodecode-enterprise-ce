## -*- coding: utf-8 -*-
<%inherit file="/base/base.mako"/>

<%def name="title()">
    ${_('%s repository group settings') % c.repo_group.name}
    %if c.rhodecode_name:
        &middot; ${h.branding(c.rhodecode_name)}
    %endif
</%def>

<%def name="menu_bar_nav()">
    ${self.menu_items(active='admin')}
</%def>

<%def name="menu_bar_subnav()">
    ${self.repo_group_menu(active='settings')}
</%def>

<%def name="main_content()">
    <%include file="/admin/repo_groups/repo_group_edit_${c.active}.mako"/>
</%def>

<%def name="main()">

<div class="box">
  <div class="sidebar-col-wrapper">
    ##main
    <div class="sidebar">
        <ul class="nav nav-pills nav-stacked">
          <li class="${'active' if c.active=='settings' else ''}"><a href="${h.route_path('edit_repo_group', repo_group_name=c.repo_group.group_name)}">${_('Settings')}</a></li>
          <li class="${'active' if c.active=='permissions' else ''}"><a href="${h.route_path('edit_repo_group_perms', repo_group_name=c.repo_group.group_name)}">${_('Permissions')}</a></li>
          <li class="${'active' if c.active=='advanced' else ''}"><a href="${h.route_path('edit_repo_group_advanced', repo_group_name=c.repo_group.group_name)}">${_('Advanced')}</a></li>
          <li class="${'active' if c.active=='integrations' else ''}"><a href="${h.route_path('repo_group_integrations_home', repo_group_name=c.repo_group.group_name)}">${_('Integrations')}</a></li>
        </ul>
    </div>

    <div class="main-content-full-width">
      ${self.main_content()}
    </div>

  </div>
</div>

</%def>
