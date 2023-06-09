<%inherit file="/summary/summary_base.mako"/>

<%namespace name="components" file="/summary/components.mako"/>


<%def name="menu_bar_subnav()">
    ${self.repo_menu(active='summary')}
</%def>

<%def name="main()">

<div id="repo-summary" class="summary">
    ${components.summary_detail(breadcrumbs_links=self.breadcrumbs_links(), show_downloads=True)}
</div><!--end repo-summary-->


<div class="box">
        %if not c.repo_commits:
            <div class="empty-repo">
                <div class="title">
                  <h3>${_('Quick start')}</h3>
                </div>
                <div class="clear-fix"></div>
            </div>
         %endif
        <div class="table">
            <div id="shortlog_data">
                <%include file='summary_commits.mako'/>
            </div>
        </div>
</div>

%if c.readme_data:
<div id="readme" class="anchor">
<div class="box">

    <div class="readme-title" title="${h.tooltip(_('Readme file from commit %s:%s') % (c.rhodecode_db_repo.landing_ref_type, c.rhodecode_db_repo.landing_ref_name))}">
        <div>
            <i class="icon-file-text"></i>
            <a href="${h.route_path('repo_files',repo_name=c.repo_name,commit_id=c.rhodecode_db_repo.landing_ref_name,f_path=c.readme_file)}">
                ${c.readme_file}
            </a>
        </div>
    </div>
    <div class="readme codeblock">
      <div class="readme_box">
        ${c.readme_data|n}
      </div>
    </div>
</div>
</div>
%endif

<script type="text/javascript">
$(document).ready(function(){

    var showCloneField = function(clone_url_format){
        $.each(['http', 'http_id', 'ssh'], function (idx, val) {
            if(val === clone_url_format){
                $('#clone_option_' + val).show();
                $('#clone_option').val(val)
            } else {
                $('#clone_option_' + val).hide();
            }
        });
    };
    // default taken from session
    showCloneField(templateContext.session_attrs.clone_url_format);

    $('#clone_option').on('change', function(e) {
        var selected = $(this).val();

        storeUserSessionAttr('rc_user_session_attr.clone_url_format', selected);
        showCloneField(selected)
    });

    var initialCommitData = {
        id: null,
        text: '${c.rhodecode_db_repo.landing_ref_name}',
        type: '${c.rhodecode_db_repo.landing_ref_type}',
        raw_id: null,
        files_url: null
    };

    select2RefSwitcher('#download_options', initialCommitData);

    // on change of download options
    $('#download_options').on('change', function(e) {
        // format of Object {text: "v0.0.3", type: "tag", id: "rev"}
        var selectedReference = e.added;
        var ico = '<i class="icon-download"></i>';

        $.each($('.archive_link'), function (key, val) {
            var ext = $(this).data('ext');
            var fname = selectedReference.raw_id + ext;
            var href = pyroutes.url('repo_archivefile', {
                'repo_name': templateContext.repo_name,
                'fname': fname,
                'with_hash': '1'
            });
            // set new label
            $(this).html(ico + ' {0}{1}'.format(escapeHtml(e.added.text), ext));
            // set new url to button,
            $(this).attr('href', href)
        });

    });


    // calculate size of repository
    calculateSize = function () {

        var callback = function (data) {
            % if c.show_stats:
                showRepoStats('lang_stats', data);
            % endif
        };

        showRepoSize('repo_size_container', templateContext.repo_name, templateContext.repo_landing_commit, callback);

    }

})
</script>

</%def>
