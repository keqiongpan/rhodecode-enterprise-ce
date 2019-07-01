## -*- coding: utf-8 -*-
<%inherit file="/base/base.mako"/>

<%def name="title()">
    ${_('Settings administration')}
    %if c.rhodecode_name:
        &middot; ${h.branding(c.rhodecode_name)}
    %endif
</%def>

<%def name="breadcrumbs_links()"></%def>

<%def name="menu_bar_nav()">
    ${self.menu_items(active='admin')}
</%def>

<%def name="menu_bar_subnav()">
    ${self.admin_menu()}
</%def>

<%def name="side_bar_nav()">

</%def>

<%def name="main_content()">
  <h2>${_('Administration area')}</h2>

  <table class="rctable">
  <tr>
    <td>${_('Repositories under administration')}</td>
    <td class="delegated-admin-repos">${len(c.auth_user.repositories_admin)}</td>
    <td>
        % if c.can_create_repo:
            <a href="${h.route_path('repo_new')}" class="">${_('Add Repository')}</a>
        % endif
    </td>
  </tr>
  <tr>
    <td>${_('Repository groups under administration')}</td>
    <td class="delegated-admin-repo-groups">${len(c.auth_user.repository_groups_admin)}</td>
    <td>
        % if c.can_create_repo_group:
            <a href="${h.route_path('repo_group_new')}" class="">${_(u'Add Repository Group')}</a>
        % endif
    </td>
  </tr>
  <tr>
    <td>${_('User groups under administration')}</td>
    <td class="delegated-admin-user-groups">${len(c.auth_user.user_groups_admin)}</td>
    <td>
        % if c.can_create_user_group:
            <a href="${h.route_path('user_groups_new')}" class="">${_(u'Add User Group')}</a>
        % endif
    </td>
  </tr>
  </table>
</%def>

<%def name="main()">
<div class="box">

    ##main
    <div class="main-content-auto-width">
        ${self.main_content()}
    </div>
</div>

</%def>