## DATA TABLE RE USABLE ELEMENTS
## usage:
## <%namespace name="dt" file="/data_table/_dt_elements.mako"/>
<%namespace name="base" file="/base/base.mako"/>

<%def name="metatags_help()">
    <table>
        <%
            example_tags = [
                ('state','[stable]'),
                ('state','[stale]'),
                ('state','[featured]'),
                ('state','[dev]'),
                ('state','[dead]'),
                ('state','[deprecated]'),

                ('label','[personal]'),
                ('generic','[v2.0.0]'),

                ('lang','[lang =&gt; JavaScript]'),
                ('license','[license =&gt; LicenseName]'),

                ('ref','[requires =&gt; RepoName]'),
                ('ref','[recommends =&gt; GroupName]'),
                ('ref','[conflicts =&gt; SomeName]'),
                ('ref','[base =&gt; SomeName]'),
                ('url','[url =&gt; [linkName](https://rhodecode.com)]'),
                ('see','[see =&gt; http://rhodecode.com]'),
            ]
        %>
        % for tag_type, tag in example_tags:
            <tr>
                <td>${tag|n}</td>
                <td>${h.style_metatag(tag_type, tag)|n}</td>
            </tr>
        % endfor
    </table>
</%def>

<%def name="render_description(description, stylify_metatags)">
<%
    tags = []
    if stylify_metatags:
        tags, description = h.extract_metatags(description)
%>
% for tag_type, tag in tags:
${h.style_metatag(tag_type, tag)|n,trim}
% endfor
<code style="white-space: pre-wrap">${description}</code>
</%def>

## REPOSITORY RENDERERS
<%def name="quick_menu(repo_name)">
  <i class="icon-more"></i>
  <div class="menu_items_container hidden">
    <ul class="menu_items">
      <li>
         <a title="${_('Summary')}" href="${h.route_path('repo_summary',repo_name=repo_name)}">
         <span>${_('Summary')}</span>
         </a>
      </li>
      <li>
         <a title="${_('Commits')}" href="${h.route_path('repo_commits',repo_name=repo_name)}">
         <span>${_('Commits')}</span>
         </a>
      </li>
      <li>
         <a title="${_('Files')}" href="${h.route_path('repo_files:default_commit',repo_name=repo_name)}">
         <span>${_('Files')}</span>
         </a>
      </li>
      <li>
         <a title="${_('Fork')}" href="${h.route_path('repo_fork_new',repo_name=repo_name)}">
         <span>${_('Fork')}</span>
         </a>
      </li>
    </ul>
  </div>
</%def>

<%def name="repo_name(name,rtype,rstate,private,archived,fork_of,short_name=False,admin=False)">
    <%
    def get_name(name,short_name=short_name):
      if short_name:
        return name.split('/')[-1]
      else:
        return name
    %>
  <div class="${'repo_state_pending' if rstate == 'repo_state_pending' else ''} truncate">
    ##NAME
    <a href="${h.route_path('edit_repo',repo_name=name) if admin else h.route_path('repo_summary',repo_name=name)}">

    ##TYPE OF REPO
    %if h.is_hg(rtype):
        <span title="${_('Mercurial repository')}"><i class="icon-hg" style="font-size: 14px;"></i></span>
    %elif h.is_git(rtype):
        <span title="${_('Git repository')}"><i class="icon-git" style="font-size: 14px"></i></span>
    %elif h.is_svn(rtype):
        <span title="${_('Subversion repository')}"><i class="icon-svn" style="font-size: 14px"></i></span>
    %endif

    ##PRIVATE/PUBLIC
    %if private is True and c.visual.show_private_icon:
      <i class="icon-lock" title="${_('Private repository')}"></i>
    %elif private is False and c.visual.show_public_icon:
      <i class="icon-unlock-alt" title="${_('Public repository')}"></i>
    %else:
      <span></span>
    %endif
    ${get_name(name)}
    </a>
    %if fork_of:
      <a href="${h.route_path('repo_summary',repo_name=fork_of.repo_name)}"><i class="icon-code-fork"></i></a>
    %endif
    %if rstate == 'repo_state_pending':
      <span class="creation_in_progress tooltip" title="${_('This repository is being created in a background task')}">
          (${_('creating...')})
      </span>
    %endif

  </div>
</%def>

<%def name="repo_desc(description, stylify_metatags)">
    <%
    tags, description = h.extract_metatags(description)
    %>

    <div class="truncate-wrap">
        % if stylify_metatags:
            % for tag_type, tag in tags:
                ${h.style_metatag(tag_type, tag)|n}
            % endfor
        % endif
        ${description}
    </div>

