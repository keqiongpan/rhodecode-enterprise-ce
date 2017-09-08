<div class="panel panel-default">
    <div class="panel-heading">
        <h3 class="panel-title">${_('Maintenance')}</h3>
    </div>
    <div class="panel-body">

        % if c.executable_tasks:
        <h4>${_('Perform maintenance tasks for this repo')}</h4>

        <span>${_('Following tasks will be performed')}:</span>
        <ol>
        % for task in c.executable_tasks:
            <li>${task}</li>
        % endfor
        </ol>
        <p>
            ${_('Maintenance can be automated by such api call. Can be called periodically in crontab etc.')}
            <br/>
            <code>
                ${h.api_call_example(method='maintenance', args={"repoid": c.rhodecode_db_repo.repo_name})}
            </code>
        </p>

        % else:
            <h4>${_('No maintenance tasks for this repo available')}</h4>
        % endif

        <div id="results" style="display:none; padding: 10px 0px;"></div>

        % if c.executable_tasks:
        <div class="form">
           <div class="fields">
               <button class="btn btn-small btn-primary" onclick="executeTask();return false">
               ${_('Run Maintenance')}
               </button>
           </div>
        </div>
        % endif

    </div>
</div>


<script>

executeTask = function() {
    var btn = $(this);
    $('#results').show();
    $('#results').html('<h4>${_('Performing Maintenance')}...</h4>');

    btn.attr('disabled', 'disabled');
    btn.addClass('disabled');

    var url = "${h.route_path('edit_repo_maintenance_execute', repo_name=c.rhodecode_db_repo.repo_name)}";
    var success = function (data) {
        var displayHtml = $('<pre></pre>');

        $(displayHtml).append(data);
        $('#results').html(displayHtml);
        btn.removeAttr('disabled');
        btn.removeClass('disabled');
    };
    ajaxGET(url, success, null);

}
</script>
