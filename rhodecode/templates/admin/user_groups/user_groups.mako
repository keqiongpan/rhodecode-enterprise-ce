## -*- coding: utf-8 -*-
<%inherit file="/base/base.mako"/>

<%def name="title()">
    ${_('User groups administration')}
    %if c.rhodecode_name:
        &middot; ${h.branding(c.rhodecode_name)}
    %endif
</%def>

<%def name="breadcrumbs_links()"></%def>

<%def name="menu_bar_nav()">
    ${self.menu_items(active='admin')}
</%def>

<%def name="menu_bar_subnav()">
    ${self.admin_menu(active='user_groups')}
</%def>

<%def name="main()">
<div class="box">

    <div class="title">
        <input class="q_filter_box" id="q_filter" size="15" type="text" name="filter" placeholder="${_('quick filter...')}" value=""/>
        <span id="user_group_count">0</span>

        <ul class="links">
        %if c.can_create_user_group:
            <li>
              <a href="${h.route_path('user_groups_new')}" class="btn btn-small btn-success">${_(u'Add User Group')}</a>
            </li>
        %endif
        </ul>
    </div>

    <div id="repos_list_wrap">
        <table id="user_group_list_table" class="display"></table>
    </div>

</div>
<script>
$(document).ready(function() {
    var $userGroupsListTable = $('#user_group_list_table');

    // user list
    $userGroupsListTable.DataTable({
      processing: true,
      serverSide: true,
      ajax: {
          "url": "${h.route_path('user_groups_data')}",
          "dataSrc": function (json) {
              var filteredCount = json.recordsFiltered;
              var filteredInactiveCount = json.recordsFilteredInactive;
              var totalInactive = json.recordsTotalInactive;
              var total = json.recordsTotal;

              var _text = _gettext(
                      "{0} ({1} inactive) of {2} user groups ({3} inactive)").format(
                      filteredCount, filteredInactiveCount, total, totalInactive);

              if (total === filteredCount) {
                  _text = _gettext(
                          "{0} user groups ({1} inactive)").format(total, totalInactive);
              }
              $('#user_group_count').text(_text);
              return json.data;
          },
      },

      dom: 'rtp',
      pageLength: ${c.visual.admin_grid_items},
      order: [[ 0, "asc" ]],
      columns: [
         { data: {"_": "users_group_name",
                  "sort": "users_group_name"}, title: "${_('Name')}", className: "td-componentname"  },
         { data: {"_": "description",
                  "sort": "description"}, title: "${_('Description')}", className: "td-description" },
         { data: {"_": "members",
                  "sort": "members"}, title: "${_('Members')}", className: "td-number" },
         { data: {"_": "sync",
                  "sort": "sync"}, title: "${_('Sync')}", className: "td-sync" },
         { data: {"_": "active",
                  "sort": "active"}, title: "${_('Active')}", className: "td-active" },
         { data: {"_": "owner",
                  "sort": "owner"}, title: "${_('Owner')}", className: "td-user" },
         { data: {"_": "action",
                  "sort": "action"}, title: "${_('Action')}", className: "td-action", orderable: false}
      ],
      language: {
          paginate: DEFAULT_GRID_PAGINATION,
          sProcessing: _gettext('loading...'),
          emptyTable: _gettext("No user groups available yet.")
      }
    });

    $userGroupsListTable.on('xhr.dt', function(e, settings, json, xhr){
        $userGroupsListTable.css('opacity', 1);
    });

    $userGroupsListTable.on('preXhr.dt', function(e, settings, data){
        $userGroupsListTable.css('opacity', 0.3);
    });

    // filter
    $('#q_filter').on('keyup',
        $.debounce(250, function() {
            $userGroupsListTable.DataTable().search(
                $('#q_filter').val()
            ).draw();
        })
    );

  });

</script>

</%def>