</%def>

<%def name="last_change(last_change)">
    ${h.age_component(last_change, time_is_local=True)}
</%def>

<%def name="revision(repo_name, rev, commit_id, author, last_msg, commit_date)">
  <div>
  %if rev >= 0:
      <code><a class="tooltip-hovercard" data-hovercard-alt=${h.tooltip(last_msg)} data-hovercard-url="${h.route_path('hovercard_repo_commit', repo_name=repo_name, commit_id=commit_id)}" href="${h.route_path('repo_commit',repo_name=repo_name,commit_id=commit_id)}">${'r{}:{}'.format(rev,h.short_id(commit_id))}</a></code>
  %else:
      ${_('No commits yet')}
  %endif
  </div>
</%def>

<%def name="rss(name)">
  %if c.rhodecode_user.username != h.DEFAULT_USER:
    <a title="${h.tooltip(_('Subscribe to %s rss feed')% name)}" href="${h.route_path('rss_feed_home', repo_name=name, _query=dict(auth_token=c.rhodecode_user.feed_token))}"><i class="icon-rss-sign"></i></a>
  %else:
    <a title="${h.tooltip(_('Subscribe to %s rss feed')% name)}" href="${h.route_path('rss_feed_home', repo_name=name)}"><i class="icon-rss-sign"></i></a>
  %endif
</%def>

<%def name="atom(name)">
  %if c.rhodecode_user.username != h.DEFAULT_USER:
    <a title="${h.tooltip(_('Subscribe to %s atom feed')% name)}" href="${h.route_path('atom_feed_home', repo_name=name, _query=dict(auth_token=c.rhodecode_user.feed_token))}"><i class="icon-rss-sign"></i></a>
  %else:
    <a title="${h.tooltip(_('Subscribe to %s atom feed')% name)}" href="${h.route_path('atom_feed_home', repo_name=name)}"><i class="icon-rss-sign"></i></a>
  %endif
</%def>

<%def name="repo_actions(repo_name, super_user=True)">
  <div>
    <div class="grid_edit">
      <a href="${h.route_path('edit_repo',repo_name=repo_name)}" title="${_('Edit')}">
        Edit
      </a>
    </div>
    <div class="grid_delete">
      ${h.secure_form(h.route_path('edit_repo_advanced_delete', repo_name=repo_name), request=request)}
        <input class="btn btn-link btn-danger" id="remove_${repo_name}" name="remove_${repo_name}"
               onclick="submitConfirm(event, this, _gettext('Confirm to delete this repository'), _gettext('Delete'), '${repo_name}')"
               type="submit" value="Delete"
        >
      ${h.end_form()}
    </div>
  </div>
</%def>

<%def name="repo_state(repo_state)">
  <div>
    %if repo_state == 'repo_state_pending':
        <div class="tag tag4">${_('Creating')}</div>
    %elif repo_state == 'repo_state_created':
        <div class="tag tag1">${_('Created')}</div>
    %else:
        <div class="tag alert2" title="${h.tooltip(repo_state)}">invalid</div>
    %endif
  </div>
</%def>


## REPO GROUP RENDERERS
<%def name="quick_repo_group_menu(repo_group_name)">
  <i class="icon-more"></i>
  <div class="menu_items_container hidden">
    <ul class="menu_items">
      <li>
         <a href="${h.route_path('repo_group_home', repo_group_name=repo_group_name)}">${_('Summary')}</a>
      </li>

    </ul>
  </div>
</%def>

<%def name="repo_group_name(repo_group_name, children_groups=None)">
  <div>
    <a href="${h.route_path('repo_group_home', repo_group_name=repo_group_name)}">
    <i class="icon-repo-group" title="${_('Repository group')}" style="font-size: 14px"></i>
      %if children_groups:
          ${h.literal(' &raquo; '.join(children_groups))}
      %else:
          ${repo_group_name}
      %endif
  </a>
  </div>
</%def>

<%def name="repo_group_desc(description, personal, stylify_metatags)">

    <%
        if stylify_metatags:
            tags, description = h.extract_metatags(description)
    %>

    <div class="truncate-wrap">
        % if personal:
            <div class="metatag" tag="personal">${_('personal')}</div>
        % endif

        % if stylify_metatags:
            % for tag_type, tag in tags:
                ${h.style_metatag(tag_type, tag)|n}
            % endfor
        % endif
        ${description}
    </div>

</%def>

