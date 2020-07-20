## -*- coding: utf-8 -*-
<%inherit file="base.mako"/>

<%def name="subject()" filter="n,trim,whitespace_filter">
Test "Subject" ${_('hello "world"')|n}
</%def>

## plain text version of the email. Empty by default
<%def name="body_plaintext()" filter="n,trim">
Email Plaintext Body
</%def>

## BODY GOES BELOW
<strong>Email Body</strong>
<br/>
<br/>
`h.short_id()`: ${h.short_id('0' * 40)}<br/>
${_('Translation String')}<br/>
