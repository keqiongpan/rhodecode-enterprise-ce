<%namespace name="base" file="/base/base.mako"/>
<div class="panel panel-default user-profile">
    <div class="panel-heading">
        <h3 class="panel-title">${_('My Profile')}</h3>
        <a href="${h.route_path('my_account_edit')}" class="panel-edit">${_('Edit')}</a>
    </div>

    <div class="panel-body fields">
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