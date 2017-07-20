
${h.secure_form(h.route_path('admin_permissions_global_update'), method='POST', request=request)}
    <div class="form permissions-global">
        <!-- fields -->
        <div class="fields">
            <%namespace name="dpb" file="/base/default_perms_box.mako"/>
            ${dpb.default_perms_radios(global_permissions_template = True)}
        </div>
    </div>
${h.end_form()}
