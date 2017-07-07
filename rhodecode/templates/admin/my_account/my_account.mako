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
          <li class="${'active' if c.active=='profile' or c.active=='profile_edit' else ''}"><a href="${h.route_path('my_account_profile')}">${_('Profile')}</a></li>
          <li class="${'active' if c.active=='password' else ''}"><a href="${h.route_path('my_account_password')}">${_('Password')}</a></li>
          <li class="${'active' if c.active=='auth_tokens' else ''}"><a href="${h.route_path('my_account_auth_tokens')}">${_('Auth Tokens')}</a></li>
          ## TODO: Find a better integration of oauth views into navigation.
          <% my_account_oauth_url = h.route_path_or_none('my_account_oauth') %>
          % if my_account_oauth_url:
          <li class="${'active' if c.active=='oauth' else ''}"><a href="${my_account_oauth_url}">${_('OAuth Identities')}</a></li>
          % endif
          <li class="${'active' if c.active=='emails' else ''}"><a href="${h.route_path('my_account_emails')}">${_('Emails')}</a></li>
          <li class="${'active' if c.active=='repos' else ''}"><a href="${h.route_path('my_account_repos')}">${_('Repositories')}</a></li>
          <li class="${'active' if c.active=='watched' else ''}"><a href="${h.route_path('my_account_watched')}">${_('Watched')}</a></li>
          <li class="${'active' if c.active=='pullrequests' else ''}"><a href="${h.route_path('my_account_pullrequests')}">${_('Pull Requests')}</a></li>
          <li class="${'active' if c.active=='perms' else ''}"><a href="${h.route_path('my_account_perms')}">${_('Permissions')}</a></li>
          <li class="${'active' if c.active=='my_notifications' else ''}"><a href="${h.route_path('my_account_notifications')}">${_('Live Notifications')}</a></li>
        </ul>
    </div>

    <div class="main-content-full-width">
        <%include file="/admin/my_account/my_account_${c.active}.mako"/>
    </div>
  </div>
</div>

</%def>
