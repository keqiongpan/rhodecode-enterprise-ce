<div class="panel panel-default">
  <div class="panel-heading">
    <h3 class="panel-title">${_('Authentication Tokens')}</h3>
  </div>
  <div class="panel-body">
      <p>
         ${_('Each token can have a role. Token with a role can be used only in given context, '
         'e.g. VCS tokens can be used together with the authtoken auth plugin for git/hg/svn operations only.')}
          ${_('Additionally scope for VCS type token can narrow the use to chosen repository.')}
      </p>
      <table class="rctable auth_tokens">
        %if c.user_auth_tokens:
            <tr>
                <th>${_('Token')}</th>
                <th>${_('Scope')}</th>
                <th>${_('Description')}</th>
                <th>${_('Role')}</th>
                <th>${_('Expiration')}</th>
                <th>${_('Action')}</th>
            </tr>
            %for auth_token in c.user_auth_tokens:
              <tr class="${'expired' if auth_token.expired else ''}">
                <td class="truncate-wrap td-authtoken">
                    <div class="user_auth_tokens truncate autoexpand">
                    <code>${auth_token.api_key}</code>
                    </div>
                </td>
                <td class="td">${auth_token.scope_humanized}</td>
                <td class="td-wrap">${auth_token.description}</td>
                <td class="td-tags">
                    <span class="tag disabled">${auth_token.role_humanized}</span>
                </td>
                <td class="td-exp">
                     %if auth_token.expires == -1:
                      ${_('never')}
                     %else:
                        %if auth_token.expired:
                            <span style="text-decoration: line-through">${h.age_component(h.time_to_utcdatetime(auth_token.expires))}</span>
                        %else:
                            ${h.age_component(h.time_to_utcdatetime(auth_token.expires))}
                        %endif
                     %endif
                </td>
                <td class="td-action">
                    ${h.secure_form(url('my_account_auth_tokens'),method='delete')}
                        ${h.hidden('del_auth_token',auth_token.api_key)}
                        <button class="btn btn-link btn-danger" type="submit"
                                onclick="return confirm('${_('Confirm to remove this auth token: %s') % auth_token.api_key}');">
                            ${_('Delete')}
                        </button>
                    ${h.end_form()}
                </td>
              </tr>
            %endfor
        %else:
        <tr><td><div class="ip">${_('No additional auth token specified')}</div></td></tr>
        %endif
      </table>

        <div class="user_auth_tokens">
            ${h.secure_form(url('my_account_auth_tokens'), method='post')}
            <div class="form form-vertical">
                <!-- fields -->
                <div class="fields">
                     <div class="field">
                        <div class="label">
                            <label for="new_email">${_('New authentication token')}:</label>
                        </div>
                        <div class="input">
                            ${h.text('description', placeholder=_('Description'))}
                            ${h.select('lifetime', '', c.lifetime_options)}
                            ${h.select('role', '', c.role_options)}
                        </div>
                     </div>
                    <div class="buttons">
                      ${h.submit('save',_('Add'),class_="btn")}
                      ${h.reset('reset',_('Reset'),class_="btn")}
                    </div>
                </div>
            </div>
            ${h.end_form()}
        </div>
    </div>
</div>
    <script>
        $(document).ready(function(){
            var select2Options = {
                'containerCssClass': "drop-menu",
                'dropdownCssClass': "drop-menu-dropdown",
                'dropdownAutoWidth': true
            };
            $("#lifetime").select2(select2Options);
            $("#role").select2(select2Options);
        });
    </script>
