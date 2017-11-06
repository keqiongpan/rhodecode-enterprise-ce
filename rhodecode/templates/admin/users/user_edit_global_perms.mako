<%namespace name="dpb" file="/base/default_perms_box.mako"/>
${dpb.default_perms_box(form_url=h.route_path('user_edit_global_perms_update', user_id=c.user.user_id))}
