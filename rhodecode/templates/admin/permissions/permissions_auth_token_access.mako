

<div class="panel panel-default">
  <div class="panel-heading">
      <h3 class="panel-title">${_('View whitelist')}</h3>
  </div>
  <div class="panel-body">
    <div class="">

<p class="pr-description">
View white list defines a set of views that can be accessed using auth token without the need to login.
Adding ?auth_token = SECRET_TOKEN to the url authenticates this request as if it
came from the the logged in user who owns this authentication token.

E.g. adding `RepoFilesView.repo_file_raw` allows to access a raw diff using such url:
    http[s]://server.com/{repo_name}/raw/{commit_id}/{file_path}?auth_token=SECRET_TOKEN

White list can be defined inside `${c.whitelist_file}` under `${c.whitelist_key}=` setting
Currently the following views are set:
</p>

<pre>
% for entry in c.whitelist_views:
${entry}
% endfor
</pre>

    </div>

  </div>
</div>


<div class="panel panel-default">
  <div class="panel-heading">
      <h3 class="panel-title">${_('List of views available for usage in whitelist access')}</h3>
  </div>
  <div class="panel-body">
    <div class="">


      <table class="rctable ip-whitelist">
        <tr>
            <th>Active</th>
            <th>View FQN</th>
            <th>URL pattern</th>
        </tr>

        % for route_name, view_fqn, view_url, active in c.view_data:
        <tr>
            <td class="td-x">
                ${h.bool2icon(active, show_at_false=False)}
            </td>
            <td class="td-x">${view_fqn}</td>
            <td class="td-x" title="${route_name}">${view_url}</td>
        </tr>
        % endfor
      </table>
    </div>

  </div>
</div>
