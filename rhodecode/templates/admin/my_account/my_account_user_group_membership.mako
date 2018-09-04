## -*- coding: utf-8 -*-

<div class="panel panel-default">
  <div class="panel-heading">
    <h3 class="panel-title">${_('User Group Membership')}</h3>
  </div>

    <div class="panel-body">
        <div class="groups_management">
            <div id="repos_list_wrap">
                <table id="user_group_list_table" class="display"></table>
            </div>
        </div>
    </div>
</div>


<script>
var api;
$(document).ready(function() {

    var get_datatable_count = function(){
        $('#user_group_count').text(api.page.info().recordsDisplay);
    };

    $('#user_group_list_table').on('click', 'a.editor_remove', function (e) {
        e.preventDefault();
        var row = api.row($(this).closest('tr'));
        row.remove().draw();
    } );

    $('#user_group_list_table').DataTable({
      data: ${c.user_groups|n},
      dom: 'rtp',
      pageLength: ${c.visual.admin_grid_items},
      order: [[ 0, "asc" ]],
      columns: [
         { data: {"_": "group_name",
                  "sort": "group_name"}, title: "${_('Name')}", className: "td-componentname," ,
            render: function (data,type,full,meta)
                    {return '<div><i class="icon-user-group" title="User group">'+data+'</i></div>'}},

         { data: {"_": "group_description",
                  "sort": "group_description"}, title: "${_('Description')}", className: "td-description" },
         { data: {"_": "users_group_id"}, className: "td-user",
                 render: function (data,type,full,meta)
                    {return '<input type="hidden" name="users_group_id" value="'+data+'">'}},
         { data: {"_": "active",
                  "sort": "active"}, title: "${_('Active')}", className: "td-active"},
         { data: {"_": "owner_data"}, title: "${_('Owner')}", className: "td-user",
             render: function (data,type,full,meta)
                    {return '<div class="rc-user tooltip">'+
                            '<img class="gravatar" src="'+ data.owner_icon +'" height="16" width="16">'+
                             data.owner +'</div>'
                    }
         }
      ],
      language: {
          paginate: DEFAULT_GRID_PAGINATION,
          emptyTable: _gettext("No user groups available yet.")
      },
      "initComplete": function( settings, json ) {
          var data_grid = $('#user_group_list_table').dataTable();
          api = data_grid.api();
          get_datatable_count();
      }
    });

    // update the counter when doing search
    $('#user_group_list_table').on( 'search.dt', function (e,settings) {
        get_datatable_count();
    });

  });
</script>