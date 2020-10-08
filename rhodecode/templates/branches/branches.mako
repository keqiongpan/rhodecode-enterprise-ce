## -*- coding: utf-8 -*-
<%inherit file="/base/base.mako"/>

<%def name="title()">
    ${_('%s Branches') % c.repo_name}
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

        %if c.has_references:
          <ul class="links">
            <li>
                <input type="submit" id="compare_action" class="btn" disabled="disabled" value="${_('Compare Selected Branches')}"/>
            </li>
          </ul>
        %endif
        %if c.has_references:
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
            <div id="obj_count">0</div>
        %endif
      </div>
      <table id="obj_list_table" class="rctable table-bordered"></table>
    </div>

<script type="text/javascript">
$(document).ready(function() {

    var get_datatable_count = function(){
      var api = $('#obj_list_table').dataTable().api();
      var total = api.page.info().recordsDisplay
      var _text = _ngettext('{0} branch', '{0} branches', total).format(total);

      $('#obj_count').text(_text);
    };

    // object list
    $('#obj_list_table').DataTable({
      data: ${c.data|n},
      dom: 'rtp',
      pageLength: ${c.visual.dashboard_items},
      order: [[ 0, "asc" ]],
      columns: [
         { data: {"_": "name",
                  "sort": "name_raw"}, title: "${_('Name')}", className: "td-tags" },
         { data: {"_": "date",
                  "sort": "date_raw"}, title: "${_('Date')}", className: "td-time" },
         { data: {"_": "author",
                  "sort": "author"}, title: "${_('Author')}", className: "td-user" },
         { data: {"_": "commit",
                  "sort": "commit_raw",
                  "type": Number}, title: "${_('Commit')}", className: "td-hash" },
         { data: {"_": "compare",
                  "sort": "compare"}, title: "${_('Compare')}", className: "td-compare" }
      ],
      language: {
            paginate: DEFAULT_GRID_PAGINATION,
            emptyTable: _gettext("No branches available yet.")
      },
      "initComplete": function( settings, json ) {
          get_datatable_count();
          timeagoActivate();
          tooltipActivate();
          compare_radio_buttons("${c.repo_name}", 'branch');
      }
    });

    // update when things change
    $('#obj_list_table').on('draw.dt', function() {
        get_datatable_count();
        timeagoActivate();
        tooltipActivate();
    });

    // filter, filter both grids
    $('#q_filter').on( 'keyup', function () {
      var obj_api = $('#obj_list_table').dataTable().api();
      obj_api
        .columns(0)
        .search(this.value)
        .draw();
    });

    // refilter table if page load via back button
    $("#q_filter").trigger('keyup');

  });

</script>
</%def>
