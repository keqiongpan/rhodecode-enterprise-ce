## permissions overview
<div id="perms_container">
<%namespace name="p" file="/base/perms_summary.mako"/>
${p.perms_summary(c.perm_user.permissions_full_details, actions=False)}
</div>
