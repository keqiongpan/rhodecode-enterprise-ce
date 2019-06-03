## -*- coding: utf-8 -*-
<%inherit file="/base/base.mako"/>
<%namespace name="cbdiffs" file="/codeblocks/diffs.mako"/>

<%def name="title()">
    %if c.compare_home:
        ${_('%s Compare') % c.repo_name}
    %else:
        ${_('%s Compare') % c.repo_name} - ${'%s@%s' % (c.source_repo.repo_name, c.source_ref)} &gt; ${'%s@%s' % (c.target_repo.repo_name, c.target_ref)}
    %endif
    %if c.rhodecode_name:
        &middot; ${h.branding(c.rhodecode_name)}
    %endif
</%def>

<%def name="breadcrumbs_links()"></%def>

<%def name="menu_bar_nav()">
    ${self.menu_items(active='repositories')}
</%def>

<%def name="menu_bar_subnav()">
    ${self.repo_menu(active='compare')}
</%def>

<%def name="main()">
    <script type="text/javascript">
        // set fake commitId on this commit-range page
        templateContext.commit_data.commit_id = "${h.EmptyCommit().raw_id}";
    </script>

    <div class="box">
        <div class="summary changeset">
            <div class="summary-detail">
              <div class="summary-detail-header">
                  <span class="breadcrumbs files_location">
                    <h4>
                        ${_('Compare Commits')}
                        % if c.file_path:
                        ${_('for file')} <a href="#${'a_' + h.FID('',c.file_path)}">${c.file_path}</a>
                        % endif

                        % if c.commit_ranges:
                        <code>
                        r${c.source_commit.idx}:${h.short_id(c.source_commit.raw_id)}...r${c.target_commit.idx}:${h.short_id(c.target_commit.raw_id)}
                        </code>
                        % endif
                    </h4>
                  </span>

                  <div class="clear-fix"></div>
              </div>

              <div class="fieldset">
                <div class="left-label-summary">
                    <p class="spacing">${_('Target')}:</p>
                    <div class="right-label-summary">
                        <div class="code-header" >
                            <div class="compare_header">
                                ## The hidden elements are replaced with a select2 widget
                                ${h.hidden('compare_source')}
                            </div>
                        </div>
                    </div>
                </div>
              </div>

              <div class="fieldset">
                <div class="left-label-summary">
                    <p class="spacing">${_('Source')}:</p>
                    <div class="right-label-summary">
                        <div class="code-header" >
                            <div class="compare_header">
                                ## The hidden elements are replaced with a select2 widget
                                ${h.hidden('compare_target')}
                            </div>
                        </div>
                    </div>
                </div>
              </div>

              <div class="fieldset">
                <div class="left-label-summary">
                    <p class="spacing">${_('Actions')}:</p>
                    <div class="right-label-summary">
                        <div class="code-header" >
                            <div class="compare_header">
                                <div class="compare-buttons">
                                % if c.compare_home:
                                  <a id="compare_revs" class="btn btn-primary"> ${_('Compare Commits')}</a>
                                  %if c.rhodecode_db_repo.fork:

                                       <a class="btn btn-default" title="${h.tooltip(_('Compare fork with %s' % c.rhodecode_db_repo.fork.repo_name))}"
                                          href="${h.route_path('repo_compare',
                                                repo_name=c.rhodecode_db_repo.fork.repo_name,
                                                source_ref_type=c.rhodecode_db_repo.landing_rev[0],
                                                source_ref=c.rhodecode_db_repo.landing_rev[1],
                                                target_repo=c.repo_name,target_ref_type='branch' if request.GET.get('branch') else c.rhodecode_db_repo.landing_rev[0],
                                                target_ref=request.GET.get('branch') or c.rhodecode_db_repo.landing_rev[1],
                                                _query=dict(merge=1))}"
                                        >
                                       ${_('Compare with origin')}
                                       </a>

                                  %endif

                                  <a class="btn disabled tooltip" disabled="disabled" title="${_('Action unavailable in current view')}">${_('Swap')}</a>
                                  <a class="btn disabled tooltip" disabled="disabled" title="${_('Action unavailable in current view')}">${_('Comment')}</a>
                                  <div id="changeset_compare_view_content">
                                     <div class="help-block">${_('Compare commits, branches, bookmarks or tags.')}</div>
                                  </div>

                                % elif c.preview_mode:
                                  <a class="btn disabled tooltip" disabled="disabled" title="${_('Action unavailable in current view')}">${_('Compare Commits')}</a>
                                  <a class="btn disabled tooltip" disabled="disabled" title="${_('Action unavailable in current view')}">${_('Swap')}</a>
                                  <a class="btn disabled tooltip" disabled="disabled" title="${_('Action unavailable in current view')}">${_('Comment')}</a>

                                % else:
                                  <a id="compare_revs" class="btn btn-primary"> ${_('Compare Commits')}</a>
                                  <a id="btn-swap" class="btn btn-primary" href="${c.swap_url}">${_('Swap')}</a>

                                  ## allow comment only if there are commits to comment on
                                  % if c.diffset and c.diffset.files and c.commit_ranges:
                                    <a id="compare_changeset_status_toggle" class="btn btn-primary">${_('Comment')}</a>
                                  % else:
                                    <a class="btn disabled tooltip" disabled="disabled" title="${_('Action unavailable in current view')}">${_('Comment')}</a>
                                  % endif
                                % endif
                                </div>
                            </div>
                        </div>
                    </div>
                    </div>
              </div>

              ## commit status form
              <div class="fieldset" id="compare_changeset_status" style="display: none; margin-bottom: -80px;">
                <div class="left-label-summary">
                    <p class="spacing">${_('Commit status')}:</p>
                    <div class="right-label-summary">
                        <%namespace name="comment" file="/changeset/changeset_file_comment.mako"/>
                        ## main comment form and it status
                        <%
                        def revs(_revs):
                            form_inputs = []
                            for cs in _revs:
                                tmpl = '<input type="hidden" data-commit-id="%(cid)s" name="commit_ids" value="%(cid)s">' % {'cid': cs.raw_id}
                                form_inputs.append(tmpl)
                            return form_inputs
                        %>
                        <div>
                            ${comment.comments(h.route_path('repo_commit_comment_create', repo_name=c.repo_name, commit_id='0'*16), None, is_compare=True, form_extras=revs(c.commit_ranges))}
                        </div>
                    </div>
                </div>
              </div>
              <div class="clear-fix"></div>
            </div> <!-- end summary-detail -->
        </div> <!-- end summary -->

        ## use JS script to load it quickly before potentially large diffs render long time
        ## this prevents from situation when large diffs block rendering of select2 fields
        <script type="text/javascript">

                var cache = {};

                var formatSelection = function(repoName){
                    return function(data, container, escapeMarkup) {
                        var selection = data ? this.text(data) : "";
                        return escapeMarkup('{0}@{1}'.format(repoName, selection));
                    }
                };

                var feedCompareData = function(query, cachedValue){
                    var data = {results: []};
                    //filter results
                    $.each(cachedValue.results, function() {
                        var section = this.text;
                        var children = [];
                        $.each(this.children, function() {
                            if (query.term.length === 0 || this.text.toUpperCase().indexOf(query.term.toUpperCase()) >= 0) {
                                children.push({
                                    'id': this.id,
                                    'text': this.text,
                                    'type': this.type
                                })
                            }
                        });
                        data.results.push({
                            'text': section,
                            'children': children
                        })
                    });
                    //push the typed in changeset
                    data.results.push({
                        'text': _gettext('specify commit'),
                        'children': [{
                            'id': query.term,
                            'text': query.term,
                            'type': 'rev'
                        }]
                    });
                    query.callback(data);
                };

                var loadCompareData = function(repoName, query, cache){
                    $.ajax({
                        url: pyroutes.url('repo_refs_data', {'repo_name': repoName}),
                        data: {},
                        dataType: 'json',
                        type: 'GET',
                        success: function(data) {
                            cache[repoName] = data;
                            query.callback({results: data.results});
                        }
                    })
                };

                var enable_fields = ${"false" if c.preview_mode else "true"};
                $("#compare_source").select2({
                    placeholder: "${'%s@%s' % (c.source_repo.repo_name, c.source_ref)}",
                    containerCssClass: "drop-menu",
                    dropdownCssClass: "drop-menu-dropdown",
                    formatSelection: formatSelection("${c.source_repo.repo_name}"),
                    dropdownAutoWidth: true,
                    query: function(query) {
                        var repoName = '${c.source_repo.repo_name}';
                        var cachedValue = cache[repoName];

                        if (cachedValue){
                            feedCompareData(query, cachedValue);
                        }
                        else {
                            loadCompareData(repoName, query, cache);
                        }
                    }
                }).select2("enable", enable_fields);

                $("#compare_target").select2({
                    placeholder: "${'%s@%s' % (c.target_repo.repo_name, c.target_ref)}",
                    dropdownAutoWidth: true,
                    containerCssClass: "drop-menu",
                    dropdownCssClass: "drop-menu-dropdown",
                    formatSelection: formatSelection("${c.target_repo.repo_name}"),
                    query: function(query) {
                        var repoName = '${c.target_repo.repo_name}';
                        var cachedValue = cache[repoName];

                        if (cachedValue){
                            feedCompareData(query, cachedValue);
                        }
                        else {
                            loadCompareData(repoName, query, cache);
                        }
                    }
                }).select2("enable", enable_fields);
                var initial_compare_source = {id: "${c.source_ref}", type:"${c.source_ref_type}"};
                var initial_compare_target = {id: "${c.target_ref}", type:"${c.target_ref_type}"};

                $('#compare_revs').on('click', function(e) {
                    var source = $('#compare_source').select2('data') || initial_compare_source;
                    var target = $('#compare_target').select2('data')  || initial_compare_target;
                    if (source && target) {
                        var url_data = {
                            repo_name: "${c.repo_name}",
                            source_ref: source.id,
                            source_ref_type: source.type,
                            target_ref: target.id,
                            target_ref_type: target.type
                        };
                        window.location = pyroutes.url('repo_compare', url_data);
                    }
                });
                $('#compare_changeset_status_toggle').on('click', function(e) {
                    $('#compare_changeset_status').toggle();
                });

        </script>

        ## table diff data
        <div class="table">


            % if not c.compare_home:
                <div id="changeset_compare_view_content">
                    <div class="pull-left">
                      <div class="btn-group">
                          <a
                              class="btn"
                              href="#"
                              onclick="$('.compare_select').show();$('.compare_select_hidden').hide(); return false">
                              ${_ungettext('Expand %s commit','Expand %s commits', len(c.commit_ranges)) % len(c.commit_ranges)}
                          </a>
                          <a
                              class="btn"
                              href="#"
                              onclick="$('.compare_select').hide();$('.compare_select_hidden').show(); return false">
                              ${_ungettext('Collapse %s commit','Collapse %s commits', len(c.commit_ranges)) % len(c.commit_ranges)}
                          </a>
                      </div>
                    </div>
                    <div style="padding:0 10px 10px 0px" class="pull-left"></div>
                    ## commit compare generated below
                    <%include file="compare_commits.mako"/>
                    ${cbdiffs.render_diffset_menu(c.diffset)}
                    ${cbdiffs.render_diffset(c.diffset)}
                 </div>
            % endif

        </div>
    </div>

</%def>
