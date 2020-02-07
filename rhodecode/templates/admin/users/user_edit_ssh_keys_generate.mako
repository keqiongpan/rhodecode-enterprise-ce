<%namespace name="base" file="/base/base.mako"/>

<div class="panel panel-default">
    <div class="panel-heading">
         <h3 class="panel-title">
          ${base.gravatar_with_user(c.user.username, 16, tooltip=False, _class='pull-left')}
          &nbsp;- ${_('New SSH Key generation')}
         </h3>
    </div>
    <div class="panel-body">
        %if c.ssh_enabled and c.ssh_key_generator_enabled:
            <p>
                ${_('Below is a 2048 bit generated SSH RSA key.')}<br/>
                ${_('If You wish to use it to access RhodeCode via the SSH please save the private key and click `Use this generated key` at the bottom.')}
            </p>
            <h4>${_('Private key')}</h4>
            <pre>
# Save the below content as
# Windows: /Users/{username}/.ssh/id_rsa_rhodecode_access_priv.key
# macOS: /Users/{yourname}/.ssh/id_rsa_rhodecode_access_priv.key
# Linux: /home/{username}/.ssh/id_rsa_rhodecode_access_priv.key

# Change permissions to 0600 to make it secure, and usable.
e.g chmod 0600 /home/{username}/.ssh/id_rsa_rhodecode_access_priv.key
            </pre>

            <div>
                <textarea style="height: 300px">${c.private}</textarea>
            </div>
            <br/>

            <h4>${_('Public key')}</h4>
            <pre>
# Save the below content as
# Windows: /Users/{username}/.ssh/id_rsa_rhodecode_access_pub.key
# macOS: /Users/{yourname}/.ssh/id_rsa_rhodecode_access_pub.key
# Linux: /home/{username}/.ssh/id_rsa_rhodecode_access_pub.key
            </pre>

            <input type="text" value="${c.public}" class="large text" size="100"/>
            <p>
                % if hasattr(c, 'target_form_url'):
                    <a href="${c.target_form_url}">${_('Use this generated key')}.</a>
                % else:
                    <a href="${h.route_path('edit_user_ssh_keys', user_id=c.user.user_id, _query=dict(default_key=c.public))}">${_('Use this generated key')}.</a>
                % endif
                ${_('Confirmation required on the next screen')}.
            </p>
        % else:
            <h2>
                ${_('SSH key generator has been disabled.')}
            </h2>
        % endif
    </div>
</div>

<script>

$(document).ready(function(){


});
</script>
