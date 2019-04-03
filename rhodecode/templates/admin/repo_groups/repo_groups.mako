## -*- coding: utf-8 -*-
<%inherit file="/base/base.mako"/>

<%def name="title()">
    ${_('Repository groups administration')}
    %if c.rhodecode_name:
        &middot; ${h.branding(c.rhodecode_name)}
    %endif
</%def>

<%def name="breadcrumbs_links()">
    <input class="q_filter_box" id="q_filter" size="15" type="text" name="filter" placeholder="${_('quick filter...')}" value=""/>
    ${h.link_to(_('Admin'),h.route_path('admin_home'))} &raquo; <span id="repo_group_count">0</span>
</%def>

<%def name="menu_bar_nav()">
    ${self.menu_items(active='admin')}
</%def>

<%def name="main()">
<div class="box">
    <div class="title">
        ${self.breadcrumbs()}
        <ul class="links">
            %if h.HasPermissionAny('hg.admin','hg.repogroup.create.true')():
             <li>
               <a href="${h.route_path('repo_group_new')}" class="btn btn-small btn-success">${_(u'Add Repository Group')}</a>
             </li>
            %endif
        </ul>
    </div>
    <div id="repos_list_wrap">
        <table id="group_list_table" class="display"></table>
    </div>
</div>

<script>
$(document).ready(function() {
    var $repoGroupsListTable = $('#group_list_table');

   // repo group list
   $repoGroupsListTable.DataTable({
      processing: true,
      serverSide: true,
      ajax: {
          "url": "${h.route_path('repo_groups_data')}",
          "dataSrc": function (json) {
              var filteredCount = json.recordsFiltered;
              var filteredInactiveCount = json.recordsFilteredInactive;
              var totalInactive = json.recordsTotalInactive;
              var total = json.recordsTotal;

              var _text = _gettext(
                      "{0} of {1} repository groups").format(
                      filteredCount, total);

              if (total === filteredCount) {
                  _text = _gettext("{0} repository groups").format(total);
              }
              $('#repo_group_count').text(_text);
              return json.data;
          },
      },

      dom: 'rtp',
      pageLength: ${c.visual.admin_grid_items},
      order: [[ 0, "asc" ]],
      columns: [
         { data: {"_": "name",
                  "sort": "name_raw"}, title: "${_('Name')}", className: "td-componentname" },
         { data: 'menu', "bSortable": false, className: "quick_repo_menu" },
         { data: {"_": "desc",
                  "sort": "desc"}, title: "${_('Description')}", className: "td-description" },
         { data: {"_": "last_change",
                  "sort": "last_change_raw",
                  "type": Number}, title: "${_('Last Change')}", className: "td-time" },
         { data: {"_": "top_level_repos",
                  "sort": "top_level_repos"}, title: "${_('Number of top level repositories')}" },
         { data: {"_": "owner",
                  "sort": "owner"}, title: "${_('Owner')}", className: "td-user" },
         { data: {"_": "action",
                  "sort": "action"}, title: "${_('Action')}", className: "td-action", orderable: false }
      ],
      language: {
          paginate: DEFAULT_GRID_PAGINATION,
          sProcessing: _gettext('loading...'),
          emptyTable: _gettext("No repository groups available yet.")
      },
    });

    $repoGroupsListTable.on('xhr.dt', function(e, settings, json, xhr){
        $repoGroupsListTable.css('opacity', 1);
    });

    $repoGroupsListTable.on('preXhr.dt', function(e, settings, data){
        $repoGroupsListTable.css('opacity', 0.3);
    });

    // filter
    $('#q_filter').on('keyup',
        $.debounce(250, function() {
            $repoGroupsListTable.DataTable().search(
                $('#q_filter').val()
            ).draw();
        })
    );
});

</script>

</%def>

