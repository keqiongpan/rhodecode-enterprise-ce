## -*- coding: utf-8 -*-
<%inherit file="root.mako"/>

<%include file="/ejs_templates/templates.html"/>

<div class="outerwrapper">
  <!-- HEADER -->
  <div class="header">
      <div id="header-inner" class="wrapper">
          <div id="logo">
              <div class="logo-wrapper">
                  <a href="${h.route_path('home')}"><img src="${h.asset('images/rhodecode-logo-white-216x60.png')}" alt="RhodeCode"/></a>
              </div>
              %if c.rhodecode_name:
               <div class="branding">- ${h.branding(c.rhodecode_name)}</div>
              %endif
          </div>
          <!-- MENU BAR NAV -->
          ${self.menu_bar_nav()}
          <!-- END MENU BAR NAV -->
      </div>
  </div>
  ${self.menu_bar_subnav()}
  <!-- END HEADER -->

  <!-- CONTENT -->
  <div id="content" class="wrapper">

      <rhodecode-toast id="notifications"></rhodecode-toast>

      <div class="main">
          ${next.main()}
      </div>
  </div>
  <!-- END CONTENT -->

</div>
<!-- FOOTER -->
<div id="footer">
   <div id="footer-inner" class="title wrapper">
       <div>
           <p class="footer-link-right">
               % if c.visual.show_version:
                   RhodeCode Enterprise ${c.rhodecode_version} ${c.rhodecode_edition}
               % endif
               &copy; 2010-${h.datetime.today().year}, <a href="${h.route_url('rhodecode_official')}" target="_blank">RhodeCode GmbH</a>. All rights reserved.
               % if c.visual.rhodecode_support_url:
                  <a href="${c.visual.rhodecode_support_url}" target="_blank">${_('Support')}</a>
               % endif
           </p>
           <% sid = 'block' if request.GET.get('showrcid') else 'none' %>
           <p class="server-instance" style="display:${sid}">
               ## display hidden instance ID if specially defined
               % if c.rhodecode_instanceid:
                   ${_('RhodeCode instance id: {}').format(c.rhodecode_instanceid)}
               % endif
           </p>
       </div>
   </div>
</div>

<!-- END FOOTER -->

### MAKO DEFS ###

<%def name="menu_bar_subnav()">
</%def>

<%def name="breadcrumbs(class_='breadcrumbs')">
    <div class="${class_}">
    ${self.breadcrumbs_links()}
    </div>
</%def>

<%def name="admin_menu()">
  <ul class="admin_menu submenu">
      <li><a href="${h.route_path('admin_audit_logs')}">${_('Admin audit logs')}</a></li>
      <li><a href="${h.route_path('repos')}">${_('Repositories')}</a></li>
      <li><a href="${h.route_path('repo_groups')}">${_('Repository groups')}</a></li>
      <li><a href="${h.route_path('users')}">${_('Users')}</a></li>
      <li><a href="${h.route_path('user_groups')}">${_('User groups')}</a></li>
      <li><a href="${h.route_path('admin_permissions_application')}">${_('Permissions')}</a></li>
      <li><a href="${h.route_path('auth_home', traverse='')}">${_('Authentication')}</a></li>
      <li><a href="${h.route_path('global_integrations_home')}">${_('Integrations')}</a></li>
      <li><a href="${h.route_path('admin_defaults_repositories')}">${_('Defaults')}</a></li>
      <li class="last"><a href="${h.route_path('admin_settings')}">${_('Settings')}</a></li>
  </ul>
</%def>


