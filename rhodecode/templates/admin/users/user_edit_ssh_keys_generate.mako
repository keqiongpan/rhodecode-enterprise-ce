<div class="panel panel-default">
    <div class="panel-heading">
      <h3 class="panel-title">${_('New SSH Key generated')}</h3>
    </div>
    <div class="panel-body">
        <p>
            ${_('Below is a 2048 bit generated SSH RSA key. You can use it to access RhodeCode via the SSH wrapper.')}
        </p>
        <h4>${_('Private key')}</h4>
        <pre>
# Save the content as
~/.ssh/id_rsa_rhodecode_access_priv.key
# Change permissions
chmod 0600 ~/.ssh/id_rsa_rhodecode_access_priv.key
        </pre>

        <div>
            <textarea style="height: 300px">${c.private}</textarea>
        </div>
        <br/>


        <h4>${_('Public key')}</h4>
        <pre>
# Save the content as
~/.ssh/id_rsa_rhodecode_access_pub.key
# Change permissions
chmod 0600 ~/.ssh/id_rsa_rhodecode_access_pub.key
        </pre>

        <input type="text" value="${c.public}" class="large text" size="100"/>
        <p>
            % if hasattr(c, 'target_form_url'):
                <a href="${c.target_form_url}">${_('Add this generated key')}</a>
            % else:
                <a href="${h.route_path('edit_user_ssh_keys', user_id=c.user.user_id, _query=dict(default_key=c.public))}">${_('Add this generated key')}</a>
            % endif
        </p>
    </div>
</div>

<script>

$(document).ready(function(){


});
</script>