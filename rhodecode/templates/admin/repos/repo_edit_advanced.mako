<%namespace name="base" file="/base/base.mako"/>

<%
 elems = [
    (_('Repository ID'), c.rhodecode_db_repo.repo_id, '', ''),
    (_('Owner'), lambda:base.gravatar_with_user(c.rhodecode_db_repo.user.email, tooltip=True), '', ''),
    (_('Created on'), h.format_date(c.rhodecode_db_repo.created_on), '', ''),
    (_('Updated on'), h.format_date(c.rhodecode_db_repo.updated_on), '', ''),
    (_('Cached Commit id'), lambda: h.link_to(c.rhodecode_db_repo.changeset_cache.get('short_id'), h.route_path('repo_commit',repo_name=c.repo_name,commit_id=c.rhodecode_db_repo.changeset_cache.get('raw_id'))), '', ''),
    (_('Cached Commit date'), c.rhodecode_db_repo.changeset_cache.get('date'), '', ''),
    (_('Cached Commit data'), lambda: h.link_to('refresh now', h.current_route_path(request, update_commit_cache=1)), '', ''),
    (_('Attached scoped tokens'), len(c.rhodecode_db_repo.scoped_tokens), '', [x.user for x in c.rhodecode_db_repo.scoped_tokens]),
    (_('Pull requests source'), len(c.rhodecode_db_repo.pull_requests_source), '', ['pr_id:{}, repo:{}'.format(x.pull_request_id,x.source_repo.repo_name) for x in c.rhodecode_db_repo.pull_requests_source]),
    (_('Pull requests target'), len(c.rhodecode_db_repo.pull_requests_target), '', ['pr_id:{}, repo:{}'.format(x.pull_request_id,x.target_repo.repo_name) for x in c.rhodecode_db_repo.pull_requests_target]),
    (_('Attached Artifacts'), len(c.rhodecode_db_repo.artifacts), '', ''),
 ]
%>

<div class="panel panel-default">
    <div class="panel-heading" id="advanced-info" >
        <h3 class="panel-title">${_('Repository: %s') % c.rhodecode_db_repo.repo_name} <a class="permalink" href="#advanced-info"> ¶</a></h3>
    </div>
    <div class="panel-body">
        ${base.dt_info_panel(elems)}
    </div>
</div>


<div class="panel panel-default">
    <div class="panel-heading" id="advanced-fork">
        <h3 class="panel-title">${_('Fork Reference')} <a class="permalink" href="#advanced-fork"> ¶</a></h3>
    </div>
    <div class="panel-body">
      ${h.secure_form(h.route_path('edit_repo_advanced_fork', repo_name=c.rhodecode_db_repo.repo_name), request=request)}

        % if c.rhodecode_db_repo.fork:
            <div class="panel-body-title-text">${h.literal(_('This repository is a fork of %(repo_link)s') % {'repo_link': h.link_to_if(c.has_origin_repo_read_perm,c.rhodecode_db_repo.fork.repo_name, h.route_path('repo_summary', repo_name=c.rhodecode_db_repo.fork.repo_name))})}
            | <button class="btn btn-link btn-danger" type="submit">Remove fork reference</button></div>
        % endif

         <div class="field">
             ${h.hidden('id_fork_of')}
             ${h.submit('set_as_fork_%s' % c.rhodecode_db_repo.repo_name,_('Set'),class_="btn btn-small",)}
         </div>
         <div class="field">
             <span class="help-block">${_('Manually set this repository as a fork of another from the list')}</span>
         </div>
      ${h.end_form()}
    </div>
</div>


<div class="panel panel-default">
    <div class="panel-heading" id="advanced-journal">
        <h3 class="panel-title">${_('Public Journal Visibility')} <a class="permalink" href="#advanced-journal"> ¶</a></h3>
    </div>
    <div class="panel-body">
      ${h.secure_form(h.route_path('edit_repo_advanced_journal', repo_name=c.rhodecode_db_repo.repo_name), request=request)}
        <div class="field">
        %if c.in_public_journal:
          <button class="btn btn-small" type="submit">
              ${_('Remove from Public Journal')}
          </button>
        %else:
          <button class="btn btn-small" type="submit">
              ${_('Add to Public Journal')}
          </button>
        %endif
        </div>
       <div class="field" >
       <span class="help-block">${_('All actions made on this repository will be visible to everyone following the public journal.')}</span>
       </div>
      ${h.end_form()}
    </div>
