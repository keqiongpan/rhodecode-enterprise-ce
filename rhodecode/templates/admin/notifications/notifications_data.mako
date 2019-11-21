<%namespace name="base" file="/base/base.mako"/>

<div class="panel panel-default">
  <div class="panel-heading">
    <h3 class="panel-title">${_('My notifications')}</h3>
  </div>

  <div class="panel-body">
    %if c.notifications:

        <div class="notification-list  notification-table">
            %for notification in c.notifications:
            <div id="notification_${notification.notification.notification_id}" class="container ${'unread' if not notification.read else '' }">
            <div class="notification-header">
              <div class="desc ${'unread' if not notification.read else '' }">
                  ${base.gravatar(notification.notification.created_by_user.email, 16)}
                  <a href="${h.route_path('notifications_show', notification_id=notification.notification.notification_id)}">
                    ${h.notification_description(notification.notification, request)}
                  </a>
              </div>
              <div class="delete-notifications">
                <span onclick="deleteNotification(${notification.notification.notification_id})" class="delete-notification tooltip" title="${_('Delete')}"><i class="icon-delete"></i></span>
              </div>
              <div class="read-notifications">
              %if not notification.read:
                <span onclick="readNotification(${notification.notification.notification_id})" class="read-notification tooltip" title="${_('Mark as read')}"><i class="icon-ok"></i></span>
              %endif
              </div>
            </div>
                <div class="notification-subject"></div>
            </div>
            %endfor
        </div>

        <div class="notification-paginator">
            <div class="pagination-wh pagination-left">
                ${c.notifications.render()}
            </div>
        </div>

    %else:
        <div class="table">${_('No notifications here yet')}</div>
    %endif

  </div>
</div>
