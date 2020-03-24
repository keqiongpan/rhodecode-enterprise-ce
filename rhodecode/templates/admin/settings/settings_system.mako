
<div id="update_notice" style="display: none; margin: 0px 0px 30px 0px">
    <div>${_('Checking for updates...')}</div>
</div>


<div class="panel panel-default">
    <div class="panel-heading">
        <h3 class="panel-title">${_('System Info')}</h3>
        % if c.allowed_to_snapshot:
            <a href="${h.route_path('admin_settings_system', _query={'snapshot':1})}" class="panel-edit">${_('create summary snapshot')}</a>
        % endif
    </div>
    <div class="panel-body">
        <dl class="dl-horizontal settings dt-400">
        % for dt, dd, warn in c.data_items:
          <dt>${dt}${':' if dt else '---'}</dt>
          <dd>${dd}${'' if dt else '---'}
              % if warn and warn['message']:
                  <div class="alert-${warn['type']}">
                    <strong>${warn['message']}</strong>
                  </div>
              % endif
          </dd>
        % endfor
        </dl>
    </div>
</div>

<div class="panel panel-default">
    <div class="panel-heading">
        <h3 class="panel-title">${_('VCS Server')}</h3>
    </div>
    <div class="panel-body">
        <dl class="dl-horizontal settings dt-400">
        % for dt, dd in c.vcsserver_data_items:
          <dt>${dt}${':' if dt else '---'}</dt>
          <dd>${dd}${'' if dt else '---'}</dd>
        % endfor
        </dl>
    </div>
</div>

<div class="panel panel-default">
    <div class="panel-heading">
        <h3 class="panel-title">${_('Python Packages')}</h3>
    </div>
    <div class="panel-body">
        <dl class="dl-horizontal settings dt-400">
        % for dt, dd in c.py_modules['human_value']:
          <dt>${dt}${':' if dt else '---'}</dt>
          <dd>${dd}${'' if dt else '---'}</dd>
        % endfor
        </dl>
    </div>
</div>

<script>
    $('#check_for_update').click(function(e){
        $('#update_notice').show();
        $('#update_notice').load("${h.route_path('admin_settings_system_update')}");
    })
</script>
