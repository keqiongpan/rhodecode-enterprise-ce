## -*- coding: utf-8 -*-
<%inherit file="/base/base.mako"/>

<%def name="title()">
    ${_('Show notification')} ${c.rhodecode_user.username}
    %if c.rhodecode_name:
        &middot; ${h.branding(c.rhodecode_name)}
    %endif
</%def>

<%def name="breadcrumbs_links()">
    ${h.link_to(_('My Notifications'), h.route_path('notifications_show_all'))}
    &raquo;
    ${_('Show notification')}
</%def>

<%def name="menu_bar_nav()">
    ${self.menu_items(active='admin')}
</%def>

<%def name="main()">
<div class="box">

    <!-- box / title -->
    <div class="title">
        Rendered plain text using markup renderer
    </div>
    <div class="table">
      <div >
        <div class="notification-header">
          GRAVATAR
          <div class="desc">
              DESC
          </div>
        </div>
        <div class="notification-body">
        <div class="notification-subject">
            <h3>${_('Subject')}: ${c.subject}</h3>
        </div>
            ${c.email_body|n}
        </div>
      </div>
    </div>
</div>

</%def>



