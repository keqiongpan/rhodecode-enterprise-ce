<%inherit file="/base/base.mako"/>

<%def name="title()">
    ${_('{} Pull Requests').format(c.repo_name)}
    %if c.rhodecode_name:
        &middot; ${h.branding(c.rhodecode_name)}
    %endif
</%def>

<%def name="breadcrumbs_links()"></%def>

<%def name="menu_bar_nav()">
    ${self.menu_items(active='repositories')}
</%def>


<%def name="menu_bar_subnav()">
    ${self.repo_menu(active='showpullrequest')}
</%def>


<%def name="main()">

<div class="box">
    <div class="title">
    <ul class="button-links">
      <li class="btn ${h.is_active('open', c.active)}"><a href="${h.route_path('pullrequest_show_all',repo_name=c.repo_name,         _query={'source':0})}">${_('Opened')}</a></li>
      <li class="btn ${h.is_active('my', c.active)}"><a href="${h.route_path('pullrequest_show_all',repo_name=c.repo_name,           _query={'source':0,'my':1})}">${_('Opened by me')}</a></li>
      <li class="btn ${h.is_active('awaiting', c.active)}"><a href="${h.route_path('pullrequest_show_all',repo_name=c.repo_name,     _query={'source':0,'awaiting_review':1})}">${_('Awaiting review')}</a></li>
      <li class="btn ${h.is_active('awaiting_my', c.active)}"><a href="${h.route_path('pullrequest_show_all',repo_name=c.repo_name,  _query={'source':0,'awaiting_my_review':1})}">${_('Awaiting my review')}</a></li>
      <li class="btn ${h.is_active('closed', c.active)}"><a href="${h.route_path('pullrequest_show_all',repo_name=c.repo_name,       _query={'source':0,'closed':1})}">${_('Closed')}</a></li>
      <li class="btn ${h.is_active('source', c.active)}"><a href="${h.route_path('pullrequest_show_all',repo_name=c.repo_name,       _query={'source':1})}">${_('From this repo')}</a></li>
    </ul>

    <ul class="links">
        % if c.rhodecode_user.username != h.DEFAULT_USER:
        <li>
            <span>
                <a id="open_new_pull_request" class="btn btn-small btn-success" href="${h.route_path('pullrequest_new',repo_name=c.repo_name)}">
                    ${_('Open new Pull Request')}
                </a>
            </span>
        </li>
        % endif

        <li>
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
        </li>

    </ul>

    </div>

    <div class="main-content-full-width">
        <table id="pull_request_list_table" class="rctable table-bordered"></table>
    </div>

</div>

<script type="text/javascript">
$(document).ready(function() {
    var $pullRequestListTable = $('#pull_request_list_table');

    // object list
    $pullRequestListTable.DataTable({
      processing: true,
      serverSide: true,
      stateSave: true,
      stateDuration: -1,
      ajax: {
          "url": "${h.route_path('pullrequest_show_all_data', repo_name=c.repo_name)}",
          "data": function (d) {
              d.source = "${c.source}";
              d.closed = "${c.closed}";
              d.my = "${c.my}";
              d.awaiting_review = "${c.awaiting_review}";
              d.awaiting_my_review = "${c.awaiting_my_review}";
          }
      },
      dom: 'rtp',
      pageLength: ${c.visual.dashboard_items},
      order: [[ 1, "desc" ]],
      columns: [
         { data: {"_": "status",
                  "sort": "status"}, title: "", className: "td-status", orderable: false},
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
            emptyTable: _gettext("No pull requests available yet.")
      },
      "drawCallback": function( settings, json ) {
          timeagoActivate();
          tooltipActivate();
      },
      "createdRow": function ( row, data, index ) {
          if (data['closed']) {
              $(row).addClass('closed');
          }
      },
      "stateSaveParams": function (settings, data) {
          data.search.search = ""; // Don't save search
          data.start = 0;  // don't save pagination
      }
    });

    $pullRequestListTable.on('xhr.dt', function(e, settings, json, xhr){
        $pullRequestListTable.css('opacity', 1);
    });

    $pullRequestListTable.on('preXhr.dt', function(e, settings, data){
        $pullRequestListTable.css('opacity', 0.3);
    });

    // filter
    $('#q_filter').on('keyup',
        $.debounce(250, function() {
            $pullRequestListTable.DataTable().search(
                $('#q_filter').val()
            ).draw();
        })
    );

});

</script>
</%def>
