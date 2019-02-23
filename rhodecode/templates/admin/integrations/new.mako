## -*- coding: utf-8 -*-
<%inherit file="base.mako"/>
<%namespace name="widgets" file="/widgets.mako"/>

<%def name="breadcrumbs_links()">
  %if c.repo:
    ${_('Settings')}
  %elif c.repo_group:
    ${_('Settings')}
  %else:
    ${h.link_to(_('Admin'),h.route_path('admin_home'))}
    &raquo;
    ${h.link_to(_('Settings'),h.route_path('admin_settings'))}
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

    %for integration, IntegrationObject in c.available_integrations.items():
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
      if IntegrationObject.is_dummy:
        create_url = request.current_route_path()
      %>
        <a href="${create_url}" class="integration-box ${'dummy-integration' if IntegrationObject.is_dummy else ''}">
          <%widgets:panel>
            <h2>
              <div class="integration-icon">
                  ${IntegrationObject.icon()|n}
              </div>
              ${IntegrationObject.display_name}
            </h2>
            ${IntegrationObject.description or _('No description available')}
          </%widgets:panel>
        </a>
    %endfor
      <div style="clear:both"></div>
</%widgets:panel>
