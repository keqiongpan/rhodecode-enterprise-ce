${h.secure_form(h.route_path('admin_settings_global_update'), request=request)}

<div class="panel panel-default">
    <div class="panel-heading" id="branding-options">
        <h3 class="panel-title">${_('Branding')} <a class="permalink" href="#branding-options"> ¶</a></h3>
    </div>
    <div class="panel-body">
        <div class="label">
            <label for="rhodecode_title">${_('Title')}</label>
        </div>
        <div class="field input">
            ${h.text('rhodecode_title',size=60)}
        </div>
        <div class="field">
            <span class="help-block">
                ${_('Set a custom title for your RhodeCode instance (limited to 40 characters).')}
            </span>
        </div>
        <div class="label">
            <label for="rhodecode_realm">${_('HTTP[S] authentication realm')}</label>
        </div>
        <div class="field input">
            ${h.text('rhodecode_realm',size=60)}
        </div>
        <div class="field">
            <span class="help-block">
                ${_('Set a custom text that is shown as authentication message to clients trying to connect.')}
            </span>
        </div>
    </div>
</div>


<div class="panel panel-default">
    <div class="panel-heading" id="personal-group-options">
        <h3 class="panel-title">${_('Personal Repository Group')} <a class="permalink" href="#personal-group-options"> ¶</a></h3>
    </div>
    <div class="panel-body">
        <div class="checkbox">
            ${h.checkbox('rhodecode_create_personal_repo_group','True')}
            <label for="rhodecode_create_personal_repo_group">${_('Create Personal Repository Group')}</label>
        </div>
        <span class="help-block">
            ${_('Always create Personal Repository Groups for new users.')} <br/>
            ${_('When creating new users from add user form or API you can still turn this off via a checkbox or flag')}
        </span>

        <div class="label">
            <label for="rhodecode_personal_repo_group_pattern">${_('Personal Repo Group Pattern')}</label>
        </div>
        <div class="field input">
            ${h.text('rhodecode_personal_repo_group_pattern',size=60, placeholder=c.personal_repo_group_default_pattern)}
        </div>
        <span class="help-block">
            ${_('Pattern used to create Personal Repository Groups. Prefix can be other existing repository group path[s], eg. /u/${username}')} <br/>
            ${_('Available variables are currently ${username} and ${user_id}')}
        </span>
    </div>
</div>


<div class="panel panel-default">
    <div class="panel-heading" id="captcha-options">
        <h3 class="panel-title">${_('Registration Captcha')} <a class="permalink" href="#captcha-options"> ¶</a></h3>
    </div>
    <div class="panel-body">
        <div class="label">
            <label for="rhodecode_captcha_public_key">${_('Google reCaptcha v2 site key.')}</label>
        </div>
        <div class="field input">
            ${h.text('rhodecode_captcha_public_key',size=60)}
        </div>
        <div class="field">
            <span class="help-block">
                ${_('Site key for reCaptcha v2 system.')}
            </span>
        </div>

        <div class="label">
            <label for="rhodecode_captcha_private_key">${_('Google reCaptcha v2 secret key.')}</label>
        </div>
        <div class="field input">
            ${h.text('rhodecode_captcha_private_key',size=60)}
        </div>
        <div class="field">
            <span class="help-block">
                ${_('Secret key for reCaptcha v2 system. Setting this value will enable captcha on registration and password reset forms.')}
            </span>
        </div>
    </div>
</div>

<div class="panel panel-default">
    <div class="panel-heading" id="header-code-options">
        <h3 class="panel-title">${_('Custom Header Code')} <a class="permalink" href="#header-code-options"> ¶</a></h3>
    </div>
    <div class="panel-body">
        <div class="select">
            <select id="pre_template" >
                <option value="#">${_('Templates...')}</option>
                <option value="ga">Google Analytics</option>
                <option value="clicky">Clicky</option>
                <option value="server_announce">${_('Server Announcement')}</option>
                <option value="flash_filtering">${_('Flash message filtering')}</option>
                <option value="custom_logo">${_('Custom logos')}</option>
            </select>
        </div>
        <div style="padding: 10px 0px"></div>
        <div class="textarea text-area">
            ${h.textarea('rhodecode_pre_code',cols=23,rows=5,class_="medium")}
            <span class="help-block">${_('Custom js/css code added at the end of the <head/> tag.')}
                         ${_('Use <script/> or <style/> tags to define custom scripting or styling.')}</span>
        </div>
    </div>
</div>

<div class="panel panel-default">
    <div class="panel-heading" id="footer-code-options">
        <h3 class="panel-title">${_('Custom Footer Code')} <a class="permalink" href="#footer-code-options"> ¶</a></h3>
    </div>
    <div class="panel-body">
        <div class="select">
            <select id="post_template" >
                <option value="#">${_('Templates...')}</option>
                <option value="ga">Google Analytics</option>
                <option value="clicky">Clicky</option>
                <option value="server_announce">${_('Server Announcement')}</option>
            </select>
        </div>
        <div style="padding: 10px 0px"></div>
        <div class="textarea text-area">
            ${h.textarea('rhodecode_post_code',cols=23,rows=5, class_="medium")}
            <span class="help-block">${_('Custom js/css code added at the end of the <body> tag.')}
                        ${_('Use <script> or <style> tags to define custom scripting or styling.')}</span>
        </div>
    </div>
</div>

<div class="buttons">
    ${h.submit('save',_('Save settings'),class_="btn")}
    ${h.reset('reset',_('Reset'),class_="btn")}
</div>
${h.end_form()}



