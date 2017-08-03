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
                <th>${_('Created')}</th>
                <th>${_('Action')}</th>
            </tr>
            %if c.user_ssh_keys:
                %for ssh_key in c.user_ssh_keys:
                  <tr class="">
                    <td class="">
                        <code>${ssh_key.ssh_key_fingerprint}</code>
                    </td>
                    <td class="td-wrap">${ssh_key.description}</td>
                    <td class="td-tags">${h.format_date(ssh_key.created_on)}</td>

                    <td class="td-action">
                        ${h.secure_form(h.route_path('edit_user_ssh_keys_delete', user_id=c.user.user_id), method='POST', request=request)}
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
            <tr><td><div class="ip">${_('No additional ssh keys specified')}</div></td></tr>
            %endif
          </table>
        </div>

        <div class="user_ssh_keys">
            ${h.secure_form(h.route_path('edit_user_ssh_keys_add', user_id=c.user.user_id), method='POST', request=request)}
            <div class="form form-vertical">
                <!-- fields -->
                <div class="fields">
                    <div class="field">
                        <div class="label">
                            <label for="new_email">${_('New ssh key')}:</label>
                        </div>
                        <div class="input">
                            ${h.text('description', class_='medium', placeholder=_('Description'))}
                            <a href="${h.route_path('edit_user_ssh_keys_generate_keypair', user_id=c.user.user_id)}">${_('Generate random RSA key')}</a>
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
                </div>
            </div>
            ${h.end_form()}
        </div>
    </div>
</div>

<script>

$(document).ready(function(){


});
</script>