<%def name="dt_info_panel(elements)">
    <dl class="dl-horizontal">
    %for dt, dd, title, show_items in elements:
      <dt>${dt}:</dt>
      <dd title="${h.tooltip(title)}">
      %if callable(dd):
          ## allow lazy evaluation of elements
          ${dd()}
      %else:
          ${dd}
      %endif
      %if show_items:
          <span class="btn-collapse" data-toggle="item-${h.md5_safe(dt)[:6]}-details">${_('Show More')} </span>
      %endif
      </dd>

      %if show_items:
          <div class="collapsable-content" data-toggle="item-${h.md5_safe(dt)[:6]}-details" style="display: none">
          %for item in show_items:
              <dt></dt>
              <dd>${item}</dd>
          %endfor
          </div>
      %endif

    %endfor
    </dl>
</%def>


<%def name="gravatar(email, size=16)">
  <%
    if (size > 16):
        gravatar_class = 'gravatar gravatar-large'
    else:
        gravatar_class = 'gravatar'
  %>
  <%doc>
    TODO: johbo: For now we serve double size images to make it smooth
    for retina. This is how it worked until now. Should be replaced
    with a better solution at some point.
  </%doc>
  <img class="${gravatar_class}" src="${h.gravatar_url(email, size * 2)}" height="${size}" width="${size}">
</%def>


<%def name="gravatar_with_user(contact, size=16, show_disabled=False)">
  <% email = h.email_or_none(contact) %>
  <div class="rc-user tooltip" title="${h.tooltip(h.author_string(email))}">
    ${self.gravatar(email, size)}
    <span class="${'user user-disabled' if show_disabled else 'user'}"> ${h.link_to_user(contact)}</span>
  </div>
</%def>


## admin menu used for people that have some admin resources
<%def name="admin_menu_simple(repositories=None, repository_groups=None, user_groups=None)">
  <ul class="submenu">
   %if repositories:
      <li class="local-admin-repos"><a href="${h.route_path('repos')}">${_('Repositories')}</a></li>
   %endif
   %if repository_groups:
      <li class="local-admin-repo-groups"><a href="${h.route_path('repo_groups')}">${_('Repository groups')}</a></li>
   %endif
   %if user_groups:
      <li class="local-admin-user-groups"><a href="${h.route_path('user_groups')}">${_('User groups')}</a></li>
   %endif
  </ul>
</%def>

<%def name="repo_page_title(repo_instance)">
<div class="title-content">
    <div class="title-main">
        ## SVN/HG/GIT icons
        %if h.is_hg(repo_instance):
            <i class="icon-hg"></i>
        %endif
        %if h.is_git(repo_instance):
            <i class="icon-git"></i>
        %endif
        %if h.is_svn(repo_instance):
            <i class="icon-svn"></i>
        %endif

        ## public/private
        %if repo_instance.private:
            <i class="icon-repo-private"></i>
        %else:
            <i class="icon-repo-public"></i>
        %endif

        ## repo name with group name
        ${h.breadcrumb_repo_link(c.rhodecode_db_repo)}

    </div>

    ## FORKED
    %if repo_instance.fork:
    <p>
        <i class="icon-code-fork"></i> ${_('Fork of')}
        ${h.link_to_if(c.has_origin_repo_read_perm,repo_instance.fork.repo_name, h.route_path('repo_summary', repo_name=repo_instance.fork.repo_name))}
    </p>
    %endif

    ## IMPORTED FROM REMOTE
    %if repo_instance.clone_uri:
    <p>
       <i class="icon-code-fork"></i> ${_('Clone from')}
       <a href="${h.safe_str(h.hide_credentials(repo_instance.clone_uri))}">${h.hide_credentials(repo_instance.clone_uri)}</a>
    </p>
    %endif

    ## LOCKING STATUS
     %if repo_instance.locked[0]:
       <p class="locking_locked">
           <i class="icon-repo-lock"></i>
           ${_('Repository locked by %(user)s') % {'user': h.person_by_id(repo_instance.locked[0])}}
       </p>
     %elif repo_instance.enable_locking:
         <p class="locking_unlocked">
             <i class="icon-repo-unlock"></i>
             ${_('Repository not locked. Pull repository to lock it.')}
         </p>
     %endif

</div>
</%def>

