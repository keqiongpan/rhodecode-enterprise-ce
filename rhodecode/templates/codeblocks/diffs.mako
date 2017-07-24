<%namespace name="commentblock" file="/changeset/changeset_file_comment.mako"/>

<%def name="diff_line_anchor(filename, line, type)"><%
return '%s_%s_%i' % (h.safeid(filename), type, line)
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

<%def name="link_for(**kw)">
<%
new_args = request.GET.mixed()
new_args.update(kw)
return h.url('', **new_args)
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
    deleted_files_comments=None

)">

%if use_comments:
<div id="cb-comments-inline-container-template" class="js-template">
  ${inline_comments_container([])}
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
              ${_('You need to be logged in to leave comments.')} <a href="${h.route_path('login', _query={'came_from': h.url.current()})}">${_('Login now')}</a>
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
<%
collapse_all = len(diffset.files) > collapse_when_files_over
%>

%if c.diffmode == 'sideside':
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
    <div class="diffset-heading ${diffset.limited_diff and 'diffset-heading-warning' or ''}">
        %if commit:
            <div class="pull-right">
                <a class="btn tooltip" title="${h.tooltip(_('Browse Files at revision {}').format(commit.raw_id))}" href="${h.route_path('repo_files',repo_name=diffset.repo_name, commit_id=commit.raw_id, f_path='')}">
                    ${_('Browse Files')}
                </a>
            </div>
        %endif
        <h2 class="clearinner">
        %if commit:
            <a class="tooltip revision" title="${h.tooltip(commit.message)}" href="${h.route_path('repo_commit',repo_name=c.repo_name,commit_id=commit.raw_id)}">${'r%s:%s' % (commit.revision,h.short_id(commit.raw_id))}</a> -
            ${h.age_component(commit.date)} -
        %endif
    %if diffset.limited_diff:
        ${_('The requested commit is too big and content was truncated.')}

        ${_ungettext('%(num)s file changed.', '%(num)s files changed.', diffset.changed_files) % {'num': diffset.changed_files}}
        <a href="${link_for(fulldiff=1)}" onclick="return confirm('${_("Showing a big diff might take some time and resources, continue?")}')">${_('Show full diff')}</a>
    %else:
        ${_ungettext('%(num)s file changed: %(linesadd)s inserted, ''%(linesdel)s deleted',
                    '%(num)s files changed: %(linesadd)s inserted, %(linesdel)s deleted', diffset.changed_files) % {'num': diffset.changed_files, 'linesadd': diffset.lines_added, 'linesdel': diffset.lines_deleted}}
    %endif

        </h2>
    </div>

    %if not diffset.files:
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
        <input ${collapse_all and 'checked' or ''} class="filediff-collapse-state" id="filediff-collapse-${id(filediff)}" type="checkbox">
        <div
            class="filediff"
            data-f-path="${filediff.patch['filename']}"
            id="a_${h.FID('', filediff.patch['filename'])}">
            <label for="filediff-collapse-${id(filediff)}" class="filediff-heading">
                <div class="filediff-collapse-indicator"></div>
                ${diff_ops(filediff)}
            </label>
            ${diff_menu(filediff, use_comments=use_comments)}
            <table class="cb cb-diff-${c.diffmode} code-highlight ${over_lines_changed_limit and 'cb-collapsed' or ''}">
        %if not filediff.hunks:
            %for op_id, op_text in filediff.patch['stats']['ops'].items():
                <tr>
                    <td class="cb-text cb-${op_class(op_id)}" ${c.diffmode == 'unified' and 'colspan=4' or 'colspan=6'}>
                        %if op_id == DEL_FILENODE:
                        ${_('File was deleted')}
                        %elif op_id == BIN_FILENODE:
                        ${_('Binary file hidden')}
                        %else:
                        ${op_text}
                        %endif
                    </td>
                </tr>
            %endfor
        %endif
        %if filediff.limited_diff:
                <tr class="cb-warning cb-collapser">
                    <td class="cb-text" ${c.diffmode == 'unified' and 'colspan=4' or 'colspan=6'}>
                        ${_('The requested commit is too big and content was truncated.')} <a href="${link_for(fulldiff=1)}" onclick="return confirm('${_("Showing a big diff might take some time and resources, continue?")}')">${_('Show full diff')}</a>
                    </td>
                </tr>
        %else:
            %if over_lines_changed_limit:
                    <tr class="cb-warning cb-collapser">
                        <td class="cb-text" ${c.diffmode == 'unified' and 'colspan=4' or 'colspan=6'}>
                            ${_('This diff has been collapsed as it changes many lines, (%i lines changed)' % lines_changed)}
                            <a href="#" class="cb-expand"
                               onclick="$(this).closest('table').removeClass('cb-collapsed'); return false;">${_('Show them')}
                            </a>
                            <a href="#" class="cb-collapse"
                               onclick="$(this).closest('table').addClass('cb-collapsed'); return false;">${_('Hide them')}
                            </a>
                        </td>
                    </tr>
            %endif
        %endif

        %for hunk in filediff.hunks:
                <tr class="cb-hunk">
                    <td ${c.diffmode == 'unified' and 'colspan=3' or ''}>
                        ## TODO: dan: add ajax loading of more context here
                        ## <a href="#">
                            <i class="icon-more"></i>
                        ## </a>
                    </td>
                    <td ${c.diffmode == 'sideside' and 'colspan=5' or ''}>
                        @@
                        -${hunk.source_start},${hunk.source_length}
                        +${hunk.target_start},${hunk.target_length}
                        ${hunk.section_header}
                    </td>
                </tr>
            %if c.diffmode == 'unified':
                    ${render_hunk_lines_unified(hunk, use_comments=use_comments)}
            %elif c.diffmode == 'sideside':
                    ${render_hunk_lines_sideside(hunk, use_comments=use_comments)}
            %else:
                <tr class="cb-line">
                    <td>unknown diff mode</td>
                </tr>
            %endif
        %endfor

        ## outdated comments that do not fit into currently displayed lines
        % for lineno, comments in filediff.left_comments.items():

        %if c.diffmode == 'unified':
            <tr class="cb-line">
                <td class="cb-data cb-context"></td>
                <td class="cb-lineno cb-context"></td>
                <td class="cb-lineno cb-context"></td>
                <td class="cb-content cb-context">
                    ${inline_comments_container(comments)}
                </td>
            </tr>
        %elif c.diffmode == 'sideside':
            <tr class="cb-line">
                <td class="cb-data cb-context"></td>
                <td class="cb-lineno cb-context"></td>
                <td class="cb-content cb-context"></td>

                <td class="cb-data cb-context"></td>
                <td class="cb-lineno cb-context"></td>
                <td class="cb-content cb-context">
                    ${inline_comments_container(comments)}
                </td>
            </tr>
        %endif

        % endfor

            </table>
        </div>
    %endfor

    ## outdated comments that are made for a file that has been deleted
    % for filename, comments_dict in (deleted_files_comments or {}).items():

        <div class="filediffs filediff-outdated" style="display: none">
            <input ${collapse_all and 'checked' or ''} class="filediff-collapse-state" id="filediff-collapse-${id(filename)}" type="checkbox">
            <div class="filediff" data-f-path="${filename}"  id="a_${h.FID('', filename)}">
                <label for="filediff-collapse-${id(filename)}" class="filediff-heading">
                    <div class="filediff-collapse-indicator"></div>
                    <span class="pill">
                        ## file was deleted
                        <strong>${filename}</strong>
                    </span>
                    <span class="pill-group" style="float: left">
                        ## file op, doesn't need translation
                        <span class="pill" op="removed">removed in this version</span>
                    </span>
                    <a class="pill filediff-anchor" href="#a_${h.FID('', filename)}">¶</a>
                    <span class="pill-group" style="float: right">
                        <span class="pill" op="deleted">-${comments_dict['stats']}</span>
                    </span>
                </label>

                <table class="cb cb-diff-${c.diffmode} code-highlight ${over_lines_changed_limit and 'cb-collapsed' or ''}">
                    <tr>
                        % if c.diffmode == 'unified':
                        <td></td>
                        %endif

                        <td></td>
                        <td class="cb-text cb-${op_class(BIN_FILENODE)}" ${c.diffmode == 'unified' and 'colspan=4' or 'colspan=5'}>
                        ${_('File was deleted in this version, and outdated comments were made on it')}
                        </td>
                    </tr>
                    %if c.diffmode == 'unified':
                    <tr class="cb-line">
                        <td class="cb-data cb-context"></td>
                        <td class="cb-lineno cb-context"></td>
                        <td class="cb-lineno cb-context"></td>
                        <td class="cb-content cb-context">
                            ${inline_comments_container(comments_dict['comments'])}
                        </td>
                    </tr>
                    %elif c.diffmode == 'sideside':
                    <tr class="cb-line">
                        <td class="cb-data cb-context"></td>
                        <td class="cb-lineno cb-context"></td>
                        <td class="cb-content cb-context"></td>

                        <td class="cb-data cb-context"></td>
                        <td class="cb-lineno cb-context"></td>
                        <td class="cb-content cb-context">
                            ${inline_comments_container(comments_dict['comments'])}
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
        %if filediff.source_file_path and filediff.target_file_path:
            %if filediff.source_file_path != filediff.target_file_path:
                 ## file was renamed, or copied
                %if RENAMED_FILENODE in filediff.patch['stats']['ops']:
                    <strong>${filediff.target_file_path}</strong> ⬅ <del>${filediff.source_file_path}</del>
                %elif COPIED_FILENODE in filediff.patch['stats']['ops']:
                    <strong>${filediff.target_file_path}</strong> ⬅ ${filediff.source_file_path}
                %endif
            %else:
                ## file was modified
                <strong>${filediff.source_file_path}</strong>
            %endif
        %else:
            %if filediff.source_file_path:
                ## file was deleted
                <strong>${filediff.source_file_path}</strong>
            %else:
                ## file was added
                <strong>${filediff.target_file_path}</strong>
            %endif
        %endif
    </span>
    <span class="pill-group" style="float: left">
        %if filediff.limited_diff:
        <span class="pill tooltip" op="limited" title="The stats for this diff are not complete">limited diff</span>
        %endif

        %if RENAMED_FILENODE in filediff.patch['stats']['ops']:
        <span class="pill" op="renamed">renamed</span>
        %endif

        %if COPIED_FILENODE in filediff.patch['stats']['ops']:
        <span class="pill" op="copied">copied</span>
        %endif

        %if NEW_FILENODE in filediff.patch['stats']['ops']:
        <span class="pill" op="created">created</span>
            %if filediff['target_mode'].startswith('120'):
        <span class="pill" op="symlink">symlink</span>
            %else:
        <span class="pill" op="mode">${nice_mode(filediff['target_mode'])}</span>
            %endif
        %endif

        %if DEL_FILENODE in filediff.patch['stats']['ops']:
        <span class="pill" op="removed">removed</span>
        %endif

        %if CHMOD_FILENODE in filediff.patch['stats']['ops']:
        <span class="pill" op="mode">
            ${nice_mode(filediff['source_mode'])} ➡ ${nice_mode(filediff['target_mode'])}
        </span>
        %endif
    </span>

    <a class="pill filediff-anchor" href="#a_${h.FID('', filediff.patch['filename'])}">¶</a>

    <span class="pill-group" style="float: right">
        %if BIN_FILENODE in filediff.patch['stats']['ops']:
        <span class="pill" op="binary">binary</span>
            %if MOD_FILENODE in filediff.patch['stats']['ops']:
            <span class="pill" op="modified">modified</span>
            %endif
        %endif
        %if filediff.patch['stats']['added']:
        <span class="pill" op="added">+${filediff.patch['stats']['added']}</span>
        %endif
        %if filediff.patch['stats']['deleted']:
        <span class="pill" op="deleted">-${filediff.patch['stats']['deleted']}</span>
        %endif
    </span>

