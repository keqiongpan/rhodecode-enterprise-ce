<div class="panel panel-default">
    <div class="panel-heading">
        <h3 class="panel-title">${_('Remote url')}</h3>
    </div>
    <div class="panel-body">

        <h4>${_('Manually pull changes from external repository.')}</h4>

        %if c.repo_info.clone_uri:

            ${_('Remote mirror url')}:
            <a href="${c.repo_info.clone_uri}">${c.repo_info.clone_uri_hidden}</a>

            <p>
                ${_('Pull can be automated by such api call. Can be called periodically in crontab etc.')}
                <br/>
                <code>
                ${h.api_call_example(method='pull', args={"repoid": c.repo_info.repo_name})}
                </code>
            </p>

            ${h.secure_form(url('edit_repo_remote', repo_name=c.repo_name), method='put')}
            <div class="form">
               <div class="fields">
                   ${h.submit('remote_pull_%s' % c.repo_info.repo_name,_('Pull changes from remote location'),class_="btn btn-small",onclick="return confirm('"+_('Confirm to pull changes from remote side')+"');")}
               </div>
            </div>
            ${h.end_form()}
        %else:

          ${_('This repository does not have any remote mirror url set.')}
          <a href="${h.route_path('edit_repo', repo_name=c.repo_info.repo_name)}">${_('Set remote url.')}</a>
          <br/>
          <br/>
          <button class="btn disabled" type="submit" disabled="disabled">
            ${_('Pull changes from remote location')}
          </button>
        %endif
    </div>
</div>
