<%namespace name="base" file="/base/base.mako"/>
<div class="panel panel-default user-profile">
    <div class="panel-heading">
        <h3 class="panel-title">${_('My Profile')}</h3>
        <a href="${h.route_path('my_account_profile')}" class="panel-edit">Close</a>
    </div>

    <div class="panel-body">
    <% readonly = None %>
    <% disabled = "" %>

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

    %if c.extern_type != 'rhodecode':
        <div class="infoform">
          <div class="fields">
            <div class="field">
               <div class="label">
                   <label for="username">${_('Username')}:</label>
               </div>
               <div class="input">
                 ${c.user.username}
               </div>
            </div>
    
            <div class="field">
               <div class="label">
                   <label for="name">${_('First Name')}:</label>
               </div>
               <div class="input">
                    ${c.user.firstname}
               </div>
            </div>
    
            <div class="field">
               <div class="label">
                   <label for="lastname">${_('Last Name')}:</label>
               </div>
               <div class="input-valuedisplay">
                    ${c.user.lastname}
               </div>
            </div>
          </div>
        </div>
    % else:
        <div class="form">
          <div class="fields">
            <div class="field">
                <div class="label photo">
                    ${_('Photo')}:
                </div>
                <div class="input profile">
                    %if c.visual.use_gravatar:
                        ${base.gravatar(c.user.email, 100)}
                        <p class="help-block">${_('Change your avatar at')} <a href="http://gravatar.com">gravatar.com</a>.</p>
                    %else:
                        ${base.gravatar(c.user.email, 100)}
                    %endif
                </div>
            </div>
                ${c.form.render()| n}
          </div>
        </div>
    % endif
    </div>
</div>