</%def>

<%def name="nice_mode(filemode)">
    ${filemode.startswith('100') and filemode[3:] or filemode}
</%def>

<%def name="diff_menu(filediff, use_comments=False)">
    <div class="filediff-menu">
%if filediff.diffset.source_ref:
    %if filediff.operation in ['D', 'M']:
        <a
            class="tooltip"
            href="${h.route_path('repo_files',repo_name=filediff.diffset.repo_name,commit_id=filediff.diffset.source_ref,f_path=filediff.source_file_path)}"
            title="${h.tooltip(_('Show file at commit: %(commit_id)s') % {'commit_id': filediff.diffset.source_ref[:12]})}"
        >
            ${_('Show file before')}
        </a> |
    %else:
        <span
            class="tooltip"
            title="${h.tooltip(_('File no longer present at commit: %(commit_id)s') % {'commit_id': filediff.diffset.source_ref[:12]})}"
        >
            ${_('Show file before')}
        </span> |
    %endif
    %if filediff.operation in ['A', 'M']:
        <a
            class="tooltip"
            href="${h.route_path('repo_files',repo_name=filediff.diffset.source_repo_name,commit_id=filediff.diffset.target_ref,f_path=filediff.target_file_path)}"
            title="${h.tooltip(_('Show file at commit: %(commit_id)s') % {'commit_id': filediff.diffset.target_ref[:12]})}"
        >
            ${_('Show file after')}
        </a> |
    %else:
        <span
            class="tooltip"
            title="${h.tooltip(_('File no longer present at commit: %(commit_id)s') % {'commit_id': filediff.diffset.target_ref[:12]})}"
            >
                ${_('Show file after')}
        </span> |
    %endif
        <a
            class="tooltip"
            title="${h.tooltip(_('Raw diff'))}"
            href="${h.route_path('repo_files_diff',repo_name=filediff.diffset.repo_name,f_path=filediff.target_file_path, _query=dict(diff2=filediff.diffset.target_ref,diff1=filediff.diffset.source_ref,diff='raw'))}"
        >
            ${_('Raw diff')}
        </a> |
        <a
            class="tooltip"
            title="${h.tooltip(_('Download diff'))}"
            href="${h.route_path('repo_files_diff',repo_name=filediff.diffset.repo_name,f_path=filediff.target_file_path, _query=dict(diff2=filediff.diffset.target_ref,diff1=filediff.diffset.source_ref,diff='download'))}"
        >
            ${_('Download diff')}
        </a>
        % if use_comments:
            |
        % endif

        ## TODO: dan: refactor ignorews_url and context_url into the diff renderer same as diffmode=unified/sideside. Also use ajax to load more context (by clicking hunks)
        %if hasattr(c, 'ignorews_url'):
        ${c.ignorews_url(request, h.FID('', filediff.patch['filename']))}
        %endif
        %if hasattr(c, 'context_url'):
        ${c.context_url(request, h.FID('', filediff.patch['filename']))}
        %endif

        %if use_comments:
        <a href="#" onclick="return Rhodecode.comments.toggleComments(this);">
            <span class="show-comment-button">${_('Show comments')}</span><span class="hide-comment-button">${_('Hide comments')}</span>
        </a>
        %endif
