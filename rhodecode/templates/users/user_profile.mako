<%namespace name="base" file="/base/base.mako"/>
<%namespace name="dt" file="/data_table/_dt_elements.mako"/>

<div class="panel panel-default user-profile">
    <div class="panel-heading">
        <h3 class="panel-title">${_('User Profile')}</h3>
        %if c.is_super_admin:
            ${h.link_to(_('Edit'), h.route_path('user_edit', user_id=c.user.user_id), class_='panel-edit')}
        %endif
    </div>

    <div class="panel-body user-profile-content fields">
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
                ${_('First name')}:
            </div>
            <div class="input">
                <div class="text-as-placeholder">
                    ${c.user.first_name}
                </div>
            </div>
        </div>
        <div class="field">
            <div class="label">
                ${_('Last name')}:
            </div>
            <div class="input">
                <div class="text-as-placeholder">
                    ${c.user.last_name}
                </div>
            </div>
        </div>
        <div class="field">
            <div class="label">
                ${_('Description')}:
            </div>
            <div class="input">
                <div class="text-as-placeholder">
                    ${dt.render_description(c.user.description, c.visual.stylify_metatags)}
                </div>
            </div>
        </div>
        <div class="field">
            <div class="label">
                ${_('Email')}:
            </div>
            <div class="input">
                <div class="text-as-placeholder">
                    ${(c.user.email or _('Missing email, please update your user email address.'))}
                </div>
            </div>
        </div>
    </div>
</div>