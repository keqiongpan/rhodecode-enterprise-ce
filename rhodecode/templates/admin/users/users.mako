## -*- coding: utf-8 -*-
<%inherit file="/base/base.mako"/>

<%def name="title()">
    ${_('Users administration')}
    %if c.rhodecode_name:
        &middot; ${h.branding(c.rhodecode_name)}
    %endif
</%def>

<%def name="breadcrumbs_links()">
    <input class="q_filter_box" id="q_filter" size="15" type="text" name="filter" placeholder="${_('quick filter...')}" value=""/>
    ${h.link_to(_('Admin'),h.route_path('admin_home'))} &raquo; <span id="user_count">0</span>
</%def>

<%def name="menu_bar_nav()">
    ${self.menu_items(active='admin')}
</%def>

<%def name="main()">

<div class="box">

    <div class="title">
        ${self.breadcrumbs()}
        <ul class="links">
          <li>
            <a href="${h.route_path('users_new')}" class="btn btn-small btn-success">${_(u'Add User')}</a>
          </li>
        </ul>
    </div>

    <div id="repos_list_wrap">
        <table id="user_list_table" class="display"></table>
    </div>
</div>

<script type="text/javascript">

$(document).ready(function() {
    var $userListTable = $('#user_list_table');
    // user list
    $userListTable.DataTable({
      processing: true,
      serverSide: true,
      ajax: {
          "url": "${h.route_path('users_data')}",
          "dataSrc": function ( json ) {
              var filteredCount = json.recordsFiltered;
              var filteredInactiveCount = json.recordsFilteredInactive;
              var totalInactive = json.recordsTotalInactive;
              var total = json.recordsTotal;

              var _text = _gettext(
                  "{0} ({1} inactive) of {2} users ({3} inactive)").format(
                      filteredCount, filteredInactiveCount, total, totalInactive);

              if(total === filteredCount){
                  _text = _gettext(
                      "{0} users ({1} inactive)").format(total, totalInactive);
              }
              $('#user_count').text(_text);
              return json.data;
          }
      },
      dom: 'rtp',
      pageLength: ${c.visual.admin_grid_items},
      order: [[ 0, "asc" ]],
      columns: [
         { data: {"_": "username",
                  "sort": "username"}, title: "${_('Username')}", className: "td-user" },
         { data: {"_": "email",
                  "sort": "email"}, title: "${_('Email')}", className: "td-email"  },
         { data: {"_": "first_name",
                  "sort": "first_name"}, title: "${_('First Name')}", className: "td-user" },
         { data: {"_": "last_name",
                  "sort": "last_name"}, title: "${_('Last Name')}", className: "td-user" },
         { data: {"_": "last_activity",
                  "sort": "last_activity",
                  "type": Number}, title: "${_('Last activity')}", className: "td-time" },
         { data: {"_": "active",
                  "sort": "active"}, title: "${_('Active')}", className: "td-active" },
         { data: {"_": "admin",
                  "sort": "admin"}, title: "${_('Admin')}", className: "td-admin" },
         { data: {"_": "extern_type",
                  "sort": "extern_type"}, title: "${_('Auth type')}", className: "td-type"  },
         { data: {"_": "action",
                  "sort": "action"}, title: "${_('Action')}", className: "td-action", orderable: false }
      ],
      language: {
          paginate: DEFAULT_GRID_PAGINATION,
          sProcessing: _gettext('loading...'),
          emptyTable: _gettext("No users available yet.")
      },

      "createdRow": function ( row, data, index ) {
          if (!data['active_raw']){
            $(row).addClass('closed')
          }
      }
    });

    $userListTable.on('xhr.dt', function(e, settings, json, xhr){
        $userListTable.css('opacity', 1);
    });

    $userListTable.on('preXhr.dt', function(e, settings, data){
        $userListTable.css('opacity', 0.3);
    });

    // filter
    $('#q_filter').on('keyup',
        $.debounce(250, function() {
            $userListTable.DataTable().search(
                $('#q_filter').val()
            ).draw();
        })
    );

  });
</script>

</%def>
