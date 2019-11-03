## -*- coding: utf-8 -*-

## base64 filter
<%!
    def base64(text):
        import base64
        from rhodecode.lib.helpers import safe_str
        return base64.encodestring(safe_str(text))
%>

<%inherit file="root.mako"/>

<%include file="/ejs_templates/templates.html"/>

<div class="outerwrapper">
  <!-- HEADER -->
  <div class="header">
      <div id="header-inner" class="wrapper">
          <div id="logo">
              <div class="logo-wrapper">
                  <a href="${h.route_path('home')}"><img src="${h.asset('images/rhodecode-logo-white-60x60.png')}" alt="RhodeCode"/></a>
              </div>
              % if c.rhodecode_name:
               <div class="branding">
                   <a href="${h.route_path('home')}">${h.branding(c.rhodecode_name)}</a>
               </div>
              % endif
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

<%def name="admin_menu(active=None)">
  <%
    def is_active(selected):
        if selected == active:
            return "active"
  %>

  <div id="context-bar">
    <div class="wrapper">
      <div class="title">
        <div class="title-content">
          <div class="title-main">
            % if c.is_super_admin:
                ${_('Super Admin Panel')}
            % else:
                ${_('Delegated Admin Panel')}
            % endif
          </div>
        </div>
      </div>

    <ul id="context-pages" class="navigation horizontal-list">

        ## super admin case
        % if c.is_super_admin:
          <li class="${is_active('audit_logs')}"><a href="${h.route_path('admin_audit_logs')}">${_('Admin audit logs')}</a></li>
          <li class="${is_active('repositories')}"><a href="${h.route_path('repos')}">${_('Repositories')}</a></li>
          <li class="${is_active('repository_groups')}"><a href="${h.route_path('repo_groups')}">${_('Repository groups')}</a></li>
          <li class="${is_active('users')}"><a href="${h.route_path('users')}">${_('Users')}</a></li>
          <li class="${is_active('user_groups')}"><a href="${h.route_path('user_groups')}">${_('User groups')}</a></li>
          <li class="${is_active('permissions')}"><a href="${h.route_path('admin_permissions_application')}">${_('Permissions')}</a></li>
          <li class="${is_active('authentication')}"><a href="${h.route_path('auth_home', traverse='')}">${_('Authentication')}</a></li>
          <li class="${is_active('integrations')}"><a href="${h.route_path('global_integrations_home')}">${_('Integrations')}</a></li>
          <li class="${is_active('defaults')}"><a href="${h.route_path('admin_defaults_repositories')}">${_('Defaults')}</a></li>
          <li class="${is_active('settings')}"><a href="${h.route_path('admin_settings')}">${_('Settings')}</a></li>

        ## delegated admin
        % elif c.is_delegated_admin:
           <%
           repositories=c.auth_user.repositories_admin or c.can_create_repo
           repository_groups=c.auth_user.repository_groups_admin or c.can_create_repo_group
           user_groups=c.auth_user.user_groups_admin or c.can_create_user_group
           %>

           %if repositories:
              <li class="${is_active('repositories')} local-admin-repos"><a href="${h.route_path('repos')}">${_('Repositories')}</a></li>
           %endif
           %if repository_groups:
              <li class="${is_active('repository_groups')} local-admin-repo-groups"><a href="${h.route_path('repo_groups')}">${_('Repository groups')}</a></li>
           %endif
           %if user_groups:
              <li class="${is_active('user_groups')} local-admin-user-groups"><a href="${h.route_path('user_groups')}">${_('User groups')}</a></li>
           %endif
        % endif
    </ul>

    </div>
    <div class="clear"></div>
  </div>
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

