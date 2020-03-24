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
        <div id="no_grid_data" class="table" style="display: none">
            <h2>
                 ${_('No repositories or repositories groups exists here.')}
            </h2>
        </div>

        <div id="grid_data_loading" class="table" style="display: none">
            <i class="icon-spin animate-spin"></i>
            ${_('loading...')}
        </div>

        <div class="table">
            <div id="groups_list_wrap" style="min-height: 200px;display: none">
                <table id="group_list_table" class="display" style="width: 100%;"></table>
            </div>
        </div>

        <div class="table">
            <div id="repos_list_wrap" style="min-height: 200px;display: none">
                <table id="repo_list_table" class="display" style="width: 100%;"></table>
            </div>
        </div>

    </div>

    <script>
    $(document).ready(function () {
        var noRepoData = null;
        var noGroupData = null;
        var $gridDataLoading = $('#grid_data_loading');

        // global show loading of hidden grids
        $(document).on('preInit.dt', function (e, settings) {
            $gridDataLoading.show();
        });

        ## repo group list
        var $groupListTable = $('#group_list_table');

        $groupListTable.on('xhr.dt', function (e, settings, json, xhr) {
            $gridDataLoading.hide();
        });
        $groupListTable.DataTable({
            processing: true,
            serverSide: true,
            ajax: {
                "url": "${h.route_path('main_page_repo_groups_data')}",
                "data": function (d) {
                    % if c.repo_group:
                        d.repo_group_id = ${c.repo_group.group_id}
                    % endif
                }
            },
            dom: 'rtp',
            pageLength: ${c.visual.dashboard_items},
            order: [[0, "asc"]],
            columns: [
                {
                    data: {
                        "_": "name",
                        "sort": "name"
                    }, title: "${_('Name')}", className: "truncate-wrap td-grid-name"
                },
                {
                    data: 'menu', "bSortable": false, className: "quick_repo_menu"
                },
                {
                    data: {
                        "_": "desc",
                        "sort": "desc"
                    }, title: "${_('Description')}", className: "td-description"
                },
                {
                    data: {
                        "_": "last_change",
                        "sort": "last_change",
                        "type": Number
                    }, title: "${_('Last Change')}", className: "td-time"
                },
                {
                    data: {
                        "_": "last_changeset",
                        "sort": "last_changeset_raw",
                        "type": Number
                    }, title: "", className: "td-hash", orderable: false
                },
                {
                    data: {
                        "_": "owner",
                        "sort": "owner"
                    }, title: "${_('Owner')}", className: "td-user"
                }
            ],
            language: {
                paginate: DEFAULT_GRID_PAGINATION,
                sProcessing: _gettext('loading...'),
                emptyTable: _gettext("No repository groups present.")
            },
            "drawCallback": function (settings, json) {

                // hide grid if it's empty
                if (settings.fnRecordsDisplay() === 0) {
                    noGroupData = true;
                    // both hidden, show no-data
                    if (noRepoData === true) {
                        $('#no_grid_data').show();
                    }
                } else {
                    $('#groups_list_wrap').show();
                }

                timeagoActivate();
                tooltipActivate();
                quick_repo_menu();
                // hide pagination for single page
                if (settings._iDisplayLength >= settings.fnRecordsDisplay()) {
                    $(settings.nTableWrapper).find('.dataTables_paginate').hide();
                }

            },
        });


        ##  repo list
        var $repoListTable = $('#repo_list_table');

        $repoListTable.on('xhr.dt', function (e, settings, json, xhr) {
            $gridDataLoading.hide();
        });
        $repoListTable.DataTable({
            processing: true,
            serverSide: true,
            ajax: {
                "url": "${h.route_path('main_page_repos_data')}",
                "data": function (d) {
                    % if c.repo_group:
                        d.repo_group_id = ${c.repo_group.group_id}
                    % endif
                }
            },
            order: [[0, "asc"]],
            dom: 'rtp',
            pageLength: ${c.visual.dashboard_items},
            columns: [
                {
                    data: {
                        "_": "name",
                        "sort": "name"
                    }, title: "${_('Name')}", className: "truncate-wrap td-grid-name"
                },
                {
                    data: 'menu', "bSortable": false, className: "quick_repo_menu"
                },
                {
                    data: {
                        "_": "desc",
                        "sort": "desc"
                    }, title: "${_('Description')}", className: "td-description"
                },
                {
                    data: {
                        "_": "last_change",
                        "sort": "last_change",
                        "type": Number
                    }, title: "${_('Last Change')}", className: "td-time"
                },
                {
                    data: {
                        "_": "last_changeset",
                        "sort": "last_changeset_raw",
                        "type": Number
                    }, title: "${_('Commit')}", className: "td-hash", orderable: false
                },
                 {
                    data: {
                        "_": "owner",
                        "sort": "owner"
                    }, title: "${_('Owner')}", className: "td-user"
                }
            ],
            language: {
                paginate: DEFAULT_GRID_PAGINATION,
                sProcessing: _gettext('loading...'),
                emptyTable: _gettext("No repositories present.")
            },
            "drawCallback": function (settings, json) {

                // hide grid if it's empty
                if (settings.fnRecordsDisplay() == 0) {
                    noRepoData = true;

                    // both hidden, show no-data
                    if (noGroupData === true) {
                        $('#no_grid_data').show()
                    }
                } else {
                    $('#repos_list_wrap').show()
                }

                timeagoActivate();
                tooltipActivate();
                quick_repo_menu();
                // hide pagination for single page
                if (settings._iDisplayLength >= settings.fnRecordsDisplay()) {
                    $(settings.nTableWrapper).find('.dataTables_paginate').hide();
                }

            },
        });

    });
    </script>
</%def>
