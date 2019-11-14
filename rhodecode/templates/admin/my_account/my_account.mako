## -*- coding: utf-8 -*-
<%inherit file="/base/base.mako"/>

<%def name="title()">
    ${_('My account')} ${c.rhodecode_user.username}
    %if c.rhodecode_name:
        &middot; ${h.branding(c.rhodecode_name)}
    %endif
</%def>

<%def name="breadcrumbs_links()">
    ${_('My Account')}
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
          <li class="${h.is_active(['profile', 'profile_edit'], c.active)}"><a href="${h.route_path('my_account_profile')}">${_('Profile')}</a></li>
          <li class="${h.is_active('emails', c.active)}"><a href="${h.route_path('my_account_emails')}">${_('Emails')}</a></li>
          <li class="${h.is_active('password', c.active)}"><a href="${h.route_path('my_account_password')}">${_('Password')}</a></li>
          <li class="${h.is_active('bookmarks', c.active)}"><a href="${h.route_path('my_account_bookmarks')}">${_('Bookmarks')}</a></li>
          <li class="${h.is_active('auth_tokens', c.active)}"><a href="${h.route_path('my_account_auth_tokens')}">${_('Auth Tokens')}</a></li>
          <li class="${h.is_active(['ssh_keys', 'ssh_keys_generate'], c.active)}"><a href="${h.route_path('my_account_ssh_keys')}">${_('SSH Keys')}</a></li>
          <li class="${h.is_active('user_group_membership', c.active)}"><a href="${h.route_path('my_account_user_group_membership')}">${_('User Group Membership')}</a></li>

          ## TODO: Find a better integration of oauth/saml views into navigation.
          <% my_account_external_url = h.route_path_or_none('my_account_external_identity') %>
          % if my_account_external_url:
          <li class="${h.is_active('external_identity', c.active)}"><a href="${my_account_external_url}">${_('External Identities')}</a></li>
          % endif

          <li class="${h.is_active('repos', c.active)}"><a href="${h.route_path('my_account_repos')}">${_('Repositories')}</a></li>
          <li class="${h.is_active('watched', c.active)}"><a href="${h.route_path('my_account_watched')}">${_('Watched')}</a></li>
          <li class="${h.is_active('pullrequests', c.active)}"><a href="${h.route_path('my_account_pullrequests')}">${_('Pull Requests')}</a></li>
          <li class="${h.is_active('perms', c.active)}"><a href="${h.route_path('my_account_perms')}">${_('Permissions')}</a></li>
          <li class="${h.is_active('my_notifications', c.active)}"><a href="${h.route_path('my_account_notifications')}">${_('Live Notifications')}</a></li>
        </ul>
    </div>

    <div class="main-content-full-width">
        <%include file="/admin/my_account/my_account_${c.active}.mako"/>
    </div>
  </div>
</div>

</%def>