<%def name="tr_info_entry(element)">
    <% key, val, title, show_items = element %>

    <tr>
        <td style="vertical-align: top">${key}</td>
        <td title="${h.tooltip(title)}">
          %if callable(val):
              ## allow lazy evaluation of elements
              ${val()}
          %else:
              ${val}
          %endif
          %if show_items:
              <div class="collapsable-content" data-toggle="item-${h.md5_safe(val)[:6]}-details" style="display: none">
              % for item in show_items:
                  <dt></dt>
                  <dd>${item}</dd>
              % endfor
              </div>
          %endif
        </td>
        <td style="vertical-align: top">
          %if show_items:
              <span class="btn-collapse" data-toggle="item-${h.md5_safe(val)[:6]}-details">${_('Show More')} </span>
          %endif
        </td>
    </tr>

</%def>

<%def name="gravatar(email, size=16, tooltip=False, tooltip_alt=None, user=None)">
  <%
    if size > 16:
        gravatar_class = ['gravatar','gravatar-large']
    else:
        gravatar_class = ['gravatar']

    data_hovercard_url = ''
    data_hovercard_alt = tooltip_alt.replace('<', '&lt;').replace('>', '&gt;') if tooltip_alt else ''

    if tooltip:
        gravatar_class += ['tooltip-hovercard']

    if tooltip and user:
        if user.username == h.DEFAULT_USER:
            gravatar_class.pop(-1)
        else:
            data_hovercard_url = request.route_path('hovercard_user', user_id=getattr(user, 'user_id', ''))
    gravatar_class = ' '.join(gravatar_class)

  %>
  <%doc>
    TODO: johbo: For now we serve double size images to make it smooth
    for retina. This is how it worked until now. Should be replaced
    with a better solution at some point.
  </%doc>

  <img class="${gravatar_class}" height="${size}" width="${size}" data-hovercard-url="${data_hovercard_url}" data-hovercard-alt="${data_hovercard_alt}" src="${h.gravatar_url(email, size * 2)}" />
</%def>


<%def name="gravatar_with_user(contact, size=16, show_disabled=False, tooltip=False)">
  <%
      email = h.email_or_none(contact)
      rc_user = h.discover_user(contact)
  %>

  <div class="rc-user">
    ${self.gravatar(email, size, tooltip=tooltip, tooltip_alt=contact, user=rc_user)}
    <span class="${('user user-disabled' if show_disabled else 'user')}"> ${h.link_to_user(rc_user or contact)}</span>
  </div>
</%def>


<%def name="user_group_icon(user_group=None, size=16, tooltip=False)">
  <%
    if (size > 16):
        gravatar_class = 'icon-user-group-alt'
    else:
        gravatar_class = 'icon-user-group-alt'

    if tooltip:
        gravatar_class += ' tooltip-hovercard'

    data_hovercard_url = request.route_path('hovercard_user_group', user_group_id=user_group.users_group_id)
  %>
  <%doc>
    TODO: johbo: For now we serve double size images to make it smooth
    for retina. This is how it worked until now. Should be replaced
    with a better solution at some point.
  </%doc>

  <i style="font-size: ${size}px" class="${gravatar_class} x-icon-size-${size}" data-hovercard-url="${data_hovercard_url}"></i>
</%def>