<%def name="repo_menu(active=None)">
    <%
    def is_active(selected):
        if selected == active:
            return "active"
    %>

  <!--- CONTEXT BAR -->
  <div id="context-bar">
    <div class="wrapper">
      <ul id="context-pages" class="navigation horizontal-list">
        <li class="${is_active('summary')}"><a class="menulink" href="${h.route_path('repo_summary', repo_name=c.repo_name)}"><div class="menulabel">${_('Summary')}</div></a></li>
        <li class="${is_active('changelog')}"><a class="menulink" href="${h.route_path('repo_changelog', repo_name=c.repo_name)}"><div class="menulabel">${_('Changelog')}</div></a></li>
        <li class="${is_active('files')}"><a class="menulink" href="${h.route_path('repo_files', repo_name=c.repo_name, commit_id=c.rhodecode_db_repo.landing_rev[1], f_path='')}"><div class="menulabel">${_('Files')}</div></a></li>
        <li class="${is_active('compare')}"><a class="menulink" href="${h.route_path('repo_compare_select',repo_name=c.repo_name)}"><div class="menulabel">${_('Compare')}</div></a></li>
        ## TODO: anderson: ideally it would have a function on the scm_instance "enable_pullrequest() and enable_fork()"
        %if c.rhodecode_db_repo.repo_type in ['git','hg']:
          <li class="${is_active('showpullrequest')}">
            <a class="menulink" href="${h.route_path('pullrequest_show_all', repo_name=c.repo_name)}" title="${h.tooltip(_('Show Pull Requests for %s') % c.repo_name)}">
              %if c.repository_pull_requests:
                <span class="pr_notifications">${c.repository_pull_requests}</span>
              %endif
              <div class="menulabel">${_('Pull Requests')}</div>
            </a>
          </li>
        %endif
        <li class="${is_active('options')}">
          <a class="menulink dropdown">
              <div class="menulabel">${_('Options')} <div class="show_more"></div></div>
          </a>
          <ul class="submenu">
             %if h.HasRepoPermissionAll('repository.admin')(c.repo_name):
                   <li><a href="${h.route_path('edit_repo',repo_name=c.repo_name)}">${_('Settings')}</a></li>
             %endif
              %if c.rhodecode_db_repo.fork:
               <li>
                   <a title="${h.tooltip(_('Compare fork with %s' % c.rhodecode_db_repo.fork.repo_name))}"
                      href="${h.route_path('repo_compare',
                            repo_name=c.rhodecode_db_repo.fork.repo_name,
                            source_ref_type=c.rhodecode_db_repo.landing_rev[0],
                            source_ref=c.rhodecode_db_repo.landing_rev[1],
                            target_repo=c.repo_name,target_ref_type='branch' if request.GET.get('branch') else c.rhodecode_db_repo.landing_rev[0],
                            target_ref=request.GET.get('branch') or c.rhodecode_db_repo.landing_rev[1],
                            _query=dict(merge=1))}"
                    >
                   ${_('Compare fork')}
                   </a>
               </li>
              %endif

              <li><a href="${h.route_path('search_repo',repo_name=c.repo_name)}">${_('Search')}</a></li>

              %if h.HasRepoPermissionAny('repository.write','repository.admin')(c.repo_name) and c.rhodecode_db_repo.enable_locking:
                %if c.rhodecode_db_repo.locked[0]:
                  <li><a class="locking_del" href="${h.route_path('repo_edit_toggle_locking',repo_name=c.repo_name)}">${_('Unlock')}</a></li>
                %else:
                  <li><a class="locking_add" href="${h.route_path('repo_edit_toggle_locking',repo_name=c.repo_name)}">${_('Lock')}</a></li>
                %endif
              %endif
              %if c.rhodecode_user.username != h.DEFAULT_USER:
                %if c.rhodecode_db_repo.repo_type in ['git','hg']:
                  <li><a href="${h.route_path('repo_fork_new',repo_name=c.repo_name)}">${_('Fork')}</a></li>
                  <li><a href="${h.route_path('pullrequest_new',repo_name=c.repo_name)}">${_('Create Pull Request')}</a></li>
                %endif
              %endif
             </ul>
        </li>
      </ul>
    </div>
    <div class="clear"></div>
  </div>
    % if c.rhodecode_db_repo.archived:
    <div class="alert alert-warning text-center">
        <strong>${_('This repository has been archived. It is now read-only.')}</strong>
    </div>
    % endif
  <!--- END CONTEXT BAR -->

