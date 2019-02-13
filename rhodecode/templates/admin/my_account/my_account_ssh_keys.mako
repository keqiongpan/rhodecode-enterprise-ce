<div class="panel panel-default">
    <div class="panel-heading">
      <h3 class="panel-title">${_('SSH Keys')}</h3>
    </div>
    <div class="panel-body">
        <div class="sshkeys_wrap">
          <table class="rctable ssh_keys">
            <tr>
                <th>${_('Fingerprint')}</th>
                <th>${_('Description')}</th>
                <th>${_('Created on')}</th>
                <th>${_('Accessed on')}</th>
                <th>${_('Action')}</th>
            </tr>
            % if not c.ssh_enabled:
                <tr><td colspan="4"><div class="">${_('SSH Keys usage is currently disabled, please ask your administrator to enable them.')}</div></td></tr>
            % else:
                %if c.user_ssh_keys:
                    %for ssh_key in c.user_ssh_keys:
                      <tr class="">
                        <td class="">
                            <code>${ssh_key.ssh_key_fingerprint}</code>
                        </td>
                        <td class="td-wrap">${ssh_key.description}</td>
                        <td class="td-tags">${h.format_date(ssh_key.created_on)}</td>
                        <td class="td-tags">${h.format_date(ssh_key.accessed_on)}</td>

                        <td class="td-action">
                            ${h.secure_form(h.route_path('my_account_ssh_keys_delete'), request=request)}
                                ${h.hidden('del_ssh_key', ssh_key.ssh_key_id)}
                                <button class="btn btn-link btn-danger" type="submit"
                                        onclick="return confirm('${_('Confirm to remove ssh key %s') % ssh_key.ssh_key_fingerprint}');">
                                    ${_('Delete')}
                                </button>
                            ${h.end_form()}
                        </td>
                      </tr>
                    %endfor
                %else:
                <tr><td colspan="4"><div class="">${_('No additional ssh keys specified')}</div></td></tr>
                %endif
            % endif
          </table>
        </div>

        % if c.ssh_enabled:
        <div class="user_ssh_keys">
            ${h.secure_form(h.route_path('my_account_ssh_keys_add'), request=request)}
            <div class="form form-vertical">
                <!-- fields -->
                <div class="fields">
                    <div class="field">
                        <div class="label">
                            <label for="new_email">${_('New ssh key')}:</label>
                        </div>
                        <div class="input">
                            ${h.text('description', class_='medium', placeholder=_('Description'))}
                            % if c.ssh_key_generator_enabled:
                                <a href="${h.route_path('my_account_ssh_keys_generate')}">${_('Generate random RSA key')}</a>
                            % endif
                        </div>
                     </div>

                    <div class="field">
                        <div class="textarea text-area editor">
                            ${h.textarea('key_data',c.default_key, size=30, placeholder=_("Public key, begins with 'ssh-rsa', 'ssh-dss', 'ssh-ed25519', 'ecdsa-sha2-nistp256', 'ecdsa-sha2-nistp384', or 'ecdsa-sha2-nistp521'"))}
                        </div>
                    </div>

                    <div class="buttons">
                      ${h.submit('save',_('Add'),class_="btn")}
                      ${h.reset('reset',_('Reset'),class_="btn")}
                    </div>
                    % if c.default_key:
                        ${_('Click add to use this generated SSH key')}
                    % endif
                </div>
            </div>
            ${h.end_form()}
        </div>
        % endif
    </div>
</div>

<script>

$(document).ready(function(){


});
</script>