%endif
    </div>
</%def>


<%def name="inline_comments_container(comments)">
<div class="inline-comments">
    %for comment in comments:
    ${commentblock.comment_block(comment, inline=True)}
    %endfor

    % if comments and comments[-1].outdated:
    <span class="btn btn-secondary cb-comment-add-button comment-outdated}"
          style="display: none;}">
        ${_('Add another comment')}
    </span>
    % else:
    <span onclick="return Rhodecode.comments.createComment(this)"
          class="btn btn-secondary cb-comment-add-button">
        ${_('Add another comment')}
    </span>
    % endif

</div>
</%def>


<%def name="render_hunk_lines_sideside(hunk, use_comments=False)">
    %for i, line in enumerate(hunk.sideside):
    <%
    old_line_anchor, new_line_anchor = None, None
    if line.original.lineno:
        old_line_anchor = diff_line_anchor(hunk.source_file_path, line.original.lineno, 'o')
    if line.modified.lineno:
        new_line_anchor = diff_line_anchor(hunk.target_file_path, line.modified.lineno, 'n')
    %>

    <tr class="cb-line">
        <td class="cb-data ${action_class(line.original.action)}"
            data-line-number="${line.original.lineno}"
            >
            <div>
            %if line.original.comments:
            <i class="icon-comment" onclick="return Rhodecode.comments.toggleLineComments(this)"></i>
            %endif
            </div>
        </td>
        <td class="cb-lineno ${action_class(line.original.action)}"
            data-line-number="${line.original.lineno}"
            %if old_line_anchor:
            id="${old_line_anchor}"
            %endif
        >
            %if line.original.lineno:
            <a name="${old_line_anchor}" href="#${old_line_anchor}">${line.original.lineno}</a>
            %endif
        </td>
        <td class="cb-content ${action_class(line.original.action)}"
            data-line-number="o${line.original.lineno}"
            >
            %if use_comments and line.original.lineno:
            ${render_add_comment_button()}
            %endif
            <span class="cb-code">${line.original.action} ${line.original.content or '' | n}</span>
            %if use_comments and line.original.lineno and line.original.comments:
            ${inline_comments_container(line.original.comments)}
            %endif
        </td>
        <td class="cb-data ${action_class(line.modified.action)}"
            data-line-number="${line.modified.lineno}"
            >
            <div>
            %if line.modified.comments:
            <i class="icon-comment" onclick="return Rhodecode.comments.toggleLineComments(this)"></i>
            %endif
            </div>
        </td>
        <td class="cb-lineno ${action_class(line.modified.action)}"
            data-line-number="${line.modified.lineno}"
            %if new_line_anchor:
            id="${new_line_anchor}"
            %endif
            >
            %if line.modified.lineno:
                <a name="${new_line_anchor}" href="#${new_line_anchor}">${line.modified.lineno}</a>
            %endif
        </td>
        <td class="cb-content ${action_class(line.modified.action)}"
            data-line-number="n${line.modified.lineno}"
            >
            %if use_comments and line.modified.lineno:
            ${render_add_comment_button()}
            %endif
            <span class="cb-code">${line.modified.action} ${line.modified.content or '' | n}</span>
            %if use_comments and line.modified.lineno and line.modified.comments:
            ${inline_comments_container(line.modified.comments)}
            %endif
        </td>
    </tr>
    %endfor
