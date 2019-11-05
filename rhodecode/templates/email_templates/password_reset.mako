## -*- coding: utf-8 -*-
<%inherit file="base.mako"/>
<%namespace name="base" file="base.mako"/>

<%def name="subject()" filter="n,trim,whitespace_filter">
RhodeCode Password reset
</%def>

## plain text version of the email. Empty by default
<%def name="body_plaintext()" filter="n,trim">
Hello ${user.username},

On ${h.format_date(date)} there was a request to reset your password using the email address `${email}`

*If you did not request a password reset, please contact your RhodeCode administrator at: ${first_admin_email}*

You can continue, and generate new password by clicking following URL:
${password_reset_url}

This link will be active for 10 minutes.

---
${self.plaintext_footer()}
</%def>

## BODY GOES BELOW
<p>
Hello ${user.username},
</p><p>
On ${h.format_date(date)} there was a request to reset your password using the email address `${email}`
<br/><br/>
<strong>If you did not request a password reset, please contact your RhodeCode administrator at: ${first_admin_email}.</strong>
</p><p>
You can continue, and generate new password by clicking following URL:<br/><br/>
<a href="${password_reset_url}" style="${base.link_css()}">${password_reset_url}</a>
<br/><br/>This link will be active for 10 minutes.
</p>
