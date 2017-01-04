<h2>${_('Default User Permissions Overview')}</h2>

## permissions overview
<%namespace name="p" file="/base/perms_summary.mako"/>
${p.perms_summary(c.perm_user.permissions, show_all=True)}
