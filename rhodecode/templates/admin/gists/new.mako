## -*- coding: utf-8 -*-
<%inherit file="/base/base.mako"/>

<%def name="title()">
    ${_('New Gist')}
    %if c.rhodecode_name:
        &middot; ${h.branding(c.rhodecode_name)}
    %endif
</%def>

<%def name="breadcrumbs_links()"></%def>

<%def name="menu_bar_nav()">
    ${self.menu_items(active='gists')}
</%def>

<%def name="main()">
<div class="box">
    <!-- box / title -->
    <div class="title">

    </div>

    <div class="table">
        <div id="files_data">
          ${h.secure_form(h.route_path('gists_create'), id='eform', request=request)}
            <div>
                <span class="gist-gravatar">
                    ${self.gravatar(c.rhodecode_user.email, 30)}
                </span>
                <label for='gistid'>${_('Gist id')}</label>
                ${h.text('gistid', placeholder=_('Auto generated'))}

                <label for='lifetime'>${_('Gist lifetime')}</label>
                ${h.dropdownmenu('lifetime', '', c.lifetime_options)}

                <label for='acl_level'>${_('Gist access level')}</label>
                ${h.dropdownmenu('gist_acl_level', '', c.acl_options)}

                <textarea style="margin-top: 5px" id="description" name="description" placeholder="${_('Gist description ...')}"></textarea>
            </div>

            <div id="codeblock" class="codeblock">
                <div class="code-header">
                    <div class="form">
                        <div class="fields">
                            ${h.text('filename', size=30, placeholder=_('name gist file...'))}
                            ${h.dropdownmenu('mimetype','plain',[('plain',_('plain'))],enable_filter=True)}
                        </div>
                    </div>
                </div>

                <div id="editor_container">
                    <div id="editor_pre"></div>
                    <textarea id="editor" name="content" ></textarea>
                </div>
            </div>

            <div class="pull-right">
            ${h.submit('private',_('Create Private Gist'),class_="btn")}
            ${h.submit('public',_('Create Public Gist'),class_="btn")}
            </div>
            ${h.end_form()}
        </div>
    </div>

</div>

<script type="text/javascript">
    var myCodeMirror = initCodeMirror('editor', '');

    var modes_select = $('#mimetype');
    fillCodeMirrorOptions(modes_select);

    var filename_selector = '#filename';
    // on change of select field set mode
    setCodeMirrorModeFromSelect(
            modes_select, filename_selector, myCodeMirror, null);

    // on entering the new filename set mode, from given extension
    setCodeMirrorModeFromInput(
        modes_select, filename_selector, myCodeMirror, null);

</script>
</%def>
