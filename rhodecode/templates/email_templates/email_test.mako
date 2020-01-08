## -*- coding: utf-8 -*-
<%inherit file="base.mako"/>
<%namespace name="base" file="base.mako"/>

<%def name="subject()" filter="n,trim,whitespace_filter">
RhodeCode test email: ${h.format_date(date)}
</%def>

## plain text version of the email. Empty by default
<%def name="body_plaintext()" filter="n,trim">
Test Email from RhodeCode version: ${rhodecode_version}
Email sent by: ${h.person(user)}

---
${self.plaintext_footer()}
</%def>

Test Email from RhodeCode version: ${rhodecode_version}
<br/><br/>
Email sent by: <strong>${h.person(user)}</strong>
