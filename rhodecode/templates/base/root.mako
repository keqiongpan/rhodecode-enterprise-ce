## -*- coding: utf-8 -*-
<!DOCTYPE html>

<%
c.template_context['repo_name'] = getattr(c, 'repo_name', '')
go_import_header = ''
if hasattr(c, 'rhodecode_db_repo'):
    c.template_context['repo_type'] = c.rhodecode_db_repo.repo_type
    c.template_context['repo_landing_commit'] = c.rhodecode_db_repo.landing_rev[1]
    c.template_context['repo_id'] = c.rhodecode_db_repo.repo_id
    c.template_context['repo_view_type'] = h.get_repo_view_type(request)

if getattr(c, 'repo_group', None):
    c.template_context['repo_group_id'] = c.repo_group.group_id
    c.template_context['repo_group_name'] = c.repo_group.group_name

if getattr(c, 'rhodecode_user', None) and c.rhodecode_user.user_id:
    c.template_context['rhodecode_user']['username'] = c.rhodecode_user.username
    c.template_context['rhodecode_user']['email'] = c.rhodecode_user.email
    c.template_context['rhodecode_user']['notification_status'] = c.rhodecode_user.get_instance().user_data.get('notification_status', True)
    c.template_context['rhodecode_user']['first_name'] = c.rhodecode_user.first_name
    c.template_context['rhodecode_user']['last_name'] = c.rhodecode_user.last_name

c.template_context['visual']['default_renderer'] = h.get_visual_attr(c, 'default_renderer')
c.template_context['default_user'] = {
    'username': h.DEFAULT_USER,
    'user_id': 1
}
c.template_context['search_context'] = {
    'repo_group_id': c.template_context.get('repo_group_id'),
    'repo_group_name': c.template_context.get('repo_group_name'),
    'repo_id': c.template_context.get('repo_id'),
    'repo_name': c.template_context.get('repo_name'),
    'repo_view_type': c.template_context.get('repo_view_type'),
}

%>
<html xmlns="http://www.w3.org/1999/xhtml">
    <head>
        <title>${self.title()}</title>
        <meta http-equiv="Content-Type" content="text/html;charset=utf-8" />

        ${h.go_import_header(request, getattr(c, 'rhodecode_db_repo', None))}

        % if 'safari' in (request.user_agent or '').lower():
            <meta name="referrer" content="origin">
        % else:
            <meta name="referrer" content="origin-when-cross-origin">
        % endif

        <%def name="robots()">
            <meta name="robots" content="index, nofollow"/>
        </%def>
        ${self.robots()}
        <link rel="icon" href="${h.asset('images/favicon.ico', ver=c.rhodecode_version_hash)}" sizes="16x16 32x32" type="image/png" />
        <script src="${h.asset('js/vendors/webcomponentsjs/custom-elements-es5-adapter.js', ver=c.rhodecode_version_hash)}"></script>
        <script src="${h.asset('js/vendors/webcomponentsjs/webcomponents-bundle.js', ver=c.rhodecode_version_hash)}"></script>

        ## CSS definitions
        <%def name="css()">
            <link rel="stylesheet" type="text/css" href="${h.asset('css/style.css', ver=c.rhodecode_version_hash)}" media="screen"/>
            ## EXTRA FOR CSS
            ${self.css_extra()}
        </%def>
        ## CSS EXTRA - optionally inject some extra CSS stuff needed for specific websites
        <%def name="css_extra()">
        </%def>

        ${self.css()}

        ## JAVASCRIPT
        <%def name="js()">

            <script src="${h.asset('js/rhodecode/i18n/%s.js' % c.language, ver=c.rhodecode_version_hash)}"></script>
            <script type="text/javascript">
            // register templateContext to pass template variables to JS
            var templateContext = ${h.json.dumps(c.template_context)|n};

            var APPLICATION_URL = "${h.route_path('home').rstrip('/')}";
            var APPLICATION_PLUGINS = [];
            var ASSET_URL = "${h.asset('')}";
            var DEFAULT_RENDERER = "${h.get_visual_attr(c, 'default_renderer')}";
            var CSRF_TOKEN = "${getattr(c, 'csrf_token', '')}";

            var APPENLIGHT = {
              enabled: ${'true' if getattr(c, 'appenlight_enabled', False) else 'false'},
              key: '${getattr(c, "appenlight_api_public_key", "")}',
              % if getattr(c, 'appenlight_server_url', None):
                  serverUrl: '${getattr(c, "appenlight_server_url", "")}',
              % endif
              requestInfo: {
              % if getattr(c, 'rhodecode_user', None):
                  ip: '${c.rhodecode_user.ip_addr}',
                  username: '${c.rhodecode_user.username}'
              % endif
              },
              tags: {
                  rhodecode_version: '${c.rhodecode_version}',
                  rhodecode_edition: '${c.rhodecode_edition}'
              }
            };

            </script>
            <%include file="/base/plugins_base.mako"/>
            <!--[if lt IE 9]>
            <script language="javascript" type="text/javascript" src="${h.asset('js/src/excanvas.min.js')}"></script>
            <![endif]-->
            <script language="javascript" type="text/javascript" src="${h.asset('js/rhodecode/routes.js', ver=c.rhodecode_version_hash)}"></script>
            <script> var alertMessagePayloads = ${h.flash.json_alerts(request=request)|n}; </script>
            ## avoide escaping the %N
            <script language="javascript" type="text/javascript" src="${h.asset('js/scripts.js', ver=c.rhodecode_version_hash)}"></script>
            <script>CodeMirror.modeURL = "${h.asset('') + 'js/mode/%N/%N.js?ver='+c.rhodecode_version_hash}";</script>


            ## JAVASCRIPT EXTRA - optionally inject some extra JS for specificed templates
            ${self.js_extra()}

            <script type="text/javascript">
            Rhodecode = (function() {
                function _Rhodecode() {
                  this.comments = new CommentsController();
                }
                return new _Rhodecode();
            })();

            $(document).ready(function(){
              show_more_event();
              timeagoActivate();
              clipboardActivate();
            })
            </script>

        </%def>

        ## JAVASCRIPT EXTRA - optionally inject some extra JS for specificed templates
        <%def name="js_extra()"></%def>
        ${self.js()}

        <%def name="head_extra()"></%def>
        ${self.head_extra()}
        ## extra stuff
        %if c.pre_code:
            ${c.pre_code|n}
        %endif
    </head>
    <body id="body">
        <noscript>
            <div class="noscript-error">
                ${_('Please enable JavaScript to use RhodeCode Enterprise')}
            </div>
        </noscript>

      ${next.body()}
      %if c.post_code:
        ${c.post_code|n}
      %endif
    <rhodecode-app></rhodecode-app>
    </body>
</html>
