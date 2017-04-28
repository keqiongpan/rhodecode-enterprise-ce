<div class="panel panel-default">
    <div class="panel-heading">
        <h3 class="panel-title">${_('Invalidate Cache for Repository')}</h3>
    </div>
    <div class="panel-body">

        <h4>${_('Manually invalidate the repository cache. On the next access a repository cache will be recreated.')}</h4>

        <p>
            ${_('Cache purge can be automated by such api call called periodically (in crontab etc)')}
            <br/>
            <code>
                curl ${h.route_url('apiv2')} -X POST -H 'content-type:text/plain' --data-binary '{"id":1, "auth_token":"SECRET", "method":"invalidate_cache", "args":{"repoid":"${c.repo_info.repo_name}"}}'
            </code>
        </p>

        ${h.secure_form(h.route_path('edit_repo_caches', repo_name=c.repo_name), method='POST')}
        <div class="form">
           <div class="fields">
               ${h.submit('reset_cache_%s' % c.repo_info.repo_name,_('Invalidate repository cache'),class_="btn btn-small",onclick="return confirm('"+_('Confirm to invalidate repository cache')+"');")}
           </div>
        </div>
        ${h.end_form()}

    </div>
</div>


<div class="panel panel-default">
    <div class="panel-heading">
        <h3 class="panel-title">
            ${(_ungettext('List of repository caches (%(count)s entry)', 'List of repository caches (%(count)s entries)' ,len(c.repo_info.cache_keys)) % {'count': len(c.repo_info.cache_keys)})}
        </h3>
    </div>
    <div class="panel-body">
      <div class="field" >
           <table class="rctable edit_cache">
           <tr>
            <th>${_('Prefix')}</th>
            <th>${_('Key')}</th>
            <th>${_('Active')}</th>
            </tr>
          %for cache in c.repo_info.cache_keys:
              <tr>
                <td class="td-prefix">${cache.get_prefix() or '-'}</td>
                <td class="td-cachekey">${cache.cache_key}</td>
                <td class="td-active">${h.bool2icon(cache.cache_active)}</td>
              </tr>
          %endfor
          </table>
      </div>
    </div>
</div>


