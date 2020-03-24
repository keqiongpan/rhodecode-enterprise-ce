<%namespace name="base" file="/base/base.mako"/>

<div class="panel panel-default">
    <div class="panel-heading">
        <h3 class="panel-title">
            ${base.gravatar_with_user(c.user.username, 16, tooltip=False, _class='pull-left')}
            &nbsp;- ${_('Caches')}
        </h3>
    </div>
    <div class="panel-body">
    <p>
        Cache keys used for storing cached values of user permissions and authentication plugin cache.
        Invalidating the cache will remove those entries.
    </p>

<pre>
region: ${c.region.name}
backend: ${c.region.actual_backend.__class__}
store: ${c.region.actual_backend.get_store()}

% if c.user_keys:
${len(c.user_keys)} <a href="#showKeys" onclick="$('#show-keys').toggle()">${_('Show all')}</a>
<span id="show-keys" style="display: none">
    % for k in c.user_keys:
 - ${k}
    % endfor
</span>
% else:
 NO KEYS FOUND
% endif
</pre>
    <p></p>
    ${h.secure_form(h.route_path('edit_user_caches_update', user_id=c.user.user_id), request=request)}
    <div class="form">
       <div class="fields">
           ${h.submit('reset_cache_%s' % c.user.user_id, _('Invalidate user cache'),class_="btn btn-small",onclick="return confirm('"+_('Confirm to invalidate user cache')+"');")}
       </div>
    </div>
    ${h.end_form()}

    </div>
</div>


