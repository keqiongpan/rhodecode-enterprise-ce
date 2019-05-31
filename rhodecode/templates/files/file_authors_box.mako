<%namespace name="base" file="/base/base.mako"/>

% if c.authors:

<table class="sidebar-right-content">
    % for email, user, commits in sorted(c.authors, key=lambda e: c.file_last_commit.author_email!=e[0]):
    <tr class="file_author tooltip" title="${h.tooltip(h.author_string(email))}">

        <td>
            <span class="user commit-author">${h.link_to_user(user)}</span>
            % if c.file_author:
                <span class="commit-date">- ${h.age_component(c.file_last_commit.date)}</span>
                <a href="#ShowAuthors" onclick="showAuthors(this, ${("1" if c.annotate else "0")}); return false" class="action_link"> - ${_('Load All Authors')}</a>
            % elif c.file_last_commit.author_email==email:
                <span> (${_('last author')})</span>
            % endif
        </td>

        <td>
            % if not c.file_author:
                <code>
                  % if commits == 1:
                    ${commits} ${_('Commit')}
                  % else:
                    ${commits} ${_('Commits')}
                  % endif
                </code>
            % endif
        </td>
    </tr>

    % endfor
</table>
% endif