## TEMPLATES ##
###############

<script id="ga_tmpl" type="text/x-template">
<%text filter="h">
<script>
 // Google Analytics
 // Put your Google Analytics code instead of _GACODE_
 var _gaq_code = '_GACODE_';
 var _gaq = _gaq || [];
 _gaq.push(['_setAccount', _gaq_code]);
 _gaq.push(['_trackPageview']);

 (function() {
  var ga = document.createElement('script'); ga.type = 'text/javascript'; ga.async = true;
  ga.src = ('https:' == document.location.protocol ? 'https://ssl' : 'http://www') + '.google-analytics.com/ga.js';
  var s = document.getElementsByTagName('script')[0]; s.parentNode.insertBefore(ga, s);
 })();

 rhodecode_statechange_callback = function(url, data){
  // ANALYTICS callback on html5 history state changed
  // triggered by file browser, url is the new url,
  // data is extra info passed from the State object
  if (typeof window._gaq !== 'undefined') {
    _gaq.push(['_trackPageview', url]);
  }
 };
</script>
</%text>
</script>



<script id="clicky_tmpl" type="text/x-template">
<%text filter="h">
<script src="//static.getclicky.com/js" type="text/javascript"></script>
<script type="text/javascript">
 // Clicky Analytics - should be used in the footer code section.
 // Put your Clicky code instead of _CLICKYCODE_ here,
 // and below in the <img> tag.
 var _cl_code = _CLICKYCODE_;
 try{clicky.init(_cl_code);}catch(e){}

 rhodecode_statechange_callback = function(url, data){
  // ANALYTICS callback on html5 history state changed
  // triggered by file browser, url is the new url,
  // data is extra info passed from the State object
  if (typeof window.clicky !== 'undefined') {
   clicky.log(url);
  }
}
</script>
<noscript>
// Put your clicky code in the src file.
<p><img alt="Clicky" width="1" height="1"
        src="//in.getclicky.com/_CLICKYCODE_ns.gif" /></p>
</noscript>
</%text>
</script>



<script id="server_announce_tmpl" type='text/x-template'>
<%text filter="h">
<script>
// Server announcement displayed on the top of the page.
// This can be used to send a global maintenance messages or other
// important messages to all users of the RhodeCode Enterprise system.

$(document).ready(function(e) {

 // EDIT - put your message below
 var message = "TYPE YOUR MESSAGE HERE";

 // EDIT - choose "info"/"warning"/"error"/"success"/"neutral" as appropriate
 var alert_level = "info";

 $("#body").prepend(
  ("<div id='server-announcement' class='"+alert_level+"'>_MSG_"+"</div>").replace("_MSG_", message)
 )
})
</script>
</%text>
</script>

<script id="flash_filtering_tmpl" type='text/x-template'>
<%text filter="h">
<script>
    // This filters out some flash messages before they are presented to user
    // based on their contents. Could be used to filter out warnings/errors
    // of license messages

    var filteredMessages = [];
    for(var i =0; i< alertMessagePayloads.length; i++){
        if (typeof alertMessagePayloads[i].message.subdata.subtype !== 'undefined' &&
                alertMessagePayloads[i].message.subdata.subtype.indexOf('rc_license') !== -1){
            continue
        }
        filteredMessages.push(alertMessagePayloads[i]);
    }
    alertMessagePayloads = filteredMessages;
</script>
</%text>
</script>


<script id="custom_logo_tmpl" type='text/x-template'>
<%text filter="h">
<script>

$(document).ready(function(e) {
    // 1) Set custom logo on login/register pages.

    // external URL, custom company logo
    //$('.sign-in-image').attr("src", "http://server.com/logo_path/custom_logo.png");

    // Alternative logo from static folder
    $('.sign-in-image').attr("src", "/_static/rhodecode/images/RhodeCode_Logo_Black.png");

    // option to set width/height, adjust if required to make your image look good.
    $('.sign-in-image').css({"width": "300px", "height": "345px"});

    // 2) Header logo on top bar
    $('.logo-wrapper').find('img').attr('src', 'http://server.com/logo_path/custom_header_logo.png')

});
</script>
</%text>
</script>


<script>
var pre_cm = initCodeMirror('rhodecode_pre_code', '', false);
var pre_old = pre_cm.getValue();

var post_cm = initCodeMirror('rhodecode_post_code', '', false);
var post_old = post_cm.getValue();

var get_data = function(type, old) {
    var get_tmpl = function(tmpl_name){
        // unescape some stuff
        return htmlEnDeCode.htmlDecode($('#'+tmpl_name+'_tmpl').html());
    };
    return {
        '#': old,
        'ga': get_tmpl('ga'),
        'clicky': get_tmpl('clicky'),
        'server_announce': get_tmpl('server_announce'),
        'flash_filtering': get_tmpl('flash_filtering'),
        'custom_logo': get_tmpl('custom_logo')
    }[type]
};

$('#pre_template').select2({
    containerCssClass: 'drop-menu',
    dropdownCssClass: 'drop-menu-dropdown',
    dropdownAutoWidth: true,
    minimumResultsForSearch: -1
});

$('#post_template').select2({
    containerCssClass: 'drop-menu',
    dropdownCssClass: 'drop-menu-dropdown',
    dropdownAutoWidth: true,
    minimumResultsForSearch: -1
});

$('#post_template').on('change', function(e){
    var sel = this.value;
    post_cm.setValue(get_data(sel, post_old))
});

$('#pre_template').on('change', function(e){
    var sel = this.value;
    pre_cm.setValue(get_data(sel, pre_old))
})
</script>
