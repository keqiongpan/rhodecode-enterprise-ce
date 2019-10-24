<%namespace name="base" file="/base/base.mako"/>

<%
 elems = [
    (_('User ID'), c.user.user_id, '', ''),
    (_('Created on'), h.format_date(c.user.created_on), '', ''),
    (_('Source of Record'), c.user.extern_type, '', ''),

    (_('Last login'), c.user.last_login or '-', '', ''),
    (_('Last activity'), c.user.last_activity, '', ''),

    (_('Repositories'), len(c.user.repositories), '', [x.repo_name for x in c.user.repositories]),
    (_('Repository groups'), len(c.user.repository_groups), '', [x.group_name for x in c.user.repository_groups]),
    (_('User groups'), len(c.user.user_groups), '', [x.users_group_name for x in c.user.user_groups]),

    (_('Owned Artifacts'), len(c.user.artifacts), '', [x.file_uid for x in c.user.artifacts]),

    (_('Reviewer of pull requests'), len(c.user.reviewer_pull_requests), '', ['Pull Request #{}'.format(x.pull_request.pull_request_id) for x in c.user.reviewer_pull_requests]),
    (_('Assigned to review rules'), len(c.user_to_review_rules), '', [x for x in c.user_to_review_rules]),

    (_('Member of User groups'), len(c.user.group_member), '', [x.users_group.users_group_name for x in c.user.group_member]),
    (_('Force password change'), c.user.user_data.get('force_password_change', 'False'), '', ''),
 ]
%>

<div class="panel panel-default">
    <div class="panel-heading">
        <h3 class="panel-title">${_('User: {}').format(c.user.username)}</h3>
    </div>
    <div class="panel-body">
        <table class="rctable">
            <tr>
                <th>Name</th>
                <th>Value</th>
                <th>Action</th>
            </tr>
            % for elem in elems:
                ${base.tr_info_entry(elem)}
            % endfor
        </table>
    </div>
</div>

<div class="panel panel-default">
    <div class="panel-heading">
        <h3 class="panel-title">${_('Force Password Reset')}</h3>
    </div>
    <div class="panel-body">
        ${h.secure_form(h.route_path('user_disable_force_password_reset', user_id=c.user.user_id), request=request)}
            <div class="field">
                <button class="btn btn-default" type="submit">
                    <i class="icon-unlock"></i> ${_('Disable forced password reset')}
                </button>
            </div>
            <div class="field">
                <span class="help-block">
                    ${_("Clear the forced password change flag.")}
                </span>
            </div>
        ${h.end_form()}

        ${h.secure_form(h.route_path('user_enable_force_password_reset', user_id=c.user.user_id), request=request)}
            <div class="field">
                <button class="btn btn-default" type="submit" onclick="return confirm('${_('Confirm to enable forced password change')}');">
                    <i class="icon-lock"></i> ${_('Enable forced password reset')}
                </button>
            </div>
            <div class="field">
                <span class="help-block">
                    ${_("When this is enabled user will have to change they password when they next use RhodeCode system. This will also forbid vcs operations until someone makes a password change in the web interface")}
                </span>
            </div>
        ${h.end_form()}

    </div>
</div>

<div class="panel panel-default">
    <div class="panel-heading">
        <h3 class="panel-title">${_('Personal Repository Group')}</h3>
    </div>
    <div class="panel-body">
        ${h.secure_form(h.route_path('user_create_personal_repo_group', user_id=c.user.user_id), request=request)}

        %if c.personal_repo_group:
            <div class="panel-body-title-text">${_('Users personal repository group')} : ${h.link_to(c.personal_repo_group.group_name, h.route_path('repo_group_home', repo_group_name=c.personal_repo_group.group_name))}</div>
        %else:
            <div class="panel-body-title-text">
                ${_('This user currently does not have a personal repository group')}
                <br/>
                ${_('New group will be created at: `/%(path)s`') % {'path': c.personal_repo_group_name}}
            </div>
        %endif
            <button class="btn btn-default" type="submit" ${'disabled="disabled"' if c.personal_repo_group else ''}>
                <i class="icon-repo-group"></i>
                ${_('Create personal repository group')}
            </button>
        ${h.end_form()}
    </div>
</div>


