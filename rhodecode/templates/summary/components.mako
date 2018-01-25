<%def name="refs_counters(branches, closed_branches, tags, bookmarks)">
    <span class="branchtag tag">
    <a href="${h.route_path('branches_home',repo_name=c.repo_name)}" class="childs">
      <i class="icon-branch"></i>${_ungettext(
      '%(num)s Branch','%(num)s Branches', len(branches)) % {'num': len(branches)}}</a>
    </span>

    %if closed_branches:
    <span class="branchtag tag">
    <a href="${h.route_path('branches_home',repo_name=c.repo_name)}" class="childs">
      <i class="icon-branch"></i>${_ungettext(
      '%(num)s Closed Branch', '%(num)s Closed Branches', len(closed_branches)) % {'num': len(closed_branches)}}</a>
    </span>
    %endif

    <span class="tagtag tag">
    <a href="${h.route_path('tags_home',repo_name=c.repo_name)}" class="childs">
        <i class="icon-tag"></i>${_ungettext(
        '%(num)s Tag', '%(num)s Tags', len(tags)) % {'num': len(tags)}}</a>
    </span>

    %if bookmarks:
    <span class="booktag tag">
    <a href="${h.route_path('bookmarks_home',repo_name=c.repo_name)}" class="childs">
        <i class="icon-bookmark"></i>${_ungettext(
        '%(num)s Bookmark', '%(num)s Bookmarks', len(bookmarks)) % {'num': len(bookmarks)}}</a>
    </span>
    %endif
</%def>

