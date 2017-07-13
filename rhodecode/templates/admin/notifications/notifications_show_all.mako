## -*- coding: utf-8 -*-
<%inherit file="/base/base.mako"/>

<%def name="title()">
    ${_('My Notifications')} ${c.rhodecode_user.username}
    %if c.rhodecode_name:
        &middot; ${h.branding(c.rhodecode_name)}
    %endif
</%def>

<%def name="breadcrumbs_links()">
    ${_('My Notifications')}
</%def>

<%def name="menu_bar_nav()">
    ${self.menu_items(active='my_account')}
</%def>

<%def name="main()">
<div class="box">
  <div class="title">
      ${self.breadcrumbs()}
      <div class="notifications_buttons">
      %if c.notifications:
          <button id='mark_all_read' class="btn btn-default" type="submit">
              ${_('Mark all as read')}
          </button>
      %else:
          <button class="btn btn-default" type="submit" disabled="disabled">
              ${_('Mark all as read')}
          </button>
      %endif
      </div>
  </div>

  <div class="sidebar-col-wrapper scw-small">
    ##main
    <div class="sidebar">
        <ul class="nav nav-pills nav-stacked">
            <li id='unread' class="${'active' if c.current_filter=='unread' else ''}"><a href="${h.route_path('notifications_show_all', _query=dict(type=c.unread_type))}">${_('Unread')} (${c.unread_count})</a></li>
            <li id='all' class="${'active' if c.current_filter=='all' else ''}"><a href="${h.route_path('notifications_show_all', _query=dict(type=c.all_type))}">${_('All')}</a></li>
            <li id='comment' class="${'active' if c.current_filter=='comment' else ''}"><a href="${h.route_path('notifications_show_all', _query=dict(type=c.comment_type))}">${_('Comments')}</a></li>
            <li id='pull_request' class="${'active' if c.current_filter=='pull_request' else ''}"><a href="${h.route_path('notifications_show_all', _query=dict(type=c.pull_request_type))}">${_('Pull Requests')}</a></li>
        </ul>
    </div>

    <div class="main-content-full-width">
        <%include file='notifications_data.mako'/>
    </div>
  </div>
</div>

<script type="text/javascript">

    $('#mark_all_read').on('click',function(e){
        //set notifications as read
        var url = "${h.route_path('notifications_mark_all_read', _query=request.GET.mixed())}";
        $.post(url, {'csrf_token': CSRF_TOKEN}).
          done(function(data){
              window.location = "${request.current_route_path(_query=request.GET.mixed())}";
            })
            .fail(function(data, textStatus, errorThrown){
                alert("Error while saving notifications.\nError code {0} ({1}). URL: {2}".format(data.status,data.statusText,$(this)[0].url));
            });
    });

</script>
</%def>
