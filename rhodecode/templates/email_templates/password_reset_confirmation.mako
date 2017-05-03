## -*- coding: utf-8 -*-
<%inherit file="base.mako"/>

<%def name="subject()" filter="n,trim,whitespace_filter">
Your new RhodeCode password
</%def>

## plain text version of the email. Empty by default
<%def name="body_plaintext()" filter="n,trim">
Hi ${user.username},

Below is your new access password for RhodeCode.

*If you didn't do this, please contact your RhodeCode administrator.*

password: ${new_password}

${self.plaintext_footer()}
</%def>

## BODY GOES BELOW
<p>
Hello ${user.username},
</p><p>
Below is your new access password for RhodeCode.
<br/>
<strong>If you didn't request a new password, please contact your RhodeCode administrator.</strong>
</p>
<p>password: <pre>${new_password}</pre>
