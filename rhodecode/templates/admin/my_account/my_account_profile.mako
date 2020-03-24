<%namespace name="base" file="/base/base.mako"/>
<%namespace name="dt" file="/data_table/_dt_elements.mako"/>

<div class="panel panel-default user-profile">
    <div class="panel-heading">
        <h3 class="panel-title">${_('My Profile')}</h3>
        <a href="${h.route_path('my_account_edit')}" class="panel-edit">${_('Edit')}</a>
    </div>

    <div class="panel-body fields">
        %if c.extern_type != 'rhodecode':
            <% readonly = "readonly" %>
            <% disabled = " disabled" %>
            <div class="alert-warning" style="margin:0px 0px 20px 0px; padding: 10px">
                <strong>${_('This user was created from external source (%s). Editing some of the settings is limited.' % c.extern_type)}</strong>
            </div>
            <div style="margin:-10px 0px 20px 0px;">
                ${_('For VCS access please generate')}
                <a href="${h.route_path('my_account_auth_tokens', _query={'token_role':'token_role_vcs'})}">Authentication Token</a> or <a href="${h.route_path('my_account_ssh_keys_generate')}">SSH Key</a>.
            </div>
        %endif
        <div class="field">
            <div class="label">
                ${_('Photo')}:
            </div>
            <div class="input">
                <div class="text-as-placeholder">
                    %if c.visual.use_gravatar:
                        ${base.gravatar(c.user.email, 100)}
                    %else:
                        ${base.gravatar(c.user.email, 100)}
                    %endif
                </div>
            </div>
        </div>
        <div class="field">
            <div class="label">
                ${_('Username')}:
            </div>
            <div class="input">
                <div class="text-as-placeholder">
                    ${c.user.username}
                </div>
            </div>
        </div>
        <div class="field">
            <div class="label">
                ${_('First Name')}:
            </div>
            <div class="input">
                <div class="text-as-placeholder">
                    ${c.user.first_name}
                </div>
            </div>
        </div>
        <div class="field">
            <div class="label">
                ${_('Last Name')}:
            </div>
            <div class="input">
                <div class="text-as-placeholder">
                    ${c.user.last_name}
                </div>
            </div>
        </div>
        <div class="field">
            <div class="label">
                ${_('Description')}:
            </div>
            <div class="input">
                <div class="text-as-placeholder">
                    ${dt.render_description(c.user.description, c.visual.stylify_metatags)}
                </div>
            </div>
        </div>
        <div class="field">
            <div class="label">
                ${_('Email')}:
            </div>
            <div class="input">
                <div class="text-as-placeholder">
                    ${c.user.email or _('Missing email, please update your user email address.')}
                </div>
            </div>
        </div>
    </div>
</div>