<%def name="repo_group_actions(repo_group_id, repo_group_name, gr_count)">
 <div class="grid_edit">
    <a href="${h.route_path('edit_repo_group',repo_group_name=repo_group_name)}" title="${_('Edit')}">Edit</a>
 </div>
 <div class="grid_delete">
    ${h.secure_form(h.route_path('edit_repo_group_advanced_delete', repo_group_name=repo_group_name), request=request)}
        <input class="btn btn-link btn-danger" id="remove_${repo_group_name}" name="remove_${repo_group_name}"
               onclick="submitConfirm(event, this, _gettext('Confirm to delete this repository group'), _gettext('Delete'), '${_ungettext('`{}` with {} repository','`{}` with {} repositories',gr_count).format(repo_group_name, gr_count)}')"
               type="submit" value="Delete"
        >
    ${h.end_form()}
 </div>
</%def>


<%def name="user_actions(user_id, username)">
 <div class="grid_edit">
   <a href="${h.route_path('user_edit',user_id=user_id)}" title="${_('Edit')}">
     ${_('Edit')}
   </a>
 </div>
 <div class="grid_delete">
  ${h.secure_form(h.route_path('user_delete', user_id=user_id), request=request)}
    <input class="btn btn-link btn-danger" id="remove_user_${user_id}" name="remove_user_${user_id}"
           onclick="submitConfirm(event, this, _gettext('Confirm to delete this user'), _gettext('Delete'), '${username}')"
           type="submit" value="Delete"
    >
  ${h.end_form()}
 </div>
</%def>

<%def name="user_group_actions(user_group_id, user_group_name)">
 <div class="grid_edit">
    <a href="${h.route_path('edit_user_group', user_group_id=user_group_id)}" title="${_('Edit')}">Edit</a>
 </div>
 <div class="grid_delete">
    ${h.secure_form(h.route_path('user_groups_delete', user_group_id=user_group_id), request=request)}
        <input class="btn btn-link btn-danger" id="remove_group_${user_group_id}" name="remove_group_${user_group_id}"
               onclick="submitConfirm(event, this, _gettext('Confirm to delete this user group'), _gettext('Delete'), '${user_group_name}')"
               type="submit" value="Delete"
        >
    ${h.end_form()}
 </div>
</%def>


<%def name="user_name(user_id, username)">
    ${h.link_to(h.person(username, 'username_or_name_or_email'), h.route_path('user_edit', user_id=user_id))}
</%def>

<%def name="user_profile(username)">
    ${base.gravatar_with_user(username, 16, tooltip=True)}
</%def>

<%def name="user_group_name(user_group_name)">
  <div>
      <i class="icon-user-group" title="${_('User group')}"></i>
      ${h.link_to_group(user_group_name)}
  </div>
</%def>


## GISTS

<%def name="gist_gravatar(full_contact)">
    <div class="gist_gravatar">
      ${base.gravatar(full_contact, 30)}
    </div>
</%def>

<%def name="gist_access_id(gist_access_id, full_contact)">
    <div>
      <code>
        <a href="${h.route_path('gist_show', gist_id=gist_access_id)}">${gist_access_id}</a>
      </code>
    </div>
</%def>

<%def name="gist_author(full_contact, created_on, expires)">
    ${base.gravatar_with_user(full_contact, 16, tooltip=True)}
</%def>


<%def name="gist_created(created_on)">
    <div class="created">
      ${h.age_component(created_on, time_is_local=True)}
    </div>
</%def>

<%def name="gist_expires(expires)">
    <div class="created">
          %if expires == -1:
            ${_('never')}
          %else:
            ${h.age_component(h.time_to_utcdatetime(expires))}
          %endif
    </div>
</%def>

<%def name="gist_type(gist_type)">
    %if gist_type == 'public':
        <span class="tag tag-gist-public disabled">${_('Public Gist')}</span>
    %else:
        <span class="tag tag-gist-private disabled">${_('Private Gist')}</span>
    %endif
</%def>

<%def name="gist_description(gist_description)">
  ${gist_description}
</%def>


## PULL REQUESTS GRID RENDERERS

<%def name="pullrequest_target_repo(repo_name)">
    <div class="truncate">
      ${h.link_to(repo_name,h.route_path('repo_summary',repo_name=repo_name))}
    </div>
</%def>

<%def name="pullrequest_status(status)">
    <i class="icon-circle review-status-${status}"></i>
</%def>

<%def name="pullrequest_title(title, description)">
    ${title}
</%def>

<%def name="pullrequest_comments(comments_nr)">
    <i class="icon-comment"></i> ${comments_nr}
</%def>

