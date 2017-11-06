## -*- coding: utf-8 -*-
<%inherit file="/base/base.mako"/>

<%def name="title()">
    %if c.repo_name:
        ${_('Search inside repository %(repo_name)s') % {'repo_name': c.repo_name}}
    %else:
        ${_('Search inside all accessible repositories')}
    %endif
    %if c.rhodecode_name:
        &middot; ${h.branding(c.rhodecode_name)}
    %endif
</%def>

<%def name="breadcrumbs_links()">
  %if c.repo_name:
    ${_('Search inside repository %(repo_name)s') % {'repo_name': c.repo_name}}
  %else:
    ${_('Search inside all accessible repositories')}
  %endif
  %if c.cur_query:
    &raquo;
    ${c.cur_query}
  %endif
</%def>

<%def name="menu_bar_nav()">
    %if c.repo_name:
    ${self.menu_items(active='repositories')}
    %else:
    ${self.menu_items(active='search')}
    %endif
</%def>

<%def name="menu_bar_subnav()">
    %if c.repo_name:
    ${self.repo_menu(active='options')}
    %endif
</%def>

<%def name="main()">
<div class="box">
    %if c.repo_name:
        <!-- box / title -->
        <div class="title">
            ${self.repo_page_title(c.rhodecode_db_repo)}
        </div>
        ${h.form(h.route_path('search_repo',repo_name=c.repo_name),method='get')}
    %else:
        <!-- box / title -->
        <div class="title">
            ${self.breadcrumbs()}
            <ul class="links">&nbsp;</ul>
        </div>
        <!-- end box / title -->
        ${h.form(h.route_path('search'), method='get')}
    %endif
    <div class="form search-form">
        <div class="fields">
            <label for="q">${_('Search item')}:</label>
            ${h.text('q', c.cur_query)}

            ${h.select('type',c.search_type,[('content',_('File contents')), ('commit',_('Commit messages')), ('path',_('File names')),],id='id_search_type')}
            <input type="submit" value="${_('Search')}" class="btn"/>
            <br/>

            <div class="search-feedback-items">
            % for error in c.errors:
              <span class="error-message">
                  % for k,v in error.asdict().items():
                    ${k} - ${v}
                  % endfor
              </span>
            % endfor
            <div class="field">
                <p class="filterexample" style="position: inherit" onclick="$('#search-help').toggle()">${_('Example Queries')}</p>
                <pre id="search-help" style="display: none">${h.tooltip(h.search_filter_help(c.searcher, c.pyramid_request))}</pre>
            </div>

            <div class="field">${c.runtime}</div>
            </div>
        </div>
    </div>

    ${h.end_form()}
    <div class="search">
    % if c.search_type == 'content':
        <%include file='search_content.mako'/>
    % elif c.search_type == 'path':
        <%include file='search_path.mako'/>
    % elif c.search_type == 'commit':
        <%include file='search_commit.mako'/>
    % elif c.search_type == 'repository':
        <%include file='search_repository.mako'/>
    % endif
    </div>
</div>
<script>
    $(document).ready(function(){
        $("#id_search_type").select2({
            'containerCssClass': "drop-menu",
            'dropdownCssClass': "drop-menu-dropdown",
            'dropdownAutoWidth': true,
            'minimumResultsForSearch': -1
        });
    })
</script>
</%def>
