<%namespace name="dpb" file="/base/default_perms_box.mako"/>
${dpb.default_perms_box(form_url=h.route_path('edit_user_group_global_perms_update', user_group_id=c.user_group.users_group_id))}

