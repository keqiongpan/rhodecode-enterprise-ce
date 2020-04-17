<div class="panel panel-default">
    <div class="panel-heading">
        <h3 class="panel-title">${_('Exceptions Tracker ')}</h3>
    </div>
    <div class="panel-body">
        % if c.exception_list_count == 1:
            ${_('There is {} stored exception.').format(c.exception_list_count)}
        % else:
            ${_('There are total {} stored exceptions.').format(c.exception_list_count)}
        % endif
        <br/>
        ${_('Store directory')}: ${c.exception_store_dir}

      ${h.secure_form(h.route_path('admin_settings_exception_tracker_delete_all'), request=request)}
        <div style="margin: 0 0 20px 0" class="fake-space"></div>
        <input type="hidden" name="type_filter", value="${c.type_filter}">
        <div class="field">
            <button class="btn btn-small btn-danger" type="submit"
                    onclick="submitConfirm(event, this, _gettext('Confirm to delete all exceptions'), _gettext('Delete'), '${'total:{}'.format(c.exception_list_count)}')"
            >
                <i class="icon-remove"></i>
                % if c.type_filter:
                    ${_('Delete All `{}`').format(c.type_filter)}
                % else:
                    ${_('Delete All')}
                % endif

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
                <td>
                    <a href="${h.current_route_path(request, type_filter=tb['exc_type'])}">${tb['exc_type']}</a>
                </td>
            </tr>
            <% cnt -=1 %>
        % endfor
        </table>
    </div>
</div>
