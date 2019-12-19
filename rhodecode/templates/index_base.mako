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
            <h2 class="no-object-border">
                 ${_('No repositories or repositories groups exists here.')}
            </h2>
        </div>

        <div class="table">
            <div id="groups_list_wrap" style="min-height: 200px;">
                <table id="group_list_table" class="display" style="width: 100%;"></table>
            </div>
        </div>

        <div class="table">
            <div id="repos_list_wrap" style="min-height: 200px;">
                <table id="repo_list_table" class="display" style="width: 100%;"></table>
            </div>
        </div>

    </div>
    <script>
    $(document).ready(function () {

        // repo group list
        var $groupListTable = $('#group_list_table');

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
                        "sort": "name_raw"
                    }, title: "${_('Name')}", className: "truncate-wrap td-grid-name"
                },
                {data: 'menu', "bSortable": false, className: "quick_repo_menu"},
                {
                    data: {
                        "_": "desc",
                        "sort": "desc"
                    }, title: "${_('Description')}", className: "td-description"
                },
                {
                    data: {
                        "_": "last_change",
                        "sort": "last_change_raw",
                        "type": Number
                    }, title: "${_('Last Change')}", className: "td-time"
                },
                {
                    data: {
                        "_": "last_changeset",
                        "sort": "last_changeset_raw",
                        "type": Number
                    }, title: "", className: "td-hash"
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
                    $('#groups_list_wrap').hide();
                    // both hidden, show no-data
                    if ($('#repos_list_wrap').is(':hidden')) {
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

        $groupListTable.on('xhr.dt', function (e, settings, json, xhr) {
            $groupListTable.css('opacity', 1);
        });

        $groupListTable.on('preXhr.dt', function (e, settings, data) {
            $groupListTable.css('opacity', 0.3);
        });


        ##  // repo list
        var $repoListTable = $('#repo_list_table');

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
                        "sort": "name_raw"
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
                        "sort": "last_change_raw",
                        "type": Number
                    }, title: "${_('Last Change')}", className: "td-time", orderable: false
                },
                {
                    data: {
                        "_": "last_changeset",
                        "sort": "last_changeset_raw",
                        "type": Number
                    }, title: "${_('Commit')}", className: "td-hash"
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
                    $('#repos_list_wrap').hide()
                    // both hidden, show no-data
                    if ($('#groups_list_wrap').is(':hidden')) {
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

        $repoListTable.on('xhr.dt', function (e, settings, json, xhr) {
            $repoListTable.css('opacity', 1);
        });

        $repoListTable.on('preXhr.dt', function (e, settings, data) {
            $repoListTable.css('opacity', 0.3);
        });

    });
    </script>
</%def>
