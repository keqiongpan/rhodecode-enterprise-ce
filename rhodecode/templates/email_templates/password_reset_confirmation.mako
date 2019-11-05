## -*- coding: utf-8 -*-
<%inherit file="base.mako"/>
<%namespace name="base" file="base.mako"/>

<%def name="subject()" filter="n,trim,whitespace_filter">
Your new RhodeCode password
</%def>

## plain text version of the email. Empty by default
<%def name="body_plaintext()" filter="n,trim">
Hello ${user.username},

Below is your new access password for RhodeCode requested via password reset link.

*If you did not request a password reset, please contact your RhodeCode administrator at: ${first_admin_email}.*

new password: ${new_password}

---
${self.plaintext_footer()}
</%def>

## BODY GOES BELOW
<p>
Hello ${user.username},
</p><p>
Below is your new access password for RhodeCode requested via password reset link.
<br/><br/>
<strong>If you did not request a password reset, please contact your RhodeCode administrator at: ${first_admin_email}.</strong>
</p>
<p>new password: <code>${new_password}</code>
