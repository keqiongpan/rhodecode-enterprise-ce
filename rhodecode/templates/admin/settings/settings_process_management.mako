
<div id="update_notice" style="display: none; margin: -40px 0px 20px 0px">
    <div>${_('Checking for updates...')}</div>
</div>


<div class="panel panel-default">
    <div class="panel-heading">
        <h3 class="panel-title">${_('Gunicorn process management')}</h3>

    </div>
    <div class="panel-body" id="app">
        <h3>List of Gunicorn processes on this machine</h3>
        <table>
        % for proc in c.gunicorn_processes:
            <% mem = proc.memory_info()%>

            <tr>
                <td>
                    <code>
                    ${proc.pid} - ${proc.name()}
                    </code>
                </td>
                <td>
                    <a href="#showCommand" onclick="$('#pid'+${proc.pid}).toggle();return false"> command </a>
                    <code id="pid${proc.pid}" style="display: none">
                    ${''.join(proc.cmdline())}
                    </code>
                </td>
                <td>
                    RSS:${h.format_byte_size_binary(mem.rss)}
                </td>
                <td>
                    VMS:${h.format_byte_size_binary(mem.vms)}
                </td>
                <td>
                    <% is_master = proc.children(recursive=True) %>
                    % if is_master:
                        MASTER
                    % else:
                        <a href="#restartProcess" onclick="restart(this, ${proc.pid});return false">
                            restart
                        </a>
                    % endif
                </td>
            </tr>
        % endfor
        </table>
    </div>
</div>


<script>


restart = function(elem, pid) {

    if ($(elem).hasClass('disabled')){
        return;
    }
    $(elem).addClass('disabled');
    $(elem).html('processing...');

    $.ajax({
        url: pyroutes.url('admin_settings_process_management_signal'),
        headers: {
            "X-CSRF-Token": CSRF_TOKEN,
        },
        data: JSON.stringify({'pids': [pid]}),
        dataType: 'json',
        type: 'POST',
        contentType: "application/json; charset=utf-8",
        success: function (data) {
            $(elem).html(data.result);
            $(elem).removeClass('disabled');
        },
        failure: function (data) {
            $(elem).text('FAILED TO LOAD RESULT');
            $(elem).removeClass('disabled');
        },
        error: function (data) {
            $(elem).text('FAILED TO LOAD RESULT');
            $(elem).removeClass('disabled');
        }
    })
}


</script>