</div>


<div class="panel panel-default">
    <div class="panel-heading" id="advanced-locking">
        <h3 class="panel-title">${_('Locking state')} <a class="permalink" href="#advanced-locking"> ¶</a></h3>
    </div>
    <div class="panel-body">
        ${h.secure_form(h.route_path('edit_repo_advanced_locking', repo_name=c.rhodecode_db_repo.repo_name), request=request)}

        %if c.rhodecode_db_repo.locked[0]:
             <div class="panel-body-title-text">${'Locked by %s on %s. Lock reason: %s' % (h.person_by_id(c.rhodecode_db_repo.locked[0]),
             h.format_date(h. time_to_datetime(c.rhodecode_db_repo.locked[1])), c.rhodecode_db_repo.locked[2])}</div>
        %else:
            <div class="panel-body-title-text">${_('This Repository is not currently locked.')}</div>
        %endif

        <div class="field" >
            %if c.rhodecode_db_repo.locked[0]:
              ${h.hidden('set_unlock', '1')}
              <button class="btn btn-small" type="submit"
                      onclick="return confirm('${_('Confirm to unlock repository.')}');">
                  <i class="icon-unlock"></i>
                  ${_('Unlock repository')}
              </button>
            %else:
              ${h.hidden('set_lock', '1')}
              <button class="btn btn-small" type="submit"
                      onclick="return confirm('${_('Confirm to lock repository.')}');">
                  <i class="icon-lock"></i>
                  ${_('Lock repository')}
              </button>
            %endif
         </div>
         <div class="field" >
            <span class="help-block">
                ${_('Force repository locking. This only works when anonymous access is disabled. Pulling from the repository locks the repository to that user until the same user pushes to that repository again.')}
            </span>
         </div>
        ${h.end_form()}
    </div>
</div>


<div class="panel panel-default">
    <div class="panel-heading" id="advanced-hooks">
        <h3 class="panel-title">${_('Hooks')} <a class="permalink" href="#advanced-hooks"> ¶</a></h3>
    </div>
    <div class="panel-body">
        <table class="rctable">
            <th>${_('Hook type')}</th>
            <th>${_('Hook version')}</th>
            <th>${_('Current version')}</th>
            % if c.ver_info_dict:
            <tr>
                <td>${_('PRE HOOK')}</td>
                <td>${c.ver_info_dict['pre_version']}</td>
                <td>${c.rhodecode_version}</td>
            </tr>
            <tr>
                <td>${_('POST HOOK')}</td>
                <td>${c.ver_info_dict['post_version']}</td>
                <td>${c.rhodecode_version}</td>
            </tr>
            % else:
                <tr>
                    <td>${_('Unable to read hook information from VCS Server')}</td>
                </tr>
            % endif
        </table>

        <a class="btn btn-primary" href="${h.route_path('edit_repo_advanced_hooks', repo_name=c.repo_name)}"
           onclick="return confirm('${_('Confirm to reinstall hooks for this repository.')}');">
            ${_('Update Hooks')}
        </a>
        % if c.hooks_outdated:
            <span class="alert-error" style="padding: 10px">
                ${_('Outdated hooks detected, please update hooks using `Update Hooks` action.')}
            </span>
        % endif
    </div>
</div>

<div class="panel panel-warning">
    <div class="panel-heading" id="advanced-archive">
        <h3 class="panel-title">${_('Archive repository')} <a class="permalink" href="#advanced-archive"> ¶</a></h3>
    </div>
    <div class="panel-body">
      ${h.secure_form(h.route_path('edit_repo_advanced_archive', repo_name=c.repo_name), request=request)}

        <div style="margin: 0 0 20px 0" class="fake-space"></div>

        <div class="field">
            <button class="btn btn-small btn-warning" type="submit"
                    onclick="return confirm('${_('Confirm to archive this repository: %s') % c.repo_name}');">
                ${_('Archive this repository')}
            </button>
        </div>
        <div class="field">
            <span class="help-block">
                ${_('Archiving the repository will make it entirely read-only. The repository cannot be committed to.'
                    'It is hidden from the search results and dashboard. ')}
            </span>
        </div>

      ${h.end_form()}
    </div>
