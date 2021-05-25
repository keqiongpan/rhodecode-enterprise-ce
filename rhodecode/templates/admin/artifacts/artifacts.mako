## -*- coding: utf-8 -*-
<%inherit file="/base/base.mako"/>

<%def name="title()">
    ${_('Artifacts Admin')}
    %if c.rhodecode_name:
        &middot; ${h.branding(c.rhodecode_name)}
    %endif
</%def>

<%def name="breadcrumbs_links()"></%def>

<%def name="menu_bar_nav()">
    ${self.menu_items(active='admin')}
</%def>

<%def name="menu_bar_subnav()">
    ${self.admin_menu(active='artifacts')}
</%def>

<%def name="main()">

<div class="box">

    <div class="panel panel-default">
        <div class="panel-heading">
            <h3 class="panel-title">${_('Artifacts Administration.')}</h3>
        </div>
        <div class="panel-body">
            <h4>${_('This feature is available in RhodeCode EE edition only. Contact {sales_email} to obtain a trial license.').format(sales_email='<a href="mailto:sales@rhodecode.com">sales@rhodecode.com</a>')|n}</h4>

        </div>
    </div>

</div>


</%def>

