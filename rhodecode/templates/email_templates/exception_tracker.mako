## -*- coding: utf-8 -*-
<%inherit file="base.mako"/>
<%namespace name="base" file="base.mako"/>

<%def name="subject()" filter="n,trim,whitespace_filter">
${email_prefix} ${exc_type_name} (${exc_id})
</%def>

## plain text version of the email. Empty by default
<%def name="body_plaintext()" filter="n,trim">
    NO PLAINTEXT VERSION
</%def>

<h4>${_('Exception `{}` generated on UTC date: {}').format(exc_traceback.get('exc_type', 'NO_TYPE'), exc_traceback.get('exc_utc_date', 'NO_DATE'))}</h4>
<p>
    View exception <a href="${exc_url}">${exc_id}</a>
</p>
<pre>${exc_traceback.get('exc_message', 'NO_MESSAGE')}</pre>
