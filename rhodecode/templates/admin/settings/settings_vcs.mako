<%namespace name="vcss" file="/base/vcs_settings.mako"/>

${h.secure_form(url('admin_settings_vcs'), method='post')}
    <div>
        ${vcss.vcs_settings_fields(
            suffix='',
            svn_tag_patterns=c.svn_tag_patterns,
            svn_branch_patterns=c.svn_branch_patterns,
            display_globals=True,
            allow_repo_location_change=c.visual.allow_repo_location_change
        )}
        <div class="buttons">
            ${h.submit('save',_('Save settings'),class_="btn")}
            ${h.reset('reset',_('Reset'),class_="btn")}
       </div>
    </div>
${h.end_form()}

<script type="text/javascript">

    function ajaxDeletePattern(pattern_id, field_id) {
        var sUrl = "${h.url('admin_settings_vcs')}";
        var callback =  function (o) {
            var elem = $("#"+field_id);
            elem.remove();
        };
        var postData = {
            '_method': 'delete',
            'delete_svn_pattern': pattern_id,
            'csrf_token': CSRF_TOKEN
        };
        var request = $.post(sUrl, postData)
                .done(callback)
                .fail(function (data, textStatus, errorThrown) {
                    alert("Error while deleting hooks.\nError code {0} ({1}). URL: {2}".format(data.status,data.statusText,$(this)[0].url));
            });
    };

    $(document).ready(function() {

        var unlockpath = function() {
            $('#path_unlock_icon').removeClass('icon-lock').addClass('icon-unlock');
            $('#paths_root_path').removeAttr('readonly').removeClass('disabled');
        };

        $('#path_unlock').on('click', function(e) {
            unlockpath();
        });

        if ($('.locked_input').children().hasClass('error-message')) {
            unlockpath();
        }

        /* On click handler for the `Generate Apache Config` button. It sends a
        POST request to trigger the (re)generation of the mod_dav_svn config. */
        $('#vcs_svn_generate_cfg').on('click', function(event) {
            event.preventDefault();
            var url = "${h.route_path('admin_settings_vcs_svn_generate_cfg')}";
            var jqxhr = $.post(url, {'csrf_token': CSRF_TOKEN});
            jqxhr.done(function(data) {
                $.Topic('/notifications').publish(data);
            });
        });

    });
</script>
