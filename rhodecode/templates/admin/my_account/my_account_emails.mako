<%namespace name="base" file="/base/base.mako"/>

<div class="panel panel-default">
  <div class="panel-heading">
    <h3 class="panel-title">${_('Account Emails')}</h3>
  </div>

    <div class="panel-body">
        <div class="emails_wrap">
          <table class="rctable account_emails">
            <tr>
            <td class="td-user">
                ${base.gravatar(c.user.email, 16)}
                <span class="user email">${c.user.email}</span>
            </td>
            <td class="td-tags">
                <span class="tag tag1">${_('Primary')}</span>
            </td>
            </tr>
            %if c.user_email_map:
                %for em in c.user_email_map:
                  <tr>
                    <td class="td-user">
                        ${base.gravatar(em.email, 16)}
                        <span class="user email">${em.email}</span>
                    </td>
                    <td class="td-action">
                        ${h.secure_form(h.route_path('my_account_emails_delete'), request=request)}
                            ${h.hidden('del_email_id',em.email_id)}
                            <button class="btn btn-link btn-danger" type="submit" id="${'remove_email_%s'.format(em.email_id)}"
                                    onclick="return confirm('${_('Confirm to delete this email: {}').format(em.email)}');">
                                ${_('Delete')}
                            </button>
                        ${h.end_form()}
                    </td>
                  </tr>
                %endfor
            %else:
                <tr class="noborder">
                    <td colspan="3">
                        <div class="td-email">
                            ${_('No additional emails specified')}
                        </div>
                    </td>
                </tr>
            %endif
          </table>
        </div>

    % if c.user.extern_type != 'rhodecode':
        <p>${_('Your user account details are managed by an external source. Details cannot be managed here.')}
           <br/>${_('Source type')}: <strong>${c.user.extern_type}</strong>
        </p>
    % else:
        <div>
           ${c.form.render() | n}
        </div>
    % endif
    </div>
</div>
