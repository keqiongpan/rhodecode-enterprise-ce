## -*- coding: utf-8 -*-
<%inherit file="/base/base.mako"/>

<%def name="title()">
    ${_('%s Forks') % c.repo_name}
    %if c.rhodecode_name:
        &middot; ${h.branding(c.rhodecode_name)}
    %endif
</%def>

<%def name="breadcrumbs_links()"></%def>

<%def name="menu_bar_nav()">
    ${self.menu_items(active='repositories')}
</%def>

<%def name="menu_bar_subnav()">
    ${self.repo_menu(active='summary')}
</%def>

<%def name="main()">
<div class="box">
    <div class="title">

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
    var $forksListTable = $('#fork_list_table');

    // fork list
    $forksListTable.DataTable({
      processing: true,
      serverSide: true,
      ajax: {
          "url": "${h.route_path('repo_forks_data', repo_name=c.repo_name)}",
      },
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

    $forksListTable.on('xhr.dt', function(e, settings, json, xhr){
        $forksListTable.css('opacity', 1);
    });

    $forksListTable.on('preXhr.dt', function(e, settings, data){
        $forksListTable.css('opacity', 0.3);
    });

    // filter
    $('#q_filter').on('keyup',
        $.debounce(250, function() {
            $forksListTable.DataTable().search(
                $('#q_filter').val()
            ).draw();
        })
    );

  });
</script>
</%def>
