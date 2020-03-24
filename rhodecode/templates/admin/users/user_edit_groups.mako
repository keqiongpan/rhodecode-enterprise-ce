## -*- coding: utf-8 -*-
<%namespace name="base" file="/base/base.mako"/>

<div class="panel panel-default">
    <div class="panel-heading">
      <h3 class="panel-title">
          ${base.gravatar_with_user(c.user.username, 16, tooltip=False, _class='pull-left')}
          &nbsp;- ${_('User groups administration')}
      </h3>
    </div>
    <div class="panel-body">
        <div class="fields">
            <div class="field">
                <div class="label label-checkbox">
                    <label for="users_group_active">${_('Add `%s` to user group') % c.user.username}:</label>
                </div>
                <div class="input">
                    ${h.text('add_user_to_group', placeholder="user group name", class_="medium")}
                </div>

            </div>
        </div>

        <div class="groups_management">
            ${h.secure_form(h.route_path('edit_user_groups_management_updates', user_id=c.user.user_id), request=request)}
            <div id="repos_list_wrap">
                <table id="user_group_list_table" class="display"></table>
            </div>
            <div class="buttons">
                ${h.submit('save',_('Save'),class_="btn")}
            </div>
            ${h.end_form()}
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
      data: ${c.groups|n},
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
         },
         { data: null,
             title: "${_('Action')}",
             className: "td-action",
             defaultContent: '-'
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

    // filter, filter both grids
    $('#q_filter').on( 'keyup', function () {
      var user_api = $('#user_group_list_table').dataTable().api();
      user_api
        .columns(0)
        .search(this.value)
        .draw();
    });

    // refilter table if page load via back button
    $("#q_filter").trigger('keyup');

  });

    $('#language').select2({
        'containerCssClass': "drop-menu",
        'dropdownCssClass': "drop-menu-dropdown",
        'dropdownAutoWidth': true
    });



$(document).ready(function(){
    $("#group_parent_id").select2({
        'containerCssClass': "drop-menu",
        'dropdownCssClass': "drop-menu-dropdown",
        'dropdownAutoWidth': true
    });

    $('#add_user_to_group').autocomplete({
        serviceUrl: pyroutes.url('user_group_autocomplete_data'),
        minChars:2,
        maxHeight:400,
        width:300,
        deferRequestBy: 300, //miliseconds
        showNoSuggestionNotice: true,
        params: { user_groups:true },
        formatResult: autocompleteFormatResult,
        lookupFilter: autocompleteFilterResult,
        onSelect: function(element, suggestion){
            var owner = {owner_icon: suggestion.owner_icon, owner:suggestion.owner};
            api.row.add(
                    {"active": suggestion.active,
                        "owner_data": owner,
                        "users_group_id": suggestion.id,
                        "group_description": suggestion.description,
                        "group_name": suggestion.value}).draw();
        }
    });
})

</script>