<%def name="summary_detail(breadcrumbs_links, show_downloads=True)">
    <% summary = lambda n:{False:'summary-short'}.get(n) %>

    <div id="summary-menu-stats" class="summary-detail">
        <div class="summary-detail-header">
            <div class="breadcrumbs files_location">
                <h4>
                  ${breadcrumbs_links}
                </h4>
            </div>
            <div id="summary_details_expand" class="btn-collapse" data-toggle="summary-details">
                ${_('Show More')}
            </div>
        </div>

        <div class="fieldset">

            <div class="left-clone">
                <select id="clone_option" name="clone_option">
                    <option value="http" selected="selected">HTTP</option>
                    <option value="http_id">HTTP UID</option>
                    <option value="ssh">SSH</option>
                </select>
            </div>
            <div class="right-clone">
                <%
                    maybe_disabled = ''
                    if h.is_svn_without_proxy(c.rhodecode_db_repo):
                        maybe_disabled = 'disabled'
                %>

                <span id="clone_option_http">
                <input type="text" class="input-monospace clone_url_input" ${maybe_disabled} readonly="readonly" value="${c.clone_repo_url}"/>
                <i class="tooltip icon-clipboard clipboard-action" data-clipboard-text="${c.clone_repo_url}" title="${_('Copy the clone url')}"></i>
                </span>

                <span style="display: none;" id="clone_option_http_id">
                <input type="text" class="input-monospace clone_url_input" ${maybe_disabled} readonly="readonly" value="${c.clone_repo_url_id}"/>
                <i class="tooltip icon-clipboard clipboard-action" data-clipboard-text="${c.clone_repo_url_id}" title="${_('Copy the clone by id url')}"></i>
                </span>

                <span style="display: none;" id="clone_option_ssh">
                <input type="text" class="input-monospace clone_url_input" ${maybe_disabled} readonly="readonly" value="${c.clone_repo_url_ssh}"/>
                <i class="tooltip icon-clipboard clipboard-action" data-clipboard-text="${c.clone_repo_url_ssh}" title="${_('Copy the clone by ssh url')}"></i>
                </span>

                % if maybe_disabled:
                    <p class="help-block">${_('SVN Protocol is disabled. To enable it, see the')} <a href="${h.route_url('enterprise_svn_setup')}" target="_blank">${_('documentation here')}</a>.</p>
                % endif

            </div>
        </div>

        <div class="fieldset collapsable-content" data-toggle="summary-details" style="display: none;">
          <div class="left-label">
            ${_('Description')}:
          </div>
          <div class="right-content">
            <div class="input ${summary(c.show_stats)}">
                <%namespace name="dt" file="/data_table/_dt_elements.mako"/>
                ${dt.repo_desc(c.rhodecode_db_repo.description_safe, c.visual.stylify_metatags)}
            </div>
          </div>
        </div>

        <div class="fieldset collapsable-content" data-toggle="summary-details" style="display: none;">
          <div class="left-label">
            ${_('Information')}:
          </div>
          <div class="right-content">

              <div class="repo-size">
                  <% commit_rev = c.rhodecode_db_repo.changeset_cache.get('revision') %>

                  ## commits
                  % if commit_rev == -1:
                      ${_ungettext('%(num)s Commit', '%(num)s Commits', 0) % {'num': 0}},
                  % else:
                      <a href="${h.route_path('repo_changelog', repo_name=c.repo_name)}">
                        ${_ungettext('%(num)s Commit', '%(num)s Commits', commit_rev) % {'num': commit_rev}}</a>,
                  % endif

                  ## forks
                  <a title="${_('Number of Repository Forks')}" href="${h.route_path('repo_forks_show_all', repo_name=c.repo_name)}">
                     ${c.repository_forks} ${_ungettext('Fork', 'Forks', c.repository_forks)}</a>,

                  ## repo size
                  % if commit_rev == -1:
                      <span class="stats-bullet">0 B</span>
                  % else:
                      <span class="stats-bullet" id="repo_size_container">
                          ${_('Calculating Repository Size...')}
                      </span>
                  % endif
              </div>

            <div class="commit-info">
                <div class="tags">
                % if c.rhodecode_repo:
                    ${refs_counters(
                        c.rhodecode_repo.branches,
                        c.rhodecode_repo.branches_closed,
                        c.rhodecode_repo.tags,
                        c.rhodecode_repo.bookmarks)}
                % else:
                    ## missing requirements can make c.rhodecode_repo None
                    ${refs_counters([], [], [], [])}
                % endif
                </div>
            </div>

          </div>
        </div>

        <div class="fieldset collapsable-content" data-toggle="summary-details" style="display: none;">
          <div class="left-label">
            ${_('Statistics')}:
          </div>
          <div class="right-content">
            <div class="input ${summary(c.show_stats)} statistics">
              % if c.show_stats:
                <div id="lang_stats" class="enabled">
                    ${_('Calculating Code Statistics...')}
                </div>
              % else:
                  <span class="disabled">
                      ${_('Statistics are disabled for this repository')}
                  </span>
                  % if h.HasPermissionAll('hg.admin')('enable stats on from summary'):
                     , ${h.link_to(_('enable statistics'),h.route_path('edit_repo',repo_name=c.repo_name, _anchor='repo_enable_statistics'))}
                  % endif
              % endif
            </div>
            
          </div>
        </div>

        % if show_downloads:
          <div class="fieldset collapsable-content" data-toggle="summary-details" style="display: none;">
            <div class="left-label">
              ${_('Downloads')}:
            </div>
            <div class="right-content">
              <div class="input ${summary(c.show_stats)} downloads">
                % if c.rhodecode_repo and len(c.rhodecode_repo.revisions) == 0:
                  <span class="disabled">
                    ${_('There are no downloads yet')}
                  </span>
                % elif not c.enable_downloads:
                    <span class="disabled">
                        ${_('Downloads are disabled for this repository')}
                    </span>
                    % if h.HasPermissionAll('hg.admin')('enable downloads on from summary'):
                       , ${h.link_to(_('enable downloads'),h.route_path('edit_repo',repo_name=c.repo_name, _anchor='repo_enable_downloads'))}
                    % endif
                % else:
                    <span class="enabled">
                        <a id="archive_link" class="btn btn-small" href="${h.route_path('repo_archivefile',repo_name=c.rhodecode_db_repo.repo_name,fname='tip.zip')}">
                            <i class="icon-archive"></i> tip.zip
                            ## replaced by some JS on select
                        </a>
                    </span>
                    ${h.hidden('download_options')}
                % endif
              </div>
            </div>
          </div>
        % endif

    </div><!--end summary-detail-->
</%def>

<%def name="summary_stats(gravatar_function)">
    <div class="sidebar-right">
      <div class="summary-detail-header">
        <h4 class="item">
             ${_('Owner')}
        </h4>
      </div>
      <div class="sidebar-right-content">
        ${gravatar_function(c.rhodecode_db_repo.user.email, 16)}
      </div>
    </div><!--end sidebar-right-->
</%def>
