<div class="panel panel-default">
    <div class="panel-heading">
        <h3 class="panel-title">${_('User Sessions Configuration')}</h3>
    </div>
    <div class="panel-body">
        <%
         elems = [
            (_('Session type'), c.session_model.SESSION_TYPE, ''),
            (_('Session expiration period'), '{} seconds'.format(c.session_conf.get('beaker.session.timeout', 0)), ''),

            (_('Total sessions'), c.session_count, ''),
            (_('Expired sessions ({} days)').format(c.cleanup_older_days ), c.session_expired_count, ''),

        ]
        %>
        <dl class="dl-horizontal settings">
        %for dt, dd, tt in elems:
          <dt>${dt}:</dt>
          <dd title="${tt}">${dd}</dd>
        %endfor
        </dl>
    </div>
</div>


<div class="panel panel-warning">
    <div class="panel-heading">
        <h3 class="panel-title">${_('Cleanup Old Sessions')}</h3>
    </div>
    <div class="panel-body">
        ${h.secure_form(h.route_path('admin_settings_sessions_cleanup'), method='post')}

            <p>
            ${_('Cleanup user sessions that were not active during chosen time frame.')} <br/>
            ${_('After performing this action users whose session will be removed will be required to log in again.')} <br/>
            <strong>${_('Picking `All` will log-out you, and all users in the system.')}</strong>
           </p>

            <script type="text/javascript">
              $(document).ready(function() {
                  $('#expire_days').select2({
                      containerCssClass: 'drop-menu',
                      dropdownCssClass: 'drop-menu-dropdown',
                      dropdownAutoWidth: true,
                      minimumResultsForSearch: -1
                  });
              });
            </script>
            <select id="expire_days" name="expire_days">
                % for n in [60, 90, 30, 7, 0]:
                    <option value="${n}">${'{} days'.format(n) if n != 0 else 'All'}</option>
                % endfor
            </select>
            <button class="btn btn-small" type="submit"
                onclick="return confirm('${_('Confirm to cleanup user sessions')}');">
                ${_('Cleanup sessions')}
            </button>
        ${h.end_form()}
    </div>
</div>


