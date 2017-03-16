<div class="panel panel-default">
    <div class="panel-heading">
        <h3 class="panel-title">${_('Remote url')}</h3>
    </div>
    <div class="panel-body">

        %if c.repo_info.clone_uri:

            <div class="panel-body-title-text">${_('Remote mirror url')}:
                <a href="${c.repo_info.clone_uri}">${c.repo_info.clone_uri_hidden}</a>
                <p>
                ${_('Pull can be automated by such api call called periodically (in crontab etc)')}
                </p>
                <code>
                curl ${h.route_url('apiv2')} -X POST -H 'content-type:text/plain' --data-binary '{"id":1, "auth_token":"SECRET","method":"pull", "args":{"repoid":"${c.repo_info.repo_name}"}}'
                </code>
            </div>

            ${h.secure_form(url('edit_repo_remote', repo_name=c.repo_name), method='put')}
            <div class="form">
               <div class="fields">
                   ${h.submit('remote_pull_%s' % c.repo_info.repo_name,_('Pull changes from remote location'),class_="btn btn-small",onclick="return confirm('"+_('Confirm to pull changes from remote side')+"');")}
               </div>
            </div>
            ${h.end_form()}
        %else:
          <div class="panel-body-title-text">${_('This repository does not have any remote mirror url set.')}</div>

          <button class="btn disabled" type="submit" disabled="disabled">
            ${_('Pull changes from remote location')}
          </button>
        %endif
    </div>
</div>



