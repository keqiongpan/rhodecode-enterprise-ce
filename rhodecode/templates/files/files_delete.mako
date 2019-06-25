<%inherit file="/base/base.mako"/>

<%def name="title()">
    ${_('{} Files Delete').format(c.repo_name)}
    %if c.rhodecode_name:
        &middot; ${h.branding(c.rhodecode_name)}
    %endif
</%def>

<%def name="menu_bar_nav()">
    ${self.menu_items(active='repositories')}
</%def>

<%def name="breadcrumbs_links()"></%def>

<%def name="menu_bar_subnav()">
    ${self.repo_menu(active='files')}
</%def>

<%def name="main()">

<div class="box">

    <div class="edit-file-title">
        <span class="title-heading">${_('Delete file')} @ <code>${h.show_id(c.commit)}</code></span>
        % if c.commit.branch:
        <span class="tag branchtag">
            <i class="icon-branch"></i> ${c.commit.branch}
        </span>
        % endif
    </div>

    ${h.secure_form(h.route_path('repo_files_delete_file', repo_name=c.repo_name, commit_id=c.commit.raw_id, f_path=c.f_path), id='eform', request=request)}
    <div class="edit-file-fieldset">
        <div class="path-items">
            <li class="breadcrumb-path">
                <div>
                    <a href="${h.route_path('repo_files', repo_name=c.repo_name, commit_id=c.commit.raw_id, f_path='')}"><i class="icon-home"></i></a> /
                    <a href="${h.route_path('repo_files', repo_name=c.repo_name, commit_id=c.commit.raw_id, f_path=c.file.dir_path)}">${c.file.dir_path}</a> ${('/' if c.file.dir_path else '')}
                </div>
            </li>
            <li class="location-path">
                <input type="hidden" value="${c.f_path}" name="root_path">
                <input  class="file-name-input input-small" type="text" value="${c.file.name}" name="filename" id="filename" disabled="disabled">
            </li>
        </div>

    </div>

    <div id="codeblock" class="codeblock delete-file-preview">
        <div class="code-body">
            %if c.file.is_binary:
                ${_('Binary file (%s)') % c.file.mimetype}
            %else:
                %if c.file.size < c.visual.cut_off_limit_file:
                    ${h.pygmentize(c.file,linenos=True,anchorlinenos=False,cssclass="code-highlight")}
                %else:
                    ${_('File size {} is bigger then allowed limit {}. ').format(h.format_byte_size_binary(c.file.size), h.format_byte_size_binary(c.visual.cut_off_limit_file))} ${h.link_to(_('Show as raw'),
                    h.route_path('repo_file_raw',repo_name=c.repo_name,commit_id=c.commit.raw_id,f_path=c.f_path))}
                %endif
            %endif
        </div>
    </div>

    <div class="edit-file-fieldset">
        <div class="fieldset">
            <div class="message">
                <textarea id="commit" name="message"  placeholder="${c.default_message}"></textarea>
            </div>
        </div>
        <div class="pull-left">
            ${h.submit('commit',_('Commit changes'),class_="btn btn-small btn-danger-action")}
        </div>
    </div>
    ${h.end_form()}
</div>


<script type="text/javascript">

    $(document).ready(function () {

        fileEditor = new FileEditor('#editor');

    });

</script>

</%def>
