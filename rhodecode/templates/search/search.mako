## -*- coding: utf-8 -*-
<%inherit file="/base/base.mako"/>

<%def name="title()">
    %if c.repo_name:
        ${_('Search inside repository {repo_name}').format(repo_name=c.repo_name)}
    %elif c.repo_group_name:
        ${_('Search inside repository group {repo_group_name}').format(repo_group_name=c.repo_group_name)}
    %else:
        ${_('Search inside all accessible repositories')}
    %endif
    %if c.rhodecode_name:
        &middot; ${h.branding(c.rhodecode_name)}
    %endif
</%def>

<%def name="breadcrumbs_links()">
  %if c.repo_name:
    ${_('Search inside repository {repo_name}').format(repo_name=c.repo_name)}
  %elif c.repo_group_name:
    ${_('Search inside repository group {repo_group_name}').format(repo_group_name=c.repo_group_name)}
  %else:
    ${_('Search inside all accessible repositories')}
  %endif

</%def>

<%def name="menu_bar_nav()">
    %if c.repo_name:
    ${self.menu_items(active='search')}
    %elif c.repo_group_name:
    ${self.menu_items(active='search')}
    %else:
    ${self.menu_items(active='search')}
    %endif
</%def>

<%def name="menu_bar_subnav()">
    %if c.repo_name:
        ${self.repo_menu(active='summary')}
    %elif c.repo_group_name:
        ${self.repo_group_menu(active='home')}
    %endif
</%def>

<%def name="repo_icon(db_repo)">
    %if h.is_hg(db_repo):
        <i class="icon-hg"></i>
    %endif
    %if h.is_git(db_repo):
        <i class="icon-git"></i>
    %endif
    %if h.is_svn(db_repo):
        <i class="icon-svn"></i>
    %endif
</%def>

<%def name="repo_group_icon()">
    <i class="icon-repo-group"></i>
</%def>

<%def name="main()">
<div class="box">
    %if c.repo_name:
        <!-- box / title -->
        ${h.form(h.route_path('search_repo',repo_name=c.repo_name),method='get')}
    %elif c.repo_group_name:
        <!-- box / title -->
        ${h.form(h.route_path('search_repo_group',repo_group_name=c.repo_group_name),method='get')}
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

            ${h.text('q', c.cur_query, placeholder="Enter query...")}

            ${h.select('type',c.search_type,[('content',_('Files')), ('path',_('File path')),('commit',_('Commits'))],id='id_search_type')}
            ${h.hidden('max_lines', '10')}

            <input type="submit" value="${_('Search')}" class="btn"/>
            <br/>

            <div class="search-tags">
                <span class="tag tag8">
                    %if c.repo_name:
                        <a href="${h.route_path('search', _query={'q': c.cur_query, 'type': request.GET.get('type', 'content')})}">${_('Global Search')}</a>
                    %elif c.repo_group_name:
                        <a href="${h.route_path('search', _query={'q': c.cur_query, 'type': request.GET.get('type', 'content')})}">${_('Global Search')}</a>
                    % else:
                        ${_('Global Search')}
                    %endif
                </span>

            %if c.repo_name:
                »
                <span class="tag tag8">
                    ${repo_icon(c.rhodecode_db_repo)}
                    ${c.repo_name}
                </span>

            %elif c.repo_group_name:
                »
                <span class="tag tag8">
                    ${repo_group_icon()}
                    ${c.repo_group_name}
                </span>
            %endif


            % for search_tag in c.search_tags:
                <br/><span class="tag disabled" style="margin-top: 3px">${search_tag}</span>
            % endfor

            </div>

            <div class="search-feedback-items">
            % for error in c.errors:
              <span class="error-message">
                  % for k,v in error.asdict().items():
                    ${k} - ${v}
                  % endfor
              </span>
            % endfor
            <div class="field">
                <p class="filterexample" style="position: inherit" onclick="$('#search-help').toggle()">${_('Query Langague examples')}</p>
<pre id="search-help" style="display: none">\

% if c.searcher.name == 'whoosh':
Example filter terms for `Whoosh` search:
query lang: <a href="${c.searcher.query_lang_doc}">Whoosh Query Language</a>
Whoosh has limited query capabilities. For advanced search use ElasticSearch 6 from RhodeCode EE edition.

Generate wildcards using '*' character:
  "repo_name:vcs*" - search everything starting with 'vcs'
  "repo_name:*vcs*" - search for repository containing 'vcs'

Optional AND / OR operators in queries
  "repo_name:vcs OR repo_name:test"
  "owner:test AND repo_name:test*" AND extension:py

Move advanced search is available via ElasticSearch6 backend in EE edition.
% elif c.searcher.name == 'elasticsearch' and c.searcher.es_version == '2':
Example filter terms for `ElasticSearch-${c.searcher.es_version}`search:
ElasticSearch-2 has limited query capabilities. For advanced search use ElasticSearch 6 from RhodeCode EE edition.

search type: content (File Content)
  indexed fields: content

  # search for `fix` string in all files
  fix

search type: commit (Commit message)
  indexed fields: message

search type: path (File name)
  indexed fields: path

% else:
Example filter terms for `ElasticSearch-${c.searcher.es_version}`search:
query lang: <a href="${c.searcher.query_lang_doc}">ES 6 Query Language</a>
The reserved characters needed espace by `\`: + - = && || > < ! ( ) { } [ ] ^ " ~ * ? : \ /
% for handler in c.searcher.get_handlers().values():

search type: ${handler.search_type_label}
  *indexed fields*: ${', '.join( [('\n    ' if x[0]%4==0 else '')+x[1] for x in enumerate(handler.es_6_field_names)])}
  % for entry in handler.es_6_example_queries:
  ${entry.rstrip()}
  % endfor
% endfor

% endif
</pre>
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

        $('#q').autoGrowInput({maxWidth: 920});

        setTimeout(function() {
            $('#q').keyup()
        }, 1);
    })
</script>
</%def>
