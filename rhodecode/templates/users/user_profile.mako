<%namespace name="base" file="/base/base.mako"/>

<div class="panel panel-default user-profile">
    <div class="panel-heading">
        <h3 class="panel-title">${_('User Profile')}</h3>
        %if h.HasPermissionAny('hg.admin')():
            ${h.link_to(_('Edit'), h.route_path('user_edit', user_id=c.user.user_id), class_='panel-edit')}
        %endif
    </div>

    <div class="panel-body user-profile-content">
        <div class="fieldset">
            <div class="left-label">
                ${_('Photo')}:
            </div>
            <div class="right-content">
                %if c.visual.use_gravatar:
                    ${base.gravatar(c.user.email, 100)}
                %else:
                    ${base.gravatar(c.user.email, 20)}
                    ${_('Avatars are disabled')}
                %endif
            </div>
        </div>
        <div class="fieldset">
            <div class="left-label">
                ${_('Username')}:
            </div>
            <div class="right-content">
                ${c.user.username}
            </div>
        </div>
        <div class="fieldset">
            <div class="left-label">
                ${_('First name')}:
            </div>
            <div class="right-content">
                ${c.user.first_name}
            </div>
        </div>
        <div class="fieldset">
            <div class="left-label">
                ${_('Last name')}:
            </div>
            <div class="right-content">
                ${c.user.last_name}
            </div>
        </div>
        <div class="fieldset">
            <div class="left-label">
                ${_('Email')}:
            </div>
            <div class="right-content">
                ${c.user.email or _('Missing email, please update your user email address.')}
            </div>
        </div>
    </div>
</div>