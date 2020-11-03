## -*- coding: utf-8 -*-
<%inherit file="base/root.mako"/>

<%def name="title()">
    ${_('Sign In')}
    %if c.rhodecode_name:
        &middot; ${h.branding(c.rhodecode_name)}
    %endif
</%def>

<style>body{background-color:#eeeeee;}</style>
<div class="loginbox">
    <div class="header-account">
        <div id="header-inner" class="title">
            <div id="logo">
                <div class="logo-wrapper">
                    <a href="${h.route_path('home')}"><img src="${h.asset('images/rhodecode-logo-white-60x60.png')}" alt="RhodeCode"/></a>
                </div>
                % if c.rhodecode_name:
                <div class="branding">
                   <a href="${h.route_path('home')}">${h.branding(c.rhodecode_name)}</a>
                </div>
                % endif
            </div>
        </div>
    </div>

    <div class="loginwrapper">
        <rhodecode-toast id="notifications"></rhodecode-toast>

        <div class="left-column">
            <img class="sign-in-image" src="${h.asset('images/sign-in.png')}" alt="RhodeCode"/>
        </div>

        <div id="login" class="right-column">
            <%block name="above_login_button" />
            <!-- login -->
            <div class="sign-in-title">
                <h1>${_('Sign In using username/password')}</h1>
            </div>
            <div class="inner form">
                ${h.form(request.route_path('login', _query={'came_from': c.came_from}), needs_csrf_token=False)}

                    <label for="username">${_('Username')}:</label>
                    ${h.text('username', class_='focus', value=defaults.get('username'))}
                    %if 'username' in errors:
                    <span class="error-message">${errors.get('username')}</span>
                    <br />
                    %endif

                    <label for="password">${_('Password')}:
                    %if h.HasPermissionAny('hg.password_reset.enabled')():
                        <div class="pull-right">${h.link_to(_('Forgot your password?'), h.route_path('reset_password'), class_='pwd_reset', tabindex="-1")}</div>
                    %endif

                    </label>
                    ${h.password('password', class_='focus')}
                    %if 'password' in errors:
                    <span class="error-message">${errors.get('password')}</span>
                    <br />
                    %endif

                    ${h.checkbox('remember', value=True, checked=defaults.get('remember'))}
                    <% timeout = request.registry.settings.get('beaker.session.timeout', '0') %>
                    % if timeout == '0':
                        <% remember_label = _('Remember my indefinitely') %>
                    % else:
                        <% remember_label = _('Remember me for {}').format(h.age_from_seconds(timeout)) %>
                    % endif
                    <label class="checkbox" for="remember">${remember_label}</label>

                    <p class="links">
                    %if h.HasPermissionAny('hg.admin', 'hg.register.auto_activate', 'hg.register.manual_activate')():
                        ${h.link_to(_("Create a new account."), request.route_path('register'), class_='new_account')}
                    %endif
                    </p>

                    %if not h.HasPermissionAny('hg.password_reset.enabled')():
                        ## password reset hidden or disabled.
                        <p class="help-block">
                            ${_('Password reset is disabled.')} <br/>
                            ${_('Please contact ')}
                            % if c.visual.rhodecode_support_url:
                                <a href="${c.visual.rhodecode_support_url}" target="_blank">${_('Support')}</a>
                                ${_('or')}
                            % endif
                            ${_('an administrator if you need help.')}
                        </p>
                    %endif

                    ${h.submit('sign_in', _('Sign In'), class_="btn sign-in", title=_('Sign in to {}').format(c.rhodecode_edition))}

                ${h.end_form()}
                <script type="text/javascript">
                    $(document).ready(function(){
                        $('#username').focus();
                    })
                </script>

            </div>
            <!-- end login -->

            <%block name="below_login_button" />
        </div>
    </div>
</div>
