## -*- coding: utf-8 -*-

## helpers
<%def name="tag_button(text, tag_type=None)">
<%
color_scheme = {
    'default': 'border:1px solid #979797;color:#666666;background-color:#f9f9f9',
    'approved': 'border:1px solid #0ac878;color:#0ac878;background-color:#f9f9f9',
    'rejected': 'border:1px solid #e85e4d;color:#e85e4d;background-color:#f9f9f9',
    'under_review': 'border:1px solid #ffc854;color:#ffc854;background-color:#f9f9f9',
}

css_style = ';'.join([
    'display:inline',
    'border-radius:2px',
    'font-size:12px',
    'padding:.2em',
])

%>
    <pre style="${css_style}; ${color_scheme.get(tag_type, color_scheme['default'])}">${text}</pre>
</%def>

<%def name="status_text(text, tag_type=None)">
    <%
    color_scheme = {
        'default': 'color:#666666',
        'approved': 'color:#0ac878',
        'rejected': 'color:#e85e4d',
        'under_review': 'color:#ffc854',
    }
    %>
    <span style="font-weight:bold;font-size:12px;padding:.2em;${color_scheme.get(tag_type, color_scheme['default'])}">${text}</span>
</%def>

<%def name="gravatar_img(email, size=16)">
<%
css_style = ';'.join([
    'padding: 0',
    'margin: -4px 0',
    'border-radius: 50%',
    'box-sizing: content-box',
    'display: inline',
    'line-height: 1em',
    'min-width: 16px',
    'min-height: 16px',
])
%>

<img alt="gravatar" style="${css_style}" src="${h.gravatar_url(email, size)}" height="${size}" width="${size}">
</%def>

<%def name="link_css()">\
<%
css_style = ';'.join([
    'color:#427cc9',
    'text-decoration:none',
    'cursor:pointer'
])
%>\
${css_style}\
</%def>

## Constants
<%
text_regular = "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen-Sans, Ubuntu, Cantarell, 'Helvetica Neue', Helvetica, sans-serif"
text_monospace = "'Menlo', 'Liberation Mono', 'Consolas', 'DejaVu Sans Mono', 'Ubuntu Mono', 'Courier New', 'andale mono', 'lucida console', monospace"

%>

<%def name="plaintext_footer()" filter="trim">
${_('This is a notification from RhodeCode.')} ${instance_url}
</%def>

<%def name="body_plaintext()" filter="n,trim">
## this example is not called itself but overridden in each template
## the plaintext_footer should be at the bottom of both html and text emails
${self.plaintext_footer()}
</%def>