<%def name="pullrequest_name(pull_request_id, state, is_wip, target_repo_name, short=False)">
    <code>
    <a href="${h.route_path('pullrequest_show',repo_name=target_repo_name,pull_request_id=pull_request_id)}">
      % if short:
        !${pull_request_id}
      % else:
        ${_('Pull request !{}').format(pull_request_id)}
      % endif
    </a>
    </code>
    % if state not in ['created']:
        <span class="tag tag-merge-state-${state} tooltip" title="Pull request state is changing">${state}</span>
    % endif

    % if is_wip:
        <span class="tag tooltip" title="${_('Work in progress')}">wip</span>
    % endif
</%def>

<%def name="pullrequest_updated_on(updated_on, pr_version=None)">
    % if pr_version:
    <code>v${pr_version}</code>
    % endif
    ${h.age_component(h.time_to_utcdatetime(updated_on))}
</%def>

<%def name="pullrequest_author(full_contact)">
    ${base.gravatar_with_user(full_contact, 16, tooltip=True)}
</%def>


## ARTIFACT RENDERERS
<%def name="repo_artifact_name(repo_name, file_uid, artifact_display_name)">
    <a href="${h.route_path('repo_artifacts_get', repo_name=repo_name, uid=file_uid)}">
        ${artifact_display_name or '_EMPTY_NAME_'}
    </a>
</%def>

<%def name="repo_artifact_admin_name(file_uid, artifact_display_name)">
    <a href="${h.route_path('admin_artifacts_show_info', uid=file_uid)}">
        ${(artifact_display_name or '_EMPTY_NAME_')}
    </a>
</%def>

<%def name="repo_artifact_uid(repo_name, file_uid)">
    <code>${h.shorter(file_uid, size=24, prefix=True)}</code>
</%def>

<%def name="repo_artifact_sha256(artifact_sha256)">
    <div class="code">${h.shorter(artifact_sha256, 12)}</div>
</%def>

<%def name="repo_artifact_actions(repo_name, file_store_id, file_uid)">
##  <div class="grid_edit">
##     <a href="#Edit" title="${_('Edit')}">${_('Edit')}</a>
##  </div>
<div class="grid_edit">
    <a href="${h.route_path('repo_artifacts_info', repo_name=repo_name, uid=file_store_id)}" title="${_('Info')}">${_('Info')}</a>
</div>
    % if h.HasRepoPermissionAny('repository.admin')(c.repo_name):
    <div class="grid_delete">
    ${h.secure_form(h.route_path('repo_artifacts_delete', repo_name=repo_name, uid=file_store_id), request=request)}
      <input class="btn btn-link btn-danger" id="remove_artifact_${file_store_id}" name="remove_artifact_${file_store_id}"
             onclick="submitConfirm(event, this, _gettext('Confirm to delete this artifact'), _gettext('Delete'), '${file_uid}')"
             type="submit" value="${_('Delete')}"
      >
    ${h.end_form()}
 </div>
% endif
</%def>


<%def name="markup_form(form_id, form_text='', help_text=None)">

  <div class="markup-form">
    <div class="markup-form-area">
        <div class="markup-form-area-header">
            <ul class="nav-links clearfix">
                <li class="active">
                    <a href="#edit-text" tabindex="-1" id="edit-btn_${form_id}">${_('Write')}</a>
                </li>
                <li class="">
                    <a href="#preview-text" tabindex="-1" id="preview-btn_${form_id}">${_('Preview')}</a>
                </li>
            </ul>
        </div>

        <div class="markup-form-area-write" style="display: block;">
            <div id="edit-container_${form_id}" style="margin-top: -1px">
                <textarea id="${form_id}" name="${form_id}" class="comment-block-ta ac-input">${form_text if form_text else ''}</textarea>
            </div>
            <div id="preview-container_${form_id}" class="clearfix" style="display: none;">
                <div id="preview-box_${form_id}" class="preview-box"></div>
            </div>
        </div>

        <div class="markup-form-area-footer">
            <div class="toolbar">
                <div class="toolbar-text">
                  ${(_('Parsed using %s syntax') % (
                           ('<a href="%s">%s</a>' % (h.route_url('%s_help' % c.visual.default_renderer), c.visual.default_renderer.upper())),
                       )
                    )|n}
                </div>
            </div>
        </div>
    </div>

    <div class="markup-form-footer">
        % if help_text:
            <span class="help-block">${help_text}</span>
        % endif
    </div>
  </div>
  <script type="text/javascript">
    new MarkupForm('${form_id}');
  </script>

</%def>
