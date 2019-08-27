<%inherit file="/base/base.mako"/>


<%def name="menu_bar_subnav()">
  % if c.repo_group:
    ${self.repo_group_menu(active='home')}
  % endif
</%def>


<%def name="main()">
   <div class="box">
        <!-- box / title -->
        <div class="title">

        </div>
        <!-- end box / title -->
        <div class="table">
            <div id="groups_list_wrap">
                <table id="group_list_table" class="display" style="width: 100%"></table>
            </div>
        </div>

        <div class="table">
            <div id="repos_list_wrap">
                <table id="repo_list_table" class="display" style="width: 100%"></table>
            </div>
        </div>

       ## no repository groups and repos present, show something to the users
       % if c.repo_groups_data == '[]' and c.repos_data == '[]':
        <div class="table">
            <h2 class="no-object-border">
                 ${_('No repositories or repositories groups exists here.')}
            </h2>
        </div>
       % endif

    </div>
    <script>
      $(document).ready(function() {

        // repo group list
        % if c.repo_groups_data != '[]':
        $('#group_list_table').DataTable({
          data: ${c.repo_groups_data|n},
          dom: 'rtp',
          pageLength: ${c.visual.dashboard_items},
          order: [[ 0, "asc" ]],
          columns: [
             { data: {"_": "name",
                      "sort": "name_raw"}, title: "${_('Name')}", className: "truncate-wrap td-grid-name" },
             { data: 'menu', "bSortable": false, className: "quick_repo_menu" },
             { data: {"_": "desc",
                      "sort": "desc"}, title: "${_('Description')}", className: "td-description" },
             { data: {"_": "last_change",
                      "sort": "last_change_raw",
                      "type": Number}, title: "${_('Last Change')}", className: "td-time" },
             { data: {"_": "last_changeset",
                      "sort": "last_changeset_raw",
                      "type": Number}, title: "", className: "td-hash" },
             { data: {"_": "owner",
                      "sort": "owner"}, title: "${_('Owner')}", className: "td-user" }
          ],
          language: {
            paginate: DEFAULT_GRID_PAGINATION,
            emptyTable: _gettext("No repository groups available yet.")
          },
          "drawCallback": function( settings, json ) {
              timeagoActivate();
              quick_repo_menu();
              // hide pagination for single page
              if (settings._iDisplayLength > settings.fnRecordsDisplay()) {
                  $(settings.nTableWrapper).find('.dataTables_paginate').hide();
              }
          }
        });
        % endif

        // repo list
        % if c.repos_data != '[]':
        $('#repo_list_table').DataTable({
          data: ${c.repos_data|n},
          dom: 'rtp',
          order: [[ 0, "asc" ]],
          pageLength: ${c.visual.dashboard_items},
          columns: [
             { data: {"_": "name",
                      "sort": "name_raw"}, title: "${_('Name')}", className: "truncate-wrap td-grid-name" },
             { data: 'menu', "bSortable": false, className: "quick_repo_menu" },
             { data: {"_": "desc",
                      "sort": "desc"}, title: "${_('Description')}", className: "td-description" },
             { data: {"_": "last_change",
                      "sort": "last_change_raw",
                      "type": Number}, title: "${_('Last Change')}", className: "td-time" },
             { data: {"_": "last_changeset",
                      "sort": "last_changeset_raw",
                      "type": Number}, title: "${_('Commit')}", className: "td-hash" },
             { data: {"_": "owner",
                      "sort": "owner"}, title: "${_('Owner')}", className: "td-user" }
          ],
          language: {
              paginate: DEFAULT_GRID_PAGINATION,
              emptyTable: _gettext("No repositories available yet.")
          },
          "drawCallback": function( settings, json ) {
              timeagoActivate();
              quick_repo_menu();
              // hide pagination for single page
              if (settings._iDisplayLength > settings.fnRecordsDisplay()) {
                  $(settings.nTableWrapper).find('.dataTables_paginate').hide();
              }
          }
        });
        % endif

      });
    </script>
</%def>