</%def>

<%def name="usermenu(active=False)">
    ## USER MENU
    <li id="quick_login_li" class="${'active' if active else ''}">
        % if c.rhodecode_user.username == h.DEFAULT_USER:
          <a id="quick_login_link" class="menulink childs" href="${h.route_path('login', _query={'came_from': h.current_route_path(request)})}">
            ${gravatar(c.rhodecode_user.email, 20)}
            <span class="user">
                <span>${_('Sign in')}</span>
            </span>
          </a>
        % else:
          ## logged in user
          <a id="quick_login_link" class="menulink childs">
            ${gravatar(c.rhodecode_user.email, 20)}
            <span class="user">
                <span class="menu_link_user">${c.rhodecode_user.username}</span>
                <div class="show_more"></div>
            </span>
          </a>
          ## subnav with menu for logged in user
          <div class="user-menu submenu">
              <div id="quick_login">
                %if c.rhodecode_user.username != h.DEFAULT_USER:
                    <div class="">
                        <div class="big_gravatar">${gravatar(c.rhodecode_user.email, 48)}</div>
                        <div class="full_name">${c.rhodecode_user.full_name_or_username}</div>
                        <div class="email">${c.rhodecode_user.email}</div>
                    </div>
                    <div class="">
                    <ol class="links">
                      <li>${h.link_to(_(u'My account'),h.route_path('my_account_profile'))}</li>
                      % if c.rhodecode_user.personal_repo_group:
                      <li>${h.link_to(_(u'My personal group'), h.route_path('repo_group_home', repo_group_name=c.rhodecode_user.personal_repo_group.group_name))}</li>
                      % endif
                      <li>${h.link_to(_(u'Pull Requests'), h.route_path('my_account_pullrequests'))}</li>
                      ## bookmark-items
                      <li class="bookmark-items">
                          ${_('Bookmarks')}
                          <div class="pull-right">
                              <a href="${h.route_path('my_account_bookmarks')}">${_('Manage')}</a>
                          </div>
                      </li>
                      % if not c.bookmark_items:
                          <li>
                              <a href="${h.route_path('my_account_bookmarks')}">${_('No Bookmarks yet.')}</a>
                          </li>
                      % endif
                      % for item in c.bookmark_items:
                      <li>
                          % if item.repository:
                              <div>
                                <a class="bookmark-item" href="${h.route_path('my_account_goto_bookmark', bookmark_id=item.position)}">
                                <code>${item.position}</code>
                                % if item.repository.repo_type == 'hg':
                                    <i class="icon-hg" title="${_('Repository')}" style="font-size: 16px"></i>
                                % elif item.repository.repo_type == 'git':
                                    <i class="icon-git" title="${_('Repository')}" style="font-size: 16px"></i>
                                % elif item.repository.repo_type == 'svn':
                                    <i class="icon-svn" title="${_('Repository')}" style="font-size: 16px"></i>
                                % endif
                                ${(item.title or h.shorter(item.repository.repo_name, 30))}
                              </a>
                              </div>
                          % elif item.repository_group:
                              <div>
                                <a class="bookmark-item" href="${h.route_path('my_account_goto_bookmark', bookmark_id=item.position)}">
                                <code>${item.position}</code>
                                <i class="icon-folder-close" title="${_('Repository group')}" style="font-size: 16px"></i>
                                ${(item.title or h.shorter(item.repository_group.group_name, 30))}
                              </a>
                              </div>
                          % else:
                              <a class="bookmark-item" href="${h.route_path('my_account_goto_bookmark', bookmark_id=item.position)}">
                                <code>${item.position}</code>
                                ${item.title}
                              </a>
                          % endif
                      </li>
                      % endfor

                      <li class="logout">
                      ${h.secure_form(h.route_path('logout'), request=request)}
                          ${h.submit('log_out', _(u'Sign Out'),class_="btn btn-primary")}
                      ${h.end_form()}
                      </li>
                    </ol>
                    </div>
                %endif
              </div>
          </div>
          ## unread counter
          <div class="pill_container">
            <a class="menu_link_notifications ${'empty' if c.unread_notifications == 0 else ''}" href="${h.route_path('notifications_show_all')}">${c.unread_notifications}</a>
          </div>
        % endif
    </li>
