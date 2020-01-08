## -*- coding: utf-8 -*-
<%namespace name="base" file="/base/base.mako"/>
%if c.repo_commits:
<table class="rctable repo_summary table_disp">
    <tr>

        <th class="status"></th>
        <th>${_('Commit')}</th>
        <th>${_('Commit message')}</th>
        <th>${_('Age')}</th>
        <th>${_('Author')}</th>
        <th colspan="2">${_('Refs')}</th>
    </tr>

## to speed up lookups cache some functions before the loop
<%
    active_patterns = h.get_active_pattern_entries(c.repo_name)
    urlify_commit_message = h.partial(h.urlify_commit_message, active_pattern_entries=active_patterns)
%>
%for cnt,cs in enumerate(c.repo_commits):
    <tr class="parity${cnt%2}">

        <td class="td-status">
            %if c.statuses.get(cs.raw_id):
                <div class="changeset-status-ico shortlog">
                    %if c.statuses.get(cs.raw_id)[2]:
                    <a class="tooltip" title="${_('Commit status: %s\nClick to open associated pull request #%s') % (c.statuses.get(cs.raw_id)[0], c.statuses.get(cs.raw_id)[2])}" href="${h.route_path('pullrequest_show',repo_name=c.statuses.get(cs.raw_id)[3],pull_request_id=c.statuses.get(cs.raw_id)[2])}">
                        <i class="icon-circle review-status-${c.statuses.get(cs.raw_id)[0]}"></i>
                    </a>
                    %else:
                    <a class="tooltip" title="${_('Commit status: {}').format(h.commit_status_lbl(c.statuses.get(cs.raw_id)[0]))}" href="${h.route_path('repo_commit',repo_name=c.repo_name,commit_id=cs.raw_id,_anchor='comment-%s' % c.comments[cs.raw_id][0].comment_id)}">
                        <i class="icon-circle review-status-${c.statuses.get(cs.raw_id)[0]}"></i>
                    </a>
                    %endif
                </div>
            %else:
                <i class="icon-circle review-status-not_reviewed" title="${_('Commit status: Not Reviewed')}"></i>
            %endif
        </td>
        <td class="td-hash">
            <code>
                <a href="${h.route_path('repo_commit', repo_name=c.repo_name, commit_id=cs.raw_id)}">${h.show_id(cs)}</a>
                <i class="tooltip icon-clipboard clipboard-action" data-clipboard-text="${cs.raw_id}" title="${_('Copy the full commit id')}"></i>
            </code>
        </td>

        <td class="td-description mid">
          <div class="log-container truncate-wrap">
              <div class="message truncate" id="c-${cs.raw_id}">${urlify_commit_message(cs.message, c.repo_name)}</div>
          </div>
        </td>

        <td class="td-time">
            ${h.age_component(cs.date)}
        </td>
        <td class="td-user author">
            ${base.gravatar_with_user(cs.author, tooltip=True)}
        </td>

        <td class="td-tags">
          <div class="autoexpand">
            %if h.is_hg(c.rhodecode_repo):
                %for book in cs.bookmarks:
                     <span class="booktag tag" title="${h.tooltip(_('Bookmark %s') % book)}">
                     <a href="${h.route_path('repo_files:default_path',repo_name=c.repo_name,commit_id=cs.raw_id, _query=dict(at=book))}"><i class="icon-bookmark"></i>${h.shorter(book)}</a>
                     </span>
                %endfor
            %endif
            ## tags
            %for tag in cs.tags:
             <span class="tagtag tag" title="${h.tooltip(_('Tag %s') % tag)}">
             <a href="${h.route_path('repo_files:default_path',repo_name=c.repo_name,commit_id=cs.raw_id, _query=dict(at=tag))}"><i class="icon-tag"></i>${h.shorter(tag)}</a>
             </span>
            %endfor

            ## branch
            %if cs.branch:
             <span class="branchtag tag" title="${h.tooltip(_('Branch %s') % cs.branch)}">
              <a href="${h.route_path('repo_commits',repo_name=c.repo_name,_query=dict(branch=cs.branch))}"><i class="icon-code-fork"></i>${h.shorter(cs.branch)}</a>
             </span>
            %endif
          </div>
        </td>
        <td class="td-comments">
            <% cs_comments = c.comments.get(cs.raw_id,[]) %>
            % if cs_comments:
                <a title="${_('Commit has comments')}" href="${h.route_path('repo_commit',repo_name=c.repo_name,commit_id=cs.raw_id,_anchor='comment-%s' % cs_comments[0].comment_id)}">
                    <i class="icon-comment"></i> ${len(cs_comments)}
                </a>
            % else:
                <i class="icon-comment"></i> ${len(cs_comments)}
            % endif
        </td>
    </tr>
%endfor

</table>

<script type="text/javascript">
  $(document).pjax('#shortlog_data .pager_link','#shortlog_data', {timeout: 5000, scrollTo: false, push: false});
  $(document).on('pjax:success', function(){ timeagoActivate(); tooltipActivate();});
  $(document).on('pjax:timeout', function(event) {
    // Prevent default timeout redirection behavior
    event.preventDefault()
  })

</script>

<div class="pagination-wh pagination-left">
${c.repo_commits.render()}
</div>
%else:

%if h.HasRepoPermissionAny('repository.write','repository.admin')(c.repo_name):
<div class="quick_start">
  <div class="fieldset">
    <p><b>${_('Add or upload files directly via RhodeCode:')}</b></p>
    <div class="pull-left">
        <a href="${h.route_path('repo_files_add_file',repo_name=c.repo_name,commit_id=0, f_path='')}" class="btn btn-default">${_('Add New File')}</a>
    </div>
    <div class="pull-left">
        <a href="${h.route_path('repo_files_upload_file',repo_name=c.repo_name,commit_id=0, f_path='')}" class="btn btn-default">${_('Upload New File')}</a>
    </div>
    %endif
  </div>

<div class="fieldset">
<p><b>${_('Push new repo:')}</b></p>
<pre>
%if h.is_git(c.rhodecode_repo):
git clone ${c.clone_repo_url}
git add README # add first file
git commit -m "Initial commit" # commit with message
git remote add origin ${c.clone_repo_url}
git push -u origin master # push changes back to default master branch
%elif h.is_hg(c.rhodecode_repo):
hg clone ${c.clone_repo_url}
hg add README # add first file
hg commit -m "Initial commit" # commit with message
hg push ${c.clone_repo_url}
%elif h.is_svn(c.rhodecode_repo):
svn co ${c.clone_repo_url}
svn add README # add first file
svn commit -m "Initial commit"
svn commit  # send changes back to the server
%endif
</pre>
</div>

<div class="fieldset">
<p><b>${_('Existing repository?')}</b></p>
<pre>
%if h.is_git(c.rhodecode_repo):
git remote add origin ${c.clone_repo_url}
git push -u origin master
%elif h.is_hg(c.rhodecode_repo):
hg push ${c.clone_repo_url}
%elif h.is_svn(c.rhodecode_repo):
svn co ${c.clone_repo_url}
%endif
</pre>

</div>


</div>
%endif
