<%inherit file="/base/base.mako"/>

<%def name="title()">
    ## represents page title
    ${_('{} Summary').format(c.repo_name)}
    %if c.rhodecode_name:
        &middot; ${h.branding(c.rhodecode_name)}
    %endif
</%def>


<%def name="head_extra()">
    <link href="${h.route_path('atom_feed_home', repo_name=c.rhodecode_db_repo.repo_uid, _query=dict(auth_token=c.rhodecode_user.feed_token))}" rel="alternate" title="${h.tooltip(_('%s ATOM feed') % c.repo_name)}" type="application/atom+xml" />
    <link href="${h.route_path('rss_feed_home', repo_name=c.rhodecode_db_repo.repo_uid, _query=dict(auth_token=c.rhodecode_user.feed_token))}" rel="alternate" title="${h.tooltip(_('%s RSS feed') % c.repo_name)}" type="application/rss+xml" />
</%def>


<%def name="menu_bar_nav()">
    ${self.menu_items(active='repositories')}
</%def>


<%def name="breadcrumbs_links()"></%def>


<%def name="main()">
    ${next.main()}
</%def>
