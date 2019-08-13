<%namespace name="commentblock" file="/changeset/changeset_file_comment.mako"/>

<%def name="diff_line_anchor(commit, filename, line, type)"><%
return '%s_%s_%i' % (h.md5_safe(commit+filename), type, line)
%></%def>

<%def name="action_class(action)">
<%
    return {
        '-': 'cb-deletion',
        '+': 'cb-addition',
        ' ': 'cb-context',
        }.get(action, 'cb-empty')
%>
</%def>

<%def name="op_class(op_id)">
<%
    return {
        DEL_FILENODE: 'deletion', # file deleted
        BIN_FILENODE: 'warning' # binary diff hidden
    }.get(op_id, 'addition')
%>
</%def>



<%def name="render_diffset(diffset, commit=None,

    # collapse all file diff entries when there are more than this amount of files in the diff
    collapse_when_files_over=20,

    # collapse lines in the diff when more than this amount of lines changed in the file diff
    lines_changed_limit=500,

    # add a ruler at to the output
    ruler_at_chars=0,

    # show inline comments
    use_comments=False,

    # disable new comments
    disable_new_comments=False,

    # special file-comments that were deleted in previous versions
    # it's used for showing outdated comments for deleted files in a PR
    deleted_files_comments=None,

    # for cache purpose
    inline_comments=None,

    # additional menu for PRs
    pull_request_menu=None

)">

<%
    diffset_container_id = h.md5(diffset.target_ref)
    collapse_all = len(diffset.files) > collapse_when_files_over
%>

%if use_comments:
<div id="cb-comments-inline-container-template" class="js-template">
  ${inline_comments_container([], inline_comments)}
</div>
<div class="js-template" id="cb-comment-inline-form-template">
    <div class="comment-inline-form ac">

    %if c.rhodecode_user.username != h.DEFAULT_USER:
        ## render template for inline comments
        ${commentblock.comment_form(form_type='inline')}
    %else:
        ${h.form('', class_='inline-form comment-form-login', method='get')}
        <div class="pull-left">
            <div class="comment-help pull-right">
              ${_('You need to be logged in to leave comments.')} <a href="${h.route_path('login', _query={'came_from': h.current_route_path(request)})}">${_('Login now')}</a>
            </div>
        </div>
        <div class="comment-button pull-right">
         <button type="button" class="cb-comment-cancel" onclick="return Rhodecode.comments.cancelComment(this);">
          ${_('Cancel')}
         </button>
        </div>
        <div class="clearfix"></div>
        ${h.end_form()}
    %endif
    </div>
</div>

%endif

%if c.user_session_attrs["diffmode"] == 'sideside':
<style>
.wrapper {
    max-width: 1600px !important;
}
</style>
%endif

