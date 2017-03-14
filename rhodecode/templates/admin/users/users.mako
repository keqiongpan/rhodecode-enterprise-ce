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
    ${h.link_to(_('Admin'),h.url('admin_home'))} &raquo; <span id="user_count">0</span>
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
            <a href="${h.url('new_user')}" class="btn btn-small btn-success">${_(u'Add User')}</a>
          </li>
        </ul>
    </div>

    <div id="repos_list_wrap">
        <table id="user_list_table" class="display"></table>
    </div>
</div>

<script type="text/javascript">

$(document).ready(function() {

    var getDatatableCount = function(){
      var table = $('#user_list_table').dataTable();
      var page = table.api().page.info();
      var  active = page.recordsDisplay;
      var  total = page.recordsTotal;

      var _text = _gettext("{0} out of {1} users").format(active, total);
      $('#user_count').text(_text);
    };

    // user list
    $('#user_list_table').DataTable({
      processing: true,
      serverSide: true,
      ajax: "${h.route_path('users_data')}",
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
                  "type": Number}, title: "${_('Last activity')}", className: "td-time", orderable: false },
         { data: {"_": "active",
                  "sort": "active"}, title: "${_('Active')}", className: "td-active" },
         { data: {"_": "admin",
                  "sort": "admin"}, title: "${_('Admin')}", className: "td-admin" },
         { data: {"_": "extern_type",
                  "sort": "extern_type"}, title: "${_('Auth type')}", className: "td-type"  },
         { data: {"_": "action",
                  "sort": "action"}, title: "${_('Action')}", className: "td-action" }
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

    $('#user_list_table').on('xhr.dt', function(e, settings, json, xhr){
        $('#user_list_table').css('opacity', 1);
    });

    $('#user_list_table').on('preXhr.dt', function(e, settings, data){
        $('#user_list_table').css('opacity', 0.3);
    });

    // refresh counters on draw
    $('#user_list_table').on('draw.dt', function(){
        getDatatableCount();
    });

    // filter
    $('#q_filter').on('keyup',
        $.debounce(250, function() {
            $('#user_list_table').DataTable().search(
                $('#q_filter').val()
            ).draw();
        })
    );

  });
</script>

</%def>
