<div class="panel panel-default">
    <div class="panel-heading">
        <h3 class="panel-title">${_('Maintenance')}</h3>
    </div>
    <div class="panel-body">

        <p>
            % if c.executable_tasks:
            ${_('Perform maintenance tasks for this repo, following tasks will be performed')}:
            <ol>
            % for task in c.executable_tasks:
                <li>${task}</li>
            % endfor
            </ol>
            % else:
                ${_('No maintenance tasks for this repo available')}
            % endif
        </p>

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

    var url = "${h.route_path('repo_maintenance_execute', repo_name=c.repo_info.repo_name)}";
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
