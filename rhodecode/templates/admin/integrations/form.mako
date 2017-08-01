## -*- coding: utf-8 -*-
<%inherit file="base.mako"/>

<%def name="breadcrumbs_links()">
  %if c.repo:
    ${h.link_to('Settings',h.route_path('edit_repo', repo_name=c.repo.repo_name))}
    &raquo;
    ${h.link_to(_('Integrations'),request.route_url(route_name='repo_integrations_home', repo_name=c.repo.repo_name))}
    &raquo;
    ${h.link_to(c.current_IntegrationType.display_name,
      request.route_url(route_name='repo_integrations_list',
                        repo_name=c.repo.repo_name,
                        integration=c.current_IntegrationType.key))}
  %elif c.repo_group:
    ${h.link_to(_('Admin'),h.route_path('admin_home'))}
    &raquo;
    ${h.link_to(_('Repository Groups'),h.url('repo_groups'))}
    &raquo;
    ${h.link_to(c.repo_group.group_name,h.url('edit_repo_group', group_name=c.repo_group.group_name))}
    &raquo;
    ${h.link_to(_('Integrations'),request.route_url(route_name='repo_group_integrations_home', repo_group_name=c.repo_group.group_name))}
    &raquo;
    ${h.link_to(c.current_IntegrationType.display_name,
      request.route_url(route_name='repo_group_integrations_list',
                        repo_group_name=c.repo_group.group_name,
                        integration=c.current_IntegrationType.key))}
  %else:
    ${h.link_to(_('Admin'),h.route_path('admin_home'))}
    &raquo;
    ${h.link_to(_('Settings'),h.url('admin_settings'))}
    &raquo;
    ${h.link_to(_('Integrations'),request.route_url(route_name='global_integrations_home'))}
    &raquo;
    ${h.link_to(c.current_IntegrationType.display_name,
      request.route_url(route_name='global_integrations_list',
                        integration=c.current_IntegrationType.key))}
  %endif

  %if c.integration:
    &raquo;
    ${c.integration.name}
  %elif c.current_IntegrationType:
    &raquo;
    ${c.current_IntegrationType.display_name}
  %endif
</%def>

<style>
.control-inputs.item-options, .control-inputs.item-settings {
  float: left;
  width: 100%;
}
</style>
<div class="panel panel-default">
  <div class="panel-heading">
    <h2 class="panel-title">
      %if c.integration:
        ${c.current_IntegrationType.display_name} - ${c.integration.name}
      %else:
        ${_('Create New %(integration_type)s Integration') % {
          'integration_type': c.current_IntegrationType.display_name
        }}
      %endif
    </h2>
  </div>
  <div class="panel-body">
    ${c.form.render() | n}
  </div>
</div>
