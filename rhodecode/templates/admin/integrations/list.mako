## -*- coding: utf-8 -*-
<%inherit file="base.mako"/>

<%def name="breadcrumbs_links()">
  %if c.repo:
    ${h.link_to('Settings',h.route_path('edit_repo', repo_name=c.repo.repo_name))}
  %elif c.repo_group:
    ${h.link_to(_('Admin'),h.route_path('admin_home'))}
    &raquo;
    ${h.link_to(_('Repository Groups'),h.url('repo_groups'))}
    &raquo;
    ${h.link_to(c.repo_group.group_name,h.url('edit_repo_group', group_name=c.repo_group.group_name))}
  %else:
    ${h.link_to(_('Admin'),h.route_path('admin_home'))}
    &raquo;
    ${h.link_to(_('Settings'),h.url('admin_settings'))}
  %endif
  %if c.current_IntegrationType:
    &raquo;
    %if c.repo:
    ${h.link_to(_('Integrations'),
      request.route_path(route_name='repo_integrations_home',
                         repo_name=c.repo.repo_name))}
    %elif c.repo_group:
    ${h.link_to(_('Integrations'),
      request.route_path(route_name='repo_group_integrations_home',
                         repo_group_name=c.repo_group.group_name))}
    %else:
    ${h.link_to(_('Integrations'),
      request.route_path(route_name='global_integrations_home'))}
    %endif
    &raquo;
    ${c.current_IntegrationType.display_name}
  %else:
    &raquo;
    ${_('Integrations')}
  %endif
</%def>

