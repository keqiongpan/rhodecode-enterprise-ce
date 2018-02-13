<div class="panel panel-default">
    <div class="panel-heading">
        <h3 class="panel-title">${_('Remote Sync')}</h3>
    </div>
    <div class="panel-body">

        <h4>${_('Manually pull/push changes from/to external URLs.')}</h4>

        <table>
                <tr>
                <td><div style="min-width: 80px"><strong>${_('Pull url')}</strong></div></td>
                <td>
                    % if c.rhodecode_db_repo.clone_uri:
                    <a href="${c.rhodecode_db_repo.clone_uri}">${c.rhodecode_db_repo.clone_uri_hidden}</a>
                    % else:
                        ${_('This repository does not have any pull url set.')}
                        <a href="${h.route_path('edit_repo', repo_name=c.rhodecode_db_repo.repo_name)}">${_('Set remote url.')}</a>
                    % endif
                </td>
                </tr>
                % if c.rhodecode_db_repo.clone_uri:
                <tr>
                    <td></td>
                    <td>
                        <p>
                            ${_('Pull can be automated by such api call. Can be called periodically in crontab etc.')}
                            <br/>
                            <code>
                            ${h.api_call_example(method='pull', args={"repoid": c.rhodecode_db_repo.repo_name})}
                            </code>
                        </p>
                    </td>
                </tr>
                <tr>
                    <td></td>
                    <td>
                        ${h.secure_form(h.route_path('edit_repo_remote_pull', repo_name=c.repo_name), request=request)}
                        <div class="form">
                           <div class="fields">
                               ${h.submit('remote_pull_%s' % c.rhodecode_db_repo.repo_name,_('Pull changes from remote location'),class_="btn btn-small",onclick="return confirm('"+_('Confirm to pull changes from remote side')+"');")}
                           </div>
                        </div>
                        ${h.end_form()}
                    </td>
                </tr>
                % endif

                <tr>
                <td><div style="min-width: 80px"><strong>${_('Push url')}</strong></div></td>
                <td>
                    % if c.rhodecode_db_repo.push_uri:
                    <a href="${c.rhodecode_db_repo.push_uri_hidden}">${c.rhodecode_db_repo.push_uri_hidden}</a>
                    % else:
                        ${_('This repository does not have any push url set.')}
                        <a href="${h.route_path('edit_repo', repo_name=c.rhodecode_db_repo.repo_name)}">${_('Set remote url.')}</a>
                    % endif
                </td>
                </tr>
                <tr>
                    <td></td>
                    <td>
                        ${_('This feature is available in RhodeCode EE edition only. Contact {sales_email} to obtain a trial license.').format(sales_email='<a href="mailto:sales@rhodecode.com">sales@rhodecode.com</a>')|n}
                    </td>
                </tr>

            </table>
    </div>
</div>
