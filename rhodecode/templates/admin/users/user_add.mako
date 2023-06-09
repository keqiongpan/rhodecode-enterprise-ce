## -*- coding: utf-8 -*-
<%inherit file="/base/base.mako"/>

<%def name="title()">
    ${_('Add user')}
    %if c.rhodecode_name:
        &middot; ${h.branding(c.rhodecode_name)}
    %endif
</%def>
<%def name="breadcrumbs_links()">
    ${h.link_to(_('Admin'),h.route_path('admin_home'))}
    &raquo;
    ${h.link_to(_('Users'),h.route_path('users'))}
    &raquo;
    ${_('Add User')}
</%def>

<%def name="menu_bar_nav()">
    ${self.menu_items(active='admin')}
</%def>

<%def name="main()">
<div class="box">
    <!-- box / title -->
    <div class="title">
        ${self.breadcrumbs()}
    </div>
    <!-- end box / title -->
    ${h.secure_form(h.route_path('users_create'), request=request)}
    <div class="form">
        <!-- fields -->
        <div class="fields">
             <div class="field">
                <div class="label">
                    <label for="username">${_('Username')}:</label>
                </div>
                <div class="input">
                    ${h.text('username', class_='medium')}
                </div>
             </div>

             <div class="field">
                <div class="label">
                    <label for="password">${_('Password')}:</label>
                </div>
                <div class="input">
                    ${h.password('password', class_='medium')}
                </div>
             </div>

             <div class="field">
                <div class="label">
                    <label for="password_confirmation">${_('Password confirmation')}:</label>
                </div>
                <div class="input">
                    ${h.password('password_confirmation',autocomplete="off", class_='medium')}
                    <div class="info-block">
                        <a id="generate_password" href="#">
                            <i class="icon-lock"></i> ${_('Generate password')}
                        </a>
                        <span id="generate_password_preview"></span>
                    </div>
                </div>
             </div>

             <div class="field">
                <div class="label">
                    <label for="firstname">${_('First Name')}:</label>
                </div>
                <div class="input">
                    ${h.text('firstname', class_='medium')}
                </div>
             </div>

             <div class="field">
                <div class="label">
                    <label for="lastname">${_('Last Name')}:</label>
                </div>
                <div class="input">
                    ${h.text('lastname', class_='medium')}
                </div>
             </div>

             <div class="field">
                <div class="label">
                    <label for="email">${_('Email')}:</label>
                </div>
                <div class="input">
                    ${h.text('email', class_='medium')}
                    ${h.hidden('extern_name', c.default_extern_type)}
                    ${h.hidden('extern_type', c.default_extern_type)}
                </div>
             </div>

             <div class="field">
                <div class="label label-checkbox">
                    <label for="active">${_('Active')}:</label>
                </div>
                <div class="checkboxes">
                    ${h.checkbox('active',value=True,checked='checked')}
                </div>
             </div>

            <div class="field">
                <div class="label label-checkbox">
                    <label for="password_change">${_('Password change')}:</label>
                </div>
                <div class="checkboxes">
                    ${h.checkbox('password_change',value=True)}
                    <span class="help-block">${_('Force user to change his password on the next login')}</span>
                </div>
             </div>

            <div class="field">
                <div class="label label-checkbox">
                    <label for="create_repo_group">${_('Add personal repository group')}:</label>
                </div>
                <div class="checkboxes">
                    ${h.checkbox('create_repo_group',value=True, checked=c.default_create_repo_group)}
                    <span class="help-block">
                        ${_('New group will be created at: `/{path}`').format(path=c.personal_repo_group_name)}<br/>
                        ${_('User will be automatically set as this group owner.')}
                    </span>
                </div>
             </div>

            <div class="buttons">
              ${h.submit('save',_('Create User'),class_="btn")}
            </div>
        </div>
    </div>
    ${h.end_form()}
</div>
<script>
    $(document).ready(function(){
        $('#username').focus();

        $('#generate_password').on('click', function(e){
            var tmpl = "(${_('generated password:')} {0})";
            var new_passwd = generatePassword(12);
            $('#generate_password_preview').html(tmpl.format(new_passwd));
            $('#password').val(new_passwd);
            $('#password_confirmation').val(new_passwd);
        })
    })
</script>
</%def>
