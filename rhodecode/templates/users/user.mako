<%inherit file="/base/base.mako"/>

<%def name="title()">
    ${_('User')}: ${c.user.username}
    %if c.rhodecode_name:
        &middot; ${h.branding(c.rhodecode_name)}
    %endif
</%def>

<%def name="breadcrumbs_links()">
    ${_('User')}: ${c.user.username}
</%def>

<%def name="menu_bar_nav()">
    ${self.menu_items(active='my_account')}
</%def>

<%def name="main()">
<div class="box">
  <div class="title">
      ${self.breadcrumbs()}
  </div>

  <div class="sidebar-col-wrapper scw-small">
    ##main
    <div class="sidebar">
        <ul class="nav nav-pills nav-stacked">
          <li class="${'active' if c.active=='user_profile' else ''}">
              <a href="${h.route_path('user_profile', username=c.user.username)}">${_('Profile')}</a>
          </li>
          % if c.is_super_admin:
              <li><a href="${h.route_path('user_edit', user_id=c.user.user_id)}">${_('User Profile')}</a></li>
              <li><a href="${h.route_path('edit_user_auth_tokens', user_id=c.user.user_id)}">${_('Auth tokens')}</a></li>
              <li><a href="${h.route_path('edit_user_ssh_keys', user_id=c.user.user_id)}">${_('SSH Keys')}</a></li>
              <li><a href="${h.route_path('user_edit_advanced', user_id=c.user.user_id)}">${_('Advanced')}</a></li>
              <li><a href="${h.route_path('user_edit_global_perms', user_id=c.user.user_id)}">${_('Global permissions')}</a></li>
              <li><a href="${h.route_path('edit_user_perms_summary', user_id=c.user.user_id)}">${_('Permissions summary')}</a></li>
              <li><a href="${h.route_path('edit_user_emails', user_id=c.user.user_id)}">${_('Emails')}</a></li>
              <li><a href="${h.route_path('edit_user_ips', user_id=c.user.user_id)}">${_('Ip Whitelist')}</a></li>
              <li><a href="${h.route_path('edit_user_groups_management', user_id=c.user.user_id)}">${_('User Groups Management')}</a></li>
              <li><a href="${h.route_path('edit_user_audit_logs', user_id=c.user.user_id)}">${_('Audit logs')}</a></li>
              <li><a href="${h.route_path('edit_user_caches', user_id=c.user.user_id)}">${_('Caches')}</a></li>
          % else:
              ## These placeholders are here only for styling purposes. For every new item added to the list, you should remove one placeholder
              <li class="placeholder"><a href="#" style="visibility: hidden;">placeholder</a></li>
              <li class="placeholder"><a href="#" style="visibility: hidden;">placeholder</a></li>
              <li class="placeholder"><a href="#" style="visibility: hidden;">placeholder</a></li>
              <li class="placeholder"><a href="#" style="visibility: hidden;">placeholder</a></li>
              <li class="placeholder"><a href="#" style="visibility: hidden;">placeholder</a></li>
              <li class="placeholder"><a href="#" style="visibility: hidden;">placeholder</a></li>
          % endif
        </ul>
    </div>

    <div class="main-content-full-width">
        <%include file="/users/${c.active}.mako"/>
    </div>
  </div>
</div>

</%def>
