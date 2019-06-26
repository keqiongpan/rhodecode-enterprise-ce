## -*- coding: utf-8 -*-

<%inherit file="/base/base.mako"/>

<%def name="title()">
    ${_('%s Changelog') % c.repo_name}
    %if c.changelog_for_path:
      /${c.changelog_for_path}
    %endif
    %if c.rhodecode_name:
        &middot; ${h.branding(c.rhodecode_name)}
    %endif
</%def>

<%def name="breadcrumbs_links()">
    %if c.changelog_for_path:
     /${c.changelog_for_path}
    %endif
</%def>

<%def name="menu_bar_nav()">
    ${self.menu_items(active='repositories')}
</%def>

<%def name="menu_bar_subnav()">
    ${self.repo_menu(active='commits')}
</%def>

<%def name="main()">

<div class="box">

    <div class="title">
        <div id="filter_changelog">
            ${h.hidden('branch_filter')}
             %if c.selected_name:
             <div class="btn btn-default" id="clear_filter" >
                 ${_('Clear filter')}
             </div>
            %endif
        </div>
        <div class="pull-left obsolete-toggle">
            % if h.is_hg(c.rhodecode_repo):
                % if c.show_hidden:
                    <a class="action-link" href="${h.current_route_path(request, evolve=0)}">${_('Hide obsolete/hidden')}</a>
                % else:
                    <a class="action-link" href="${h.current_route_path(request, evolve=1)}">${_('Show obsolete/hidden')}</a>
                % endif
            % else:
                    <span class="action-link disabled">${_('Show hidden')}</span>
            % endif
        </div>
        <ul class="links">
            <li>

                %if c.rhodecode_db_repo.fork:
                    <span>
                        <a  id="compare_fork_button"
                            title="${h.tooltip(_('Compare fork with %s' % c.rhodecode_db_repo.fork.repo_name))}"
                            class="btn btn-small"
                            href="${h.route_path('repo_compare',
                                repo_name=c.rhodecode_db_repo.fork.repo_name,
                                source_ref_type=c.rhodecode_db_repo.landing_rev[0],
                                source_ref=c.rhodecode_db_repo.landing_rev[1],
                                target_ref_type='branch' if request.GET.get('branch') else c.rhodecode_db_repo.landing_rev[0],
                                target_ref=request.GET.get('branch') or c.rhodecode_db_repo.landing_rev[1],
                                _query=dict(merge=1, target_repo=c.repo_name))}"
                        >
                        ${_('Compare fork with Parent (%s)' % c.rhodecode_db_repo.fork.repo_name)}
                        </a>
                    </span>
                %endif

                ## pr open link
                %if h.is_hg(c.rhodecode_repo) or h.is_git(c.rhodecode_repo):
                    <span>
                        <a id="open_new_pull_request" class="btn btn-small btn-success" href="${h.route_path('pullrequest_new',repo_name=c.repo_name)}">
                            ${_('Open new pull request')}
                        </a>
                    </span>
                %endif

            </li>
        </ul>
    </div>

    % if c.pagination:
        <script type="text/javascript" src="${h.asset('js/src/plugins/jquery.commits-graph.js')}"></script>

        <div class="graph-header">
            ${self.breadcrumbs('breadcrumbs_light')}
        </div>

        <div id="graph">
            <div class="graph-col-wrapper">
              <div id="graph_nodes">
                <div id="graph_canvas"></div>
            </div>
            <div id="graph_content" class="graph_full_width">

              <div class="table">
                <table id="changesets" class="rctable">
                    <tr>
                      ## checkbox
                      <th colspan="4">
                        ## clear selection
                        <div title="${_('Clear selection')}" class="btn btn-sm" id="rev_range_clear" style="display:none">
                            <i class="icon-cancel-circled2"></i>
                        </div>
                        <div class="btn btn-sm disabled" disabled="disabled" id="rev_range_more" style="display:none;">${_('Select second commit')}</div>
                        <a href="#" class="btn btn-success btn-sm" id="rev_range_container" style="display:none;"></a>
                      </th>
                      ## graph

                      ## review box

                      <th>${_('Commit')}</th>

                      ## commit message expand arrow
                      <th></th>
                      <th>${_('Commit Message')}</th>

                      <th>${_('Age')}</th>
                      <th>${_('Author')}</th>

                      <th>${_('Refs')}</th>
                      ## comments
                      <th></th>
                    </tr>

                    <tbody class="commits-range">
                        <%include file='changelog_elements.mako'/>
                    </tbody>
                </table>
              </div>
            </div>
            <div class="pagination-wh pagination-left">
            ${c.pagination.pager('$link_previous ~2~ $link_next')}
            </div>
            <div id="commit-counter" data-total=${c.total_cs} class="pull-right">
                ${_ungettext('showing %d out of %d commit', 'showing %d out of %d commits', c.showing_commits) % (c.showing_commits, c.total_cs)}
            </div>
        </div>

        <script type="text/javascript">
        var cache = {};
        $(function(){

            // Create links to commit ranges when range checkboxes are selected
            var $commitCheckboxes = $('.commit-range');
            // cache elements
            var $commitRangeMore = $('#rev_range_more');
            var $commitRangeContainer = $('#rev_range_container');
            var $commitRangeClear = $('#rev_range_clear');

            var checkboxRangeSelector = function(e){
                var selectedCheckboxes = [];
                for (pos in $commitCheckboxes){
                    if($commitCheckboxes[pos].checked){
                        selectedCheckboxes.push($commitCheckboxes[pos]);
                    }
                }
                var open_new_pull_request = $('#open_new_pull_request');

                if (open_new_pull_request) {
                    var selected_changes = selectedCheckboxes.length;
                    open_new_pull_request.hide();
                    if (selected_changes == 1) {
                        open_new_pull_request.html(_gettext('Open new pull request for selected commit'));
                    } else {
                        open_new_pull_request.html(_gettext('Open new pull request'));
                    }
                    open_new_pull_request.show();
                }

                if (selectedCheckboxes.length > 0) {
                    $('#compare_fork_button').hide();
                    var commitStart = $(selectedCheckboxes[selectedCheckboxes.length-1]).data();

                    var revStart = commitStart.commitId;

                    var commitEnd = $(selectedCheckboxes[0]).data();
                    var revEnd = commitEnd.commitId;

                    var lbl_start = 'r{0}:{1}'.format(commitStart.commitIdx, commitStart.commitId.substr(0,6));
                    var lbl_end = 'r{0}:{1}'.format(commitEnd.commitIdx, commitEnd.commitId.substr(0,6));
                    var url = pyroutes.url('repo_commit', {'repo_name': '${c.repo_name}', 'commit_id': revStart+'...'+revEnd});
                    var link = _gettext('Show selected commits {0} ... {1}').format(lbl_start, lbl_end);

                    if (selectedCheckboxes.length > 1) {
                        $commitRangeClear.show();
                        $commitRangeMore.hide();

                        $commitRangeContainer
                            .attr('href',url)
                            .html(link)
                            .show();


                    } else {
                        $commitRangeContainer.hide();
                        $commitRangeClear.show();
                        $commitRangeMore.show();
                    }

                    // pull-request link
                    if (selectedCheckboxes.length == 1){
                        var _url = pyroutes.url('pullrequest_new', {'repo_name': '${c.repo_name}', 'commit': revEnd});
                        open_new_pull_request.attr('href', _url);
                    } else {
                        var _url = pyroutes.url('pullrequest_new', {'repo_name': '${c.repo_name}'});
                        open_new_pull_request.attr('href', _url);
                    }

                } else {
                    $commitRangeContainer.hide();
                    $commitRangeClear.hide();
                    $commitRangeMore.hide();

                    %if c.branch_name:
                        var _url = pyroutes.url('pullrequest_new', {'repo_name': '${c.repo_name}', 'branch':'${c.branch_name}'});
                        open_new_pull_request.attr('href', _url);
                    %else:
                        var _url = pyroutes.url('pullrequest_new', {'repo_name': '${c.repo_name}'});
                        open_new_pull_request.attr('href', _url);
                    %endif
                    $('#compare_fork_button').show();
                }
            };

            $commitCheckboxes.on('click', checkboxRangeSelector);

            $commitRangeClear.on('click',function(e) {
                $commitCheckboxes.attr('checked', false);
                checkboxRangeSelector();
                e.preventDefault();
            });

            // make sure the buttons are consistent when navigate back and forth
            checkboxRangeSelector();

            var msgs = $('.message');
            // get first element height
            var el = $('#graph_content .container')[0];
            var row_h = el.clientHeight;
            for (var i=0; i < msgs.length; i++) {
                var m = msgs[i];

                var h = m.clientHeight;
                var pad = $(m).css('padding');
                if (h > row_h) {
                    var offset = row_h - (h+12);
                    $(m.nextElementSibling).css('display','block');
                    $(m.nextElementSibling).css('margin-top',offset+'px');
                }
            }

            $("#clear_filter").on("click", function() {
                var filter = {'repo_name': '${c.repo_name}'};
                window.location = pyroutes.url('repo_commits', filter);
            });

            $("#branch_filter").select2({
                'dropdownAutoWidth': true,
                'width': 'resolve',
                'placeholder': "${c.selected_name or _('Branch filter')}",
                containerCssClass: "drop-menu",
                dropdownCssClass: "drop-menu-dropdown",
                query: function(query){
                  var key = 'cache';
                  var cached = cache[key] ;
                  if(cached) {
                    var data = {results: []};
                    //filter results
                    $.each(cached.results, function(){
                        var section = this.text;
                        var children = [];
                        $.each(this.children, function(){
                            if(query.term.length == 0 || this.text.toUpperCase().indexOf(query.term.toUpperCase()) >= 0 ){
                                children.push({'id': this.id, 'text': this.text, 'type': this.type})
                            }
                        });
                        data.results.push({'text': section, 'children': children});
                        query.callback({results: data.results});
                    });
                  }else{
                      $.ajax({
                        url: pyroutes.url('repo_refs_changelog_data', {'repo_name': '${c.repo_name}'}),
                        data: {},
                        dataType: 'json',
                        type: 'GET',
                        success: function(data) {
                          cache[key] = data;
                          query.callback({results: data.results});
                        }
                      })
                  }
                }
            });
            $('#branch_filter').on('change', function(e){
                var data = $('#branch_filter').select2('data');
                //type: branch_closed
                var selected = data.text;
                var filter = {'repo_name': '${c.repo_name}'};
                if(data.type == 'branch' || data.type == 'branch_closed'){
                    filter["branch"] = selected;
                    if (data.type == 'branch_closed') {
                        filter["evolve"] = '1';
                    }
                }
                else if (data.type == 'book'){
                    filter["bookmark"] = selected;
                }
                window.location = pyroutes.url('repo_commits', filter);
            });

            commitsController = new CommitsController();
            % if not c.changelog_for_path:
                commitsController.reloadGraph();
            % endif

        });

    </script>
        </div>
    % else:
        ${_('There are no changes yet')}
    % endif
</div>
</%def>
