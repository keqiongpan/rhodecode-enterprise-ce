<%inherit file="/base/base.mako"/>

<%def name="title()">
   ${_('User group')}: ${c.user_group.users_group_name}
    %if c.rhodecode_name:
        &middot; ${h.branding(c.rhodecode_name)}
    %endif
</%def>

<%def name="breadcrumbs_links()"></%def>

<%def name="menu_bar_nav()">
    ${self.menu_items(active='my_account')}
</%def>

<%def name="main()">
<div class="box">
    <div style="min-height: 25px"></div>
    <div class="main-content-full-width">
        <%include file="/user_group/${c.active}.mako"/>
    </div>
</div>

</%def>
