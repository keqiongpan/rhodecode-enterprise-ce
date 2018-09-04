## -*- coding: utf-8 -*-
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml">
    <head>
        <title>Error - ${c.error_message}</title>
        <meta http-equiv="Content-Type" content="text/html;charset=utf-8" />
        <meta name="robots" content="index, nofollow"/>
        <link rel="icon" href="${h.asset('images/favicon.ico')}" sizes="16x16 32x32" type="image/png" />

        <meta http-equiv="Content-Type" content="text/html;charset=utf-8" />
        %if c.redirect_time:
            <meta http-equiv="refresh" content="${c.redirect_time}; url=${c.url_redirect}"/>
        %endif

        <link rel="stylesheet" type="text/css" href="${h.asset('css/style.css', ver=c.rhodecode_version_hash)}" media="screen"/>
        <!--[if IE]>
            <link rel="stylesheet" type="text/css" href="${h.asset('css/ie.css')}" media="screen"/>
        <![endif]-->
        <style>body { background:#eeeeee; }</style>
        <script type="text/javascript">
            // register templateContext to pass template variables to JS
            var templateContext = {timeago: {}};
        </script>
        <script type="text/javascript" src="${h.asset('js/scripts.js', ver=c.rhodecode_version_hash)}"></script>
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
                    ${c.error_message} | <span class="error_message">${c.error_explanation}</span>
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

                Super Admins can see detailed traceback information from this exception by checking the below Exception ID.<br/>
                Please include the above link for further details of this exception.
                </p>
            </div>
            % endif
        </div>

    </body>

</html>
