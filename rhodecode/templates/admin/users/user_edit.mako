## -*- coding: utf-8 -*-
<%inherit file="/base/base.mako"/>

<%def name="title()">
    ${_('{} user settings').format(c.user.username)}
    %if c.rhodecode_name:
        &middot; ${h.branding(c.rhodecode_name)}
    %endif
</%def>

<%def name="breadcrumbs_links()">
    ${h.link_to(_('Admin'),h.route_path('admin_home'))}
    &raquo;
    ${h.link_to(_('Users'),h.route_path('users'))}
    &raquo;
</%def>

<%def name="menu_bar_nav()">
    ${self.menu_items(active='admin')}
</%def>

<%def name="menu_bar_subnav()">
    ${self.admin_menu(active='users')}
</%def>


<%def name="main()">
<div class="box user_settings">
  % if not c.user.active:
    <div class="alert alert-warning text-center" style="margin: 0 0 15px 0">
        <strong>${_('This user is set as non-active and disabled.')}</strong>
    </div>
  % endif

  ##main
  <div class="sidebar-col-wrapper">
    <div class="sidebar">
        <ul class="nav nav-pills nav-stacked">
          <li class="${h.is_active('profile', c.active)}"><a href="${h.route_path('user_edit', user_id=c.user.user_id)}">${_('User Profile')}</a></li>
          <li class="${h.is_active('auth_tokens', c.active)}"><a href="${h.route_path('edit_user_auth_tokens', user_id=c.user.user_id)}">${_('Auth tokens')}</a></li>
          <li class="${h.is_active(['ssh_keys','ssh_keys_generate'], c.active)}"><a href="${h.route_path('edit_user_ssh_keys', user_id=c.user.user_id)}">${_('SSH Keys')}</a></li>
          <li class="${h.is_active('advanced', c.active)}"><a href="${h.route_path('user_edit_advanced', user_id=c.user.user_id)}">${_('Advanced')}</a></li>
          <li class="${h.is_active('global_perms', c.active)}"><a href="${h.route_path('user_edit_global_perms', user_id=c.user.user_id)}">${_('Global permissions')}</a></li>
          <li class="${h.is_active('perms_summary', c.active)}"><a href="${h.route_path('edit_user_perms_summary', user_id=c.user.user_id)}">${_('Permissions summary')}</a></li>
          <li class="${h.is_active('emails', c.active)}"><a href="${h.route_path('edit_user_emails', user_id=c.user.user_id)}">${_('Emails')}</a></li>
          <li class="${h.is_active('ips', c.active)}"><a href="${h.route_path('edit_user_ips', user_id=c.user.user_id)}">${_('Ip Whitelist')}</a></li>
          <li class="${h.is_active('groups', c.active)}"><a href="${h.route_path('edit_user_groups_management', user_id=c.user.user_id)}">${_('User Groups Management')}</a></li>
          <li class="${h.is_active('audit', c.active)}"><a href="${h.route_path('edit_user_audit_logs', user_id=c.user.user_id)}">${_('Audit logs')}</a></li>
          <li class="${h.is_active('caches', c.active)}"><a href="${h.route_path('edit_user_caches', user_id=c.user.user_id)}">${_('Caches')}</a></li>
        </ul>
    </div>

    <div class="main-content-full-width">
        <%include file="/admin/users/user_edit_${c.active}.mako"/>
    </div>
  </div>
</div>

</%def>