<%def name="repo_page_title(repo_instance)">
<div class="title-content repo-title">

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
        ${h.breadcrumb_repo_link(repo_instance)}

        ## Context Actions
        <div class="pull-right">
            %if c.rhodecode_user.username != h.DEFAULT_USER:
                <a href="${h.route_path('atom_feed_home', repo_name=c.rhodecode_db_repo.repo_uid, _query=dict(auth_token=c.rhodecode_user.feed_token))}" title="${_('RSS Feed')}" class="btn btn-sm"><i class="icon-rss-sign"></i>RSS</a>

                <a href="#WatchRepo" onclick="toggleFollowingRepo(this, templateContext.repo_id); return false" title="${_('Watch this Repository and actions on it in your personalized journal')}" class="btn btn-sm ${('watching' if c.repository_is_user_following else '')}">
                    % if c.repository_is_user_following:
                        <i class="icon-eye-off"></i>${_('Unwatch')}
                    % else:
                        <i class="icon-eye"></i>${_('Watch')}
                    % endif

                </a>
            %else:
                <a href="${h.route_path('atom_feed_home', repo_name=c.rhodecode_db_repo.repo_uid)}" title="${_('RSS Feed')}" class="btn btn-sm"><i class="icon-rss-sign"></i>RSS</a>
            %endif
        </div>

    </div>

    ## FORKED
    %if repo_instance.fork:
    <p class="discreet">
        <i class="icon-code-fork"></i> ${_('Fork of')}
        ${h.link_to_if(c.has_origin_repo_read_perm,repo_instance.fork.repo_name, h.route_path('repo_summary', repo_name=repo_instance.fork.repo_name))}
    </p>
    %endif

    ## IMPORTED FROM REMOTE
    %if repo_instance.clone_uri:
    <p class="discreet">
       <i class="icon-code-fork"></i> ${_('Clone from')}
       <a href="${h.safe_str(h.hide_credentials(repo_instance.clone_uri))}">${h.hide_credentials(repo_instance.clone_uri)}</a>
    </p>
    %endif

    ## LOCKING STATUS
     %if repo_instance.locked[0]:
       <p class="locking_locked discreet">
           <i class="icon-repo-lock"></i>
           ${_('Repository locked by %(user)s') % {'user': h.person_by_id(repo_instance.locked[0])}}
       </p>
     %elif repo_instance.enable_locking:
         <p class="locking_unlocked discreet">
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
    ## determine if we have "any" option available
    can_lock = h.HasRepoPermissionAny('repository.write','repository.admin')(c.repo_name) and c.rhodecode_db_repo.enable_locking
    has_actions = can_lock

    %>
    % if c.rhodecode_db_repo.archived:
    <div class="alert alert-warning text-center">
        <strong>${_('This repository has been archived. It is now read-only.')}</strong>
    </div>
    % endif

  <!--- REPO CONTEXT BAR -->
  <div id="context-bar">
    <div class="wrapper">

      <div class="title">
          ${self.repo_page_title(c.rhodecode_db_repo)}
      </div>

      <ul id="context-pages" class="navigation horizontal-list">
        <li class="${is_active('summary')}"><a class="menulink" href="${h.route_path('repo_summary', repo_name=c.repo_name)}"><div class="menulabel">${_('Summary')}</div></a></li>
        <li class="${is_active('commits')}"><a class="menulink" href="${h.route_path('repo_commits', repo_name=c.repo_name)}"><div class="menulabel">${_('Commits')}</div></a></li>
        <li class="${is_active('files')}"><a class="menulink" href="${h.route_path('repo_files', repo_name=c.repo_name, commit_id=c.rhodecode_db_repo.landing_rev[1], f_path='')}"><div class="menulabel">${_('Files')}</div></a></li>
        <li class="${is_active('compare')}"><a class="menulink" href="${h.route_path('repo_compare_select',repo_name=c.repo_name)}"><div class="menulabel">${_('Compare')}</div></a></li>

        ## TODO: anderson: ideally it would have a function on the scm_instance "enable_pullrequest() and enable_fork()"
        %if c.rhodecode_db_repo.repo_type in ['git','hg']:
          <li class="${is_active('showpullrequest')}">
            <a class="menulink" href="${h.route_path('pullrequest_show_all', repo_name=c.repo_name)}" title="${h.tooltip(_('Show Pull Requests for %s') % c.repo_name)}">
              <div class="menulabel">
                  ${_('Pull Requests')} <span class="menulink-counter">${c.repository_pull_requests}</span>
              </div>
            </a>
          </li>
        %endif

        <li class="${is_active('artifacts')}">
            <a class="menulink" href="${h.route_path('repo_artifacts_list',repo_name=c.repo_name)}">
                <div class="menulabel">
                    ${_('Artifacts')}  <span class="menulink-counter">${c.repository_artifacts}</span>
                </div>
            </a>
        </li>

        %if h.HasRepoPermissionAll('repository.admin')(c.repo_name):
            <li class="${is_active('settings')}"><a class="menulink" href="${h.route_path('edit_repo',repo_name=c.repo_name)}"><div class="menulabel">${_('Repository Settings')}</div></a></li>
        %endif

        <li class="${is_active('options')}">
          % if has_actions:
            <a class="menulink dropdown">
              <div class="menulabel">${_('Options')}<div class="show_more"></div></div>
            </a>
            <ul class="submenu">
                %if can_lock:
                    %if c.rhodecode_db_repo.locked[0]:
                      <li><a class="locking_del" href="${h.route_path('repo_edit_toggle_locking',repo_name=c.repo_name)}">${_('Unlock Repository')}</a></li>
                    %else:
                      <li><a class="locking_add" href="${h.route_path('repo_edit_toggle_locking',repo_name=c.repo_name)}">${_('Lock Repository')}</a></li>
                    %endif
                %endif
            </ul>
          % else:
            <a class="menulink disabled">
              <div class="menulabel">${_('Options')}<div class="show_more"></div></div>
            </a>
          % endif
        </li>

      </ul>
    </div>
    <div class="clear"></div>
  </div>

  <!--- REPO END CONTEXT BAR -->

