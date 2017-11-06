<%def name="refs(commit)">
    %if commit.merge:
        <span class="mergetag tag">
         <i class="icon-merge">${_('merge')}</i>
        </span>
    %endif

    %if h.is_hg(c.rhodecode_repo):
        %for book in commit.bookmarks:
            <span class="booktag tag" title="${h.tooltip(_('Bookmark %s') % book)}">
              <a href="${h.route_path('repo_files:default_path',repo_name=c.repo_name,commit_id=commit.raw_id,_query=dict(at=book))}"><i class="icon-bookmark"></i>${h.shorter(book)}</a>
            </span>
        %endfor
    %endif

    %for tag in commit.tags:
        <span class="tagtag tag"  title="${h.tooltip(_('Tag %s') % tag)}">
            <a href="${h.route_path('repo_files:default_path',repo_name=c.repo_name,commit_id=commit.raw_id,_query=dict(at=tag))}"><i class="icon-tag"></i>${tag}</a>
        </span>
    %endfor

    %if commit.branch:
        <span class="branchtag tag" title="${h.tooltip(_('Branch %s') % commit.branch)}">
          <a href="${h.route_path('repo_files:default_path',repo_name=c.repo_name,commit_id=commit.raw_id,_query=dict(at=commit.branch))}"><i class="icon-code-fork"></i>${h.shorter(commit.branch)}</a>
        </span>
    %endif

</%def>