</%def>

<%def name="menu_items(active=None)">
    <%
    def is_active(selected):
        if selected == active:
            return "active"
        return ""
    %>

    <ul id="quick" class="main_nav navigation horizontal-list">
       ## notice box for important system messages
       <li style="display: none">
          <a class="notice-box" href="#openNotice" onclick="showNoticeBox(); return false">
            <div class="menulabel-notice" >
                0
            </div>
          </a>
       </li>

        ## Main filter
       <li>
        <div class="menulabel main_filter_box">
            <div class="main_filter_input_box">
                <input class="main_filter_input" id="main_filter" size="15" type="text" name="main_filter" placeholder="${_('search / go to...')}" value=""/>
            </div>
            <div class="main_filter_help_box">
                <a href="#showFilterHelp" onclick="showMainFilterBox(); return false">?</a>
            </div>
        </div>

        <div id="main_filter_help" style="display: none">
Use '/' key to quickly access this field.
Enter name of repository, or repository group for quick search.

Prefix query to allow special search:

user:admin, to search for usernames

user_group:devops, to search for user groups

commit:efced4, to search for commits

        </div>
       </li>

      ## ROOT MENU
      %if c.rhodecode_user.username != h.DEFAULT_USER:
        <li class="${is_active('journal')}">
          <a class="menulink" title="${_('Show activity journal')}" href="${h.route_path('journal')}">
            <div class="menulabel">${_('Journal')}</div>
          </a>
        </li>
      %else:
        <li class="${is_active('journal')}">
          <a class="menulink" title="${_('Show Public activity journal')}" href="${h.route_path('journal_public')}">
            <div class="menulabel">${_('Public journal')}</div>
          </a>
        </li>
      %endif
        <li class="${is_active('gists')}">
          <a class="menulink childs" title="${_('Show Gists')}" href="${h.route_path('gists_show')}">
            <div class="menulabel">${_('Gists')}</div>
          </a>
        </li>
      <li class="${is_active('search')}">
          <a class="menulink" title="${_('Search in repositories you have access to')}" href="${h.route_path('search')}">
            <div class="menulabel">${_('Search')}</div>
          </a>
      </li>
      % if h.HasPermissionAll('hg.admin')('access admin main page'):
        <li class="${is_active('admin')}">
          <a class="menulink childs" title="${_('Admin settings')}" href="#" onclick="return false;">
            <div class="menulabel">${_('Admin')} <div class="show_more"></div></div>
          </a>
          ${admin_menu()}
        </li>
      % elif c.rhodecode_user.repositories_admin or c.rhodecode_user.repository_groups_admin or c.rhodecode_user.user_groups_admin:
      <li class="${is_active('admin')}">
          <a class="menulink childs" title="${_('Delegated Admin settings')}">
            <div class="menulabel">${_('Admin')} <div class="show_more"></div></div>
          </a>
          ${admin_menu_simple(c.rhodecode_user.repositories_admin,
                              c.rhodecode_user.repository_groups_admin,
                              c.rhodecode_user.user_groups_admin or h.HasPermissionAny('hg.usergroup.create.true')())}
      </li>
      % endif
      ## render extra user menu
      ${usermenu(active=(active=='my_account'))}

      % if c.debug_style:
      <li>
          <a class="menulink" title="${_('Style')}" href="${h.route_path('debug_style_home')}">
            <div class="menulabel">${_('[Style]')}</div>
          </a>
      </li>
      % endif
    </ul>

    <script type="text/javascript">
        var visualShowPublicIcon = "${c.visual.show_public_icon}" == "True";

        var formatRepoResult = function(result, container, query, escapeMarkup) {
            return function(data, escapeMarkup) {
                if (!data.repo_id){
                  return data.text; // optgroup text Repositories
                }

                var tmpl = '';
                var repoType = data['repo_type'];
                var repoName = data['text'];

                if(data && data.type == 'repo'){
                    if(repoType === 'hg'){
                        tmpl += '<i class="icon-hg"></i> ';
                    }
                    else if(repoType === 'git'){
                        tmpl += '<i class="icon-git"></i> ';
                    }
                    else if(repoType === 'svn'){
                        tmpl += '<i class="icon-svn"></i> ';
                    }
                    if(data['private']){
                        tmpl += '<i class="icon-lock" ></i> ';
                    }
                    else if(visualShowPublicIcon){
                        tmpl += '<i class="icon-unlock-alt"></i> ';
                    }
                }
                tmpl += escapeMarkup(repoName);
                return tmpl;

            }(result, escapeMarkup);
        };

        var formatRepoGroupResult = function(result, container, query, escapeMarkup) {
            return function(data, escapeMarkup) {
                if (!data.repo_group_id){
                  return data.text; // optgroup text Repositories
                }

                var tmpl = '';
                var repoGroupName = data['text'];

                if(data){

                    tmpl += '<i class="icon-folder-close"></i> ';

                }
                tmpl += escapeMarkup(repoGroupName);
                return tmpl;

            }(result, escapeMarkup);
        };


        var autocompleteMainFilterFormatResult = function (data, value, org_formatter) {

            if (value.split(':').length === 2) {
                value = value.split(':')[1]
            }

            var searchType = data['type'];
            var valueDisplay = data['value_display'];

            var escapeRegExChars = function (value) {
            return value.replace(/[\-\[\]\/\{\}\(\)\*\+\?\.\\\^\$\|]/g, "\\$&");
            };
            var pattern = '(' + escapeRegExChars(value) + ')';

            // highlight match
            valueDisplay = Select2.util.escapeMarkup(valueDisplay);
            valueDisplay = valueDisplay.replace(new RegExp(pattern, 'gi'), '<strong>$1<\/strong>');

            var icon = '';

            if (searchType === 'hint') {
                icon += '<i class="icon-folder-close"></i> ';
            }
            else if (searchType === 'search') {
                icon += '<i class="icon-more"></i> ';
            }
            else if (searchType === 'repo') {
                if (data['repo_type'] === 'hg') {
                    icon += '<i class="icon-hg"></i> ';
                }
                else if (data['repo_type'] === 'git') {
                    icon += '<i class="icon-git"></i> ';
                }
                else if (data['repo_type'] === 'svn') {
                    icon += '<i class="icon-svn"></i> ';
                }
                if (data['private']) {
                    icon += '<i class="icon-lock" ></i> ';
                }
                else if (visualShowPublicIcon) {
                    icon += '<i class="icon-unlock-alt"></i> ';
                }
            }
            else if (searchType === 'repo_group') {
                icon += '<i class="icon-folder-close"></i> ';
            }
            else if (searchType === 'user_group') {
                icon += '<i class="icon-group"></i> ';
            }
            else if (searchType === 'user') {
                icon += '<img class="gravatar" src="{0}"/>'.format(data['icon_link']);
            }
            else if (searchType === 'commit') {
                icon += '<i class="icon-tag"></i>';
            }

            var tmpl = '<div class="ac-container-wrap">{0}{1}</div>';
            return tmpl.format(icon, valueDisplay);
        };

        var handleSelect = function(element, suggestion) {
            if (suggestion.type === "hint") {
                // we skip action
                $('#main_filter').focus();
            } else {
              window.location = suggestion['url'];
            }
        };
        var autocompleteMainFilterResult = function (suggestion, originalQuery, queryLowerCase) {
            if (queryLowerCase.split(':').length === 2) {
                queryLowerCase = queryLowerCase.split(':')[1]
            }
            return suggestion.value_display.toLowerCase().indexOf(queryLowerCase) !== -1;
        };

        $('#main_filter').autocomplete({
            serviceUrl: pyroutes.url('goto_switcher_data'),
            params: {"search_context": templateContext.search_context},
            minChars:2,
            maxHeight:400,
            deferRequestBy: 300, //miliseconds
            tabDisabled: true,
            autoSelectFirst: true,
            formatResult: autocompleteMainFilterFormatResult,
            lookupFilter: autocompleteMainFilterResult,
            onSelect: function (element, suggestion) {
                handleSelect(element, suggestion);
                return false;
            },
            onSearchError: function (element, query, jqXHR, textStatus, errorThrown) {
                if (jqXHR !== 'abort') {
                    alert("Error during search.\nError code: {0}".format(textStatus));
                    window.location = '';
                }
            }
        });

        showMainFilterBox = function () {
            $('#main_filter_help').toggle();
        }

    </script>
    <script src="${h.asset('js/rhodecode/base/keyboard-bindings.js', ver=c.rhodecode_version_hash)}"></script>
