<%namespace name="base" file="/base/base.mako"/>

<%
 elems = [
    (_('User Group ID'), c.user_group.users_group_id, '', ''),
    (_('Owner'), lambda:base.gravatar_with_user(c.user_group.user.email), '', ''),
    (_('Created on'), h.format_date(c.user_group.created_on), '', '',),

    (_('Members'), len(c.group_members_obj),'', [x for x in c.group_members_obj]),
    (_('Automatic member sync'), 'Yes' if c.user_group.group_data.get('extern_type') else 'No', '', '',),

    (_('Assigned to repositories'), len(c.group_to_repos),'', [x for x in c.group_to_repos]),
    (_('Assigned to repo groups'), len(c.group_to_repo_groups), '', [x for x in c.group_to_repo_groups]),

    (_('Assigned to review rules'), len(c.group_to_review_rules), '', [x for x in c.group_to_review_rules]),
 ]
%>

<div class="panel panel-default">
    <div class="panel-heading">
        <h3 class="panel-title">
            <i class="icon-user-group" title="${_('User group')}"></i>
            ${h.link_to_group(c.user_group.users_group_name)}
            - ${_('Advanced')}
        </h3>
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
                ${_('This group synchronization was set by')}: <strong>${sync_type}</strong>
            </p>
        % else:
            <p>
                ${_('This group is not set to be automatically synchronised')}
            </p>
        % endif

        <div>
        ${h.secure_form(h.route_path('edit_user_group_advanced_sync', user_group_id=c.user_group.users_group_id), request=request)}
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
                    ${_('Users will be added or removed from this group when they authenticate with RhodeCode system, based on LDAP group membership. '
                        'This requires `LDAP+User group` authentication plugin to be configured and enabled. (EE only feature)')}
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
        ${h.secure_form(h.route_path('user_groups_delete', user_group_id=c.user_group.users_group_id), request=request)}
            ${h.hidden('force', 1)}
            <button class="btn btn-small btn-danger" type="submit"
                    onclick="return confirm('${_('Confirm to delete user group `%(ugroup)s` with all permission assignments') % {'ugroup': c.user_group.users_group_name}}');">
                <i class="icon-remove"></i>
                ${_('Delete This User Group')}
            </button>
        ${h.end_form()}
    </div>
</div>
