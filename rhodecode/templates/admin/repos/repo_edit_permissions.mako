<%namespace name="base" file="/base/base.mako"/>

<div class="panel panel-default">
    <div class="panel-heading">
        <h3 class="panel-title">${_('Repository Permissions')}</h3>
    </div>
    <div class="panel-body">
        ${h.secure_form(h.route_path('edit_repo_perms', repo_name=c.repo_name), request=request)}
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
            %for _user in c.rhodecode_db_repo.permissions():
                %if getattr(_user, 'admin_row', None) or getattr(_user, 'owner_row', None):
                    <tr class="perm_admin_row">
                        <td class="td-radio">${h.radio('admin_perm_%s' % _user.user_id,'repository.none', disabled="disabled")}</td>
                        <td class="td-radio">${h.radio('admin_perm_%s' % _user.user_id,'repository.read', disabled="disabled")}</td>
                        <td class="td-radio">${h.radio('admin_perm_%s' % _user.user_id,'repository.write', disabled="disabled")}</td>
                        <td class="td-radio">${h.radio('admin_perm_%s' % _user.user_id,'repository.admin', 'repository.admin', disabled="disabled")}</td>
                        <td class="td-user">
                            ${base.gravatar(_user.email, 16)}
                            ${h.link_to_user(_user.username)}
                            %if getattr(_user, 'admin_row', None):
                                (${_('super admin')})
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
                                     ${h.link_to('show permissions', h.route_path('edit_user_perms_summary', user_id=_user.user_id, _anchor='repositories-permissions'))}
                                  </li>
                                </ul>
                                </div>
                            % endif
                        </td>
                    </tr>
                %elif _user.username == h.DEFAULT_USER and c.rhodecode_db_repo.private:
                    <tr>
                        <td colspan="4">
                            <span class="private_repo_msg">
                            <strong title="${h.tooltip(_user.permission)}">${_('private repository')}</strong>
                            </span>
                        </td>
                        <td class="private_repo_msg">
                            ${base.gravatar(h.DEFAULT_USER_EMAIL, 16)}
                            ${h.DEFAULT_USER} - ${_('only users/user groups explicitly added here will have access')}</td>
                        <td></td>
                        <td class="quick_repo_menu">
                            % if c.rhodecode_user.is_admin:
                                <i class="icon-more"></i>
                                <div class="menu_items_container" style="display: none;">
                                <ul class="menu_items">
                                  <li>
                                     ${h.link_to('show permissions', h.route_path('admin_permissions_overview', _anchor='repositories-permissions'))}
                                  </li>
                                </ul>
                                </div>
                            % endif
                        </td>
                    </tr>
                %else:
                    <% used_by_n_rules = len(getattr(_user, 'branch_rules', None) or []) %>
                    <tr>
                        <td class="td-radio">${h.radio('u_perm_%s' % _user.user_id,'repository.none', checked=_user.permission=='repository.none', disabled="disabled" if (used_by_n_rules and _user.username != h.DEFAULT_USER) else None)}</td>
                        <td class="td-radio">${h.radio('u_perm_%s' % _user.user_id,'repository.read', checked=_user.permission=='repository.read', disabled="disabled" if (used_by_n_rules and _user.username != h.DEFAULT_USER) else None)}</td>
                        <td class="td-radio">${h.radio('u_perm_%s' % _user.user_id,'repository.write', checked=_user.permission=='repository.write')}</td>
                        <td class="td-radio">${h.radio('u_perm_%s' % _user.user_id,'repository.admin', checked=_user.permission=='repository.admin')}</td>
                        <td class="td-user">
                            ${base.gravatar(_user.email, 16)}
                            <span class="user">
                                % if _user.username == h.DEFAULT_USER:
                                    ${h.DEFAULT_USER} <span class="user-perm-help-text"> - ${_('permission for all other users')}</span>
                                % else:
                                    ${h.link_to_user(_user.username)}
                                    %if getattr(_user, 'duplicate_perm', None):
                                        (${_('inactive duplicate')})
                                    %endif
                                    %if getattr(_user, 'branch_rules', None):
                                        % if used_by_n_rules == 1:
                                            (${_('used by {} branch rule, requires write+ permissions').format(used_by_n_rules)})
                                        % else:
                                            (${_('used by {} branch rules, requires write+ permissions').format(used_by_n_rules)})
                                        % endif
                                    %endif
                                % endif
                            </span>
                        </td>
                        <td class="td-action">
                          %if _user.username != h.DEFAULT_USER and getattr(_user, 'branch_rules', None) is None:
                            <span class="btn btn-link btn-danger revoke_perm"
                                  member="${_user.user_id}" member_type="user">
                            ${_('Remove')}
                            </span>
                          %elif _user.username == h.DEFAULT_USER:
                            <span class="tooltip btn btn-link btn-default" onclick="enablePrivateRepo(); return false" title="${_('Private repositories are only visible to people explicitly added as collaborators.')}">
                            ${_('set private mode')}
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
                                        ${h.link_to('show permissions', h.route_path('admin_permissions_overview', _anchor='repositories-permissions'))}
                                    % else:
                                        ${h.link_to('show permissions', h.route_path('edit_user_perms_summary', user_id=_user.user_id, _anchor='repositories-permissions'))}
                                    % endif
                                  </li>
                                </ul>
                                </div>
                            % endif
                        </td>
                    </tr>
                %endif
            %endfor

            ## USER GROUPS
            %for _user_group in c.rhodecode_db_repo.permission_user_groups(with_members=True):
                <tr>
                    <td class="td-radio">${h.radio('g_perm_%s' % _user_group.users_group_id,'repository.none', checked=_user_group.permission=='repository.none')}</td>
                    <td class="td-radio">${h.radio('g_perm_%s' % _user_group.users_group_id,'repository.read', checked=_user_group.permission=='repository.read')}</td>
                    <td class="td-radio">${h.radio('g_perm_%s' % _user_group.users_group_id,'repository.write', checked=_user_group.permission=='repository.write')}</td>
                    <td class="td-radio">${h.radio('g_perm_%s' % _user_group.users_group_id,'repository.admin', checked=_user_group.permission=='repository.admin')}</td>
                    <td class="td-componentname">
                        <i class="icon-user-group"></i>
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
                        <span class="btn btn-link btn-danger revoke_perm"
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
                                 ${h.link_to('show permissions', h.route_path('edit_user_group_perms_summary', user_group_id=_user_group.users_group_id, _anchor='repositories-permissions'))}
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

        <div class="buttons">
          ${h.submit('save',_('Save'),class_="btn btn-primary")}
          ${h.reset('reset',_('Reset'),class_="btn btn-danger")}
        </div>
        ${h.end_form()}
    </div>
</div>

<script type="text/javascript">
    $('#add_perm').on('click', function(e){
        addNewPermInput($(this), 'repository');
    });
    $('.revoke_perm').on('click', function(e){
        markRevokePermInput($(this), 'repository');
    });
    quick_repo_menu();

    var enablePrivateRepo = function () {
        var postData = {
            'csrf_token': CSRF_TOKEN
        };

        var success = function(o) {
            var defaultUrl = pyroutes.url('edit_repo_perms', {"repo_name": templateContext.repo_name});
            window.location = o.redirect_url || defaultUrl;
        };

        ajaxPOST(
            pyroutes.url('edit_repo_perms_set_private', {"repo_name": templateContext.repo_name}),
            postData,
            success);
    }
</script>