</%def>

<%def name="repo_group_page_title(repo_group_instance)">
<div class="title-content">
    <div class="title-main">
        ## Repository Group icon
        <i class="icon-repo-group"></i>

        ## repo name with group name
        ${h.breadcrumb_repo_group_link(repo_group_instance)}
    </div>

    <%namespace name="dt" file="/data_table/_dt_elements.mako"/>
    <div class="repo-group-desc discreet">
    ${dt.repo_group_desc(repo_group_instance.description_safe, repo_group_instance.personal, c.visual.stylify_metatags)}
    </div>

</div>
</%def>


<%def name="repo_group_menu(active=None)">
    <%
    def is_active(selected):
        if selected == active:
            return "active"

    gr_name = c.repo_group.group_name if c.repo_group else None
    # create repositories with write permission on group is set to true
    group_admin = h.HasRepoGroupPermissionAny('group.admin')(gr_name, 'group admin index page')

    %>


  <!--- REPO GROUP CONTEXT BAR -->
  <div id="context-bar">
    <div class="wrapper">
      <div class="title">
          ${self.repo_group_page_title(c.repo_group)}
      </div>

      <ul id="context-pages" class="navigation horizontal-list">
        <li class="${is_active('home')}">
            <a class="menulink" href="${h.route_path('repo_group_home', repo_group_name=c.repo_group.group_name)}"><div class="menulabel">${_('Group Home')}</div></a>
        </li>
        % if c.is_super_admin or group_admin:
            <li class="${is_active('settings')}">
                <a class="menulink" href="${h.route_path('edit_repo_group',repo_group_name=c.repo_group.group_name)}" title="${_('You have admin right to this group, and can edit it')}"><div class="menulabel">${_('Group Settings')}</div></a>
            </li>
        % endif

      </ul>
    </div>
    <div class="clear"></div>
  </div>

  <!--- REPO GROUP CONTEXT BAR -->

</%def>


