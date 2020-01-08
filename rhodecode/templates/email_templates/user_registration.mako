## -*- coding: utf-8 -*-
<%inherit file="base.mako"/>
<%namespace name="base" file="base.mako"/>

<%def name="subject()" filter="n,trim,whitespace_filter">
RhodeCode new user registration: ${user.username}
</%def>

<%def name="body_plaintext()" filter="n,trim">

A new user `${user.username}` has registered on ${h.format_date(date)}

- Username: ${user.username}
- Full Name: ${user.first_name} ${user.last_name}
- Email: ${user.email}
- Profile link: ${h.route_url('user_profile', username=user.username)}

---
${self.plaintext_footer()}
</%def>


<table style="text-align:left;vertical-align:middle;width: 100%">
    <tr>
    <td style="width:100%;border-bottom:1px solid #dbd9da;">
        <h4 style="margin: 0">
            <a href="${h.route_url('user_profile', username=user.username)}" style="${base.link_css()}">
                ${_('New user {user} has registered on {date}').format(user=user.username, date=h.format_date(date))}
            </a>
        </h4>
    </td>
    </tr>
</table>

<table style="text-align:left;vertical-align:middle;width: 100%">
    ## spacing def
    <tr>
        <td style="width: 130px"></td>
        <td></td>
    </tr>
    <tr>
        <td style="padding-right:20px;padding-top:20px;">${_('Username')}:</td>
        <td style="line-height:1;padding-top:20px;">${user.username}</td>
    </tr>
    <tr>
        <td style="padding-right:20px;">${_('Full Name')}:</td>
        <td>${user.first_name} ${user.last_name}</td>
    </tr>
    <tr>
        <td style="padding-right:20px;">${_('Email')}:</td>
        <td>${user.email}</td>
    </tr>
    <tr>
        <td style="padding-right:20px;">${_('Profile')}:</td>
        <td>
            <a href="${h.route_url('user_profile', username=user.username)}">${h.route_url('user_profile', username=user.username)}</a>
        </td>
    </tr>
</table>