<div class="panel panel-danger">
    <div class="panel-heading">
        <h3 class="panel-title">${_('Delete User')}</h3>
    </div>
    <div class="panel-body">
        ${h.secure_form(h.route_path('user_delete', user_id=c.user.user_id), request=request)}

            <table class="display rctable">
                <tr>
                    <td>
                        ${_ungettext('This user owns %s repository.', 'This user owns %s repositories.', len(c.user.repositories)) % len(c.user.repositories)}
                    </td>
                    <td>
                        <input type="radio" id="user_repos_1" name="user_repos" value="detach" checked="checked" ${'disabled=1' if len(c.user.repositories) == 0 else ''} /> <label for="user_repos_1">${_('Detach repositories')}</label>
                    </td>
                    <td>
                        <input type="radio" id="user_repos_2" name="user_repos" value="delete" ${'disabled=1' if len(c.user.repositories) == 0 else ''} /> <label for="user_repos_2">${_('Delete repositories')}</label>
                    </td>
                </tr>

                <tr>
                    <td>
                        ${_ungettext('This user owns %s repository group.', 'This user owns %s repository groups.', len(c.user.repository_groups)) % len(c.user.repository_groups)}
                    </td>
                    <td>
                        <input type="radio" id="user_repo_groups_1" name="user_repo_groups" value="detach" checked="checked" ${'disabled=1' if len(c.user.repository_groups) == 0 else ''} /> <label for="user_repo_groups_1">${_('Detach repository groups')}</label>
                    </td>
                    <td>
                        <input type="radio" id="user_repo_groups_2" name="user_repo_groups" value="delete" ${'disabled=1' if len(c.user.repository_groups) == 0 else ''}/> <label for="user_repo_groups_2">${_('Delete repositories')}</label>
                    </td>
                </tr>

                <tr>
                    <td>
                        ${_ungettext('This user owns %s user group.', 'This user owns %s user groups.', len(c.user.user_groups)) % len(c.user.user_groups)}
                    </td>
                    <td>
                        <input type="radio" id="user_user_groups_1" name="user_user_groups" value="detach" checked="checked" ${'disabled=1' if len(c.user.user_groups) == 0 else ''}/> <label for="user_user_groups_1">${_('Detach user groups')}</label>
                    </td>
                    <td>
                        <input type="radio" id="user_user_groups_2" name="user_user_groups" value="delete" ${'disabled=1' if len(c.user.user_groups) == 0 else ''}/> <label for="user_user_groups_2">${_('Delete repositories')}</label>
                    </td>
                </tr>

                <tr>
                    <td>
                        ${_ungettext('This user owns %s artifact.', 'This user owns %s artifacts.', len(c.user.artifacts)) % len(c.user.artifacts)}
                    </td>
                    <td>
                        <input type="radio" id="user_artifacts_1" name="user_artifacts" value="detach" checked="checked" ${'disabled=1' if len(c.user.artifacts) == 0 else ''}/> <label for="user_artifacts_1">${_('Detach Artifacts')}</label>
                    </td>
                    <td>
                        <input type="radio" id="user_artifacts_2" name="user_artifacts" value="delete" ${'disabled=1' if len(c.user.artifacts) == 0 else ''}/> <label for="user_artifacts_2">${_('Delete Artifacts')}</label>
                    </td>
                </tr>

            </table>
            <div style="margin: 0 0 20px 0" class="fake-space"></div>
            <div class="pull-left">
                % if len(c.user.repositories) > 0 or len(c.user.repository_groups) > 0 or len(c.user.user_groups) > 0:
                % endif

                <span style="padding: 0 5px 0 0">${_('New owner for detached objects')}:</span>
                <div class="pull-right">${base.gravatar_with_user(c.first_admin.email, 16)}</div>
            </div>
            <div style="clear: both">

            <div>
            <p class="help-block">
                ${_("When selecting the detach option, the depending objects owned by this user will be assigned to the above user.")}
                <br/>
                ${_("The delete option will delete the user and all his owned objects!")}
            </p>
            </div>

            % if c.can_delete_user_message:
            <p class="pre-formatting">${c.can_delete_user_message}</p>
            % endif
            </div>

            <div style="margin: 0 0 20px 0" class="fake-space"></div>

            <div class="field">
                <button class="btn btn-small btn-danger" type="submit"
                        onclick="return confirm('${_('Confirm to delete this user: %s') % c.user.username}');"
                        ${"disabled" if not c.can_delete_user else ""}>
                    ${_('Delete this user')}
                </button>
            </div>

        ${h.end_form()}
    </div>
</div>
