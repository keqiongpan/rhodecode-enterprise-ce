<%def name="refs(commit, at_rev=None)">

    ## Build a cache of refs for selector, based on this the files ref selector gets pre-selected values
    <script>
        fileTreeRefs = {}
    </script>

    % if h.is_svn(c.rhodecode_repo):
        ## since SVN doesn't have an commit<->refs association, we simply inject it
        ## based on our at_rev marker
        % if at_rev and at_rev.startswith('branches/'):
            <%
                commit.branch = at_rev
            %>
        % endif
        % if at_rev and at_rev.startswith('tags/'):
            <%
                commit.tags.append(at_rev)
            %>
        % endif

    % endif

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
            <script>
                fileTreeRefs["${book}"] = {raw_id: "${commit.raw_id}", type:"book", text: "${book}"};
            </script>
        %endfor
    %endif

    %for tag in commit.tags:
        <span class="tagtag tag"  title="${h.tooltip(_('Tag %s') % tag)}">
            <a href="${h.route_path('repo_files:default_path',repo_name=c.repo_name,commit_id=commit.raw_id,_query=dict(at=tag))}"><i class="icon-tag"></i>${tag}</a>
        </span>
        <script>
            fileTreeRefs["${tag}"] = {raw_id: "${commit.raw_id}", type:"tag", text: "${tag}"};
        </script>
    %endfor

    %if commit.branch:
        <span class="branchtag tag" title="${h.tooltip(_('Branch %s') % commit.branch)}">
          <a href="${h.route_path('repo_files:default_path',repo_name=c.repo_name,commit_id=commit.raw_id,_query=dict(at=commit.branch))}"><i class="icon-code-fork"></i>${h.shorter(commit.branch)}</a>
        </span>
        <script>
            fileTreeRefs["${commit.branch}"] = {raw_id: "${commit.raw_id}", type:"branch", text: "${commit.branch}"};
        </script>
    %endif

</%def>
