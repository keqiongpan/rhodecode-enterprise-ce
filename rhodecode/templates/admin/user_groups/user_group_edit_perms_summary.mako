## permissions overview
<%namespace name="p" file="/base/perms_summary.mako"/>
${p.perms_summary(c.permissions, side_link=h.route_path('edit_user_group_perms_summary_json', user_group_id=c.user_group.users_group_id))}
