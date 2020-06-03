<%inherit file="/base/base.mako"/>

<%def name="title()">
    ${_('{} Files Add').format(c.repo_name)}
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
        <span class="title-heading">${_('Add new file')} @ <code>${h.show_id(c.commit)}</code></span>
        % if c.commit.branch:
        <span class="tag branchtag">
            <i class="icon-branch"></i> ${c.commit.branch}
        </span>
        % endif
    </div>

    ${h.secure_form(h.route_path('repo_files_create_file', repo_name=c.repo_name, commit_id=c.commit.raw_id, f_path=c.f_path), id='eform', request=request)}
    <div class="edit-file-fieldset">
        <div class="path-items">
            <ul>
            <li class="breadcrumb-path">
                <div>
                    ${h.files_breadcrumbs(c.repo_name, c.commit.raw_id, c.f_path, c.rhodecode_db_repo.landing_ref_name, request.GET.get('at'), limit_items=True, hide_last_item=False, linkify_last_item=True, copy_path_icon=False)} /
                </div>
            </li>
            <li class="location-path">
                <input  class="file-name-input input-small" type="text" value="${request.GET.get('filename')}" name="filename" id="filename" placeholder="${_('Filename e.g example.py, or docs/readme.md')}">
            </li>
            </ul>
        </div>

    </div>

    <div class="table">
        <div>
            <div id="codeblock" class="codeblock">
                <div class="editor-items">
                    <div class="editor-action active show-editor pull-left" onclick="fileEditor.showEditor(); return false">
                        ${_('Edit')}
                    </div>

                    <div class="editor-action show-preview pull-left"  onclick="fileEditor.showPreview(); return false">
                        ${_('Preview')}
                    </div>

                    <div class="pull-right">
                        ${h.dropdownmenu('line_wrap', 'off', [('on', _('Line wraps on')), ('off', _('line wraps off'))], extra_classes=['last-item'])}
                    </div>
                    <div class="pull-right">
                        ${h.dropdownmenu('set_mode','plain',[('plain', _('plain'))], enable_filter=True)}
                    </div>
                </div>

                <div id="editor_container">
                    <pre id="editor_pre"></pre>
                    <textarea id="editor" name="content" ></textarea>
                    <div id="editor_preview"></div>
                </div>
            </div>
        </div>
    </div>

    <div class="edit-file-fieldset">
        <div class="fieldset">
            <div class="message">
                <textarea id="commit" name="message"  placeholder="${c.default_message}"></textarea>
            </div>
        </div>
        <div class="pull-left">
            ${h.submit('commit_btn',_('Commit changes'), class_="btn btn-small btn-success")}
        </div>
    </div>
    ${h.end_form()}
</div>

<script type="text/javascript">

    $(document).ready(function () {
        var modes_select = $('#set_mode');
        var filename_selector = '#filename';
        fillCodeMirrorOptions(modes_select);

        fileEditor = new FileEditor('#editor');

        // on change of select field set mode
        setCodeMirrorModeFromSelect(modes_select, filename_selector, fileEditor.cm, null);

        // on entering the new filename set mode, from given extension
        setCodeMirrorModeFromInput(modes_select, filename_selector, fileEditor.cm, null);

        $('#filename').focus();

        var commit_id =  "${c.commit.raw_id}";
        var f_path = "${c.f_path}";

        checkFileHead($('#eform'), commit_id, f_path, 'create')
    });

</script>
</%def>