</div>


<div class="panel panel-danger">
    <div class="panel-heading" id="advanced-delete">
        <h3 class="panel-title">${_('Delete repository')} <a class="permalink" href="#advanced-delete"> ¶</a></h3>
    </div>
    <div class="panel-body">
      ${h.secure_form(h.route_path('edit_repo_advanced_delete', repo_name=c.repo_name), request=request)}
        <table class="display">
            <tr>
                <td>
                    ${_ungettext('This repository has %s fork.', 'This repository has %s forks.', c.rhodecode_db_repo.forks.count()) % c.rhodecode_db_repo.forks.count()}
                </td>
                <td>
                    %if c.rhodecode_db_repo.forks.count():
                        <input type="radio" name="forks" value="detach_forks" checked="checked"/> <label for="forks">${_('Detach forks')}</label>
                    %endif
                </td>
                <td>
                    %if c.rhodecode_db_repo.forks.count():
                        <input type="radio" name="forks" value="delete_forks"/> <label for="forks">${_('Delete forks')}</label>
                    %endif
                </td>
            </tr>
            <% attached_prs = len(c.rhodecode_db_repo.pull_requests_source + c.rhodecode_db_repo.pull_requests_target) %>
            % if c.rhodecode_db_repo.pull_requests_source or c.rhodecode_db_repo.pull_requests_target:
            <tr>
                <td>
                    ${_ungettext('This repository has %s attached pull request.', 'This repository has %s attached pull requests.', attached_prs) % attached_prs}
                    <br/>
                    ${_('Consider to archive this repository instead.')}
                </td>
                <td></td>
                <td></td>
            </tr>
            % endif
        </table>
        <div style="margin: 0 0 20px 0" class="fake-space"></div>

        <div class="field">
            <button class="btn btn-small btn-danger" type="submit"
                    onclick="return confirm('${_('Confirm to delete this repository: %s') % c.repo_name}');">
                ${_('Delete this repository')}
            </button>
        </div>
        <div class="field">
            <span class="help-block">
                ${_('This repository will be renamed in a special way in order to make it inaccessible to RhodeCode Enterprise and its VCS systems. If you need to fully delete it from the file system, please do it manually, or with rhodecode-cleanup-repos command available in rhodecode-tools.')}
            </span>
        </div>

      ${h.end_form()}
    </div>
</div>


<script>

var currentRepoId = ${c.rhodecode_db_repo.repo_id};

var repoTypeFilter = function(data) {
    var results = [];

    if (!data.results[0]) {
        return data
    }

    $.each(data.results[0].children, function() {
        // filter out the SAME repo, it cannot be used as fork of itself
        if (this.repo_id != currentRepoId) {
            this.id = this.repo_id;
            results.push(this)
        }
    });
    data.results[0].children = results;
    return data;
};

$("#id_fork_of").select2({
    cachedDataSource: {},
    minimumInputLength: 2,
    placeholder: "${_('Change repository') if c.rhodecode_db_repo.fork else _('Pick repository')}",
    dropdownAutoWidth: true,
    containerCssClass: "drop-menu",
    dropdownCssClass: "drop-menu-dropdown",
    formatResult: formatRepoResult,
    query: $.debounce(250, function(query){
        self = this;
        var cacheKey = query.term;
        var cachedData = self.cachedDataSource[cacheKey];

        if (cachedData) {
            query.callback({results: cachedData.results});
        } else {
            $.ajax({
                url: pyroutes.url('repo_list_data'),
                data: {'query': query.term, repo_type: '${c.rhodecode_db_repo.repo_type}'},
                dataType: 'json',
                type: 'GET',
                success: function(data) {
                    data = repoTypeFilter(data);
                    self.cachedDataSource[cacheKey] = data;
                    query.callback({results: data.results});
                },
                error: function(data, textStatus, errorThrown) {
                    alert("Error while fetching entries.\nError code {0} ({1}).".format(data.status, data.statusText));
                }
            })
        }
    })
});
</script>

