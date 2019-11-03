<%namespace name="base" file="/base/base.mako"/>
<%namespace name="dt" file="/data_table/_dt_elements.mako"/>

<div class="clear-fix">${base.gravatar_with_user(c.commit.author, tooltip=True)}</div>
<br/>
<a href="${h.route_path('repo_commit', repo_name=c.repo_name, commit_id=c.commit.raw_id)}">${h.show_id(c.commit)}</a> - ${c.commit.date}
<br/><br/>
<pre>${h.urlify_commit_message(c.commit.message, c.repo_name)}</pre>