<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd"> 
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
    <meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
    <title>${self.subject()}</title>
    <style type="text/css">
        /* Based on The MailChimp Reset INLINE: Yes. */
        #outlook a {
            padding: 0;
        }

        /* Force Outlook to provide a "view in browser" menu link. */
        body {
            width: 100% !important;
            -webkit-text-size-adjust: 100%;
            -ms-text-size-adjust: 100%;
            margin: 0;
            padding: 0;
            font-family: ${text_regular|n};
            color: #000000;
        }

        /* Prevent Webkit and Windows Mobile platforms from changing default font sizes.*/
        .ExternalClass {
            width: 100%;
        }

        /* Force Hotmail to display emails at full width */
        .ExternalClass, .ExternalClass p, .ExternalClass span, .ExternalClass font, .ExternalClass td, .ExternalClass div {
            line-height: 100%;
        }

        /* Forces Hotmail to display normal line spacing.  More on that: http://www.emailonacid.com/forum/viewthread/43/ */
        #backgroundTable {
            margin: 0;
            padding: 0;
            line-height: 100% !important;
        }

        /* End reset */

        /* defaults for images*/
        img {
            outline: none;
            text-decoration: none;
            -ms-interpolation-mode: bicubic;
        }

        a img {
            border: none;
        }

        .image_fix {
            display: block;
        }

        body {
            line-height: 1.2em;
        }

        p {
            margin: 0 0 20px;
        }

        h1, h2, h3, h4, h5, h6 {
            color: #323232 !important;
        }

        a {
            color: #427cc9;
            text-decoration: none;
            outline: none;
            cursor: pointer;
        }

        a:focus {
            outline: none;
        }

        a:hover {
            color: #305b91;
        }

        h1 a, h2 a, h3 a, h4 a, h5 a, h6 a {
            color: #427cc9 !important;
            text-decoration: none !important;
        }

        h1 a:active, h2 a:active, h3 a:active, h4 a:active, h5 a:active, h6 a:active {
            color: #305b91 !important;
        }

        h1 a:visited, h2 a:visited, h3 a:visited, h4 a:visited, h5 a:visited, h6 a:visited {
            color: #305b91 !important;
        }

        table {
            font-size: 13px;
            border-collapse: collapse;
            mso-table-lspace: 0pt;
            mso-table-rspace: 0pt;
        }

        table tr {
            display: table-row;
            vertical-align: inherit;
            border-color: inherit;
            border-spacing: 0 3px;
        }

        table td {
            padding: .65em 1em .65em 0;
            border-collapse: collapse;
            vertical-align: top;
            text-align: left;
        }

        input {
            display: inline;
            border-radius: 2px;
            border: 1px solid #dbd9da;
            padding: .5em;
        }

        input:focus {
            outline: 1px solid #979797
        }

        code {
            font-family: ${text_monospace|n};
            white-space: pre-line !important;
            color: #000000;
        }

        ul.changes-ul {
            list-style: none;
            list-style-type: none;
            padding: 0;
            margin: 10px 0;
        }
        ul.changes-ul li {
            list-style: none;
            list-style-type: none;
            margin: 2px 0;
        }

        @media only screen and (-webkit-min-device-pixel-ratio: 2) {
            /* Put your iPhone 4g styles in here */
        }

        /* Android targeting */
        @media only screen and (-webkit-device-pixel-ratio:.75){
        /* Put CSS for low density (ldpi) Android layouts in here */
        }
        @media only screen and (-webkit-device-pixel-ratio:1){
        /* Put CSS for medium density (mdpi) Android layouts in here */
        }
        @media only screen and (-webkit-device-pixel-ratio:1.5){
        /* Put CSS for high density (hdpi) Android layouts in here */
        }
        /* end Android targeting */

        /** MARKDOWN styling **/
        div.markdown-block {
            clear: both;
            overflow: hidden;
            margin: 0;
            padding: 3px 5px 3px
        }

        div.markdown-block h1,
        div.markdown-block h2,
        div.markdown-block h3,
        div.markdown-block h4,
        div.markdown-block h5,
        div.markdown-block h6 {
            border-bottom: none !important;
            padding: 0 !important;
            overflow: visible !important
        }

        div.markdown-block h1,
        div.markdown-block h2 {
            border-bottom: 1px #e6e5e5 solid !important
        }

        div.markdown-block h1 {
            font-size: 32px;
            margin: 15px 0 15px 0 !important;
            padding-bottom: 5px !important
        }

        div.markdown-block h2 {
            font-size: 24px !important;
            margin: 34px 0 10px 0 !important;
            padding-top: 15px !important;
            padding-bottom: 8px !important
        }

        div.markdown-block h3 {
            font-size: 18px !important;
            margin: 30px 0 8px 0 !important;
            padding-bottom: 2px !important
        }

        div.markdown-block h4 {
            font-size: 13px !important;
            margin: 18px 0 3px 0 !important
        }

        div.markdown-block h5 {
            font-size: 12px !important;
            margin: 15px 0 3px 0 !important
        }

        div.markdown-block h6 {
            font-size: 12px;
            color: #777777;
            margin: 15px 0 3px 0 !important
        }

        div.markdown-block hr {
            border: 0;
            color: #e6e5e5;
            background-color: #e6e5e5;
            height: 3px;
            margin-bottom: 13px
        }

        div.markdown-block ol,
        div.markdown-block ul,
        div.markdown-block p,
        div.markdown-block blockquote,
        div.markdown-block dl,
        div.markdown-block li,
        div.markdown-block table {
            margin: 3px 0 13px 0 !important;
            color: #424242 !important;
            font-size: 13px !important;
            font-family: ${text_regular|n};
            font-weight: normal !important;
            overflow: visible !important;
            line-height: 140% !important
        }

        div.markdown-block pre {
            margin: 3px 0 13px 0 !important;
            padding: .5em;
            color: #424242 !important;
            font-size: 13px !important;
            overflow: visible !important;
            line-height: 140% !important;
            background-color: #F5F5F5
        }

        div.markdown-block img {
            border-style: none;
            background-color: #fff;
            max-width: 100%
        }

        div.markdown-block strong {
            font-weight: 600;
            margin: 0
        }

        div.markdown-block ul.checkbox, div.markdown-block ol.checkbox {
            padding-left: 20px !important;
            margin-top: 0 !important;
            margin-bottom: 18px !important
        }

        div.markdown-block ul, div.markdown-block ol {
            padding-left: 30px !important;
            margin-top: 0 !important;
            margin-bottom: 18px !important
        }

        div.markdown-block ul.checkbox li, div.markdown-block ol.checkbox li {
            list-style: none !important;
            margin: 0px !important;
            padding: 0 !important
        }

        div.markdown-block ul li, div.markdown-block ol li {
            list-style: disc !important;
            margin: 0px !important;
            padding: 0 !important
        }

        div.markdown-block ol li {
            list-style: decimal !important
        }

        div.markdown-block #message {
            -webkit-border-radius: 2px;
            -moz-border-radius: 2px;
            border-radius: 2px;
            border: 1px solid #dbd9da;
            display: block;
            width: 100%;
            height: 60px;
            margin: 6px 0
        }

        div.markdown-block button, div.markdown-block #ws {
            font-size: 13px;
            padding: 4px 6px;
            -webkit-border-radius: 2px;
            -moz-border-radius: 2px;
            border-radius: 2px;
            border: 1px solid #dbd9da;
            background-color: #eeeeee
        }

        div.markdown-block p {
            margin-top: 0;
            margin-bottom: 16px;
            padding: 0;
            line-height: unset;
        }

        div.markdown-block code,
        div.markdown-block pre,
        div.markdown-block #ws,
        div.markdown-block #message {
            font-family: ${text_monospace|n};
            font-size: 11px;
            -webkit-border-radius: 2px;
            -moz-border-radius: 2px;
            border-radius: 2px;
            background-color: #FFFFFF;
            color: #7E7F7F
        }

        div.markdown-block code {
            border: 1px solid #7E7F7F;
            margin: 0 2px;
            padding: 0 5px
        }

        div.markdown-block pre {
            border: 1px solid #7E7F7F;
            overflow: auto;
            padding: .5em;
            background-color: #FFFFFF;
        }

        div.markdown-block pre > code {
            border: 0;
            margin: 0;
            padding: 0
        }

        div.rst-block {
            clear: both;
            overflow: hidden;
            margin: 0;
            padding: 3px 5px 3px
        }

        div.rst-block h2 {
            font-weight: normal
        }

        div.rst-block h1,
        div.rst-block h2,
        div.rst-block h3,
        div.rst-block h4,
        div.rst-block h5,
        div.rst-block h6 {
            border-bottom: 0 !important;
            margin: 0 !important;
            padding: 0 !important;
            line-height: 1.5em !important
        }

        div.rst-block h1:first-child {
            padding-top: .25em !important
        }

        div.rst-block h2, div.rst-block h3 {
            margin: 1em 0 !important
        }

        div.rst-block h1, div.rst-block h2 {
            border-bottom: 1px #e6e5e5 solid !important
        }

        div.rst-block h2 {
            margin-top: 1.5em !important;
            padding-top: .5em !important
        }

        div.rst-block p {
            color: black !important;
            margin: 1em 0 !important;
            line-height: 1.5em !important
        }

        div.rst-block ul {
            list-style: disc !important;
            margin: 1em 0 1em 2em !important;
            clear: both
        }

        div.rst-block ol {
            list-style: decimal;
            margin: 1em 0 1em 2em !important
        }

        div.rst-block pre, div.rst-block code {
            font: 12px "Bitstream Vera Sans Mono", "Courier", monospace
        }

        div.rst-block code {
            font-size: 12px !important;
            background-color: ghostWhite !important;
            color: #444 !important;
            padding: 0 .2em !important;
            border: 1px solid #7E7F7F !important
        }

        div.rst-block pre code {
            padding: 0 !important;
            font-size: 12px !important;
            background-color: #eee !important;
            border: none !important
        }

        div.rst-block pre {
            margin: 1em 0;
            padding: 15px;
            border: 1px solid #7E7F7F;
            -webkit-border-radius: 2px;
            -moz-border-radius: 2px;
            border-radius: 2px;
            overflow: auto;
            font-size: 12px;
            color: #444;
            background-color: #FFFFFF;
        }

        .clear-both {
            clear:both;
        }

        /*elasticmatch is custom rhodecode tag*/
        .codehilite .c-ElasticMatch {
            background-color: #faffa6;
            padding: 0.2em;
        }

        .codehilite .c-ElasticMatch { background-color: #faffa6; padding: 0.2em;}
        .codehilite .hll { background-color: #ffffcc }
        .codehilite .c { color: #408080; font-style: italic } /* Comment */
        .codehilite .err { border: none } /* Error */
        .codehilite .k { color: #008000; font-weight: bold } /* Keyword */
        .codehilite .o { color: #666666 } /* Operator */
        .codehilite .ch { color: #408080; font-style: italic } /* Comment.Hashbang */
        .codehilite .cm { color: #408080; font-style: italic } /* Comment.Multiline */
        .codehilite .cp { color: #BC7A00 } /* Comment.Preproc */
        .codehilite .cpf { color: #408080; font-style: italic } /* Comment.PreprocFile */
        .codehilite .c1 { color: #408080; font-style: italic } /* Comment.Single */
        .codehilite .cs { color: #408080; font-style: italic } /* Comment.Special */
        .codehilite .gd { color: #A00000 } /* Generic.Deleted */
        .codehilite .ge { font-style: italic } /* Generic.Emph */
        .codehilite .gr { color: #FF0000 } /* Generic.Error */
        .codehilite .gh { color: #000080; font-weight: bold } /* Generic.Heading */
        .codehilite .gi { color: #00A000 } /* Generic.Inserted */
        .codehilite .go { color: #888888 } /* Generic.Output */
        .codehilite .gp { color: #000080; font-weight: bold } /* Generic.Prompt */
        .codehilite .gs { font-weight: bold } /* Generic.Strong */
        .codehilite .gu { color: #800080; font-weight: bold } /* Generic.Subheading */
        .codehilite .gt { color: #0044DD } /* Generic.Traceback */
        .codehilite .kc { color: #008000; font-weight: bold } /* Keyword.Constant */
        .codehilite .kd { color: #008000; font-weight: bold } /* Keyword.Declaration */
        .codehilite .kn { color: #008000; font-weight: bold } /* Keyword.Namespace */
        .codehilite .kp { color: #008000 } /* Keyword.Pseudo */
        .codehilite .kr { color: #008000; font-weight: bold } /* Keyword.Reserved */
        .codehilite .kt { color: #B00040 } /* Keyword.Type */
        .codehilite .m { color: #666666 } /* Literal.Number */
        .codehilite .s { color: #BA2121 } /* Literal.String */
        .codehilite .na { color: #7D9029 } /* Name.Attribute */
        .codehilite .nb { color: #008000 } /* Name.Builtin */
        .codehilite .nc { color: #0000FF; font-weight: bold } /* Name.Class */
        .codehilite .no { color: #880000 } /* Name.Constant */
        .codehilite .nd { color: #AA22FF } /* Name.Decorator */
        .codehilite .ni { color: #999999; font-weight: bold } /* Name.Entity */
        .codehilite .ne { color: #D2413A; font-weight: bold } /* Name.Exception */
        .codehilite .nf { color: #0000FF } /* Name.Function */
        .codehilite .nl { color: #A0A000 } /* Name.Label */
        .codehilite .nn { color: #0000FF; font-weight: bold } /* Name.Namespace */
        .codehilite .nt { color: #008000; font-weight: bold } /* Name.Tag */
        .codehilite .nv { color: #19177C } /* Name.Variable */
        .codehilite .ow { color: #AA22FF; font-weight: bold } /* Operator.Word */
        .codehilite .w { color: #bbbbbb } /* Text.Whitespace */
        .codehilite .mb { color: #666666 } /* Literal.Number.Bin */
        .codehilite .mf { color: #666666 } /* Literal.Number.Float */
        .codehilite .mh { color: #666666 } /* Literal.Number.Hex */
        .codehilite .mi { color: #666666 } /* Literal.Number.Integer */
        .codehilite .mo { color: #666666 } /* Literal.Number.Oct */
        .codehilite .sa { color: #BA2121 } /* Literal.String.Affix */
        .codehilite .sb { color: #BA2121 } /* Literal.String.Backtick */
        .codehilite .sc { color: #BA2121 } /* Literal.String.Char */
        .codehilite .dl { color: #BA2121 } /* Literal.String.Delimiter */
        .codehilite .sd { color: #BA2121; font-style: italic } /* Literal.String.Doc */
        .codehilite .s2 { color: #BA2121 } /* Literal.String.Double */
        .codehilite .se { color: #BB6622; font-weight: bold } /* Literal.String.Escape */
        .codehilite .sh { color: #BA2121 } /* Literal.String.Heredoc */
        .codehilite .si { color: #BB6688; font-weight: bold } /* Literal.String.Interpol */
        .codehilite .sx { color: #008000 } /* Literal.String.Other */
        .codehilite .sr { color: #BB6688 } /* Literal.String.Regex */
        .codehilite .s1 { color: #BA2121 } /* Literal.String.Single */
        .codehilite .ss { color: #19177C } /* Literal.String.Symbol */
        .codehilite .bp { color: #008000 } /* Name.Builtin.Pseudo */
        .codehilite .fm { color: #0000FF } /* Name.Function.Magic */
        .codehilite .vc { color: #19177C } /* Name.Variable.Class */
        .codehilite .vg { color: #19177C } /* Name.Variable.Global */
        .codehilite .vi { color: #19177C } /* Name.Variable.Instance */
        .codehilite .vm { color: #19177C } /* Name.Variable.Magic */
        .codehilite .il { color: #666666 } /* Literal.Number.Integer.Long */

    </style>

</head>
<body>

<div>
<!-- Wrapper/Container Table: Use a wrapper table to control the width and the background color consistently of your email. Use this approach instead of setting attributes on the body tag. -->
<table cellpadding="0" cellspacing="0" border="0" id="backgroundTable" align="left" style="margin:1%;width:97%;padding:0;font-family:${text_regular|n};font-weight:100;border:1px solid #dbd9da">
    <tr>
        <td valign="top" style="padding:0;">
            <table cellpadding="0" cellspacing="0" border="0" align="left" width="100%">
                <tr>
                    <td style="width:100%;padding:10px 15px;background-color:#202020" valign="top">
                        <a style="color:#eeeeee;text-decoration:none;" href="${instance_url}">
                            ${_('RhodeCode')}
                            % if rhodecode_instance_name:
                                - ${rhodecode_instance_name}
                            % endif
                        </a>
                    </td>
                </tr>
                <tr style="background-color: #fff">
                    <td style="padding:15px;" valign="top">${self.body()}</td>
                </tr>
            </table>
        </td>
    </tr>
</table>  
<!-- End of wrapper table -->
</div>

<div style="width:100%; clear: both; height: 1px">&nbsp;</div>

<div style="margin-left:1%;font-weight:100;font-size:11px;color:#666666;text-decoration:none;font-family:${text_monospace};">
    ${_('This is a notification from RhodeCode.')}
    <a style="font-weight:100;font-size:11px;color:#666666;text-decoration:none;font-family:${text_monospace};" href="${instance_url}">
        ${instance_url}
    </a>
</div>
</body>
</html>