</%def>


<%def name="render_hunk_lines_unified(hunk, use_comments=False)">
    %for old_line_no, new_line_no, action, content, comments in hunk.unified:
    <%
    old_line_anchor, new_line_anchor = None, None
    if old_line_no:
        old_line_anchor = diff_line_anchor(hunk.source_file_path, old_line_no, 'o')
    if new_line_no:
        new_line_anchor = diff_line_anchor(hunk.target_file_path, new_line_no, 'n')
    %>
    <tr class="cb-line">
        <td class="cb-data ${action_class(action)}">
            <div>
            %if comments:
            <i class="icon-comment" onclick="return Rhodecode.comments.toggleLineComments(this)"></i>
            %endif
            </div>
        </td>
        <td class="cb-lineno ${action_class(action)}"
            data-line-number="${old_line_no}"
            %if old_line_anchor:
            id="${old_line_anchor}"
            %endif
        >
            %if old_line_anchor:
            <a name="${old_line_anchor}" href="#${old_line_anchor}">${old_line_no}</a>
            %endif
        </td>
        <td class="cb-lineno ${action_class(action)}"
            data-line-number="${new_line_no}"
            %if new_line_anchor:
            id="${new_line_anchor}"
            %endif
        >
            %if new_line_anchor:
            <a name="${new_line_anchor}" href="#${new_line_anchor}">${new_line_no}</a>
            %endif
        </td>
        <td class="cb-content ${action_class(action)}"
            data-line-number="${new_line_no and 'n' or 'o'}${new_line_no or old_line_no}"
            >
            %if use_comments:
            ${render_add_comment_button()}
            %endif
            <span class="cb-code">${action} ${content or '' | n}</span>
            %if use_comments and comments:
            ${inline_comments_container(comments)}
            %endif
        </td>
    </tr>
    %endfor
