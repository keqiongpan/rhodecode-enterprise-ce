<%namespace name="base" file="/base/base.mako"/>

<div class="panel panel-default user-profile">
    <div class="panel-heading">
        <h3 class="panel-title">${_('User Group Profile')}</h3>
        %if c.is_super_admin:
            ${h.link_to(_('Edit'), h.route_path('edit_user_group', user_group_id=c.user_group.users_group_id), class_='panel-edit')}
        %endif
    </div>

    <div class="panel-body user-profile-content fields">
        <div class="field">
            <div class="label">
                ${_('Group Name')}:
            </div>
            <div class="input">
                <div class="text-as-placeholder">
                ${c.user_group.users_group_name}
                </div>
            </div>
        </div>
        <div class="field">
            <div class="label">
                ${_('Owner')}:
            </div>
            <div class="group_member">
                ${base.gravatar(c.user_group.user.email, 16)}
                <span class="username user">${h.link_to_user(c.user_group.user)}</span>

            </div>
        </div>
        <div class="field">
            <div class="label">
                ${_('Active')}:
            </div>
            <div class="input">
                <div class="text-as-placeholder">
                ${c.user_group.users_group_active}
                </div>
            </div>
        </div>
        % if not c.anonymous:
        <div class="field">
                <div class="label">
                    ${_('Members')}:
                </div>

            <div class="input">
                <div class="text-as-placeholder">
                <table id="group_members_placeholder" class="rctable group_members">
                    <th>${_('Username')}</th>
                    % if c.group_members:
                      % for user in c.group_members:
                        <tr>
                          <td id="member_user_${user.user_id}" class="td-author">
                            <div class="group_member">
                              ${base.gravatar(user.email, 16)}
                              <span class="username user">${h.link_to(h.person(user), h.route_path('user_edit',user_id=user.user_id))}</span>
                              <input type="hidden" name="__start__" value="member:mapping">
                              <input type="hidden" name="member_user_id" value="${user.user_id}">
                              <input type="hidden" name="type" value="existing" id="member_${user.user_id}">
                              <input type="hidden" name="__end__" value="member:mapping">
                            </div>
                          </td>
                        </tr>
                      % endfor
                    % else:
                      <tr><td colspan="2">${_('No members yet')}</td></tr>
                    % endif
                </table>
                </div>
            </div>
        </div>
        % endif
    </div>
</div>