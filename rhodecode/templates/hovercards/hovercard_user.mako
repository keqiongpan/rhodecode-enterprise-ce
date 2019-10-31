<%namespace name="base" file="/base/base.mako"/>
<%namespace name="dt" file="/data_table/_dt_elements.mako"/>

<div class="user-hovercard">
    <div class="user-hovercard-header">

    </div>

    <div class="user-hovercard-icon">
        ${base.gravatar(c.user.email, 64)}
    </div>

    <div class="user-hovercard-name">
        <strong>${c.user.full_name_or_username}</strong> <br/>
        <code>@${h.link_to_user(c.user.username)}</code>

        <div class="user-hovercard-bio">${dt.render_description(c.user.description, c.visual.stylify_metatags)}</div>
    </div>

    <div class="user-hovercard-footer">

    </div>

</div>
