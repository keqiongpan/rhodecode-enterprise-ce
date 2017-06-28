<%def name="refs(commit)">
    %if commit.merge:
        <span class="mergetag tag">
         <i class="icon-merge">${_('merge')}</i>
        </span>
    %endif

    %if h.is_hg(c.rhodecode_repo):
        %for book in commit.bookmarks:
            <span class="booktag tag" title="${h.tooltip(_('Bookmark %s') % book)}">
              <a href="${h.url('files_home',repo_name=c.repo_name,revision=commit.raw_id)}"><i class="icon-bookmark"></i>${h.shorter(book)}</a>
            </span>
        %endfor
    %endif

    %for tag in commit.tags:
        <span class="tagtag tag"  title="${h.tooltip(_('Tag %s') % tag)}">
            <a href="${h.url('files_home',repo_name=c.repo_name,revision=commit.raw_id)}"><i class="icon-tag"></i>${tag}</a>
        </span>
    %endfor

    %if commit.branch:
        <span class="branchtag tag" title="${h.tooltip(_('Branch %s') % commit.branch)}">
          <a href="${h.url('files_home',repo_name=c.repo_name,revision=commit.raw_id)}"><i class="icon-code-fork"></i>${h.shorter(commit.branch)}</a>
        </span>
    %endif

</%def>
