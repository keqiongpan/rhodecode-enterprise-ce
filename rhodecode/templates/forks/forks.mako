## -*- coding: utf-8 -*-
<%inherit file="/base/base.mako"/>

<%def name="title()">
    ${_('%s Forks') % c.repo_name}
    %if c.rhodecode_name:
        &middot; ${h.branding(c.rhodecode_name)}
    %endif
</%def>

<%def name="breadcrumbs_links()">
    ${_('Forks')}
</%def>

<%def name="menu_bar_nav()">
    ${self.menu_items(active='repositories')}
</%def>

<%def name="menu_bar_subnav()">
    ${self.repo_menu(active='summary')}
</%def>

<%def name="main()">
<div class="box">
    <div class="title">
        ${self.repo_page_title(c.rhodecode_db_repo)}
        <ul class="links">
            <li>
                <a class="btn btn-small btn-success" href="${h.route_path('repo_fork_new',repo_name=c.repo_name)}">
                    ${_('Create new fork')}
                </a>
            </li>
        </ul>
    </div>

    <div id="fork_list_wrap">
        <table id="fork_list_table" class="display"></table>
    </div>
</div>



<script type="text/javascript">

$(document).ready(function() {
    var $userListTable = $('#fork_list_table');

    var getDatatableCount = function(){
      var table = $userListTable.dataTable();
      var page = table.api().page.info();
      var  active = page.recordsDisplay;
      var  total = page.recordsTotal;

      var _text = _gettext("{0} out of {1} users").format(active, total);
      $('#user_count').text(_text);
    };

    // user list
    $userListTable.DataTable({
      processing: true,
      serverSide: true,
      ajax: "${h.route_path('repo_forks_data', repo_name=c.repo_name)}",
      dom: 'rtp',
      pageLength: ${c.visual.dashboard_items},
      order: [[ 0, "asc" ]],
      columns: [
         { data: {"_": "username",
                  "sort": "username"}, title: "${_('Owner')}", className: "td-user" },
         { data: {"_": "fork_name",
                  "sort": "fork_name"}, title: "${_('Fork name')}", className: "td-email"  },
         { data: {"_": "description",
                  "sort": "description"}, title: "${_('Description')}", className: "td-user" },
         { data: {"_": "fork_date",
                  "sort": "fork_date"}, title: "${_('Forked')}", className: "td-user" },
         { data: {"_": "last_activity",
                  "sort": "last_activity",
                  "type": Number}, title: "${_('Last activity')}", className: "td-time" },
         { data: {"_": "action",
                  "sort": "action"}, title: "${_('Action')}", className: "td-action", orderable: false }
      ],

      language: {
          paginate: DEFAULT_GRID_PAGINATION,
          sProcessing: _gettext('loading...'),
          emptyTable: _gettext("No forks available yet.")
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

    // refresh counters on draw
    $userListTable.on('draw.dt', function(){
        getDatatableCount();
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
