## -*- coding: utf-8 -*-
<%inherit file="base/root.mako"/>

<%def name="title()">
    ${_('Reset Password')}
    %if c.rhodecode_name:
        &middot; ${h.branding(c.rhodecode_name)}
    %endif
</%def>
<style>body{background-color:#eeeeee;}</style>

<div class="loginbox">
    <div class="header">
        <div id="header-inner" class="title">
            <div id="logo">
                <div class="logo-wrapper">
                    <a href="${h.route_path('home')}"><img src="${h.asset('images/rhodecode-logo-white-216x60.png')}" alt="RhodeCode"/></a>
                </div>
                %if c.rhodecode_name:
                <div class="branding"> ${h.branding(c.rhodecode_name)}</div>
                %endif
            </div>
        </div>
    </div>

    <div class="loginwrapper">
        <rhodecode-toast id="notifications"></rhodecode-toast>
        <div class="left-column">
            <img class="sign-in-image" src="${h.asset('images/sign-in.png')}" alt="RhodeCode"/>
        </div>

        %if h.HasPermissionAny('hg.password_reset.disabled')():
            <div class="right-column">
                <p>
                    ${_('Password reset is disabled. Please contact ')}
                    % if c.visual.rhodecode_support_url:
                        <a href="${c.visual.rhodecode_support_url}" target="_blank">${_('Support')}</a>
                        ${_('or')}
                    % endif
                    ${_('an administrator if you need help.')}
                </p>
            </div>
        %else:
            <div id="register" class="right-column">
                <!-- login -->
                <div class="sign-in-title">
                    <h1>${_('Reset your Password')}</h1>
                    <h4>${h.link_to(_("Go to the login page to sign in."), request.route_path('login'))}</h4>
                </div>
                <div class="inner form">
                    ${h.form(request.route_path('reset_password'), needs_csrf_token=False)}
                        <label for="email">${_('Email Address')}:</label>
                        ${h.text('email', defaults.get('email'))}
                        %if 'email' in errors:
                          <span class="error-message">${errors.get('email')}</span>
                          <br />
                        %endif
                        <p class="help-block">${_('Password reset link will be sent to matching email address')}</p>
    
                        %if captcha_active:
                        <div class="login-captcha">
                            <label for="email">${_('Captcha')}:</label>
                            ${h.hidden('recaptcha_field')}
                            <div id="recaptcha"></div>

                            %if 'recaptcha_field' in errors:
                              <span class="error-message">${errors.get('recaptcha_field')}</span>
                              <br />
                            %endif
                        </div>
                        %endif
    
                        ${h.submit('send', _('Send password reset email'), class_="btn sign-in")}
                        <p class="help-block pull-right">
                            RhodeCode ${c.rhodecode_edition}
                        </p>
    
                    ${h.end_form()}
                </div>
            </div>
        %endif
    </div>
</div>

<script type="text/javascript">
 $(document).ready(function(){
    $('#email').focus();
 });
</script>

% if captcha_active:
<script type="text/javascript">
var onloadCallback = function() {
    grecaptcha.render('recaptcha', {
      'sitekey' : "${captcha_public_key}"
    });
};
</script>
<script src="https://www.google.com/recaptcha/api.js?onload=onloadCallback&render=explicit" async defer></script>
% endif

