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
    ${self.repo_menu(active='changelog')}
</%def>

<%def name="main()">

<div class="box">
    <div class="title">
        ${self.repo_page_title(c.rhodecode_db_repo)}
        <ul class="links">
            <li>
                <a href="#" class="btn btn-small" id="rev_range_container" style="display:none;"></a>
                %if c.rhodecode_db_repo.fork:
                    <span>
                        <a  id="compare_fork_button"
                            title="${h.tooltip(_('Compare fork with %s' % c.rhodecode_db_repo.fork.repo_name))}"
                            class="btn btn-small"
                            href="${h.url('compare_url',
                                repo_name=c.rhodecode_db_repo.fork.repo_name,
                                source_ref_type=c.rhodecode_db_repo.landing_rev[0],
                                source_ref=c.rhodecode_db_repo.landing_rev[1],
                                target_repo=c.repo_name,
                                target_ref_type='branch' if request.GET.get('branch') else c.rhodecode_db_repo.landing_rev[0],
                                target_ref=request.GET.get('branch') or c.rhodecode_db_repo.landing_rev[1],
                                merge=1)}"
                        >
                                <i class="icon-loop"></i>
                                ${_('Compare fork with Parent (%s)' % c.rhodecode_db_repo.fork.repo_name)}
                        </a>
                    </span>
                %endif

                ## pr open link
                %if h.is_hg(c.rhodecode_repo) or h.is_git(c.rhodecode_repo):
                    <span>
                        <a id="open_new_pull_request" class="btn btn-small btn-success" href="${h.url('pullrequest_home',repo_name=c.repo_name)}">
                            ${_('Open new pull request')}
                        </a>
                    </span>
                %endif

                ## clear selection
                <div title="${_('Clear selection')}" class="btn" id="rev_range_clear" style="display:none">
                    ${_('Clear selection')}
                </div>

            </li>
        </ul>
    </div>

    % if c.pagination:
        <script type="text/javascript" src="${h.asset('js/jquery.commits-graph.js')}"></script>

        <div class="graph-header">
            <div id="filter_changelog">
                ${h.hidden('branch_filter')}
                 %if c.selected_name:
                 <div class="btn btn-default" id="clear_filter" >
                     ${_('Clear filter')}
                 </div>
                %endif
            </div>
            ${self.breadcrumbs('breadcrumbs_light')}
            <div id="commit-counter" data-total=${c.total_cs} class="pull-right">
                ${_ungettext('showing %d out of %d commit', 'showing %d out of %d commits', c.showing_commits) % (c.showing_commits, c.total_cs)}
            </div>
        </div>

        <div id="graph">
            <div class="graph-col-wrapper">
              <div id="graph_nodes">
                <div id="graph_canvas"></div>
            </div>
            <div id="graph_content" class="main-content graph_full_width">

              <div class="table">
                <table id="changesets" class="rctable">
                    <tr>
                      ## checkbox
                      <th></th>
                      <th colspan="2"></th>

                      <th>${_('Commit')}</th>
                      ## commit message expand arrow
                      <th></th>
                      <th>${_('Commit Message')}</th>

                      <th>${_('Age')}</th>
                      <th>${_('Author')}</th>

                      <th>${_('Refs')}</th>
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
        </div>

        <script type="text/javascript">
        var cache = {};
        $(function(){

            // Create links to commit ranges when range checkboxes are selected
            var $commitCheckboxes = $('.commit-range');
            // cache elements
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
                if(open_new_pull_request){
                      var selected_changes = selectedCheckboxes.length;
                      if (selected_changes > 1 || selected_changes == 1 && templateContext.repo_type != 'hg') {
                          open_new_pull_request.hide();
                      } else {
                          if (selected_changes == 1) {
                             open_new_pull_request.html(_gettext('Open new pull request for selected commit'));
                          } else if (selected_changes == 0) {
                             open_new_pull_request.html(_gettext('Open new pull request'));
                          }
                          open_new_pull_request.show();
                      }
                }

                if (selectedCheckboxes.length>0){
                    var revEnd = selectedCheckboxes[0].name;
                    var revStart = selectedCheckboxes[selectedCheckboxes.length-1].name;
                    var url = pyroutes.url('changeset_home',
                            {'repo_name': '${c.repo_name}',
                             'revision': revStart+'...'+revEnd});

                    var link = (revStart == revEnd)
                        ? _gettext('Show selected commit __S')
                        : _gettext('Show selected commits __S ... __E');

                    link = link.replace('__S', revStart.substr(0,6));
                    link = link.replace('__E', revEnd.substr(0,6));

                    $commitRangeContainer
                        .attr('href',url)
                        .html(link)
                        .show();

                    $commitRangeClear.show();
                    var _url = pyroutes.url('pullrequest_home',
                                    {'repo_name': '${c.repo_name}',
                                     'commit': revEnd});
                    open_new_pull_request.attr('href', _url);
                    $('#compare_fork_button').hide();
                } else {
                    $commitRangeContainer.hide();
                    $commitRangeClear.hide();

                    %if c.branch_name:
                        var _url = pyroutes.url('pullrequest_home',
                                        {'repo_name': '${c.repo_name}',
                                         'branch':'${c.branch_name}'});
                        open_new_pull_request.attr('href', _url);
                    %else:
                        var _url = pyroutes.url('pullrequest_home',
                                        {'repo_name': '${c.repo_name}'});
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
                window.location = pyroutes.url('repo_changelog', filter);
            });

            $("#branch_filter").select2({
                'dropdownAutoWidth': true,
                'width': 'resolve',
                'placeholder': "${c.selected_name or _('Filter changelog')}",
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
                var selected = data.text;
                var filter = {'repo_name': '${c.repo_name}'};
                if(data.type == 'branch' || data.type == 'branch_closed'){
                    filter["branch"] = selected;
                }
                else if (data.type == 'book'){
                    filter["bookmark"] = selected;
                }
                window.location = pyroutes.url('repo_changelog', filter);
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
