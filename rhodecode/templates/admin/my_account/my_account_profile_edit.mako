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
        <% disabled = "disabled" %>
        <div class="infoform">
          <div class="fields">
            <p>${_('Your user account details are managed by an external source. Details cannot be managed here.')}
               <br/>${_('Source type')}: <strong>${c.extern_type}</strong>
            </p>

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