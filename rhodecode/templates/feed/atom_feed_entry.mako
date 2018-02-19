## -*- coding: utf-8 -*-

${_('%(user)s commited on %(date)s UTC') % {
'user': h.person(commit.author),
'date': h.format_date(commit.date)
}}
<br/>
% if commit.branch:
    branch: ${commit.branch} <br/>
% endif

% for bookmark in getattr(commit, 'bookmarks', []):
    bookmark: ${bookmark} <br/>
% endfor

% for tag in commit.tags:
    tag: ${tag} <br/>
% endfor

% if has_hidden_changes:
    Has hidden changes<br/>
% endif

commit: <a href="${h.route_url('repo_commit', repo_name=c.rhodecode_db_repo.repo_name, commit_id=commit.raw_id)}">${h.show_id(commit)}</a>
<pre>
${h.urlify_commit_message(commit.message)}

% for change in parsed_diff:
  % if limited_diff:
  ${_('Commit was too big and was cut off...')}
  % endif
  ${change['operation']} ${change['filename']} ${'(%(added)s lines added, %(removed)s lines removed)' % {'added': change['stats']['added'], 'removed': change['stats']['deleted']}}
% endfor

% if feed_include_diff:
${c.path_filter.get_raw_patch(diff_processor)}
% endif
</pre>
