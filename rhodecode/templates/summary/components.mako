<%namespace name="base" file="/base/base.mako"/>

<%def name="refs_counters(branches, closed_branches, tags, bookmarks)">
    <span class="summary-branchtag summary-tag">
    <a href="${h.route_path('branches_home',repo_name=c.repo_name)}" class="childs">
      <i class="icon-branch"></i>
      % if len(branches) == 1:
          <span>${len(branches)}</span> ${_('Branch')}
      % else:
          <span>${len(branches)}</span> ${_('Branches')}
      % endif
    </a>
    </span>

    %if closed_branches:
    <span class="summary-branchtag summary-tag">
    <a href="${h.route_path('branches_home',repo_name=c.repo_name)}" class="childs">
      <i class="icon-branch"></i>
      % if len(closed_branches) == 1:
          <span>${len(closed_branches)}</span> ${_('Closed Branch')}
      % else:
          <span>${len(closed_branches)}</span> ${_('Closed Branches')}
      % endif
      </a>
    </span>
    %endif

    <span class="summary-tagtag summary-tag">
    <a href="${h.route_path('tags_home',repo_name=c.repo_name)}" class="childs">
        <i class="icon-tag"></i>
        % if len(tags) == 1:
            <span>${len(tags)}</span> ${_('Tag')}
        % else:
            <span>${len(tags)}</span> ${_('Tags')}
        % endif
        </a>
    </span>

    %if bookmarks:
    <span class="summary-booktag summary-tag">
    <a href="${h.route_path('bookmarks_home',repo_name=c.repo_name)}" class="childs">
        <i class="icon-bookmark"></i>
        % if len(bookmarks) == 1:
            <span>${len(bookmarks)}</span> ${_('Bookmark')}
        % else:
            <span>${len(bookmarks)}</span> ${_('Bookmarks')}
        % endif
        </a>
    </span>
    %endif
</%def>

<%def name="summary_detail(breadcrumbs_links, show_downloads=True)">
    <% summary = lambda n:{False:'summary-short'}.get(n) %>

    <div id="summary-menu-stats" class="summary-detail">
        <div class="fieldset">
          <div class="left-content">
            <div class="left-clone">
                <select id="clone_option" name="clone_option">
                    <option value="http" selected="selected">HTTP</option>
                    <option value="http_id">HTTP UID</option>
                    % if c.ssh_enabled:
                        <option value="ssh">SSH</option>
                    % endif
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

          <div class="right-content">
            <div class="commit-info">
                <div class="tags">
                <% commit_rev = h.safe_int(c.rhodecode_db_repo.changeset_cache.get('revision'), 0) + 1 %>
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

                ## commits
                <span class="summary-tag">
                  % if commit_rev == -1:
                      <i class="icon-history"></i>
                      % if commit_rev == -1:
                            <span>0</span> ${_('Commit')}
                        % else:
                            <span>0</span> ${_('Commits')}
                        % endif
                  % else:
                      <a href="${h.route_path('repo_commits', repo_name=c.repo_name)}">
                        <i class="icon-history"></i>
                        % if commit_rev == 1:
                            <span>${commit_rev}</span> ${_('Commit')}
                        % else:
                            <span>${commit_rev}</span> ${_('Commits')}
                        % endif
                        </a>
                  % endif
                </span>

                ## forks
                <span class="summary-tag">
                  <a title="${_('Number of Repository Forks')}" href="${h.route_path('repo_forks_show_all', repo_name=c.repo_name)}">
                     <i class="icon-code-fork"></i>
                     <span>${c.repository_forks}</span> ${_ungettext('Fork', 'Forks', c.repository_forks)}</a>
                </span>
                </div>
            </div>
        </div>
    </div>
        ## owner, description, downloads, statistics

        ## Owner
        <div class="fieldset collapsable-content" data-toggle="summary-details" style="display: none;">
          <div class="left-label-summary">
            <p>${_('Owner')}</p>
            <div class="right-label-summary">
                ${base.gravatar_with_user(c.rhodecode_db_repo.user.email, 16, tooltip=True)}
            </div>

          </div>
        </div>

        ## Description
        <div class="fieldset collapsable-content" data-toggle="summary-details" style="display: none;">
          <div class="left-label-summary">
            <p>${_('Description')}</p>

            <div class="right-label-summary input ${summary(c.show_stats)}">
                <%namespace name="dt" file="/data_table/_dt_elements.mako"/>
                ${dt.repo_desc(c.rhodecode_db_repo.description_safe, c.visual.stylify_metatags)}
            </div>
          </div>
        </div>

        ## Downloads
        % if show_downloads:
          <div class="fieldset collapsable-content" data-toggle="summary-details" style="display: none;">
            <div class="left-label-summary">
              <p>${_('Downloads')}</p>

              <div class="right-label-summary input ${summary(c.show_stats)} downloads">
                % if c.rhodecode_repo and len(c.rhodecode_repo.commit_ids) == 0:
                  <span class="disabled">
                    ${_('There are no downloads yet')}
                  </span>
                % elif not c.enable_downloads:
                    <span class="disabled">
                        ${_('Downloads are disabled for this repository')}.
                    </span>
                    % if c.is_super_admin:
                       ${h.link_to(_('Enable downloads'),h.route_path('edit_repo',repo_name=c.repo_name, _anchor='repo_enable_downloads'))}
                    % endif
                % else:
                    <span class="enabled">

                        <a id="archive_link" class="btn btn-small" href="${h.route_path('repo_archivefile',repo_name=c.rhodecode_db_repo.repo_name, fname=c.rhodecode_db_repo.landing_ref_name+'.zip')}">
                            <i class="icon-download"></i>
                            ${c.rhodecode_db_repo.landing_ref_name}.zip
                            ## replaced by some JS on select
                        </a>
                    </span>
                    ${h.hidden('download_options')}
                % endif
              </div>
            </div>
          </div>
        % endif

        ## Repo size
        <div class="fieldset collapsable-content" data-toggle="summary-details" style="display: none;">
          <div class="left-label-summary">
            <p>${_('Repository size')}</p>

            <div class="right-label-summary">
                <div class="tags">
                   ## repo size
                    % if commit_rev == -1:
                          <span class="stats-bullet">0 B</span>
                    % else:
                          <span>
                              <a href="#showSize" onclick="calculateSize(); $(this).hide(); return false" id="show-repo-size">Show repository size</a>
                          </span>
                          <span class="stats-bullet" id="repo_size_container" style="display:none">
                              ${_('Calculating Repository Size...')}
                          </span>
                    % endif
                </div>
            </div>
          </div>
        </div>

        ## Statistics
        <div class="fieldset collapsable-content" data-toggle="summary-details" style="display: none;">
          <div class="left-label-summary">
            <p>${_('Code Statistics')}</p>

            <div class="right-label-summary input ${summary(c.show_stats)} statistics">
              % if c.show_stats:
                <div id="lang_stats" class="enabled">
                    <a href="#showSize" onclick="calculateSize(); $('#show-repo-size').hide(); $(this).hide(); return false" id="show-repo-size">Show code statistics</a>
                </div>
              % else:
                  <span class="disabled">
                      ${_('Statistics are disabled for this repository')}.
                  </span>
                  % if c.is_super_admin:
                     ${h.link_to(_('Enable statistics'),h.route_path('edit_repo',repo_name=c.repo_name, _anchor='repo_enable_statistics'))}
                  % endif
              % endif
            </div>

          </div>
        </div>


    </div><!--end summary-detail-->

    <div id="summary_details_expand" class="btn-collapse" data-toggle="summary-details">
            ${_('Show More')}
    </div>
</%def>
