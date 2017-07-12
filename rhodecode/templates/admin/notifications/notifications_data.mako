<%namespace name="base" file="/base/base.mako"/>
%if c.notifications:
<%
unread = lambda n:{False:'unread'}.get(n)
%>


<div class="notification-list  notification-table">
%for notification in c.notifications:
  <div id="notification_${notification.notification.notification_id}" class="container ${unread(notification.read)}">
    <div class="notification-header">
      <div class="desc ${unread(notification.read)}">
        <a href="${h.url('notification', notification_id=notification.notification.notification_id)}">
          ${base.gravatar(notification.notification.created_by_user.email, 16)}
          ${notification.notification.description}
        </a>
      </div>
      <div class="delete-notifications">
        <span id="${notification.notification.notification_id}" class="delete-notification"><i class="icon-delete" ></i></span>
      </div>
      <div class="read-notifications">
      %if not notification.read:
        <span id="${notification.notification.notification_id}" class="read-notification"><i class="icon-ok" ></i></span>
      %endif
      </div>
    </div>
        <div class="notification-subject"></div>
  </div>
%endfor
</div>

<div class="notification-paginator">
  <div class="pagination-wh pagination-left">
  ${c.notifications.pager('$link_previous ~2~ $link_next')}
  </div>
</div>

%else:
    <div class="table">${_('No notifications here yet')}</div>
%endif
