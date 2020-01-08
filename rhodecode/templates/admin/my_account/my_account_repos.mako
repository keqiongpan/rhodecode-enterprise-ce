<div class="panel panel-default">
  <div class="panel-heading">
    <h3 class="panel-title">${_('Repositories You Own')}</h3>
  </div>

  <div class="panel-body">
    <input class="q_filter_box" id="q_filter" size="15" type="text" name="filter" placeholder="${_('quick filter...')}" value=""/>

    <div id="repos_list_wrap">
        <table id="repo_list_table" class="display"></table>
    </div>
  </div>
</div>

<script>
$(document).ready(function() {

    // repo list
    $repoListTable = $('#repo_list_table');

    $repoListTable.DataTable({
      data: ${c.data|n},
      dom: 'rtp',
      pageLength: ${c.visual.admin_grid_items},
      order: [[ 0, "asc" ]],
      columns: [
         { data: {"_": "name",
                  "sort": "name_raw"}, title: "${_('Name')}", className: "td-componentname" },
      ],
      language: {
          paginate: DEFAULT_GRID_PAGINATION,
          emptyTable: _gettext("No repositories available yet.")
      },

    });

    // filter
    $('#q_filter').on('keyup',
        $.debounce(250, function() {
            $repoListTable.DataTable().search(
                $('#q_filter').val()
            ).draw();
        })
    );


  });

</script>