<%def name="usermenu(active=False)">
    <%
    not_anonymous = c.rhodecode_user.username != h.DEFAULT_USER

    gr_name = c.repo_group.group_name if (hasattr(c, 'repo_group') and c.repo_group) else None
    # create repositories with write permission on group is set to true

    can_fork = c.is_super_admin or h.HasPermissionAny('hg.fork.repository')()
    create_on_write = h.HasPermissionAny('hg.create.write_on_repogroup.true')()
    group_write = h.HasRepoGroupPermissionAny('group.write')(gr_name, 'can write into group index page')
    group_admin = h.HasRepoGroupPermissionAny('group.admin')(gr_name, 'group admin index page')

    can_create_repos = c.is_super_admin or c.can_create_repo
    can_create_repo_groups = c.is_super_admin or c.can_create_repo_group

    can_create_repos_in_group = c.is_super_admin or group_admin or (group_write and create_on_write)
    can_create_repo_groups_in_group = c.is_super_admin or group_admin
    %>

    % if not_anonymous:
    <%
    default_target_group = dict()
    if c.rhodecode_user.personal_repo_group:
        default_target_group = dict(parent_group=c.rhodecode_user.personal_repo_group.group_id)
    %>

    ## create action
    <li>
       <a href="#create-actions" onclick="return false;" class="menulink childs">
        <i class="icon-plus-circled"></i>
       </a>

       <div class="action-menu submenu">

        <ol>
            ## scope of within a repository
            % if hasattr(c, 'rhodecode_db_repo') and c.rhodecode_db_repo:
                <li class="submenu-title">${_('This Repository')}</li>
                <li>
                    <a href="${h.route_path('pullrequest_new',repo_name=c.repo_name)}">${_('Create Pull Request')}</a>
                </li>
                % if can_fork:
                <li>
                    <a href="${h.route_path('repo_fork_new',repo_name=c.repo_name,_query=default_target_group)}">${_('Fork this repository')}</a>
                </li>
                % endif
            % endif

            ## scope of within repository groups
            % if hasattr(c, 'repo_group') and c.repo_group and (can_create_repos_in_group or can_create_repo_groups_in_group):
                <li class="submenu-title">${_('This Repository Group')}</li>

                % if can_create_repos_in_group:
                    <li>
                    <a href="${h.route_path('repo_new',_query=default_target_group)}">${_('New Repository')}</a>
                    </li>
                % endif

                % if can_create_repo_groups_in_group:
                    <li>
                        <a href="${h.route_path('repo_group_new',_query=default_target_group)}">${_(u'New Repository Group')}</a>
                    </li>
                % endif
            % endif

            ## personal group
            % if c.rhodecode_user.personal_repo_group:
                <li class="submenu-title">Personal Group</li>

                <li>
                <a href="${h.route_path('repo_new',_query=dict(parent_group=c.rhodecode_user.personal_repo_group.group_id))}" >${_('New Repository')} </a>
                </li>

                <li>
                <a href="${h.route_path('repo_group_new',_query=dict(parent_group=c.rhodecode_user.personal_repo_group.group_id))}">${_('New Repository Group')} </a>
                </li>
            % endif

            ## Global actions
            <li class="submenu-title">RhodeCode</li>
            % if can_create_repos:
                <li>
                <a href="${h.route_path('repo_new')}" >${_('New Repository')}</a>
                </li>
            % endif

            % if can_create_repo_groups:
                <li>
                <a href="${h.route_path('repo_group_new')}" >${_(u'New Repository Group')}</a>
                </li>
            % endif

            <li>
                <a href="${h.route_path('gists_new')}">${_(u'New Gist')}</a>
            </li>

        </ol>

       </div>
    </li>

    ## notifications
    <li>
       <a class="${('empty' if c.unread_notifications == 0 else '')}" href="${h.route_path('notifications_show_all')}">
           ${c.unread_notifications}
       </a>
    </li>
   % endif

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

                      % if c.debug_style:
                      <li>
                          <a class="menulink" title="${_('Style')}" href="${h.route_path('debug_style_home')}">
                            <div class="menulabel">${_('[Style]')}</div>
                          </a>
                      </li>
                      % endif

                      ## bookmark-items
                      <li class="bookmark-items">
                          ${_('Bookmarks')}
                          <div class="pull-right">
                              <a href="${h.route_path('my_account_bookmarks')}">

                                  <i class="icon-cog"></i>
                              </a>
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
                                <i class="icon-repo-group" title="${_('Repository group')}" style="font-size: 14px"></i>
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
          <a class="notice-box" href="#openNotice" onclick="return false">
            <div class="menulabel-notice" >
                0
            </div>
          </a>
       </li>

        ## Main filter
       <li>
        <div class="menulabel main_filter_box">
            <div class="main_filter_input_box">
                <ul class="searchItems">

                    % if c.template_context['search_context']['repo_id']:
                        <li class="searchTag searchTagFilter searchTagHidable" >
                        ##<a href="${h.route_path('search_repo',repo_name=c.template_context['search_context']['repo_name'])}">
                            <span class="tag">
                                This repo
                                <a href="#removeGoToFilter" onclick="removeGoToFilter(); return false"><i class="icon-cancel-circled"></i></a>
                            </span>
                        ##</a>
                        </li>
                    % elif c.template_context['search_context']['repo_group_id']:
                        <li class="searchTag searchTagFilter searchTagHidable">
                        ##<a href="${h.route_path('search_repo_group',repo_group_name=c.template_context['search_context']['repo_group_name'])}">
                            <span class="tag">
                                This group
                                <a href="#removeGoToFilter" onclick="removeGoToFilter(); return false"><i class="icon-cancel-circled"></i></a>
                            </span>
                        ##</a>
                        </li>
                    % endif

                    <li class="searchTagInput">
                        <input class="main_filter_input" id="main_filter" size="25" type="text" name="main_filter" placeholder="${_('search / go to...')}" value="" />
                    </li>
                    <li class="searchTag searchTagHelp">
                        <a href="#showFilterHelp" onclick="showMainFilterBox(); return false">?</a>
                    </li>
                </ul>
            </div>
        </div>

        <div id="main_filter_help" style="display: none">
