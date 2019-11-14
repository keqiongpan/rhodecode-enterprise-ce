## -*- coding: utf-8 -*-
##
## See also repo_settings.html
##
<%inherit file="/base/base.mako"/>

<%def name="title()">
    ${_('{} repository settings').format(c.rhodecode_db_repo.repo_name)}
    %if c.rhodecode_name:
        &middot; ${h.branding(c.rhodecode_name)}
    %endif
</%def>

<%def name="breadcrumbs_links()">
    ${_('Settings')}
</%def>

<%def name="menu_bar_nav()">
    ${self.menu_items(active='repositories')}
</%def>

<%def name="menu_bar_subnav()">
    ${self.repo_menu(active='settings')}
</%def>

<%def name="main_content()">
  % if hasattr(c, 'repo_edit_template'):
    <%include file="${c.repo_edit_template}"/>
  % else:
    <%include file="/admin/repos/repo_edit_${c.active}.mako"/>
  % endif
</%def>


<%def name="main()">
<div class="box">

  <div class="sidebar-col-wrapper scw-small">
    <div class="sidebar">
        <ul class="nav nav-pills nav-stacked">
          <li class="${h.is_active('settings', c.active)}">
              <a href="${h.route_path('edit_repo', repo_name=c.repo_name)}">${_('Settings')}</a>
          </li>
          <li class="${h.is_active('permissions', c.active)}">
              <a href="${h.route_path('edit_repo_perms', repo_name=c.repo_name)}">${_('Access Permissions')}</a>
          </li>
          <li class="${h.is_active('permissions_branch', c.active)}">
              <a href="${h.route_path('edit_repo_perms_branch', repo_name=c.repo_name)}">${_('Branch Permissions')}</a>
          </li>
          <li class="${h.is_active('advanced', c.active)}">
              <a href="${h.route_path('edit_repo_advanced', repo_name=c.repo_name)}">${_('Advanced')}</a>
          </li>
          <li class="${h.is_active('vcs', c.active)}">
              <a href="${h.route_path('edit_repo_vcs', repo_name=c.repo_name)}">${_('VCS')}</a>
          </li>
          <li class="${h.is_active('fields', c.active)}">
              <a href="${h.route_path('edit_repo_fields', repo_name=c.repo_name)}">${_('Extra Fields')}</a>
          </li>
          <li class="${h.is_active('issuetracker', c.active)}">
              <a href="${h.route_path('edit_repo_issuetracker', repo_name=c.repo_name)}">${_('Issue Tracker')}</a>
          </li>
          <li class="${h.is_active('caches', c.active)}">
              <a href="${h.route_path('edit_repo_caches', repo_name=c.repo_name)}">${_('Caches')}</a>
          </li>
          %if c.rhodecode_db_repo.repo_type != 'svn':
          <li class="${h.is_active('remote', c.active)}">
              <a href="${h.route_path('edit_repo_remote', repo_name=c.repo_name)}">${_('Remote sync')}</a>
          </li>
          %endif
          <li class="${h.is_active('statistics', c.active)}">
              <a href="${h.route_path('edit_repo_statistics', repo_name=c.repo_name)}">${_('Statistics')}</a>
          </li>
          <li class="${h.is_active('integrations', c.active)}">
              <a href="${h.route_path('repo_integrations_home', repo_name=c.repo_name)}">${_('Integrations')}</a>
          </li>
          %if c.rhodecode_db_repo.repo_type != 'svn':
          <li class="${h.is_active('reviewers', c.active)}">
              <a href="${h.route_path('repo_reviewers', repo_name=c.repo_name)}">${_('Reviewer Rules')}</a>
          </li>
          %endif
          <li class="${h.is_active('automation', c.active)}">
              <a href="${h.route_path('repo_automation', repo_name=c.repo_name)}">${_('Automation')}</a>
          </li>
          <li class="${h.is_active('maintenance', c.active)}">
              <a href="${h.route_path('edit_repo_maintenance', repo_name=c.repo_name)}">${_('Maintenance')}</a>
          </li>
          <li class="${h.is_active('strip', c.active)}">
              <a href="${h.route_path('edit_repo_strip', repo_name=c.repo_name)}">${_('Strip')}</a>
          </li>
          <li class="${h.is_active('audit', c.active)}">
              <a href="${h.route_path('edit_repo_audit_logs', repo_name=c.repo_name)}">${_('Audit logs')}</a>
          </li>

        </ul>
    </div>

    <div class="main-content-full-width">
      ${self.main_content()}
    </div>

  </div>
</div>

</%def>