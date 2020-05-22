<%namespace name="base" file="/base/base.mako"/>
<%namespace name="file_base" file="/files/base.mako"/>

<div class="summary">
  <div class="fieldset">
    <div class="left-content">
      <%
        rc_user = h.discover_user(c.commit.author_email)
      %>
      <div class="left-content-avatar">
        ${base.gravatar(c.commit.author_email, 30, tooltip=(True if rc_user else False), user=rc_user)}
      </div>

      <div class="left-content-message">
        <div class="fieldset collapsable-content no-hide" data-toggle="summary-details">
          <div class="commit truncate-wrap">${h.urlify_commit_message(h.chop_at_smart(c.commit.message, '\n', suffix_if_chopped='...'), c.repo_name)}</div>
        </div>

        <div class="fieldset collapsable-content" data-toggle="summary-details">
          <div class="commit">${h.urlify_commit_message(c.commit.message,c.repo_name)}</div>
        </div>

        <div class="fieldset clear-fix">
          <span class="commit-author">${h.link_to_user(c.commit.author)}</span><span class="commit-date"> - ${h.age_component(c.commit.date)}</span>
        </div>
      </div>
    </div>

    <div class="right-content">
      <div class="tags">
        <code>
            <a href="${h.route_path('repo_commit',repo_name=c.repo_name,commit_id=c.commit.raw_id)}">${h.show_id(c.commit)}</a>
        </code>

        <i class="tooltip icon-clipboard clipboard-action" data-clipboard-text="${c.commit.raw_id}" title="${_('Copy the full commit id')}"></i>
        ${file_base.refs(c.commit, request.GET.get('at'))}

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
