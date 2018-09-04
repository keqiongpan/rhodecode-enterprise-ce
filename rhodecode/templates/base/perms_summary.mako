## snippet for displaying permissions overview for users
## usage:
##    <%namespace name="p" file="/base/perms_summary.mako"/>
##    ${p.perms_summary(c.perm_user.permissions)}

<%def name="perms_summary(permissions, show_all=False, actions=True, side_link=None)">
<% section_to_label = {
    'global': 'Global Permissions',
    'repository_branches': 'Repository Branch Rules',
    'repositories': 'Repository Permissions',
    'user_groups': 'User Group Permissions',
    'repositories_groups': 'Repository Group Permissions',
} %>

<div id="perms" class="table fields">
  %for section in sorted(permissions.keys(), key=lambda item: {'global': 0, 'repository_branches': 1}.get(item, 1000)):
  <% total_counter = 0 %>

  <div class="panel panel-default">
    <div class="panel-heading" id="${section.replace("_","-")}-permissions">
        <h3 class="panel-title">${section_to_label.get(section, section)} - <span id="total_count_${section}"></span>
        <a class="permalink" href="#${section.replace("_","-")}-permissions"> ¶</a>
        </h3>
        % if side_link:
            <div class="pull-right">
                <a href="${side_link}">${_('in JSON format')}</a>
            </div>
        % endif
    </div>
    <div class="panel-body">
      <div class="perms_section_head field">
        <div class="radios">
          % if section == 'repository_branches':
              <span class="permissions_boxes">
              <span class="desc">${_('show')}: </span>
              ${h.checkbox('perms_filter_none_%s' % section, 'none', 'checked', class_='perm_filter filter_%s' % section, section=section, perm_type='none')}   <label for="${'perms_filter_none_{}'.format(section)}"><span class="perm_tag none">${_('none')}</span></label>
              ${h.checkbox('perms_filter_merge_%s' % section, 'merge', 'checked', class_='perm_filter filter_%s' % section, section=section, perm_type='merge')}   <label for="${'perms_filter_merge_{}'.format(section)}"><span class="perm_tag merge">${_('merge')}</span></label>
              ${h.checkbox('perms_filter_push_%s' % section, 'push', 'checked', class_='perm_filter filter_%s' % section, section=section, perm_type='push')} <label for="${'perms_filter_push_{}'.format(section)}"> <span class="perm_tag push">${_('push')}</span></label>
              ${h.checkbox('perms_filter_push_force_%s' % section, 'push_force', 'checked', class_='perm_filter filter_%s' % section, section=section, perm_type='push_force')} <label for="${'perms_filter_push_force_{}'.format(section)}"><span class="perm_tag push_force">${_('push force')}</span></label>
              </span>
          % elif section != 'global':
              <span class="permissions_boxes">
              <span class="desc">${_('show')}: </span>
              ${h.checkbox('perms_filter_none_%s' % section, 'none', '', class_='perm_filter filter_%s' % section, section=section, perm_type='none')}   <label for="${'perms_filter_none_{}'.format(section)}"><span class="perm_tag none">${_('none')}</span></label>
              ${h.checkbox('perms_filter_read_%s' % section, 'read', 'checked', class_='perm_filter filter_%s' % section, section=section, perm_type='read')}   <label for="${'perms_filter_read_{}'.format(section)}"><span class="perm_tag read">${_('read')}</span></label>
              ${h.checkbox('perms_filter_write_%s' % section, 'write', 'checked', class_='perm_filter filter_%s' % section, section=section, perm_type='write')} <label for="${'perms_filter_write_{}'.format(section)}"> <span class="perm_tag write">${_('write')}</span></label>
              ${h.checkbox('perms_filter_admin_%s' % section, 'admin', 'checked', class_='perm_filter filter_%s' % section, section=section, perm_type='admin')} <label for="${'perms_filter_admin_{}'.format(section)}"><span class="perm_tag admin">${_('admin')}</span></label>
              </span>
          % endif

        </div>
      </div>
      <div class="field">
        %if not permissions[section]:
            <p class="empty_data help-block">${_('No permissions defined')}</p>
        %else:
        <div id='tbl_list_wrap_${section}'>
         <table id="tbl_list_${section}" class="rctable">
          ## global permission box
          %if section == 'global':
            <thead>
                <tr>
                <th colspan="2" class="left">${_('Permission')}</th>
                %if actions:
                <th colspan="2">${_('Edit Permission')}</th>
                %endif
            </thead>
            <tbody>

            <%
              def get_section_perms(prefix, opts):
                  _selected = []
                  for op in opts:
                      if op.startswith(prefix) and not op.startswith('hg.create.write_on_repogroup'):
                          _selected.append(op)
                  admin = 'hg.admin' in opts
                  _selected_vals = [x.partition(prefix)[-1] for x in _selected]
                  return admin, _selected_vals, _selected
            %>

            <%def name="glob(lbl, val, val_lbl=None, edit_url=None, edit_global_url=None)">
              <tr>
                <td class="td-tags">
                    ${lbl}
                </td>
                <td class="td-tags">
                    %if val[0]:
                      %if not val_lbl:
                          ## super admin case
                          True
                      %else:
                          <span class="perm_tag admin">${val_lbl}.admin</span>
                      %endif
                    %else:
                      %if not val_lbl:
                          ${{'false': False,
                             'true': True,
                             'none': False,
                             'repository': True}.get(val[1][0] if 0 < len(val[1]) else 'false')}
                      %else:
                          <span class="perm_tag ${val[1][0]}">${val_lbl}.${val[1][0]}</span>
                      %endif
                    %endif
                </td>
                %if actions:

                    % if edit_url or edit_global_url:

                        <td class="td-action">
                            % if edit_url:
                            <a href="${edit_url}">${_('edit')}</a>
                            % else:
                                -
                            % endif
                        </td>

                        <td class="td-action">
                            % if edit_global_url:
                            <a href="${edit_global_url}">${_('edit global')}</a>
                            % else:
                                -
                            % endif
                        </td>

                    % else:
                        <td class="td-action"></td>
                        <td class="td-action">
                            <a href="${h.route_path('admin_permissions_global')}">${_('edit global')}</a>
                        <td class="td-action">
                    % endif

                %endif
              </tr>
            </%def>

           ${glob(_('Repository default permission'), get_section_perms('repository.', permissions[section]), 'repository',
                edit_url=None, edit_global_url=h.route_path('admin_permissions_object'))}

           ${glob(_('Repository group default permission'), get_section_perms('group.', permissions[section]), 'group',
                edit_url=None, edit_global_url=h.route_path('admin_permissions_object'))}

           ${glob(_('User group default permission'), get_section_perms('usergroup.', permissions[section]), 'usergroup',
                edit_url=None, edit_global_url=h.route_path('admin_permissions_object'))}

           ${glob(_('Super admin'), get_section_perms('hg.admin', permissions[section]),
                edit_url=h.route_path('user_edit', user_id=c.user.user_id, _anchor='admin'), edit_global_url=None)}

           ${glob(_('Inherit permissions'), get_section_perms('hg.inherit_default_perms.', permissions[section]),
                edit_url=h.route_path('user_edit_global_perms', user_id=c.user.user_id), edit_global_url=None)}

           ${glob(_('Create repositories'), get_section_perms('hg.create.', permissions[section]),
                edit_url=h.route_path('user_edit_global_perms', user_id=c.user.user_id), edit_global_url=h.route_path('admin_permissions_object'))}

           ${glob(_('Fork repositories'), get_section_perms('hg.fork.', permissions[section]),
                edit_url=h.route_path('user_edit_global_perms', user_id=c.user.user_id), edit_global_url=h.route_path('admin_permissions_object'))}

           ${glob(_('Create repository groups'), get_section_perms('hg.repogroup.create.', permissions[section]),
                edit_url=h.route_path('user_edit_global_perms', user_id=c.user.user_id), edit_global_url=h.route_path('admin_permissions_object'))}

           ${glob(_('Create user groups'), get_section_perms('hg.usergroup.create.', permissions[section]),
                edit_url=h.route_path('user_edit_global_perms', user_id=c.user.user_id), edit_global_url=h.route_path('admin_permissions_object'))}

           </tbody>
          ## Branch perms
          %elif section == 'repository_branches':
            <thead>
                <tr>
                <th>${_('Name')}</th>
                <th>${_('Pattern')}</th>
                <th>${_('Permission')}</th>
                %if actions:
                <th>${_('Edit Branch Permission')}</th>
                %endif
            </thead>
            <tbody class="section_${section}">
            <%
                def name_sorter(permissions):
                    def custom_sorter(item):
                        return item[0]
                    return sorted(permissions, key=custom_sorter)

                def branch_sorter(permissions):
                    def custom_sorter(item):
                       ## none, merge, push, push_force
                       section = item[1].split('.')[-1]
                       section_importance = {'none': u'0',
                                             'merge': u'1',
                                             'push': u'2',
                                             'push_force': u'3'}.get(section)
                       ## sort by importance + name
                       return section_importance + item[0]
                    return sorted(permissions, key=custom_sorter)
            %>
            %for k, section_perms in name_sorter(permissions[section].items()):
                ## for display purposes, for non super-admins we need to check if shown
                ## repository is actually accessible for user
                <% repo_perm = permissions['repositories'][k] %>
                % if repo_perm == 'repository.none' and not c.rhodecode_user.is_admin:
                    ## skip this entry
                    <% continue %>
                % endif

                <% total_counter +=1 %>
                % for pattern, perm in branch_sorter(section_perms.items()):
                    <tr class="perm_row ${'{}_{}'.format(section, perm.split('.')[-1])}">
                        <td class="td-name">
                            <a href="${h.route_path('repo_summary',repo_name=k)}">${k}</a>
                        </td>
                        <td>${pattern}</td>
                        <td class="td-tags">
                            ## TODO: calculate origin somehow
                            ## % for i, ((_pat, perm), origin) in enumerate((permissions[section].perm_origin_stack[k])):

                             <div>
                                 <% i = 0 %>
                                 <% origin = 'unknown' %>
                                 <% _css_class = i > 0 and 'perm_overriden' or '' %>

                                 <span class="${_css_class} perm_tag ${perm.split('.')[-1]}">
                                  ${perm}
                                  ##(${origin})
                                 </span>
                             </div>
                            ## % endfor
                        </td>
                        %if actions:
                        <td class="td-action">
                            <a href="${h.route_path('edit_repo_perms_branch',repo_name=k)}">${_('edit')}</a>
                        </td>
                        %endif
                    </tr>
                % endfor
            %endfor
            </tbody>

          ## Repos/Repo Groups/users groups perms
          %else:

           ## none/read/write/admin permissions on groups/repos etc
            <thead>
                <tr>
                <th>${_('Name')}</th>
                <th>${_('Permission')}</th>
                %if actions:
                <th>${_('Edit Permission')}</th>
                %endif
            </thead>
            <tbody class="section_${section}">
            <%
                def sorter(permissions):
                    def custom_sorter(item):
                       ## read/write/admin
                       section = item[1].split('.')[-1]
                       section_importance = {'none': u'0',
                                             'read': u'1',
                                             'write':u'2',
                                             'admin':u'3'}.get(section)
                       ## sort by group importance+name
                       return section_importance+item[0]
                    return sorted(permissions, key=custom_sorter)
            %>
            %for k, section_perm in sorter(permissions[section].items()):
                <% perm_value = section_perm.split('.')[-1] %>
                <% _css_class = 'display:none' if perm_value in ['none'] else '' %>

                %if perm_value != 'none' or show_all:
                <tr class="perm_row ${'{}_{}'.format(section, section_perm.split('.')[-1])}" style="${_css_class}">
                    <td class="td-name">
                        %if section == 'repositories':
                            <a href="${h.route_path('repo_summary',repo_name=k)}">${k}</a>
                        %elif section == 'repositories_groups':
                            <a href="${h.route_path('repo_group_home', repo_group_name=k)}">${k}</a>
                        %elif section == 'user_groups':
                            ##<a href="${h.route_path('edit_user_group',user_group_id=k)}">${k}</a>
                            ${k}
                        %endif
                    </td>
                    <td class="td-tags">
                      %if hasattr(permissions[section], 'perm_origin_stack'):
                         <div>
                         %for i, (perm, origin) in enumerate(reversed(permissions[section].perm_origin_stack[k])):
                         <% _css_class =  i > 0 and 'perm_overriden' or '' %>
                         % if i > 0:
                             <div style="color: #979797">
                             <i class="icon-arrow_up"></i>
                                 ${_('overridden by')}
                             <i class="icon-arrow_up"></i>
                             </div>
                         % endif

                         <div>
                             <span class="${_css_class} perm_tag ${perm.split('.')[-1]}">
                              ${perm} (${origin})
                             </span>
                         </div>

                         %endfor
                         </div>
                      %else:
                         <span class="perm_tag ${section_perm.split('.')[-1]}">${section_perm}</span>
                      %endif
                    </td>
                    %if actions:
                    <td class="td-action">
                        %if section == 'repositories':
                            <a href="${h.route_path('edit_repo_perms',repo_name=k,_anchor='permissions_manage')}">${_('edit')}</a>
                        %elif section == 'repositories_groups':
                            <a href="${h.route_path('edit_repo_group_perms',repo_group_name=k,_anchor='permissions_manage')}">${_('edit')}</a>
                        %elif section == 'user_groups':
                            ##<a href="${h.route_path('edit_user_group',user_group_id=k)}">${_('edit')}</a>
                        %endif
                    </td>
                    %endif
                </tr>
                <% total_counter +=1 %>
                %endif

            %endfor

            <tr id="empty_${section}" class="noborder" style="display:none;">
              <td colspan="6">${_('No matching permission defined')}</td>
            </tr>

            </tbody>
          %endif
         </table>
        </div>
        %endif
      </div>
    </div>
  </div>

  <script>
    $('#total_count_${section}').html(${total_counter})
  </script>

  %endfor
</div>

<script>
    $(document).ready(function(){
        var showEmpty = function(section){
            var visible = $('.section_{0} tr.perm_row:visible'.format(section)).length;
            if(visible === 0){
                $('#empty_{0}'.format(section)).show();
            }
            else{
                $('#empty_{0}'.format(section)).hide();
            }
        };

        $('.perm_filter').on('change', function(e){
            var self = this;
            var section = $(this).attr('section');

            var opts = {};
            var elems = $('.filter_' + section).each(function(el){
                var perm_type = $(this).attr('perm_type');
                var checked = this.checked;
                opts[perm_type] = checked;
                if(checked){
                    $('.'+section+'_'+perm_type).show();
                }
                else{
                    $('.'+section+'_'+perm_type).hide();
                }
            });
            showEmpty(section);
        })
    })
</script>
</%def>