- Use '/' key to quickly access this field.

- Enter a name of repository, or repository group for quick search.

- Prefix query to allow special search:

   user:admin, to search for usernames, always global

   user_group:devops, to search for user groups, always global

   commit:efced4, to search for commits, scoped to repositories or groups

   file:models.py, to search for file paths, scoped to repositories or groups

% if c.template_context['search_context']['repo_id']:
   For advanced full text search visit: <a href="${h.route_path('search_repo',repo_name=c.template_context['search_context']['repo_name'])}">repository search</a>
% elif c.template_context['search_context']['repo_group_id']:
   For advanced full text search visit: <a href="${h.route_path('search_repo_group',repo_group_name=c.template_context['search_context']['repo_group_name'])}">repository group search</a>
% else:
   For advanced full text search visit: <a href="${h.route_path('search')}">global search</a>
% endif
        </div>
       </li>

      ## ROOT MENU
        <li class="${is_active('home')}">
          <a class="menulink" title="${_('Home')}" href="${h.route_path('home')}">
            <div class="menulabel">${_('Home')}</div>
          </a>
        </li>

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

        % if c.is_super_admin or c.is_delegated_admin:
        <li class="${is_active('admin')}">
          <a class="menulink childs" title="${_('Admin settings')}" href="${h.route_path('admin_home')}">
            <div class="menulabel">${_('Admin')} </div>
          </a>
        </li>
        % endif

      ## render extra user menu
      ${usermenu(active=(active=='my_account'))}

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

                    tmpl += '<i class="icon-repo-group"></i> ';

                }
                tmpl += escapeMarkup(repoGroupName);
                return tmpl;

            }(result, escapeMarkup);
        };

        var escapeRegExChars = function (value) {
            return value.replace(/[\-\[\]\/\{\}\(\)\*\+\?\.\\\^\$\|]/g, "\\$&");
        };

        var getRepoIcon = function(repo_type) {
            if (repo_type === 'hg') {
                return '<i class="icon-hg"></i> ';
            }
            else if (repo_type === 'git') {
                return '<i class="icon-git"></i> ';
            }
            else if (repo_type === 'svn') {
                return '<i class="icon-svn"></i> ';
            }
            return ''
        };

        var autocompleteMainFilterFormatResult = function (data, value, org_formatter) {

            if (value.split(':').length === 2) {
                value = value.split(':')[1]
            }

            var searchType = data['type'];
            var searchSubType = data['subtype'];
            var valueDisplay = data['value_display'];

            var pattern = '(' + escapeRegExChars(value) + ')';

            valueDisplay = Select2.util.escapeMarkup(valueDisplay);

            // highlight match
            if (searchType != 'text') {
                valueDisplay = valueDisplay.replace(new RegExp(pattern, 'gi'), '<strong>$1<\/strong>');
            }

            var icon = '';

            if (searchType === 'hint') {
                icon += '<i class="icon-repo-group"></i> ';
            }
            // full text search/hints
            else if (searchType === 'search') {
                icon += '<i class="icon-more"></i> ';
                if (searchSubType !== undefined && searchSubType == 'repo') {
                    valueDisplay += '<div class="pull-right tag">repository</div>';
                }
                else if (searchSubType !== undefined && searchSubType == 'repo_group') {
                    valueDisplay += '<div class="pull-right tag">repo group</div>';
                }
            }
            // repository
            else if (searchType === 'repo') {

                var repoIcon = getRepoIcon(data['repo_type']);
                icon += repoIcon;

                if (data['private']) {
                    icon += '<i class="icon-lock" ></i> ';
                }
                else if (visualShowPublicIcon) {
                    icon += '<i class="icon-unlock-alt"></i> ';
                }
            }
            // repository groups
            else if (searchType === 'repo_group') {
                icon += '<i class="icon-repo-group"></i> ';
            }
            // user group
            else if (searchType === 'user_group') {
                icon += '<i class="icon-group"></i> ';
            }
            // user
            else if (searchType === 'user') {
                icon += '<img class="gravatar" src="{0}"/>'.format(data['icon_link']);
            }
            // commit
            else if (searchType === 'commit') {
                var repo_data = data['repo_data'];
                var repoIcon = getRepoIcon(repo_data['repository_type']);
                if (repoIcon) {
                    icon += repoIcon;
                } else {
                    icon += '<i class="icon-tag"></i>';
                }
            }
            // file
            else if (searchType === 'file') {
                var repo_data = data['repo_data'];
                var repoIcon = getRepoIcon(repo_data['repository_type']);
                if (repoIcon) {
                    icon += repoIcon;
                } else {
                    icon += '<i class="icon-tag"></i>';
                }
            }
            // generic text
            else if (searchType === 'text') {
                icon = '';
            }

            var tmpl = '<div class="ac-container-wrap">{0}{1}</div>';
            return tmpl.format(icon, valueDisplay);
        };

        var handleSelect = function(element, suggestion) {
            if (suggestion.type === "hint") {
                // we skip action
                $('#main_filter').focus();
            }
            else if (suggestion.type === "text") {
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
            if (suggestion.type === "text") {
                // special case we don't want to "skip" display for
                return true
            }
            return suggestion.value_display.toLowerCase().indexOf(queryLowerCase) !== -1;
        };

        var cleanContext = {
            repo_view_type: null,

            repo_id: null,
            repo_name: "",

            repo_group_id: null,
            repo_group_name: null
        };
        var removeGoToFilter = function () {
            $('.searchTagHidable').hide();
            $('#main_filter').autocomplete(
                'setOptions', {params:{search_context: cleanContext}});
        };

        $('#main_filter').autocomplete({
            serviceUrl: pyroutes.url('goto_switcher_data'),
            params: {
                "search_context": templateContext.search_context
            },
            minChars:2,
            maxHeight:400,
            deferRequestBy: 300, //miliseconds
            tabDisabled: true,
            autoSelectFirst: false,
            containerClass: 'autocomplete-qfilter-suggestions',
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
        };

        $('#main_filter').on('keydown.autocomplete', function (e) {

            var BACKSPACE = 8;
            var el = $(e.currentTarget);
            if(e.which === BACKSPACE){
                var inputVal = el.val();
                if (inputVal === ""){
                    removeGoToFilter()
                }
            }
        });

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
                         ('g O', 'Goto repository access permissions settings'),
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
