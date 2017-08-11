<div class="panel panel-default">
    <div class="panel-heading">
        <h3 class="panel-title">${_('Repository statistics')}</h3>
    </div>
    <div class="panel-body">
        ${h.secure_form(h.route_path('edit_repo_statistics_reset', repo_name=c.repo_info.repo_name), method='POST', request=request)}
        <div class="form">
            <div class="fields">
               <div class="field" >
                <dl class="dl-horizontal settings">
                    <dt>${_('Processed commits')}:</dt><dd>${c.stats_revision}/${c.repo_last_rev}</dd>
                    <dt>${_('Processed progress')}:</dt><dd>${c.stats_percentage}%</dd>
                </dl>
               </div>
                ${h.submit('reset_stats_%s' % c.repo_info.repo_name,_('Reset statistics'),class_="btn btn-small",onclick="return confirm('"+_('Confirm to remove current statistics')+"');")}
           </div>
        </div>
        ${h.end_form()}
    </div>
</div>


