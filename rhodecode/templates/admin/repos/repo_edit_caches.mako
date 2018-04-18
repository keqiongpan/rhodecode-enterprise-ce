<div class="panel panel-default">
    <div class="panel-heading">
        <h3 class="panel-title">${_('Invalidate Cache for Repository')}</h3>
    </div>
    <div class="panel-body">

        <h4>${_('Manually invalidate the repository cache. On the next access a repository cache will be recreated.')}</h4>

        <p>
            ${_('Cache purge can be automated by such api call. Can be called periodically in crontab etc.')}
            <br/>
            <code>
            ${h.api_call_example(method='invalidate_cache', args={"repoid": c.rhodecode_db_repo.repo_name})}
            </code>
        </p>

        ${h.secure_form(h.route_path('edit_repo_caches', repo_name=c.repo_name), request=request)}
        <div class="form">
           <div class="fields">
               ${h.submit('reset_cache_%s' % c.rhodecode_db_repo.repo_name,_('Invalidate repository cache'),class_="btn btn-small",onclick="return confirm('"+_('Confirm to invalidate repository cache')+"');")}
           </div>
        </div>
        ${h.end_form()}

    </div>
</div>


<div class="panel panel-default">
    <div class="panel-heading">
        <h3 class="panel-title">
            ${(_ungettext('List of repository caches (%(count)s entry)', 'List of repository caches (%(count)s entries)' ,len(c.rhodecode_db_repo.cache_keys)) % {'count': len(c.rhodecode_db_repo.cache_keys)})}
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
          %for cache in c.rhodecode_db_repo.cache_keys:
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


<div class="panel panel-default">
    <div class="panel-heading">
        <h3 class="panel-title">${_('Diff Caches')}</h3>
    </div>
    <div class="panel-body">
        <table class="rctable edit_cache">
            <tr>
                <td>${_('Cached diff name')}:</td>
                <td>${c.rhodecode_db_repo.cached_diffs_relative_dir}</td>
            </tr>
            <tr>
                <td>${_('Cached diff files')}:</td>
                <td>${c.cached_diff_count}</td>
            </tr>
            <tr>
                <td>${_('Cached diff size')}:</td>
                <td>${h.format_byte_size(c.cached_diff_size)}</td>
            </tr>
        </table>
    </div>
</div>
