<%namespace name="base" file="/base/base.mako"/>
<%namespace name="file_base" file="/files/base.mako"/>

<div class="summary">
  <div class="fieldset">
    <div class="left-content">

      <div class="left-content-avatar">
        ${base.gravatar(c.file_last_commit.author_email, 30)}
      </div>

      <div class="left-content-message">
      <div class="fieldset collapsable-content no-hide" data-toggle="summary-details">
        <div class="commit truncate-wrap">${h.urlify_commit_message(h.chop_at_smart(c.commit.message, '\n', suffix_if_chopped='...'), c.repo_name)}</div>
      </div>

      <div class="fieldset collapsable-content" data-toggle="summary-details">
        <div class="commit">${h.urlify_commit_message(c.commit.message,c.repo_name)}</div>
      </div>

      <div class="fieldset" data-toggle="summary-details">
        <div class="" id="file_authors">
          ## loads single author, or ALL
          <%include file='file_authors_box.mako'/>
        </div>
      </div>
      </div>

      <div class="fieldset collapsable-content" data-toggle="summary-details">
        <div class="left-label-summary-files">
            <p>${_('File last commit')}</p>
            <div class="right-label-summary">
              <code><a href="${h.route_path('repo_commit',repo_name=c.repo_name,commit_id=c.file_last_commit.raw_id)}">${h.show_id(c.file_last_commit)}</a></code>

            ${file_base.refs(c.file_last_commit)}
          </div>
        </div>
      </div>
    </div>

    <div class="right-content">
      <div data-toggle="summary-details">
          <div class="tags commit-info tags-main">
            <code><a href="${h.route_path('repo_commit',repo_name=c.repo_name,commit_id=c.commit.raw_id)}">${h.show_id(c.commit)}</a></code>
            ${file_base.refs(c.commit)}
          </div>
      </div>
    </div>

    <div class="clear-fix"></div>

    <div  class="btn-collapse" data-toggle="summary-details">
        ${_('Show More')}
    </div>

  </div>
</div>

<script>
  collapsableContent();
</script>
