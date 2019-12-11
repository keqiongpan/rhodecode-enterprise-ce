<%namespace name="base" file="/base/base.mako"/>

<div class="panel panel-default">
    <div class="panel-heading">
        <h3 class="panel-title">${_('Repository Group Permissions: {}').format(c.repo_group.name)}</h3>
    </div>
    <div class="panel-body">
        ${h.secure_form(h.route_path('edit_repo_group_perms_update', repo_group_name=c.repo_group.group_name), request=request)}
        <table id="permissions_manage" class="rctable permissions">
            <tr>
                <th class="td-radio">${_('None')}</th>
                <th class="td-radio">${_('Read')}</th>
                <th class="td-radio">${_('Write')}</th>
                <th class="td-radio">${_('Admin')}</th>
                <th class="td-owner">${_('User/User Group')}</th>
                <th class="td-action"></th>
                <th class="td-action"></th>
            </tr>
            ## USERS
            %for _user in c.repo_group.permissions():
                ## super admin/owner row
                %if getattr(_user, 'admin_row', None) or getattr(_user, 'owner_row', None):
                    <tr class="perm_admin_row">
                        <td class="td-radio">${h.radio('admin_perm_%s' % _user.user_id,'repository.none', disabled="disabled")}</td>
                        <td class="td-radio">${h.radio('admin_perm_%s' % _user.user_id,'repository.read', disabled="disabled")}</td>
                        <td class="td-radio">${h.radio('admin_perm_%s' % _user.user_id,'repository.write', disabled="disabled")}</td>
                        <td class="td-radio">${h.radio('admin_perm_%s' % _user.user_id,'repository.admin', 'repository.admin', disabled="disabled")}</td>
                        <td class="td-user">
                                ${base.gravatar(_user.email, 16, user=_user, tooltip=True)}
                                ${h.link_to_user(_user.username)}
                                %if getattr(_user, 'admin_row', None):
                                    (${_('super-admin')})
                                %endif
                                %if getattr(_user, 'owner_row', None):
                                    (${_('owner')})
                                %endif
                        </td>
                        <td></td>
                        <td class="quick_repo_menu">
                            % if c.rhodecode_user.is_admin:
                                <i class="icon-more"></i>
                                <div class="menu_items_container" style="display: none;">
                                <ul class="menu_items">
                                  <li>
                                     ${h.link_to('show permissions', h.route_path('edit_user_perms_summary', user_id=_user.user_id, _anchor='repositories-groups-permissions'))}
                                  </li>
                                </ul>
                                </div>
                            % endif
                        </td>
                    </tr>
                %else:
                    <tr>
                        ##forbid revoking permission from yourself, except if you're an super admin
                        %if c.rhodecode_user.user_id != _user.user_id or c.rhodecode_user.is_admin:
                        <td class="td-radio">${h.radio('u_perm_%s' % _user.user_id,'group.none', checked=_user.permission=='group.none')}</td>
                        <td class="td-radio">${h.radio('u_perm_%s' % _user.user_id,'group.read', checked=_user.permission=='group.read')}</td>
                        <td class="td-radio">${h.radio('u_perm_%s' % _user.user_id,'group.write', checked=_user.permission=='group.write')}</td>
                        <td class="td-radio">${h.radio('u_perm_%s' % _user.user_id,'group.admin', checked=_user.permission=='group.admin')}</td>
                        <td class="td-user">
                            ${base.gravatar(_user.email, 16, user=_user, tooltip=True)}
                            <span class="user">
                                % if _user.username == h.DEFAULT_USER:
                                    ${h.DEFAULT_USER} <span class="user-perm-help-text"> - ${_('permission for all other users')}</span>
                                % else:
                                    ${h.link_to_user(_user.username)}
                                    %if getattr(_user, 'duplicate_perm', None):
                                        (${_('inactive duplicate')})
                                    %endif
                                % endif
                            </span>
                        </td>
                        <td class="td-action">
                            %if _user.username != h.DEFAULT_USER:
                                <span  class="btn btn-link btn-danger revoke_perm"
                                  member="${_user.user_id}" member_type="user">
                                ${_('Remove')}
                                </span>
                            %endif
                        </td>
                        <td class="quick_repo_menu">
                            % if c.rhodecode_user.is_admin:
                                <i class="icon-more"></i>
                                <div class="menu_items_container" style="display: none;">
                                <ul class="menu_items">
                                  <li>
                                    % if _user.username == h.DEFAULT_USER:
                                        ${h.link_to('show permissions', h.route_path('admin_permissions_overview', _anchor='repositories-groups-permissions'))}
                                    % else:
                                        ${h.link_to('show permissions', h.route_path('edit_user_perms_summary', user_id=_user.user_id, _anchor='repositories-groups-permissions'))}
                                    % endif
                                  </li>
                                </ul>
                                </div>
                            % endif
                        </td>
                        %else:
                            ## special case for currently logged-in user permissions, we make sure he cannot take his own permissions
                            <td class="td-radio">${h.radio('u_perm_%s' % _user.user_id,'group.none', disabled="disabled")}</td>
                            <td class="td-radio">${h.radio('u_perm_%s' % _user.user_id,'group.read', disabled="disabled")}</td>
                            <td class="td-radio">${h.radio('u_perm_%s' % _user.user_id,'group.write', disabled="disabled")}</td>
                            <td class="td-radio">${h.radio('u_perm_%s' % _user.user_id,'group.admin', disabled="disabled")}</td>
                            <td class="td-user">
                                ${base.gravatar(_user.email, 16, user=_user, tooltip=True)}
                                <span class="user">
                                    % if _user.username == h.DEFAULT_USER:
                                        ${h.DEFAULT_USER} <span class="user-perm-help-text"> - ${_('permission for all other users')}</span>
                                    % else:
                                        ${h.link_to_user(_user.username)}
                                        %if getattr(_user, 'duplicate_perm', None):
                                            (${_('inactive duplicate')})
                                        %endif
                                    % endif
                                    <span class="user-perm-help-text">(${_('delegated admin')})</span>
                                </span>
                            </td>
                            <td></td>
                            <td class="quick_repo_menu">
                                % if c.rhodecode_user.is_admin:
                                    <i class="icon-more"></i>
                                    <div class="menu_items_container" style="display: none;">
                                    <ul class="menu_items">
                                      <li>
                                         ${h.link_to('show permissions', h.route_path('edit_user_perms_summary', user_id=_user.user_id, _anchor='repositories-groups-permissions'))}
                                      </li>
                                    </ul>
                                    </div>
                                % endif
                            </td>
                        %endif
                    </tr>
                %endif
            %endfor

            ## USER GROUPS
            %for _user_group in c.repo_group.permission_user_groups(with_members=True):
                <tr id="id${id(_user_group.users_group_name)}">
                    <td class="td-radio">${h.radio('g_perm_%s' % _user_group.users_group_id,'group.none', checked=_user_group.permission=='group.none')}</td>
                    <td class="td-radio">${h.radio('g_perm_%s' % _user_group.users_group_id,'group.read', checked=_user_group.permission=='group.read')}</td>
                    <td class="td-radio">${h.radio('g_perm_%s' % _user_group.users_group_id,'group.write', checked=_user_group.permission=='group.write')}</td>
                    <td class="td-radio">${h.radio('g_perm_%s' % _user_group.users_group_id,'group.admin', checked=_user_group.permission=='group.admin')}</td>
                    <td class="td-componentname">
                        ${base.user_group_icon(_user_group, tooltip=True)}

                        %if c.is_super_admin:
                         <a href="${h.route_path('edit_user_group',user_group_id=_user_group.users_group_id)}">
                             ${_user_group.users_group_name}
                         </a>
                        %else:
                         ${h.link_to_group(_user_group.users_group_name)}
                        %endif
                        (${_('members')}: ${len(_user_group.members)})
                    </td>
                    <td class="td-action">
                        <span  class="btn btn-link btn-danger revoke_perm"
                              member="${_user_group.users_group_id}" member_type="user_group">
                        ${_('Remove')}
                        </span>
                    </td>
                    <td class="quick_repo_menu">
                        % if c.rhodecode_user.is_admin:
                            <i class="icon-more"></i>
                            <div class="menu_items_container" style="display: none;">
                            <ul class="menu_items">
                              <li>
                                 ${h.link_to('show permissions', h.route_path('edit_user_group_perms_summary', user_group_id=_user_group.users_group_id, _anchor='repositories-groups-permissions'))}
                              </li>
                            </ul>
                            </div>
                        % endif
                    </td>
                </tr>
            %endfor

            <tr class="new_members" id="add_perm_input"></tr>
            <tr>
                <td></td>
                <td></td>
                <td></td>
                <td></td>
                <td></td>
                <td>
                    <span id="add_perm" class="link">
                        ${_('Add user/user group')}
                    </span>
                </td>
                <td></td>
            </tr>
        </table>

        <div class="fields">
            <div class="field">
               <div class="label label-radio">
                   ${_('Apply to children')}:
               </div>
               <div class="radios">
                   ${h.radio('recursive', 'none', label=_('None'), checked="checked")}
                   ${h.radio('recursive', 'groups', label=_('Repository Groups'))}
                   ${h.radio('recursive', 'repos', label=_('Repositories'))}
                   ${h.radio('recursive', 'all', label=_('Both'))}
               <span class="help-block">${_('Set or revoke permissions to selected types of children of this group, including non-private repositories and other groups if chosen.')}</span>
               </div>
            </div>
        </div>
        <div class="buttons">
          ${h.submit('save',_('Save'),class_="btn btn-primary")}
          ${h.reset('reset',_('Reset'),class_="btn btn-danger")}
        </div>
        ${h.end_form()}
    </div>
</div>
<script type="text/javascript">
    $('#add_perm').on('click', function(e){
        addNewPermInput($(this), 'group');
    });
    $('.revoke_perm').on('click', function(e){
        markRevokePermInput($(this), 'group');
    });
    quick_repo_menu();
</script>
