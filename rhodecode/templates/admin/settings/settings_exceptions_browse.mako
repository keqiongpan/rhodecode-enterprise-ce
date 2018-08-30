<div class="panel panel-default">
    <div class="panel-heading">
        <h3 class="panel-title">${_('Exceptions Tracker ')}</h3>
    </div>
    <div class="panel-body">
        % if c.exception_list_count == 1:
            ${_('There is {} stored exception.').format(c.exception_list_count)}
        % else:
            ${_('There are {} stored exceptions.').format(c.exception_list_count)}
        % endif
        ${_('Store directory')}: ${c.exception_store_dir}

      ${h.secure_form(h.route_path('admin_settings_exception_tracker_delete_all'), request=request)}
        <div style="margin: 0 0 20px 0" class="fake-space"></div>

        <div class="field">
            <button class="btn btn-small btn-danger" type="submit"
                    onclick="return confirm('${_('Confirm to delete all exceptions')}');">
                <i class="icon-remove-sign"></i>
                ${_('Delete All')}
            </button>
        </div>

      ${h.end_form()}

    </div>
</div>


<div class="panel panel-default">
    <div class="panel-heading">
        <h3 class="panel-title">${_('Exceptions Tracker - Showing the last {} Exceptions').format(c.limit)}.</h3>
        <a class="panel-edit" href="${h.current_route_path(request, limit=c.next_limit)}">${_('Show more')}</a>
    </div>
    <div class="panel-body">
        <table class="rctable">
        <tr>
            <th>#</th>
            <th>Exception ID</th>
            <th>Date</th>
            <th>App Type</th>
            <th>Exc Type</th>
        </tr>
        <% cnt = len(c.exception_list)%>
        % for tb in c.exception_list:
            <tr>
                <td>${cnt}</td>
                <td><a href="${h.route_path('admin_settings_exception_tracker_show', exception_id=tb['exc_id'])}"><code>${tb['exc_id']}</code></a></td>
                <td>${h.format_date(tb['exc_utc_date'])}</td>
                <td>${tb['app_type']}</td>
                <td>${tb['exc_type']}</td>
            </tr>
            <% cnt -=1 %>
        % endfor
        </table>
    </div>
</div>
