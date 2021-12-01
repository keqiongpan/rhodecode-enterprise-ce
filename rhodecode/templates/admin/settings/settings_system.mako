
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
        <table>
            <th></th>
            <th></th>
            <th></th>
            % for name, package_data in c.py_modules['human_value']:
                <tr>
                    <td>${name.lower()}</td>
                    <td>${package_data['version']}</td>
                    <td>(${package_data['location']})</td>
                </tr>
            % endfor
        </table>

    </div>
</div>

<div class="panel panel-default">
    <div class="panel-heading">
        <h3 class="panel-title">${_('Env Variables')}</h3>
    </div>
    <div class="panel-body">
        <table>
            <th></th>
            <th></th>
            % for env_key, env_val in c.env_data:
                <tr>
                    <td style="vertical-align: top">${env_key}</td>
                    <td>${env_val}</td>
                </tr>
            % endfor
        </table>

    </div>
</div>

<script>
    $('#check_for_update').click(function(e){
        $('#update_notice').show();
        $('#update_notice').load("${h.route_path('admin_settings_system_update')}");
    })
</script>
