## -*- coding: utf-8 -*-
<%inherit file="/base/base.mako"/>

<%def name="title()">
    ${_('%s user settings') % c.user.username}
    %if c.rhodecode_name:
        &middot; ${h.branding(c.rhodecode_name)}
    %endif
</%def>

<%def name="breadcrumbs_links()">
    ${h.link_to(_('Admin'),h.route_path('admin_home'))}
    &raquo;
    ${h.link_to(_('Users'),h.route_path('users'))}
    &raquo;
    % if c.user.active:
    ${c.user.username}
    % else:
    <strike title="${_('This user is set as disabled')}">${c.user.username}</strike>
    % endif

</%def>

<%def name="menu_bar_nav()">
    ${self.menu_items(active='admin')}
</%def>

<%def name="main()">
<div class="box user_settings">
    <div class="title">
        ${self.breadcrumbs()}
    </div>

    ##main
  <div class="sidebar-col-wrapper">
    <div class="sidebar">
        <ul class="nav nav-pills nav-stacked">
          <li class="${'active' if c.active=='profile' else ''}"><a href="${h.url('edit_user', user_id=c.user.user_id)}">${_('User Profile')}</a></li>
          <li class="${'active' if c.active=='auth_tokens' else ''}"><a href="${h.route_path('edit_user_auth_tokens', user_id=c.user.user_id)}">${_('Auth tokens')}</a></li>
          <li class="${'active' if c.active in ['ssh_keys','ssh_keys_generate'] else ''}"><a href="${h.route_path('edit_user_ssh_keys', user_id=c.user.user_id)}">${_('SSH Keys')}</a></li>
          <li class="${'active' if c.active=='advanced' else ''}"><a href="${h.url('edit_user_advanced', user_id=c.user.user_id)}">${_('Advanced')}</a></li>
          <li class="${'active' if c.active=='global_perms' else ''}"><a href="${h.url('edit_user_global_perms', user_id=c.user.user_id)}">${_('Global permissions')}</a></li>
          <li class="${'active' if c.active=='perms_summary' else ''}"><a href="${h.url('edit_user_perms_summary', user_id=c.user.user_id)}">${_('Permissions summary')}</a></li>
          <li class="${'active' if c.active=='emails' else ''}"><a href="${h.route_path('edit_user_emails', user_id=c.user.user_id)}">${_('Emails')}</a></li>
          <li class="${'active' if c.active=='ips' else ''}"><a href="${h.route_path('edit_user_ips', user_id=c.user.user_id)}">${_('Ip Whitelist')}</a></li>
          <li class="${'active' if c.active=='groups' else ''}"><a href="${h.route_path('edit_user_groups_management', user_id=c.user.user_id)}">${_('User Groups Management')}</a></li>
          <li class="${'active' if c.active=='audit' else ''}"><a href="${h.route_path('edit_user_audit_logs', user_id=c.user.user_id)}">${_('User audit')}</a></li>
        </ul>
    </div>

    <div class="main-content-full-width">
        <%include file="/admin/users/user_edit_${c.active}.mako"/>
    </div>
  </div>
</div>

</%def>
