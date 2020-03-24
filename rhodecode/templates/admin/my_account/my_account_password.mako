<%namespace name="widgets" file="/widgets.mako"/>

<%widgets:panel title="${_('Change Your Account Password')}">

% if c.extern_type != 'rhodecode':
    <p>${_('Your user account details are managed by an external source. Details cannot be managed here.')}
    <br/>${_('For VCS access please generate')}
        <a href="${h.route_path('my_account_auth_tokens', _query={'token_role':'token_role_vcs'})}">Authentication Token</a> or <a href="${h.route_path('my_account_ssh_keys_generate')}">SSH Key</a>.
    <br/>${_('Source type')}: <strong>${c.extern_type}</strong>
    </p>
% else:
    ${c.form.render() | n}
% endif

</%widgets:panel>
