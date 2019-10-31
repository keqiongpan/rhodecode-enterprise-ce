<%namespace name="base" file="/base/base.mako"/>
<%namespace name="dt" file="/data_table/_dt_elements.mako"/>

<div class="user-group-hovercard">
    <div class="user-group-hovercard-header">

    </div>

    <div class="user-group-hovercard-icon">
        ${base.user_group_icon(c.user_group, 64)}
    </div>

    <div class="user-group-hovercard-name">
        <strong><a href="${h.route_path('user_group_profile', user_group_name=c.user_group.users_group_name)}">${c.user_group.users_group_name}</a></strong> <br/>
        Members: ${len(c.user_group.members)}

        <div class="user-group-hovercard-bio">${dt.render_description(c.user_group.user_group_description, c.visual.stylify_metatags)}</div>
    </div>

    <div class="user-group-hovercard-footer">

    </div>

</div>
