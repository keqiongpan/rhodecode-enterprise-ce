## -*- coding: utf-8 -*-
<%!
   def inherit(context):
      if context['c'].repo:
        return "/admin/repos/repo_edit.mako"
      elif context['c'].repo_group:
        return "/admin/repo_groups/repo_group_edit.mako"
      else:
        return "/admin/integrations/global.mako"
%>
<%inherit file="${inherit(context)}" />

<%def name="title()">
    ${_('Integrations Settings')}
    %if c.rhodecode_name:
        &middot; ${h.branding(c.rhodecode_name)}
    %endif
</%def>

<%def name="breadcrumbs_links()">
    ${h.link_to(_('Admin'),h.route_path('admin_home'))}
    &raquo;
    ${_('Integrations')}
</%def>

<%def name="menu_bar_nav()">
  %if c.repo:
    ${self.menu_items(active='repositories')}
  %else:
    ${self.menu_items(active='admin')}
  %endif
</%def>

<%def name="main_content()">
  ${next.body()}
</%def>
