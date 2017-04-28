## -*- coding: utf-8 -*-
<%inherit file="base.mako"/>
<%namespace name="widgets" file="/widgets.mako"/>

<%def name="breadcrumbs_links()">
  %if c.repo:
    ${h.link_to('Settings',h.route_path('edit_repo', repo_name=c.repo.repo_name))}
    &raquo;
    ${h.link_to(_('Integrations'),request.route_url(route_name='repo_integrations_home', repo_name=c.repo.repo_name))}
  %elif c.repo_group:
    ${h.link_to(_('Admin'),h.url('admin_home'))}
    &raquo;
    ${h.link_to(_('Repository Groups'),h.url('repo_groups'))}
    &raquo;
    ${h.link_to(c.repo_group.group_name,h.url('edit_repo_group', group_name=c.repo_group.group_name))}
    &raquo;
    ${h.link_to(_('Integrations'),request.route_url(route_name='repo_group_integrations_home', repo_group_name=c.repo_group.group_name))}
  %else:
    ${h.link_to(_('Admin'),h.url('admin_home'))}
    &raquo;
    ${h.link_to(_('Settings'),h.url('admin_settings'))}
    &raquo;
    ${h.link_to(_('Integrations'),request.route_url(route_name='global_integrations_home'))}
  %endif
    &raquo;
    ${_('Create new integration')}
</%def>
<%widgets:panel class_='integrations'>
    <%def name="title()">
        %if c.repo:
            ${_('Create New Integration for repository: {repo_name}').format(repo_name=c.repo.repo_name)}
        %elif c.repo_group:
            ${_('Create New Integration for repository group: {repo_group_name}').format(repo_group_name=c.repo_group.group_name)}
        %else:
            ${_('Create New Global Integration')}
        %endif
    </%def>

    %for integration, IntegrationType in available_integrations.items():
      <%
      if c.repo:
        create_url = request.route_path('repo_integrations_create',
                                        repo_name=c.repo.repo_name,
                                        integration=integration)
      elif c.repo_group:
        create_url = request.route_path('repo_group_integrations_create',
                                        repo_group_name=c.repo_group.group_name,
                                        integration=integration)
      else:
        create_url = request.route_path('global_integrations_create',
                                        integration=integration)
      %>
        <a href="${create_url}" class="integration-box">
          <%widgets:panel>
            <h2>
              <div class="integration-icon">
                  ${IntegrationType.icon|n}
              </div>
              ${IntegrationType.display_name}
            </h2>
            ${IntegrationType.description or _('No description available')}
          </%widgets:panel>
        </a>
    %endfor
      <div style="clear:both"></div>
</%widgets:panel>
