## -*- coding: utf-8 -*-
<%inherit file="/base/base.mako"/>

<%def name="title()">
    ${_('Repositories administration')}
    %if c.rhodecode_name:
        &middot; ${h.branding(c.rhodecode_name)}
    %endif
</%def>

<%def name="breadcrumbs_links()"></%def>

<%def name="menu_bar_nav()">
    ${self.menu_items(active='admin')}
</%def>

<%def name="menu_bar_subnav()">
    ${self.admin_menu(active='repositories')}
</%def>

<%def name="main()">
<div class="box">

    <div class="title">
        <input class="q_filter_box" id="q_filter" size="15" type="text" name="filter" placeholder="${_('quick filter...')}" value=""/>
        <span id="repo_count"></span>

        <ul class="links">
        %if c.can_create_repo:
            <li>
              <a href="${h.route_path('repo_new')}" class="btn btn-small btn-success">${_(u'Add Repository')}</a>
            </li>
        %endif
        </ul>
    </div>
    <div id="repos_list_wrap">
        <table id="repo_list_table" class="display"></table>
    </div>

</div>

<script>
$(document).ready(function() {
    var $repoListTable = $('#repo_list_table');

    // repo list
    $repoListTable.DataTable({
        processing: true,
        serverSide: true,
        ajax: {
            "url": "${h.route_path('repos_data')}",
            "dataSrc": function (json) {
                var filteredCount = json.recordsFiltered;
                var total = json.recordsTotal;

                var _text = _gettext(
                        "{0} of {1} repositories").format(
                        filteredCount, total);

                if (total === filteredCount) {
                    _text = _gettext("{0} repositories").format(total);
                }
                $('#repo_count').text(_text);

                return json.data;
            },
        },
        dom: 'rtp',
        pageLength: ${c.visual.admin_grid_items},
        order: [[ 0, "asc" ]],
        columns: [
            {
                data: {
                    "_": "name",
                    "sort": "name_raw"
                }, title: "${_('Name')}", className: "td-componentname"
            },
            {
                data: 'menu', "bSortable": false, className: "quick_repo_menu"},
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
                }, title: "${_('Commit')}", className: "td-commit", orderable: false
            },
            {
                data: {
                    "_": "owner",
                    "sort": "owner"
                }, title: "${_('Owner')}", className: "td-user"
            },
            {
                data: {
                    "_": "state",
                    "sort": "state"
                }, title: "${_('State')}", className: "td-tags td-state"
            },
            {
                data: {
                    "_": "action",
                    "sort": "action"
                }, title: "${_('Action')}", className: "td-action", orderable: false
            }
        ],
        language: {
          paginate: DEFAULT_GRID_PAGINATION,
          sProcessing: _gettext('loading...'),
          emptyTable:_gettext("No repositories present.")
        },
        "initComplete": function( settings, json ) {
            quick_repo_menu();
        }
    });

    $repoListTable.on('xhr.dt', function(e, settings, json, xhr){
        $repoListTable.css('opacity', 1);
    });

    $repoListTable.on('preXhr.dt', function(e, settings, data){
        $repoListTable.css('opacity', 0.3);
    });

    $('#q_filter').on('keyup',
        $.debounce(250, function() {
            $repoListTable.DataTable().search(
                $('#q_filter').val()
            ).draw();
        })
    );

  });

</script>

</%def>
