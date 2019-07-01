## -*- coding: utf-8 -*-
<%inherit file="/base/base.mako"/>

<%def name="title()">
    ${_('{} Artifacts').format(c.repo_name)}
    %if c.rhodecode_name:
        &middot; ${h.branding(c.rhodecode_name)}
    %endif
</%def>

<%def name="breadcrumbs_links()"></%def>

<%def name="menu_bar_nav()">
    ${self.menu_items(active='repositories')}
</%def>

<%def name="menu_bar_subnav()">
    ${self.repo_menu(active='artifacts')}
</%def>

<%def name="main()">
    <div class="box">

    <h4>${_('This feature is available in RhodeCode EE edition only. Contact {sales_email} to obtain a trial license.').format(sales_email='<a href="mailto:sales@rhodecode.com">sales@rhodecode.com</a>')|n}</h4>
    ##<img style="width: 100%; height: 100%" src="${h.asset('images/ee_features/repo_artifacts.png')}"/>
    </div>

</%def>