%if ruler_at_chars:
<style>
.diff table.cb .cb-content:after {
    content: "";
    border-left: 1px solid blue;
    position: absolute;
    top: 0;
    height: 18px;
    opacity: .2;
    z-index: 10;
    //## +5 to account for diff action (+/-)
    left: ${ruler_at_chars + 5}ch;
</style>
%endif

<div class="diffset ${disable_new_comments and 'diffset-comments-disabled'}">

    <div style="height: 20px; line-height: 20px">
        ## expand/collapse action
        <div class="pull-left">
            <a class="${'collapsed' if collapse_all else ''}" href="#expand-files" onclick="toggleExpand(this, '${diffset_container_id}'); return false">
            % if collapse_all:
                <i class="icon-plus-squared-alt icon-no-margin"></i>${_('Expand all files')}
            % else:
                <i class="icon-minus-squared-alt icon-no-margin"></i>${_('Collapse all files')}
            % endif
            </a>

        </div>

        ## todos
        % if getattr(c, 'at_version', None):
        <div class="pull-right">
            <i class="icon-flag-filled" style="color: #949494">TODOs:</i>
             ${_('not available in this view')}
        </div>
        % else:
        <div class="pull-right">
            <div class="comments-number" style="padding-left: 10px">
                % if hasattr(c, 'unresolved_comments') and hasattr(c, 'resolved_comments'):
                    <i class="icon-flag-filled" style="color: #949494">TODOs:</i>
                    % if c.unresolved_comments:
                        <a href="#show-todos" onclick="$('#todo-box').toggle(); return false">
                            ${_('{} unresolved').format(len(c.unresolved_comments))}
                        </a>
                    % else:
                        ${_('0 unresolved')}
                    % endif

                    ${_('{} Resolved').format(len(c.resolved_comments))}
                % endif
            </div>
        </div>
        % endif

        ## comments
        <div class="pull-right">
            <div class="comments-number" style="padding-left: 10px">
                % if hasattr(c, 'comments') and hasattr(c, 'inline_cnt'):
                    <i class="icon-comment" style="color: #949494">COMMENTS:</i>
                    % if c.comments:
                        <a href="#comments">${_ungettext("{} General", "{} General", len(c.comments)).format(len(c.comments))}</a>,
                    % else:
                        ${_('0 General')}
                    % endif

                    % if c.inline_cnt:
                        <a href="#" onclick="return Rhodecode.comments.nextComment();"
                           id="inline-comments-counter">${_ungettext("{} Inline", "{} Inline", c.inline_cnt).format(c.inline_cnt)}
                        </a>
                    % else:
                        ${_('0 Inline')}
                    % endif
                % endif

                % if pull_request_menu:
                    <%
                    outdated_comm_count_ver = pull_request_menu['outdated_comm_count_ver']
                    %>

                    % if outdated_comm_count_ver:
                        <a href="#" onclick="showOutdated(); Rhodecode.comments.nextOutdatedComment(); return false;">
                            (${_("{} Outdated").format(outdated_comm_count_ver)})
                        </a>
                        <a href="#" class="showOutdatedComments" onclick="showOutdated(this); return false;"> | ${_('show outdated')}</a>
                        <a href="#" class="hideOutdatedComments" style="display: none" onclick="hideOutdated(this); return false;"> | ${_('hide outdated')}</a>
                    % else:
                        (${_("{} Outdated").format(outdated_comm_count_ver)})
                    % endif

                % endif

            </div>
        </div>

    </div>

    % if diffset.limited_diff:
        <div class="diffset-heading ${(diffset.limited_diff and 'diffset-heading-warning' or '')}">
            <h2 class="clearinner">
                ${_('The requested changes are too big and content was truncated.')}
                <a href="${h.current_route_path(request, fulldiff=1)}" onclick="return confirm('${_("Showing a big diff might take some time and resources, continue?")}')">${_('Show full diff')}</a>
            </h2>
        </div>
    ## commit range header for each individual diff
    % elif commit and hasattr(c, 'commit_ranges') and len(c.commit_ranges) > 1:
        <div class="diffset-heading ${(diffset.limited_diff and 'diffset-heading-warning' or '')}">
            <div class="clearinner">
                <a class="tooltip revision" title="${h.tooltip(commit.message)}" href="${h.route_path('repo_commit',repo_name=diffset.repo_name,commit_id=commit.raw_id)}">${('r%s:%s' % (commit.idx,h.short_id(commit.raw_id)))}</a>
            </div>
        </div>
    % endif

    <div id="todo-box">
        % if hasattr(c, 'unresolved_comments') and c.unresolved_comments:
            % for co in c.unresolved_comments:
                <a class="permalink" href="#comment-${co.comment_id}"
                   onclick="Rhodecode.comments.scrollToComment($('#comment-${co.comment_id}'))">
                    <i class="icon-flag-filled-red"></i>
                    ${co.comment_id}</a>${('' if loop.last else ',')}
            % endfor
        % endif
    </div>
    %if diffset.has_hidden_changes:
        <p class="empty_data">${_('Some changes may be hidden')}</p>
    %elif not diffset.files:
        <p class="empty_data">${_('No files')}</p>
    %endif

    <div class="filediffs">

    ## initial value could be marked as False later on
    <% over_lines_changed_limit = False %>
    %for i, filediff in enumerate(diffset.files):

        <%
        lines_changed = filediff.patch['stats']['added'] + filediff.patch['stats']['deleted']
        over_lines_changed_limit = lines_changed > lines_changed_limit
        %>
        ## anchor with support of sticky header
        <div class="anchor" id="a_${h.FID(filediff.raw_id, filediff.patch['filename'])}"></div>

        <input ${(collapse_all and 'checked' or '')} class="filediff-collapse-state collapse-${diffset_container_id}" id="filediff-collapse-${id(filediff)}" type="checkbox" onchange="updateSticky();">
        <div
            class="filediff"
            data-f-path="${filediff.patch['filename']}"
            data-anchor-id="${h.FID(filediff.raw_id, filediff.patch['filename'])}"
        >
        <label for="filediff-collapse-${id(filediff)}" class="filediff-heading">
            <div class="filediff-collapse-indicator icon-"></div>
            ${diff_ops(filediff)}
        </label>

        ${diff_menu(filediff, use_comments=use_comments)}
        <table data-f-path="${filediff.patch['filename']}" data-anchor-id="${h.FID(filediff.raw_id, filediff.patch['filename'])}" class="code-visible-block cb cb-diff-${c.user_session_attrs["diffmode"]} code-highlight ${(over_lines_changed_limit and 'cb-collapsed' or '')}">

        ## new/deleted/empty content case
        % if not filediff.hunks:
            ## Comment container, on "fakes" hunk that contains all data to render comments
            ${render_hunk_lines(filediff, c.user_session_attrs["diffmode"], filediff.hunk_ops, use_comments=use_comments, inline_comments=inline_comments)}
        % endif

        %if filediff.limited_diff:
                <tr class="cb-warning cb-collapser">
                    <td class="cb-text" ${(c.user_session_attrs["diffmode"] == 'unified' and 'colspan=4' or 'colspan=6')}>
                        ${_('The requested commit or file is too big and content was truncated.')} <a href="${h.current_route_path(request, fulldiff=1)}" onclick="return confirm('${_("Showing a big diff might take some time and resources, continue?")}')">${_('Show full diff')}</a>
                    </td>
                </tr>
        %else:
            %if over_lines_changed_limit:
                <tr class="cb-warning cb-collapser">
                    <td class="cb-text" ${(c.user_session_attrs["diffmode"] == 'unified' and 'colspan=4' or 'colspan=6')}>
                        ${_('This diff has been collapsed as it changes many lines, (%i lines changed)' % lines_changed)}
                        <a href="#" class="cb-expand"
                           onclick="$(this).closest('table').removeClass('cb-collapsed'); updateSticky(); return false;">${_('Show them')}
                        </a>
                        <a href="#" class="cb-collapse"
                           onclick="$(this).closest('table').addClass('cb-collapsed'); updateSticky(); return false;">${_('Hide them')}
                        </a>
                    </td>
                </tr>
            %endif
        %endif

        % for hunk in filediff.hunks:
            <tr class="cb-hunk">
                <td ${(c.user_session_attrs["diffmode"] == 'unified' and 'colspan=3' or '')}>
                    ## TODO: dan: add ajax loading of more context here
                    ## <a href="#">
                        <i class="icon-more"></i>
                    ## </a>
                </td>
                <td ${(c.user_session_attrs["diffmode"] == 'sideside' and 'colspan=5' or '')}>
                    @@
                    -${hunk.source_start},${hunk.source_length}
                    +${hunk.target_start},${hunk.target_length}
                    ${hunk.section_header}
                </td>
            </tr>
            ${render_hunk_lines(filediff, c.user_session_attrs["diffmode"], hunk, use_comments=use_comments, inline_comments=inline_comments)}
        % endfor

        <% unmatched_comments = (inline_comments or {}).get(filediff.patch['filename'], {}) %>

        ## outdated comments that do not fit into currently displayed lines
        % for lineno, comments in unmatched_comments.items():

            %if c.user_session_attrs["diffmode"] == 'unified':
                % if loop.index == 0:
                <tr class="cb-hunk">
                    <td colspan="3"></td>
                    <td>
                        <div>
                        ${_('Unmatched inline comments below')}
                        </div>
                    </td>
                </tr>
                % endif
                <tr class="cb-line">
                    <td class="cb-data cb-context"></td>
                    <td class="cb-lineno cb-context"></td>
                    <td class="cb-lineno cb-context"></td>
                    <td class="cb-content cb-context">
                        ${inline_comments_container(comments, inline_comments)}
                    </td>
                </tr>
            %elif c.user_session_attrs["diffmode"] == 'sideside':
                % if loop.index == 0:
                <tr class="cb-comment-info">
                    <td colspan="2"></td>
                    <td class="cb-line">
                        <div>
                        ${_('Unmatched inline comments below')}
                        </div>
                    </td>
                    <td colspan="2"></td>
                    <td class="cb-line">
                        <div>
                        ${_('Unmatched comments below')}
                        </div>
                    </td>
                </tr>
                % endif
                <tr class="cb-line">
                    <td class="cb-data cb-context"></td>
                    <td class="cb-lineno cb-context"></td>
                    <td class="cb-content cb-context">
                        % if lineno.startswith('o'):
                            ${inline_comments_container(comments, inline_comments)}
                        % endif
                    </td>

                    <td class="cb-data cb-context"></td>
                    <td class="cb-lineno cb-context"></td>
                    <td class="cb-content cb-context">
                        % if lineno.startswith('n'):
                            ${inline_comments_container(comments, inline_comments)}
                        % endif
                    </td>
                </tr>
            %endif

        % endfor

            </table>
        </div>
    %endfor

    ## outdated comments that are made for a file that has been deleted
    % for filename, comments_dict in (deleted_files_comments or {}).items():
        <%
            display_state = 'display: none'
            open_comments_in_file = [x for x in comments_dict['comments'] if x.outdated is False]
            if open_comments_in_file:
                display_state = ''
        %>
        <div class="filediffs filediff-outdated" style="${display_state}">
            <input ${(collapse_all and 'checked' or '')} class="filediff-collapse-state collapse-${diffset_container_id}" id="filediff-collapse-${id(filename)}" type="checkbox" onchange="updateSticky();">
            <div class="filediff" data-f-path="${filename}"  id="a_${h.FID(filediff.raw_id, filename)}">
                <label for="filediff-collapse-${id(filename)}" class="filediff-heading">
                    <div class="filediff-collapse-indicator icon-"></div>

                    <span class="pill">
                        ## file was deleted
                        ${filename}
                    </span>
                    <span class="pill-group pull-left" >
                        ## file op, doesn't need translation
                        <span class="pill" op="removed">removed in this version</span>
                    </span>
                    <a class="pill filediff-anchor" href="#a_${h.FID(filediff.raw_id, filename)}">¶</a>
                    <span class="pill-group pull-right">
                        <span class="pill" op="deleted">-${comments_dict['stats']}</span>
                    </span>
                </label>

                <table class="cb cb-diff-${c.user_session_attrs["diffmode"]} code-highlight ${(over_lines_changed_limit and 'cb-collapsed' or '')}">
                    <tr>
                        % if c.user_session_attrs["diffmode"] == 'unified':
                        <td></td>
                        %endif

                        <td></td>
                        <td class="cb-text cb-${op_class(BIN_FILENODE)}" ${(c.user_session_attrs["diffmode"] == 'unified' and 'colspan=4' or 'colspan=5')}>
                        ${_('File was deleted in this version. There are still outdated/unresolved comments attached to it.')}
                        </td>
                    </tr>
                    %if c.user_session_attrs["diffmode"] == 'unified':
                    <tr class="cb-line">
                        <td class="cb-data cb-context"></td>
                        <td class="cb-lineno cb-context"></td>
                        <td class="cb-lineno cb-context"></td>
                        <td class="cb-content cb-context">
                            ${inline_comments_container(comments_dict['comments'], inline_comments)}
                        </td>
                    </tr>
                    %elif c.user_session_attrs["diffmode"] == 'sideside':
                    <tr class="cb-line">
                        <td class="cb-data cb-context"></td>
                        <td class="cb-lineno cb-context"></td>
                        <td class="cb-content cb-context"></td>

                        <td class="cb-data cb-context"></td>
                        <td class="cb-lineno cb-context"></td>
                        <td class="cb-content cb-context">
                            ${inline_comments_container(comments_dict['comments'], inline_comments)}
                        </td>
                    </tr>
                    %endif
                </table>
            </div>
        </div>
    % endfor

</div>
</div>
</%def>

<%def name="diff_ops(filediff)">
<%
from rhodecode.lib.diffs import NEW_FILENODE, DEL_FILENODE, \
    MOD_FILENODE, RENAMED_FILENODE, CHMOD_FILENODE, BIN_FILENODE, COPIED_FILENODE
%>
    <span class="pill">
        <i class="icon-file-text"></i>
        %if filediff.source_file_path and filediff.target_file_path:
            %if filediff.source_file_path != filediff.target_file_path:
                 ## file was renamed, or copied
                %if RENAMED_FILENODE in filediff.patch['stats']['ops']:
                    ${filediff.target_file_path} ⬅ <del>${filediff.source_file_path}</del>
                    <% final_path = filediff.target_file_path %>
                %elif COPIED_FILENODE in filediff.patch['stats']['ops']:
                    ${filediff.target_file_path} ⬅ ${filediff.source_file_path}
                    <% final_path = filediff.target_file_path %>
                %endif
            %else:
                ## file was modified
                ${filediff.source_file_path}
                <% final_path = filediff.source_file_path %>
            %endif
        %else:
            %if filediff.source_file_path:
                ## file was deleted
                ${filediff.source_file_path}
                <% final_path = filediff.source_file_path %>
            %else:
                ## file was added
                ${filediff.target_file_path}
                <% final_path = filediff.target_file_path %>
            %endif
        %endif
        <i style="color: #aaa" class="tooltip icon-clipboard clipboard-action" data-clipboard-text="${final_path}" title="${_('Copy the full path')}" onclick="return false;"></i>
    </span>
    ## anchor link
    <a class="pill filediff-anchor" href="#a_${h.FID(filediff.raw_id, filediff.patch['filename'])}">¶</a>

    <span class="pill-group pull-right">

        ## ops pills
        %if filediff.limited_diff:
        <span class="pill tooltip" op="limited" title="The stats for this diff are not complete">limited diff</span>
        %endif

        %if NEW_FILENODE in filediff.patch['stats']['ops']:
        <span class="pill" op="created">created</span>
            %if filediff['target_mode'].startswith('120'):
        <span class="pill" op="symlink">symlink</span>
            %else:
        <span class="pill" op="mode">${nice_mode(filediff['target_mode'])}</span>
            %endif
        %endif

        %if RENAMED_FILENODE in filediff.patch['stats']['ops']:
        <span class="pill" op="renamed">renamed</span>
        %endif

        %if COPIED_FILENODE in filediff.patch['stats']['ops']:
        <span class="pill" op="copied">copied</span>
        %endif

        %if DEL_FILENODE in filediff.patch['stats']['ops']:
        <span class="pill" op="removed">removed</span>
        %endif

        %if CHMOD_FILENODE in filediff.patch['stats']['ops']:
        <span class="pill" op="mode">
            ${nice_mode(filediff['source_mode'])} ➡ ${nice_mode(filediff['target_mode'])}
        </span>
        %endif

        %if BIN_FILENODE in filediff.patch['stats']['ops']:
        <span class="pill" op="binary">binary</span>
            %if MOD_FILENODE in filediff.patch['stats']['ops']:
        <span class="pill" op="modified">modified</span>
            %endif
        %endif

        <span class="pill" op="added">${('+' if filediff.patch['stats']['added'] else '')}${filediff.patch['stats']['added']}</span>
        <span class="pill" op="deleted">${((h.safe_int(filediff.patch['stats']['deleted']) or 0) * -1)}</span>

    </span>

</%def>

<%def name="nice_mode(filemode)">
    ${(filemode.startswith('100') and filemode[3:] or filemode)}
</%def>

<%def name="diff_menu(filediff, use_comments=False)">
    <div class="filediff-menu">

    %if filediff.diffset.source_ref:

    ## FILE BEFORE CHANGES
    %if filediff.operation in ['D', 'M']:
        <a
            class="tooltip"
            href="${h.route_path('repo_files',repo_name=filediff.diffset.target_repo_name,commit_id=filediff.diffset.source_ref,f_path=filediff.source_file_path)}"
            title="${h.tooltip(_('Show file at commit: %(commit_id)s') % {'commit_id': filediff.diffset.source_ref[:12]})}"
        >
            ${_('Show file before')}
        </a> |
    %else:
        <span
            class="tooltip"
            title="${h.tooltip(_('File not present at commit: %(commit_id)s') % {'commit_id': filediff.diffset.source_ref[:12]})}"
        >
            ${_('Show file before')}
        </span> |
    %endif

    ## FILE AFTER CHANGES
    %if filediff.operation in ['A', 'M']:
        <a
            class="tooltip"
            href="${h.route_path('repo_files',repo_name=filediff.diffset.source_repo_name,commit_id=filediff.diffset.target_ref,f_path=filediff.target_file_path)}"
            title="${h.tooltip(_('Show file at commit: %(commit_id)s') % {'commit_id': filediff.diffset.target_ref[:12]})}"
        >
            ${_('Show file after')}
        </a>
    %else:
        <span
            class="tooltip"
            title="${h.tooltip(_('File not present at commit: %(commit_id)s') % {'commit_id': filediff.diffset.target_ref[:12]})}"
            >
            ${_('Show file after')}
        </span>
    %endif

    % if use_comments:
    |
    <a href="#" onclick="return Rhodecode.comments.toggleComments(this);">
        <span class="show-comment-button">${_('Show comments')}</span><span class="hide-comment-button">${_('Hide comments')}</span>
    </a>
    % endif

    %endif

    </div>
</%def>


<%def name="inline_comments_container(comments, inline_comments)">
<div class="inline-comments">
    %for comment in comments:
        ${commentblock.comment_block(comment, inline=True)}
    %endfor
    % if comments and comments[-1].outdated:
    <span class="btn btn-secondary cb-comment-add-button comment-outdated}" style="display: none;}">
        ${_('Add another comment')}
    </span>
    % else:
    <span onclick="return Rhodecode.comments.createComment(this)" class="btn btn-secondary cb-comment-add-button">
        ${_('Add another comment')}
    </span>
    % endif

</div>
</%def>

<%!
def get_comments_for(diff_type, comments, filename, line_version, line_number):
    if hasattr(filename, 'unicode_path'):
        filename = filename.unicode_path

    if not isinstance(filename, (unicode, str)):
        return None

    line_key = '{}{}'.format(line_version, line_number) ## e.g o37, n12

    if comments and filename in comments:
        file_comments = comments[filename]
        if line_key in file_comments:
            data = file_comments.pop(line_key)
            return data
%>

<%def name="render_hunk_lines_sideside(filediff, hunk, use_comments=False, inline_comments=None)">
    %for i, line in enumerate(hunk.sideside):
    <%
    old_line_anchor, new_line_anchor = None, None

    if line.original.lineno:
        old_line_anchor = diff_line_anchor(filediff.raw_id, hunk.source_file_path, line.original.lineno, 'o')
    if line.modified.lineno:
        new_line_anchor = diff_line_anchor(filediff.raw_id, hunk.target_file_path, line.modified.lineno, 'n')
    %>

    <tr class="cb-line">
        <td class="cb-data ${action_class(line.original.action)}"
            data-line-no="${line.original.lineno}"
            >
            <div>

            <% line_old_comments = None %>
            %if line.original.get_comment_args:
                <% line_old_comments = get_comments_for('side-by-side', inline_comments, *line.original.get_comment_args) %>
            %endif
            %if line_old_comments:
                <% has_outdated = any([x.outdated for x in line_old_comments]) %>
                % if has_outdated:
                    <i title="${_('comments including outdated')}:${len(line_old_comments)}" class="icon-comment-toggle" onclick="return Rhodecode.comments.toggleLineComments(this)"></i>
                % else:
                    <i title="${_('comments')}: ${len(line_old_comments)}" class="icon-comment" onclick="return Rhodecode.comments.toggleLineComments(this)"></i>
                % endif
            %endif
            </div>
        </td>
        <td class="cb-lineno ${action_class(line.original.action)}"
            data-line-no="${line.original.lineno}"
            %if old_line_anchor:
            id="${old_line_anchor}"
            %endif
        >
            %if line.original.lineno:
            <a name="${old_line_anchor}" href="#${old_line_anchor}">${line.original.lineno}</a>
            %endif
        </td>
        <td class="cb-content ${action_class(line.original.action)}"
            data-line-no="o${line.original.lineno}"
            >
            %if use_comments and line.original.lineno:
            ${render_add_comment_button()}
            %endif
            <span class="cb-code"><span class="cb-action ${action_class(line.original.action)}"></span>${line.original.content or '' | n}</span>

            %if use_comments and line.original.lineno and line_old_comments:
                ${inline_comments_container(line_old_comments, inline_comments)}
            %endif

        </td>
        <td class="cb-data ${action_class(line.modified.action)}"
            data-line-no="${line.modified.lineno}"
            >
            <div>

            %if line.modified.get_comment_args:
                <% line_new_comments = get_comments_for('side-by-side', inline_comments, *line.modified.get_comment_args) %>
            %else:
                <% line_new_comments = None%>
            %endif
            %if line_new_comments:
                <% has_outdated = any([x.outdated for x in line_new_comments]) %>
                % if has_outdated:
                    <i title="${_('comments including outdated')}:${len(line_new_comments)}" class="icon-comment-toggle" onclick="return Rhodecode.comments.toggleLineComments(this)"></i>
                % else:
                    <i title="${_('comments')}: ${len(line_new_comments)}" class="icon-comment" onclick="return Rhodecode.comments.toggleLineComments(this)"></i>
                % endif
            %endif
            </div>
        </td>
        <td class="cb-lineno ${action_class(line.modified.action)}"
            data-line-no="${line.modified.lineno}"
            %if new_line_anchor:
            id="${new_line_anchor}"
            %endif
            >
            %if line.modified.lineno:
                <a name="${new_line_anchor}" href="#${new_line_anchor}">${line.modified.lineno}</a>
            %endif
        </td>
        <td class="cb-content ${action_class(line.modified.action)}"
            data-line-no="n${line.modified.lineno}"
            >
            %if use_comments and line.modified.lineno:
            ${render_add_comment_button()}
            %endif
            <span class="cb-code"><span class="cb-action ${action_class(line.modified.action)}"></span>${line.modified.content or '' | n}</span>
            %if use_comments and line.modified.lineno and line_new_comments:
            ${inline_comments_container(line_new_comments, inline_comments)}
            %endif
        </td>
    </tr>
    %endfor
</%def>


<%def name="render_hunk_lines_unified(filediff, hunk, use_comments=False,  inline_comments=None)">
    %for old_line_no, new_line_no, action, content, comments_args in hunk.unified:

    <%
    old_line_anchor, new_line_anchor = None, None
    if old_line_no:
        old_line_anchor = diff_line_anchor(filediff.raw_id, hunk.source_file_path, old_line_no, 'o')
    if new_line_no:
        new_line_anchor = diff_line_anchor(filediff.raw_id, hunk.target_file_path, new_line_no, 'n')
    %>
    <tr class="cb-line">
        <td class="cb-data ${action_class(action)}">
            <div>

            %if comments_args:
                <% comments = get_comments_for('unified', inline_comments, *comments_args) %>
            %else:
                <% comments = None %>
            %endif

            % if comments:
                <% has_outdated = any([x.outdated for x in comments]) %>
                % if has_outdated:
                    <i title="${_('comments including outdated')}:${len(comments)}" class="icon-comment-toggle" onclick="return Rhodecode.comments.toggleLineComments(this)"></i>
                % else:
                    <i title="${_('comments')}: ${len(comments)}" class="icon-comment" onclick="return Rhodecode.comments.toggleLineComments(this)"></i>
                % endif
            % endif
            </div>
        </td>
        <td class="cb-lineno ${action_class(action)}"
            data-line-no="${old_line_no}"
            %if old_line_anchor:
            id="${old_line_anchor}"
            %endif
        >
            %if old_line_anchor:
            <a name="${old_line_anchor}" href="#${old_line_anchor}">${old_line_no}</a>
            %endif
        </td>
        <td class="cb-lineno ${action_class(action)}"
            data-line-no="${new_line_no}"
            %if new_line_anchor:
            id="${new_line_anchor}"
            %endif
        >
            %if new_line_anchor:
            <a name="${new_line_anchor}" href="#${new_line_anchor}">${new_line_no}</a>
            %endif
        </td>
        <td class="cb-content ${action_class(action)}"
            data-line-no="${(new_line_no and 'n' or 'o')}${(new_line_no or old_line_no)}"
            >
            %if use_comments:
            ${render_add_comment_button()}
            %endif
            <span class="cb-code"><span class="cb-action ${action_class(action)}"></span> ${content or '' | n}</span>
            %if use_comments and comments:
            ${inline_comments_container(comments, inline_comments)}
            %endif
        </td>
    </tr>
    %endfor
</%def>


<%def name="render_hunk_lines(filediff, diff_mode, hunk, use_comments, inline_comments)">
    % if diff_mode == 'unified':
        ${render_hunk_lines_unified(filediff, hunk, use_comments=use_comments, inline_comments=inline_comments)}
    % elif diff_mode == 'sideside':
        ${render_hunk_lines_sideside(filediff, hunk, use_comments=use_comments, inline_comments=inline_comments)}
    % else:
        <tr class="cb-line">
            <td>unknown diff mode</td>
        </tr>
    % endif
</%def>file changes


<%def name="render_add_comment_button()">
<button class="btn btn-small btn-primary cb-comment-box-opener" onclick="return Rhodecode.comments.createComment(this)">
    <span><i class="icon-comment"></i></span>
</button>
</%def>

<%def name="render_diffset_menu(diffset, range_diff_on=None)">
    <% diffset_container_id = h.md5(diffset.target_ref) %>

    <div id="diff-file-sticky" class="diffset-menu clearinner">
        ## auto adjustable
        <div class="sidebar__inner">
            <div class="sidebar__bar">
            <div class="pull-right">
                <div class="btn-group">
                    <a class="btn tooltip toggle-wide-diff" href="#toggle-wide-diff" onclick="toggleWideDiff(this); return false" title="${h.tooltip(_('Toggle wide diff'))}">
                    <i class="icon-wide-mode"></i>
                    </a>
                </div>
                <div class="btn-group">

                <a
                  class="btn ${(c.user_session_attrs["diffmode"] == 'sideside' and 'btn-active')} tooltip"
                  title="${h.tooltip(_('View diff as side by side'))}"
                  href="${h.current_route_path(request, diffmode='sideside')}">
                    <span>${_('Side by Side')}</span>
                </a>

                <a
                  class="btn ${(c.user_session_attrs["diffmode"] == 'unified' and 'btn-active')} tooltip"
                  title="${h.tooltip(_('View diff as unified'))}" href="${h.current_route_path(request, diffmode='unified')}">
                    <span>${_('Unified')}</span>
                </a>

                % if range_diff_on is True:
                    <a
                      title="${_('Turn off: Show the diff as commit range')}"
                      class="btn btn-primary"
                      href="${h.current_route_path(request, **{"range-diff":"0"})}">
                        <span>${_('Range Diff')}</span>
                   </a>
                % elif range_diff_on is False:
                    <a
                      title="${_('Show the diff as commit range')}"
                      class="btn"
                      href="${h.current_route_path(request, **{"range-diff":"1"})}">
                        <span>${_('Range Diff')}</span>
                   </a>
                % endif
            </div>
                <div class="btn-group">

                <div class="pull-left">
                    ${h.hidden('diff_menu_{}'.format(diffset_container_id))}
                </div>

                </div>
        </div>
            <div class="pull-left">
            <div class="btn-group">
              <div class="pull-left">
                ${h.hidden('file_filter_{}'.format(diffset_container_id))}
              </div>

            </div>
            </div>
        </div>
        <div class="fpath-placeholder">
            <i class="icon-file-text"></i>
            <strong class="fpath-placeholder-text">
            Context file:
            </strong>
        </div>
        <div class="sidebar_inner_shadow"></div>
        </div>
    </div>

    % if diffset:
        %if diffset.limited_diff:
            <% file_placeholder = _ungettext('%(num)s file changed', '%(num)s files changed', diffset.changed_files) % {'num': diffset.changed_files} %>
        %else:
            <% file_placeholder = h.literal(_ungettext('%(num)s file changed: <span class="op-added">%(linesadd)s inserted</span>, <span class="op-deleted">%(linesdel)s deleted</span>', '%(num)s files changed: <span class="op-added">%(linesadd)s inserted</span>, <span class="op-deleted">%(linesdel)s deleted</span>',
            diffset.changed_files) % {'num': diffset.changed_files, 'linesadd': diffset.lines_added, 'linesdel': diffset.lines_deleted}) %>

        %endif
        ## case on range-diff placeholder needs to be updated
        % if range_diff_on is True:
            <% file_placeholder = _('Disabled on range diff') %>
        % endif

        <script type="text/javascript">
        var feedFilesOptions = function (query, initialData) {
            var data = {results: []};
            var isQuery = typeof query.term !== 'undefined';

            var section = _gettext('Changed files');
            var filteredData = [];

            //filter results
            $.each(initialData.results, function (idx, value) {

                if (!isQuery || query.term.length === 0 || value.text.toUpperCase().indexOf(query.term.toUpperCase()) >= 0) {
                    filteredData.push({
                        'id': this.id,
                        'text': this.text,
                        "ops": this.ops,
                    })
                }

            });

            data.results = filteredData;

            query.callback(data);
        };

        var selectionFormatter = function(data, escapeMarkup) {
            var container = '<div class="filelist" style="padding-right:100px">{0}</div>';
            var tmpl = '<div><strong>{0}</strong></div>'.format(escapeMarkup(data['text']));
            var pill = '<div class="pill-group" style="position: absolute; top:7px; right: 0">' +
                        '<span class="pill" op="added">{0}</span>' +
                        '<span class="pill" op="deleted">{1}</span>' +
                       '</div>'
                    ;
            var added = data['ops']['added'];
            if (added === 0) {
                // don't show +0
                added = 0;
            } else {
                added = '+' + added;
            }

            var deleted = -1*data['ops']['deleted'];

            tmpl += pill.format(added, deleted);
            return container.format(tmpl);
        };
        var formatFileResult = function(result, container, query, escapeMarkup) {
            return selectionFormatter(result, escapeMarkup);
        };

        var formatSelection = function (data, container) {
            return '${file_placeholder}'
        };

        if (window.preloadFileFilterData === undefined) {
            window.preloadFileFilterData = {}
        }

        preloadFileFilterData["${diffset_container_id}"] = {
            results: [
                % for filediff in diffset.files:
                    {id:"a_${h.FID(filediff.raw_id, filediff.patch['filename'])}",
                     text:"${filediff.patch['filename']}",
                     ops:${h.json.dumps(filediff.patch['stats'])|n}}${('' if loop.last else ',')}
                % endfor
            ]
        };

        var diffFileFilterId = "#file_filter_" + "${diffset_container_id}";
        var diffFileFilter = $(diffFileFilterId).select2({
            'dropdownAutoWidth': true,
            'width': 'auto',

            containerCssClass: "drop-menu",
            dropdownCssClass: "drop-menu-dropdown",
            data: preloadFileFilterData["${diffset_container_id}"],
            query: function(query) {
                feedFilesOptions(query, preloadFileFilterData["${diffset_container_id}"]);
            },
            initSelection: function(element, callback) {
              callback({'init': true});
            },
            formatResult: formatFileResult,
            formatSelection: formatSelection
        });

        % if range_diff_on is True:
            diffFileFilter.select2("enable", false);
        % endif

        $(diffFileFilterId).on('select2-selecting', function (e) {
            var idSelector = e.choice.id;

            // expand the container if we quick-select the field
            $('#'+idSelector).next().prop('checked', false);
            // hide the mast as we later do preventDefault()
            $("#select2-drop-mask").click();

            window.location.hash = '#'+idSelector;
            updateSticky();

            e.preventDefault();
        });

        </script>
    % endif

    <script type="text/javascript">
        $(document).ready(function () {

            var contextPrefix = _gettext('Context file: ');
            ## sticky sidebar
            var sidebarElement = document.getElementById('diff-file-sticky');
            sidebar = new StickySidebar(sidebarElement, {
                  topSpacing: 0,
                  bottomSpacing: 0,
                  innerWrapperSelector: '.sidebar__inner'
            });
            sidebarElement.addEventListener('affixed.static.stickySidebar', function () {
                // reset our file so it's not holding new value
                $('.fpath-placeholder-text').html(contextPrefix + ' - ')
            });

            updateSticky = function () {
                sidebar.updateSticky();
                Waypoint.refreshAll();
            };

            var animateText = function (fPath, anchorId) {
                fPath = Select2.util.escapeMarkup(fPath);
                $('.fpath-placeholder-text').html(contextPrefix + '<a href="#a_' + anchorId + '">' + fPath + '</a>')
            };

            ## dynamic file waypoints
            var setFPathInfo = function(fPath, anchorId){
                animateText(fPath, anchorId)
            };

            var codeBlock = $('.filediff');

            // forward waypoint
            codeBlock.waypoint(
                function(direction) {
                    if (direction === "down"){
                        setFPathInfo($(this.element).data('fPath'), $(this.element).data('anchorId'))
                    }
                }, {
                    offset: function () {
                        return 70;
                    },
                    context: '.fpath-placeholder'
                }
            );

            // backward waypoint
            codeBlock.waypoint(
                function(direction) {
                    if (direction === "up"){
                        setFPathInfo($(this.element).data('fPath'), $(this.element).data('anchorId'))
                    }
                }, {
                    offset: function () {
                        return -this.element.clientHeight + 90;
                    },
                    context: '.fpath-placeholder'
                }
            );

            toggleWideDiff = function (el) {
                updateSticky();
                var wide = Rhodecode.comments.toggleWideMode(this);
                storeUserSessionAttr('rc_user_session_attr.wide_diff_mode', wide);
                if (wide === true) {
                    $(el).addClass('btn-active');
                } else {
                    $(el).removeClass('btn-active');
                }
                return null;
            };

            var preloadDiffMenuData = {
                results: [

                    ## Whitespace change
                    % if request.GET.get('ignorews', '') == '1':
                    {
                        id: 2,
                        text: _gettext('Show whitespace changes'),
                        action: function () {},
                        url: "${h.current_route_path(request, ignorews=0)|n}"
                    },
                    % else:
                    {
                        id: 2,
                        text: _gettext('Hide whitespace changes'),
                        action: function () {},
                        url: "${h.current_route_path(request, ignorews=1)|n}"
                    },
                    % endif

                    ## FULL CONTEXT
                    % if request.GET.get('fullcontext', '') == '1':
                    {
                        id: 3,
                        text: _gettext('Hide full context diff'),
                        action: function () {},
                        url: "${h.current_route_path(request, fullcontext=0)|n}"
                    },
                    % else:
                    {
                        id: 3,
                        text: _gettext('Show full context diff'),
                        action: function () {},
                        url: "${h.current_route_path(request, fullcontext=1)|n}"
                    },
                    % endif

                ]
            };

            // get stored diff mode and pre-enable it
            if (templateContext.session_attrs.wide_diff_mode === "true") {
                Rhodecode.comments.toggleWideMode(null);
                $('.toggle-wide-diff').addClass('btn-active');
            }

            var diffMenuId = "#diff_menu_" + "${diffset_container_id}";
            $(diffMenuId).select2({
                minimumResultsForSearch: -1,
                containerCssClass: "drop-menu-no-width",
                dropdownCssClass: "drop-menu-dropdown",
                dropdownAutoWidth: true,
                data: preloadDiffMenuData,
                placeholder: "${_('...')}",
            });
            $(diffMenuId).on('select2-selecting', function (e) {
                e.choice.action();
                if (e.choice.url !== null) {
                    window.location = e.choice.url
                }
            });
            toggleExpand = function (el, diffsetEl) {
                var el = $(el);
                if (el.hasClass('collapsed')) {
                    $('.filediff-collapse-state.collapse-{0}'.format(diffsetEl)).prop('checked', false);
                    el.removeClass('collapsed');
                    el.html(
                        '<i class="icon-minus-squared-alt icon-no-margin"></i>' +
                        _gettext('Collapse all files'));
                }
                else {
                    $('.filediff-collapse-state.collapse-{0}'.format(diffsetEl)).prop('checked', true);
                    el.addClass('collapsed');
                    el.html(
                        '<i class="icon-plus-squared-alt icon-no-margin"></i>' +
                        _gettext('Expand all files'));
                }
                updateSticky()
            }
        });
    </script>

</%def>
