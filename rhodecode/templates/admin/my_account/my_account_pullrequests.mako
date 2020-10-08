<%namespace name="base" file="/base/base.mako"/>

<div class="panel panel-default">
  <div class="panel-body">
    <div style="height: 35px">
        <%
        selected_filter = 'all'
        if c.closed:
            selected_filter = 'all_closed'
        %>

        <ul class="button-links">
          <li class="btn ${h.is_active('all', selected_filter)}"><a href="${h.route_path('my_account_pullrequests')}">${_('All')}</a></li>
          <li class="btn ${h.is_active('all_closed', selected_filter)}"><a href="${h.route_path('my_account_pullrequests', _query={'pr_show_closed':1})}">${_('All + Closed')}</a></li>
        </ul>

        <div class="grid-quick-filter">
            <ul class="grid-filter-box">
                <li class="grid-filter-box-icon">
                    <i class="icon-search"></i>
                </li>
                <li class="grid-filter-box-input">
                    <input class="q_filter_box" id="q_filter" size="15" type="text" name="filter" placeholder="${_('quick filter...')}" value=""/>
                </li>
            </ul>
        </div>
    </div>
  </div>
</div>

<div class="panel panel-default">
    <div class="panel-heading">
        <h3 class="panel-title">${_('Pull Requests You Participate In')}</h3>
    </div>
    <div class="panel-body panel-body-min-height">
        <table id="pull_request_list_table" class="rctable table-bordered"></table>
    </div>
</div>

<script type="text/javascript">
    $(document).ready(function () {

        var $pullRequestListTable = $('#pull_request_list_table');

        // participating object list
        $pullRequestListTable.DataTable({
            processing: true,
            serverSide: true,
            ajax: {
                "url": "${h.route_path('my_account_pullrequests_data')}",
                "data": function (d) {
                    d.closed = "${c.closed}";
                },
                "dataSrc": function (json) {
                    return json.data;
                }
            },

            dom: 'rtp',
            pageLength: ${c.visual.dashboard_items},
            order: [[2, "desc"]],
            columns: [
                {
                    data: {
                        "_": "target_repo",
                        "sort": "target_repo"
                    }, title: "${_('Target Repo')}", className: "td-targetrepo", orderable: false
                },
                {
                    data: {
                        "_": "status",
                        "sort": "status"
                    }, title: "", className: "td-status", orderable: false
                },
                {
                    data: {
                        "_": "name",
                        "sort": "name_raw"
                    }, title: "${_('Id')}", className: "td-componentname", "type": "num"
                },
                {
                    data: {
                        "_": "title",
                        "sort": "title"
                    }, title: "${_('Title')}", className: "td-description"
                },
                {
                    data: {
                        "_": "author",
                        "sort": "author_raw"
                    }, title: "${_('Author')}", className: "td-user", orderable: false
                },
                {
                    data: {
                        "_": "comments",
                        "sort": "comments_raw"
                    }, title: "", className: "td-comments", orderable: false
                },
                {
                    data: {
                        "_": "updated_on",
                        "sort": "updated_on_raw"
                    }, title: "${_('Last Update')}", className: "td-time"
                }
            ],
            language: {
                paginate: DEFAULT_GRID_PAGINATION,
                sProcessing: _gettext('loading...'),
                emptyTable: _gettext("There are currently no open pull requests requiring your participation.")
            },
            "drawCallback": function (settings, json) {
                timeagoActivate();
                tooltipActivate();
            },
            "createdRow": function (row, data, index) {
                if (data['closed']) {
                    $(row).addClass('closed');
                }
                if (data['owned']) {
                    $(row).addClass('owned');
                }
            }
        });
        $pullRequestListTable.on('xhr.dt', function (e, settings, json, xhr) {
            $pullRequestListTable.css('opacity', 1);
        });

        $pullRequestListTable.on('preXhr.dt', function (e, settings, data) {
            $pullRequestListTable.css('opacity', 0.3);
        });

        // filter
        $('#q_filter').on('keyup',
            $.debounce(250, function () {
                $pullRequestListTable.DataTable().search(
                        $('#q_filter').val()
                ).draw();
            })
        );

    });


</script>
