<%namespace name="base" file="/base/base.mako"/>

<div class="summary-detail-header">
    <h4 class="item">
        % if c.file_author:
            ${_('Last Author')}
        % else:
            ${h.literal(_ungettext(u'File Author (%s)',u'File Authors (%s)',len(c.authors)) % ('<b>%s</b>' % len(c.authors))) }
        % endif
    </h4>
    <a href="#" id="show_authors" class="action_link">${_('Show All')}</a>
</div>

% if c.authors:
<ul class="sidebar-right-content">
    % for email, user, commits in sorted(c.authors, key=lambda e: c.file_last_commit.author_email!=e[0]):
    <li class="file_author">
        <div class="tooltip" title="${h.tooltip(h.author_string(email))}">
          ${base.gravatar(email, 16)}
          <div class="user">${h.link_to_user(user)}</div>

            % if c.file_author:
                <span>- ${h.age_component(c.file_last_commit.date)}</span>
            % elif c.file_last_commit.author_email==email:
                <span> (${_('last author')})</span>
            % endif

            % if not c.file_author:
                <span>
                  % if commits == 1:
                    ${commits} ${_('Commit')}
                  % else:
                    ${commits} ${_('Commits')}
                  % endif
                </span>
            % endif

        </div>
    </li>
    % endfor
</ul>
% endif
