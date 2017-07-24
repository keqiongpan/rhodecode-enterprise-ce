<%namespace name="file_base" file="/files/base.mako"/>

<div class="fieldset collapsable-content no-hide" data-toggle="summary-details">
  <div class="left-label">
    ${_('Commit Description')}:
  </div>
  <div class="commit right-content truncate-wrap">${h.urlify_commit_message(h.chop_at_smart(c.commit.message, '\n', suffix_if_chopped='...'), c.repo_name)}</div>
</div>

<div class="fieldset collapsable-content" data-toggle="summary-details">
  <div class="left-label">
    ${_('Commit Description')}:
  </div>
  <div class="commit right-content">${h.urlify_commit_message(c.commit.message,c.repo_name)}</div>
</div>


<div class="fieldset " data-toggle="summary-details">
  <div class="left-label">
    ${_('References')}:
  </div>
  <div class="right-content">
    <div class="tags tags-main">
      <code><a href="${h.route_path('repo_commit',repo_name=c.repo_name,commit_id=c.commit.raw_id)}">${h.show_id(c.commit)}</a></code>
      ${file_base.refs(c.commit)}
    </div>
  </div>
</div>

<div class="fieldset collapsable-content" data-toggle="summary-details">
  <div class="left-label">
    ${_('File last commit')}:
  </div>
  <div class="right-content">
    <div class="tags">
      <code><a href="${h.route_path('repo_commit',repo_name=c.repo_name,commit_id=c.file_last_commit.raw_id)}">${h.show_id(c.file_last_commit)}</a></code>

      ${file_base.refs(c.file_last_commit)}
    </div>
  </div>
</div>


<div class="fieldset collapsable-content" data-toggle="summary-details">
  <div class="left-label">
    ${_('Show/Diff file')}:
  </div>
  <div class="right-content">
  ${h.hidden('diff1')}
  ${h.hidden('diff2',c.commit.raw_id)}
  ${h.hidden('annotate', c.annotate)}
  </div>
</div>


<div class="fieldset collapsable-content" data-toggle="summary-details">
  <div class="left-label">
    ${_('Action')}:
  </div>
  <div class="right-content">
  ${h.submit('diff_to_commit',_('Diff to Commit'),class_="btn disabled",disabled="true")}
  ${h.submit('show_at_commit',_('Show at Commit'),class_="btn disabled",disabled="true")}
  </div>
</div>


<script>
  collapsableContent();
</script>