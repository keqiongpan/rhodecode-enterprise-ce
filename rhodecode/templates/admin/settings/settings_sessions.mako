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
        ${h.secure_form(h.url('admin_settings_sessions_cleanup'), method='post')}

            <div style="margin: 0 0 20px 0" class="fake-space">
            ${_('Cleanup all sessions that were not active during choosen time frame')} <br/>
            ${_('Picking All will log-out all users in the system, and each user will be required to log in again.')}
            </div>
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