</%def>

<%def name="render_add_comment_button()">
<button class="btn btn-small btn-primary cb-comment-box-opener" onclick="return Rhodecode.comments.createComment(this)">
    <span><i class="icon-comment"></i></span>
</button>
</%def>

<%def name="render_diffset_menu()">

    <div class="diffset-menu clearinner">
        <div class="pull-right">
            <div class="btn-group">

                <a
                  class="btn ${c.diffmode == 'sideside' and 'btn-primary'} tooltip"
                  title="${h.tooltip(_('View side by side'))}"
                  href="${h.url_replace(diffmode='sideside')}">
                    <span>${_('Side by Side')}</span>
                </a>
                <a
                  class="btn ${c.diffmode == 'unified' and 'btn-primary'} tooltip"
                  title="${h.tooltip(_('View unified'))}" href="${h.url_replace(diffmode='unified')}">
                    <span>${_('Unified')}</span>
                </a>
            </div>
        </div>

        <div class="pull-left">
          <div class="btn-group">
              <a
                  class="btn"
                  href="#"
                  onclick="$('input[class=filediff-collapse-state]').prop('checked', false); return false">${_('Expand All Files')}</a>
              <a
                  class="btn"
                  href="#"
                  onclick="$('input[class=filediff-collapse-state]').prop('checked', true); return false">${_('Collapse All Files')}</a>
              <a
                  class="btn"
                  href="#"
                  onclick="return Rhodecode.comments.toggleWideMode(this)">${_('Wide Mode Diff')}</a>
          </div>
        </div>
    </div>
</%def>
