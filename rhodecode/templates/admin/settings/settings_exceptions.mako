<div class="panel panel-default">
    <div class="panel-heading">
        <h3 class="panel-title">${_('Exceptions Tracker - Exception ID')}: ${c.exception_id}</h3>
    </div>
    <div class="panel-body">
    % if c.traceback:

    <h4>${_('Exception `{}` generated on UTC date: {}').format(c.traceback.get('exc_type', 'NO_TYPE'), c.traceback.get('exc_utc_date', 'NO_DATE'))}</h4>
    <pre>${c.traceback.get('exc_message', 'NO_MESSAGE')}</pre>

    % else:
        ${_('Unable to Read Exception. It might be removed or non-existing.')}
    % endif
    </div>
</div>


% if c.traceback:
<div class="panel panel-danger">
    <div class="panel-heading" id="advanced-delete">
        <h3 class="panel-title">${_('Delete this Exception')}</h3>
    </div>
    <div class="panel-body">
      ${h.secure_form(h.route_path('admin_settings_exception_tracker_delete', exception_id=c.exception_id), request=request)}
        <div style="margin: 0 0 20px 0" class="fake-space"></div>

        <div class="field">
            <button class="btn btn-small btn-danger" type="submit"
                    onclick="return confirm('${_('Confirm to delete this exception')}');">
                <i class="icon-remove"></i>
                ${_('Delete This Exception')}
            </button>
        </div>

      ${h.end_form()}
    </div>
</div>
% endif
