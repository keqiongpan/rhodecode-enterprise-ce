## permissions overview
<%namespace name="p" file="/base/perms_summary.mako"/>
${p.perms_summary(c.perm_user.permissions_full_details, show_all=True, side_link=h.route_path('edit_user_perms_summary_json', user_id=c.user.user_id))}
