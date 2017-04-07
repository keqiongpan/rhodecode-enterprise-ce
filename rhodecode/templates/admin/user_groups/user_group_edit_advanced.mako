<%namespace name="base" file="/base/base.mako"/>

<%
 elems = [
    (_('Owner'), lambda:base.gravatar_with_user(c.user_group.user.email), '', ''),
    (_('Created on'), h.format_date(c.user_group.created_on), '', '',),

    (_('Members'), len(c.group_members_obj),'', [x for x in c.group_members_obj]),
    (_('Automatic member sync'), 'Yes' if c.user_group.group_data.get('extern_type') else 'No', '', '',),

    (_('Assigned to repositories'), len(c.group_to_repos),'', [x for x in c.group_to_repos]),
    (_('Assigned to repo groups'), len(c.group_to_repo_groups), '', [x for x in c.group_to_repo_groups]),

 ]
%>

<div class="panel panel-default">
    <div class="panel-heading">
        <h3 class="panel-title">${_('User Group: %s') % c.user_group.users_group_name}</h3>
    </div>
    <div class="panel-body">
        ${base.dt_info_panel(elems)}
    </div>

</div>

<div class="panel panel-default">
    <div class="panel-heading">
        <h3 class="panel-title">${_('Group members sync')}</h3>
    </div>
    <div class="panel-body">
        <% sync_type = c.user_group.group_data.get('extern_type') %>

        % if sync_type:
            <p>
                ${_('This group is set to be automatically synchronised.')}<br/>
                ${_('Each member will be added or removed from this groups once they interact with RhodeCode system.')}<br/>
                ${_('This group synchronization was set by')}: <strong>${sync_type}</strong>
            </p>
        % else:
            <p>
                ${_('This group is not set to be automatically synchronised')}
            </p>
        % endif

        <div>
        ${h.secure_form(h.url('edit_user_group_advanced_sync', user_group_id=c.user_group.users_group_id), method='post')}
            <div class="field">
                <button class="btn btn-default" type="submit">
                    %if sync_type:
                        ${_('Disable synchronization')}
                    %else:
                        ${_('Enable synchronization')}
                    %endif
                </button>
            </div>
            <div class="field">
                <span class="help-block">
                    %if sync_type:
                        ${_('User group will no longer synchronize membership')}
                    %else:
                        ${_('User group will start to synchronize membership')}
                    %endif
                </span>
            </div>
        ${h.end_form()}
        </div>

    </div>
</div>


<div class="panel panel-danger">
    <div class="panel-heading">
        <h3 class="panel-title">${_('Delete User Group')}</h3>
    </div>
    <div class="panel-body">
        ${h.secure_form(h.url('delete_users_group', user_group_id=c.user_group.users_group_id),method='delete')}
            ${h.hidden('force', 1)}
            <button class="btn btn-small btn-danger" type="submit"
                    onclick="return confirm('${_('Confirm to delete user group `%(ugroup)s` with all permission assignments') % {'ugroup': c.user_group.users_group_name}}');">
                <i class="icon-remove-sign"></i>
                ${_('Delete This User Group')}
            </button>
        ${h.end_form()}
    </div>
</div>
