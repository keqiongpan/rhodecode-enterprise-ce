## DATA TABLE RE USABLE ELEMENTS FOR TAGS
## usage:
## <%namespace name="tags" file="/tags/tags_data.mako"/>
## tags.<func_name>(arg,arg2)
<%namespace name="base" file="/base/base.mako"/>

<%def name="compare(commit_id)">
    <input class="compare-radio-button" type="radio" name="compare_source" value="${commit_id}"/>
    <input class="compare-radio-button" type="radio" name="compare_target" value="${commit_id}"/>
</%def>

<%def name="name(name, files_url, closed)">
     <span class="tagtag tag">
     <a href="${files_url}"><i class="icon-tag"></i>${name}</a>
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
        <pre><a class="tooltip" title="${h.tooltip(message)}" href="${h.route_path('repo_files:default_path',repo_name=c.repo_name,commit_id=commit_id)}">r${commit_idx}:${h.short_id(commit_id)}</a></pre>
    </div>
</%def>