</%def>

<div class="modal" id="help_kb" tabindex="-1" role="dialog" aria-labelledby="myModalLabel" aria-hidden="true">
    <div class="modal-dialog">
      <div class="modal-content">
        <div class="modal-header">
          <button type="button" class="close" data-dismiss="modal" aria-hidden="true">&times;</button>
          <h4 class="modal-title" id="myModalLabel">${_('Keyboard shortcuts')}</h4>
        </div>
        <div class="modal-body">
              <div class="block-left">
                <table class="keyboard-mappings">
                    <tbody>
                  <tr>
                    <th></th>
                    <th>${_('Site-wide shortcuts')}</th>
                  </tr>
                  <%
                     elems = [
                         ('/', 'Use quick search box'),
                         ('g h', 'Goto home page'),
                         ('g g', 'Goto my private gists page'),
                         ('g G', 'Goto my public gists page'),
                         ('g 0-9', 'Goto bookmarked items from 0-9'),
                         ('n r', 'New repository page'),
                         ('n g', 'New gist page'),
                     ]
                  %>
                  %for key, desc in elems:
                  <tr>
                    <td class="keys">
                      <span class="key tag">${key}</span>
                    </td>
                    <td>${desc}</td>
                  </tr>
                %endfor
                </tbody>
                  </table>
              </div>
              <div class="block-left">
                <table class="keyboard-mappings">
                <tbody>
                  <tr>
                    <th></th>
                    <th>${_('Repositories')}</th>
                  </tr>
                  <%
                     elems = [
                         ('g s', 'Goto summary page'),
                         ('g c', 'Goto changelog page'),
                         ('g f', 'Goto files page'),
                         ('g F', 'Goto files page with file search activated'),
                         ('g p', 'Goto pull requests page'),
                         ('g o', 'Goto repository settings'),
                         ('g O', 'Goto repository permissions settings'),
                     ]
                  %>
                  %for key, desc in elems:
                  <tr>
                    <td class="keys">
                      <span class="key tag">${key}</span>
                    </td>
                    <td>${desc}</td>
                  </tr>
                %endfor
                </tbody>
              </table>
            </div>
        </div>
        <div class="modal-footer">
        </div>
      </div><!-- /.modal-content -->
    </div><!-- /.modal-dialog -->
</div><!-- /.modal -->

