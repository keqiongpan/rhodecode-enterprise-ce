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
        ${self.breadcrumbs()}
    </div>
    <div class="table">
      <div id="notification_${c.notification.notification_id}" class="main-content-full">
        <div class="notification-header">
          ${self.gravatar(c.notification.created_by_user.email, 30)}
          <div class="desc">
              ${c.notification.description}
          </div>
          <div class="delete-notifications">
            <span class="delete-notification tooltip" title="${_('Delete')}" onclick="deleteNotification(${c.notification.notification_id}, [function(){window.location=pyroutes.url('notifications_show_all')}])" class="delete-notification action"><i class="icon-delete" ></i></span>
          </div>
        </div>
        <div class="notification-body">
        <div class="notification-subject">
            <h3>${_('Subject')}: ${c.notification.subject}</h3>
        </div>
        %if c.notification.body:
            ${h.render(c.notification.body, renderer=c.visual.default_renderer, mentions=True)}
        %endif
        </div>
      </div>
    </div>
</div>

</%def>