<div class="panel panel-default">
  <div class="panel-heading">
    <h3 class="panel-title">
      %if c.repo:
        ${_('Current Integrations for Repository: {repo_name}').format(repo_name=c.repo.repo_name)}
      %elif c.repo_group:
        ${_('Current Integrations for repository group: {repo_group_name}').format(repo_group_name=c.repo_group.group_name)}
      %else:
          ${_('Current Integrations')}
      %endif
      </h3>
  </div>
  <div class="panel-body">
    <%
    if c.repo:
      home_url = request.route_path('repo_integrations_home',
                                    repo_name=c.repo.repo_name)
    elif c.repo_group:
      home_url = request.route_path('repo_group_integrations_home',
                                    repo_group_name=c.repo_group.group_name)
    else:
      home_url = request.route_path('global_integrations_home')
    %>

    <a href="${home_url}" class="btn ${not c.current_IntegrationType and 'btn-primary' or ''}">${_('All')}</a>

    %for integration_key, IntegrationType in c.available_integrations.items():
        <%
        if c.repo:
          list_url = request.route_path('repo_integrations_list',
                                        repo_name=c.repo.repo_name,
                                        integration=integration_key)
        elif c.repo_group:
          list_url = request.route_path('repo_group_integrations_list',
                                        repo_group_name=c.repo_group.group_name,
                                        integration=integration_key)
        else:
          list_url = request.route_path('global_integrations_list',
                                       integration=integration_key)
        %>
      <a href="${list_url}"
         class="btn ${c.current_IntegrationType and integration_key == c.current_IntegrationType.key and 'btn-primary' or ''}">
        ${IntegrationType.display_name}
      </a>
    %endfor

    <%
    integration_type = c.current_IntegrationType and c.current_IntegrationType.display_name or ''

    if c.repo:
      create_url = h.route_path('repo_integrations_new', repo_name=c.repo.repo_name)
    elif c.repo_group:
      create_url = h.route_path('repo_group_integrations_new', repo_group_name=c.repo_group.group_name)
    else:
      create_url = h.route_path('global_integrations_new')
    %>
    <p class="pull-right">
      <a href="${create_url}" class="btn btn-small btn-success">${_(u'Create new integration')}</a>
    </p>

    <table class="rctable integrations">
      <thead>
        <tr>
            <th><a href="?sort=enabled:${c.rev_sort_dir}">${_('Enabled')}</a></th>
            <th><a href="?sort=name:${c.rev_sort_dir}">${_('Name')}</a></th>
            <th colspan="2"><a href="?sort=integration_type:${c.rev_sort_dir}">${_('Type')}</a></th>
            <th><a href="?sort=scope:${c.rev_sort_dir}">${_('Scope')}</a></th>
            <th>${_('Actions')}</th>
            <th></th>
        </tr>
      </thead>
      <tbody>
  %if not c.integrations_list:
        <tr>
          <td colspan="7">

            %if c.repo:
              ${_('No {type} integrations for repo {repo} exist yet.').format(type=integration_type, repo=c.repo.repo_name)}
            %elif c.repo_group:
              ${_('No {type} integrations for repogroup {repogroup} exist yet.').format(type=integration_type, repogroup=c.repo_group.group_name)}
            %else:
              ${_('No {type} integrations exist yet.').format(type=integration_type)}
            %endif

            %if c.current_IntegrationType:
            <%
            if c.repo:
              create_url = h.route_path('repo_integrations_create', repo_name=c.repo.repo_name, integration=c.current_IntegrationType.key)
            elif c.repo_group:
              create_url = h.route_path('repo_group_integrations_create', repo_group_name=c.repo_group.group_name, integration=c.current_IntegrationType.key)
            else:
              create_url = h.route_path('global_integrations_create', integration=c.current_IntegrationType.key)
            %>
            %endif

            <a href="${create_url}">${_(u'Create one')}</a>
          </td>
        </tr>
  %endif
  %for IntegrationType, integration in c.integrations_list:
        <tr id="integration_${integration.integration_id}">
          <td class="td-enabled">
            %if integration.enabled:
            <div class="flag_status approved pull-left"></div>
            %else:
            <div class="flag_status rejected pull-left"></div>
            %endif
          </td>
          <td class="td-description">
            ${integration.name}
          </td>
          <td class="td-icon">
            %if integration.integration_type in c.available_integrations:
            <div class="integration-icon">
              ${c.available_integrations[integration.integration_type].icon|n}
            </div>
            %else:
              ?
            %endif
          </td>
          <td class="td-type">
            ${integration.integration_type}
          </td>
          <td class="td-scope">
            %if integration.repo:
            <a href="${h.route_path('repo_summary', repo_name=integration.repo.repo_name)}">
              ${_('repo')}:${integration.repo.repo_name}
            </a>
            %elif integration.repo_group:
            <a href="${h.route_path('repo_group_home', repo_group_name=integration.repo_group.group_name)}">
              ${_('repogroup')}:${integration.repo_group.group_name}
              %if integration.child_repos_only:
              ${_('child repos only')}
              %else:
              ${_('cascade to all')}
              %endif
            </a>
            %else:
              %if integration.child_repos_only:
              ${_('top level repos only')}
              %else:
              ${_('global')}
              %endif
          </td>
          %endif
          <td class="td-action">
          %if not IntegrationType:
          ${_('unknown integration')}
          %else:
            <%
            if c.repo:
              edit_url = request.route_path('repo_integrations_edit',
                                            repo_name=c.repo.repo_name,
                                            integration=integration.integration_type,
                                            integration_id=integration.integration_id)
            elif c.repo_group:
              edit_url = request.route_path('repo_group_integrations_edit',
                                            repo_group_name=c.repo_group.group_name,
                                            integration=integration.integration_type,
                                            integration_id=integration.integration_id)
            else:
              edit_url = request.route_path('global_integrations_edit',
                                           integration=integration.integration_type,
                                           integration_id=integration.integration_id)
            %>
            <div class="grid_edit">
              <a href="${edit_url}">${_('Edit')}</a>
            </div>
            <div class="grid_delete">
              <a href="${edit_url}"
                 class="btn btn-link btn-danger delete_integration_entry"
                 data-desc="${integration.name}"
                 data-uid="${integration.integration_id}">
                  ${_('Delete')}
              </a>
            </div>
          %endif
          </td>
        </tr>
    %endfor
      <tr id="last-row"></tr>
      </tbody>
    </table>
    <div class="integrations-paginator">
      <div class="pagination-wh pagination-left">
      ${c.integrations_list.pager('$link_previous ~2~ $link_next')}
      </div>
    </div>
  </div>
</div>
<script type="text/javascript">
  var delete_integration = function(entry) {
    if (confirm("Confirm to remove this integration: "+$(entry).data('desc'))) {
      var request = $.ajax({
        type: "POST",
        url: $(entry).attr('href'),
        data: {
          'delete': 'delete',
          'csrf_token': CSRF_TOKEN
        },
        success: function(){
          location.reload();
        },
        error: function(data, textStatus, errorThrown){
          alert("Error while deleting entry.\nError code {0} ({1}). URL: {2}".format(data.status,data.statusText,$(entry)[0].url));
        }
      });
    };
  };

  $('.delete_integration_entry').on('click', function(e){
    e.preventDefault();
    delete_integration(this);
  });
</script>