## DATA TABLE RE USABLE ELEMENTS FOR BOOKMARKS
## usage:
## <%namespace name="bookmarks" file="/bookmarks/bookmarks_data.mako"/>
## bookmarks.<func_name>(arg,arg2)
<%namespace name="base" file="/base/base.mako"/>

<%def name="compare(commit_id)">
    <input class="compare-radio-button" type="radio" name="compare_source" value="${commit_id}"/>
    <input class="compare-radio-button" type="radio" name="compare_target" value="${commit_id}"/>
</%def>


<%def name="name(name, files_url, closed)">
     <span class="tag booktag">
     <a href="${files_url}">
         <i class="icon-bookmark"></i>
         ${name}
     </a>
     </span>
</%def>

<%def name="date(date)">
    ${h.age_component(date)}
</%def>

<%def name="author(author)">
    ${base.gravatar_with_user(author, tooltip=True)}
</%def>

<%def name="commit(message, commit_id, commit_idx)">
    <div>
        <pre><a title="${h.tooltip(message)}" href="${h.route_path('repo_files:default_path',repo_name=c.repo_name,commit_id=commit_id)}">r${commit_idx}:${h.short_id(commit_id)}</a></pre>
    </div>
</%def>
