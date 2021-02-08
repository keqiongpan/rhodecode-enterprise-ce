## -*- coding: utf-8 -*-
<%inherit file="base.mako"/>

<%def name="subject()" filter="n,trim,whitespace_filter">
New Version of RhodeCode is available !
</%def>

## plain text version of the email. Empty by default
<%def name="body_plaintext()" filter="n,trim">
A new version of RhodeCode is available!

Your version: ${current_ver}
New version: ${latest_ver}

Release notes:

https://docs.rhodecode.com/RhodeCode-Enterprise/release-notes/release-notes-${latest_ver}.html
</%def>

## BODY GOES BELOW

<h3>A new version of RhodeCode is available!</h3>
<br/>
Your version: ${current_ver}<br/>
New version: <strong>${latest_ver}</strong><br/>

<h4>Release notes</h4>

<a href="https://docs.rhodecode.com/RhodeCode-Enterprise/release-notes/release-notes-${latest_ver}.html">
    https://docs.rhodecode.com/RhodeCode-Enterprise/release-notes/release-notes-${latest_ver}.html
</a>

