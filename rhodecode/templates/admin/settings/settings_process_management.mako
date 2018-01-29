
<div id="update_notice" style="display: none; margin: -40px 0px 20px 0px">
    <div>${_('Checking for updates...')}</div>
</div>


<div class="panel panel-default">
    <div class="panel-heading">
        <h3 class="panel-title">${_('Gunicorn process management')}</h3>
        <div class="pull-right">
            <a id="autoRefreshEnable" href="#autoRefreshEnable" onclick="enableAutoRefresh(); return false">${_('start auto refresh')}</a>
            <a id="autoRefreshDisable" href="#autoRefreshDisable" onclick="disableAutoRefresh(); return false" style="display: none">${_('stop auto refresh')}</a>
        </div>
    </div>
    <div class="panel-body" id="app">
        <h3>List of Gunicorn processes on this machine</h3>
        <%
            def get_name(proc):
                cmd = ' '.join(proc.cmdline())
                if 'vcsserver.ini' in cmd:
                    return 'VCSServer'
                elif 'rhodecode.ini' in cmd:
                    return 'RhodeCode'
                return proc.name()
        %>
        <%include file='settings_process_management_data.mako'/>
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
};

var intervalID = null;
var currentRequest = null;

autoRefresh = function(value) {
    var url = pyroutes.url('admin_settings_process_management_data');
    var loadData = function() {
        currentRequest = $.get(url)
            .done(function(data) {
                currentRequest = null;
                $('#procList').html(data);
                timeagoActivate();
                var beat = function(doCallback) {
                    var callback = function () {};
                    if (doCallback){
                        var callback = function () {beat(false)};
                    }
                    $('#processTimeStamp').animate({
                        opacity: $('#processTimeStamp').css('opacity') == '1' ? '0.3' : '1'
                    }, 500, callback);
                };
                beat(true)
            });
    };

    if (value) {
        intervalID = setInterval(loadData, 5000);
    } else {
        clearInterval(intervalID);
    }
};

enableAutoRefresh = function() {
  $('#autoRefreshEnable').hide();
  $('#autoRefreshDisable').show();
  autoRefresh(true)
};

disableAutoRefresh = function() {
  $('#autoRefreshEnable').show();
  $('#autoRefreshDisable').hide();
  autoRefresh(false)
};


</script>
