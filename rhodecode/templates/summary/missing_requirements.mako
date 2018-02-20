<%inherit file="/summary/summary_base.mako"/>

<%namespace name="components" file="/summary/components.mako"/>

<%def name="main()">
    <div class="title">
      ${self.repo_page_title(c.rhodecode_db_repo)}
    </div>

  <div id="repo-summary" class="summary">
    ${components.summary_detail(breadcrumbs_links=self.breadcrumbs_links(), show_downloads=False)}
    ${components.summary_stats(gravatar_function=self.gravatar_with_user)}
  </div><!--end repo-summary-->

  <div class="alert alert-dismissable alert-warning">
    <strong>Missing requirements</strong>
    Commits cannot be displayed, because this repository uses one or more extensions, which was not enabled. <br/>
    Please <a href="${h.route_path('edit_repo_vcs', repo_name=c.repo_name)}">enable extension in settings</a>, or contact the repository owner for help.
    Missing extensions could be:
<pre>

- Mercurial largefiles
- Git LFS
</pre>
  <br/>
  Requirement error: ${c.repository_requirements_missing.get('error')}
  </div>

</%def>


<%def name="menu_bar_subnav()">
    ${self.repo_menu(active='summary')}
</%def>
