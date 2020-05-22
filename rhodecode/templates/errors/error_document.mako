## -*- coding: utf-8 -*-
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml">
    <head>
        <title>Error - ${c.error_message}</title>
        <meta http-equiv="Content-Type" content="text/html;charset=utf-8" />
        <meta name="robots" content="index, nofollow"/>

        <meta http-equiv="Content-Type" content="text/html;charset=utf-8" />
        %if c.redirect_time:
            <meta http-equiv="refresh" content="${c.redirect_time}; url=${c.url_redirect}"/>
        %endif

        <link id="favicon" rel="shortcut icon" type="image/png" href="data:image/png;base64,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">
        <script src="${h.asset('js/vendors/webcomponentsjs/custom-elements-es5-adapter.js', ver=c.rhodecode_version_hash)}"></script>
        <script src="${h.asset('js/vendors/webcomponentsjs/webcomponents-bundle.js', ver=c.rhodecode_version_hash)}"></script>

        <link rel="stylesheet" type="text/css" href="${h.asset('css/style.css', ver=c.rhodecode_version_hash)}" media="screen"/>
        <style>body { background:#eeeeee; }</style>
        <script type="text/javascript">
            // register templateContext to pass template variables to JS
            var templateContext = {timeago: {}};
        </script>
        <%include file="/base/plugins_base.mako"/>
        <script type="text/javascript" src="${h.asset('js/scripts.min.js', ver=c.rhodecode_version_hash)}"></script>
    </head>
    <body>

        <div class="wrapper error_page">
            <div class="sidebar">
                <a href="${h.route_path('home')}"><img class="error-page-logo" src="${h.asset('images/RhodeCode_Logo_Black.png')}" alt="RhodeCode"/></a>
            </div>
            <div class="main-content">
                <h1>
                    <span class="error-branding">
                        ${h.branding(c.rhodecode_name)}
                    </span><br/>
                    ${c.error_message}
                    <br/>
                    <span class="error_message">${c.error_explanation}</span>
                </h1>
                % if c.messages:
                    % for message in c.messages:
                        <div class="alert alert-${message.category}">${message}</div>
                    % endfor
                % endif    
                %if c.redirect_time:
                    <p>${_('You will be redirected to %s in %s seconds') % (c.redirect_module,c.redirect_time)}</p>
                %endif
                <div class="inner-column">
                    <h4>Possible Causes</h4>
                    <ul>
                    % if c.causes:
                        %for cause in c.causes:
                            <li>${cause}</li>
                        %endfor
                    %else:
                        <li>The resource may have been deleted.</li>
                        <li>You may not have access to this repository.</li>
                        <li>The link may be incorrect.</li>
                    %endif
                    </ul>
                </div>
                <div class="inner-column">
                    <h4>Support</h4>
                    <p>For help and support, go to the <a href="${c.visual.rhodecode_support_url}" target="_blank">${_('Support Page')}</a>.
                       It may be useful to include your log file; see the log file locations <a href="${h.route_url('enterprise_log_file_locations')}">here</a>.
                    </p>

                </div>
                <div class="inner-column">
                    <h4>Documentation</h4>
                    <p>For more information, see <a href="${h.route_url('enterprise_docs')}">docs.rhodecode.com</a>.</p>
                </div>
            </div>

            % if c.show_exception_id:
            <div class="sidebar" style="width: 130px">

            </div>
            <div class="main-content">
                <p>
                <strong>Exception ID: <code><a href="${c.exception_id_url}">${c.exception_id}</a></code> </strong> <br/>

                Super-admins can see detailed traceback information from this exception by checking the below Exception ID.<br/>
                Please include the above link for further details of this exception.
                </p>
            </div>
            % endif
        </div>

    </body>

</html>
