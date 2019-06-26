## small box that displays changed/added/removed details fetched by AJAX
<%namespace name="base" file="/base/base.mako"/>

% if c.prev_page:
    <tr>
        <td colspan="9" class="load-more-commits">
            <a class="prev-commits" href="#loadPrevCommits" onclick="commitsController.loadPrev(this, ${c.prev_page}, '${c.branch_name}', '${c.commit_id}', '${c.f_path}');return false">
            ${_('load previous')}
            </a>
        </td>
    </tr>
% endif

## to speed up lookups cache some functions before the loop
<%
    active_patterns = h.get_active_pattern_entries(c.repo_name)
    urlify_commit_message = h.partial(h.urlify_commit_message, active_pattern_entries=active_patterns)
%>

% for cnt,commit in enumerate(c.pagination):
    <tr id="sha_${commit.raw_id}" class="changelogRow container ${'tablerow%s' % (cnt%2)}">

    <td class="td-checkbox">
        ${h.checkbox(commit.raw_id,class_="commit-range", **{'data-commit-idx':commit.idx, 'data-commit-id': commit.raw_id})}
    </td>
    ##
    <td class="td-graphbox">

    </td>

    <td class="td-status">
    %if c.statuses.get(commit.raw_id):
      <div class="changeset-status-ico">
        %if c.statuses.get(commit.raw_id)[2]:
          <a class="tooltip" title="${_('Commit status: %s\nClick to open associated pull request #%s') % (h.commit_status_lbl(c.statuses.get(commit.raw_id)[0]), c.statuses.get(commit.raw_id)[2])}" href="${h.route_path('pullrequest_show',repo_name=c.statuses.get(commit.raw_id)[3],pull_request_id=c.statuses.get(commit.raw_id)[2])}">
            <div class="${'flag_status {}'.format(c.statuses.get(commit.raw_id)[0])}"></div>
          </a>
        %else:
          <a class="tooltip" title="${_('Commit status: {}').format(h.commit_status_lbl(c.statuses.get(commit.raw_id)[0]))}" href="${h.route_path('repo_commit',repo_name=c.repo_name,commit_id=commit.raw_id,_anchor='comment-%s' % c.comments[commit.raw_id][0].comment_id)}">
            <div class="${'flag_status {}'.format(c.statuses.get(commit.raw_id)[0])}"></div>
          </a>
        %endif
      </div>
    %else:
        <div class="tooltip flag_status not_reviewed" title="${_('Commit status: Not Reviewed')}"></div>
    %endif
    </td>

    <td class="td-hash">
    <code>

      <a href="${h.route_path('repo_commit',repo_name=c.repo_name,commit_id=commit.raw_id)}">
        <span class="${'commit_hash obsolete' if getattr(commit, 'obsolete', None) else 'commit_hash'}">${h.show_id(commit)}</span>
      </a>

      <i class="tooltip icon-clipboard clipboard-action" data-clipboard-text="${commit.raw_id}" title="${_('Copy the full commit id')}"></i>

      ## COMMIT PHASES

      ## Draft
      % if hasattr(commit, 'phase'):
          % if commit.phase != 'public':
              <span class="tag phase-${commit.phase} tooltip" title="${_('{} commit phase').format(commit.phase)}">${commit.phase[0].upper()}</span>
          % endif
      % endif

      ## obsolete commits
      % if hasattr(commit, 'obsolete') and commit.obsolete:
          <span class="tag obsolete-${commit.obsolete} tooltip" title="${_('Obsolete Evolve State')}">O</span>
      % endif

      ## hidden commits
      % if hasattr(commit, 'hidden') and commit.hidden:
          <span class="tag obsolete-${commit.hidden} tooltip" title="${_('Hidden Evolve State')}">H</span>
      % endif

    </code>
    </td>

    <td class="td-message expand_commit" data-commit-id="${commit.raw_id}" title="${_('Expand commit message')}" onclick="commitsController.expandCommit(this, true); return false">
        <i class="icon-expand-linked"></i>&nbsp;
    </td>
    <td class="td-description mid">
      <div class="log-container truncate-wrap">
          <div class="message truncate" id="c-${commit.raw_id}" data-message-raw="${commit.message}">${urlify_commit_message(commit.message, c.repo_name)}</div>
      </div>
    </td>

    <td class="td-time">
        ${h.age_component(commit.date)}
    </td>
    <td class="td-user">
        ${base.gravatar_with_user(commit.author)}
    </td>

    <td class="td-tags tags-col">
    <div id="t-${commit.raw_id}">

        ## merge
        %if commit.merge:
            <span class="tag mergetag">
                <i class="icon-merge"></i>${_('merge')}
            </span>
        %endif

        ## branch
        %if commit.branch:
          <span class="tag branchtag" title="${h.tooltip(_('Branch %s') % commit.branch)}">
             <a href="${h.route_path('repo_commits',repo_name=c.repo_name,_query=dict(branch=commit.branch))}"><i class="icon-code-fork"></i>${h.shorter(commit.branch)}</a>
          </span>
        %endif

        ## bookmarks
        %if h.is_hg(c.rhodecode_repo):
            %for book in commit.bookmarks:
                <span class="tag booktag" title="${h.tooltip(_('Bookmark %s') % book)}">
                  <a href="${h.route_path('repo_files:default_path',repo_name=c.repo_name,commit_id=commit.raw_id, _query=dict(at=book))}"><i class="icon-bookmark"></i>${h.shorter(book)}</a>
                </span>
            %endfor
        %endif

        ## tags
        %for tag in commit.tags:
          <span class="tag tagtag"  title="${h.tooltip(_('Tag %s') % tag)}">
            <a href="${h.route_path('repo_files:default_path',repo_name=c.repo_name,commit_id=commit.raw_id, _query=dict(at=tag))}"><i class="icon-tag"></i>${h.shorter(tag)}</a>
          </span>
        %endfor

      </div>
    </td>

    <td class="td-comments comments-col">
        <% cs_comments = c.comments.get(commit.raw_id,[]) %>
        % if cs_comments:
            <a title="${_('Commit has comments')}" href="${h.route_path('repo_commit',repo_name=c.repo_name,commit_id=commit.raw_id,_anchor='comment-%s' % cs_comments[0].comment_id)}">
                <i class="icon-comment"></i> ${len(cs_comments)}
            </a>
        % else:
            <i class="icon-comment"></i> ${len(cs_comments)}
        % endif
    </td>

</tr>
% endfor

% if c.next_page:
    <tr>
        <td colspan="10" class="load-more-commits">
            <a  class="next-commits" href="#loadNextCommits" onclick="commitsController.loadNext(this, ${c.next_page}, '${c.branch_name}', '${c.commit_id}', '${c.f_path}');return false">
            ${_('load next')}
            </a>
        </td>
    </tr>
% endif
<tr class="chunk-graph-data" style="display:none"
    data-graph='${c.graph_data|n}'
    data-node='${c.prev_page}:${c.next_page}'
    data-commits='${c.graph_commits|n}'>
</tr>