<%namespace name="base" file="/base/base.mako"/>

<div class="panel panel-default">
    <div class="panel-heading">
        <h3 class="panel-title">${_('Caches')}</h3>
    </div>
    <div class="panel-body">
        <pre>
region: ${c.region.name}
backend: ${c.region.actual_backend.__class__}
store: ${c.region.actual_backend.get_store()}

% for k in c.user_keys:
 - ${k}
% endfor
        </pre>

    ${h.secure_form(h.route_path('edit_user_caches_update', user_id=c.user.user_id), request=request)}
    <div class="form">
       <div class="fields">
           ${h.submit('reset_cache_%s' % c.user.user_id, _('Invalidate user cache'),class_="btn btn-small",onclick="return confirm('"+_('Confirm to invalidate user cache')+"');")}
       </div>
    </div>
    ${h.end_form()}

    </div>
</div>


