<%namespace name="base" file="/base/base.mako"/>

<div class="panel panel-default">
  <div class="panel-body">
      %if c.closed:
        ${h.checkbox('show_closed',checked="checked", label=_('Show Closed Pull Requests'))}
      %else:
        ${h.checkbox('show_closed',label=_('Show Closed Pull Requests'))}
      %endif
  </div>
</div>

<div class="panel panel-default">
    <div class="panel-heading">
        <h3 class="panel-title">${_('Pull Requests You Participate In')}</h3>
    </div>
    <div class="panel-body panel-body-min-height">
        <table id="pull_request_list_table" class="display"></table>
    </div>
</div>

<script type="text/javascript">
$(document).ready(function() {

    $('#show_closed').on('click', function(e){
        if($(this).is(":checked")){
            window.location = "${h.route_path('my_account_pullrequests', _query={'pr_show_closed':1})}";
        }
        else{
            window.location = "${h.route_path('my_account_pullrequests')}";
        }
    });

    var $pullRequestListTable = $('#pull_request_list_table');

        // participating object list
        $pullRequestListTable.DataTable({
          processing: true,
          serverSide: true,
          ajax: {
              "url": "${h.route_path('my_account_pullrequests_data')}",
              "data": function (d) {
                  d.closed = "${c.closed}";
              }
          },
          dom: 'rtp',
          pageLength: ${c.visual.dashboard_items},
          order: [[ 2, "desc" ]],
          columns: [
             { data: {"_": "status",
                      "sort": "status"}, title: "", className: "td-status", orderable: false},
             { data: {"_": "target_repo",
                      "sort": "target_repo"}, title: "${_('Target Repo')}", className: "td-targetrepo", orderable: false},
             { data: {"_": "name",
                      "sort": "name_raw"}, title: "${_('Id')}", className: "td-componentname", "type": "num" },
             { data: {"_": "title",
                      "sort": "title"}, title: "${_('Title')}", className: "td-description" },
             { data: {"_": "author",
                      "sort": "author_raw"}, title: "${_('Author')}", className: "td-user", orderable: false },
             { data: {"_": "comments",
                      "sort": "comments_raw"}, title: "", className: "td-comments", orderable: false},
             { data: {"_": "updated_on",
                      "sort": "updated_on_raw"}, title: "${_('Last Update')}", className: "td-time" }
          ],
          language: {
                paginate: DEFAULT_GRID_PAGINATION,
                sProcessing: _gettext('loading...'),
                emptyTable: _gettext("There are currently no open pull requests requiring your participation.")
          },
          "drawCallback": function( settings, json ) {
              timeagoActivate();
              tooltipActivate();
          },
          "createdRow": function ( row, data, index ) {
              if (data['closed']) {
                $(row).addClass('closed');
              }
              if (data['owned']) {
                $(row).addClass('owned');
              }
              if (data['state'] !== 'created') {
                  $(row).addClass('state-' + data['state']);
              }
          }
        });
        $pullRequestListTable.on('xhr.dt', function(e, settings, json, xhr){
            $pullRequestListTable.css('opacity', 1);
        });

        $pullRequestListTable.on('preXhr.dt', function(e, settings, data){
            $pullRequestListTable.css('opacity', 0.3);
        });
    });
</script>
