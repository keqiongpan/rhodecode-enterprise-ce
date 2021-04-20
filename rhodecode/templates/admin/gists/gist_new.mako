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

                <label for='acl_level'>${_('Private Gist access level')}</label>
                ${h.dropdownmenu('gist_acl_level', '', c.acl_options)}

                <textarea style="margin-top: 5px; border-color: #dbd9da" id="description" name="description" placeholder="${_('Gist description ...')}"></textarea>
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

            <div class="pull-left">
                <div class="pull-right">
                    ${h.submit('create',_('Create Gist'),class_="btn")}
                </div>
                <div class="rcform-element pull-right">
                  <div class="fields gist-type-fields">
                    <fieldset>
                        <div class="gist-type-fields-wrapper">

                        <input type="radio" id="private_gist" checked="" name="gist_type" value="private" onchange="setGistId('private')">
                        <label for="private_gist">${_('Private Gist')}</label>
                        <span class="tooltip label" title="${_('Private Gists are not listed and only accessible through their secret url.')}">${_('Private Gist')}</span>

                        <input type="radio" id="public_gist" name="gist_type" value="public" onchange="setGistId('public')">
                        <label for="public_gist">${_('Public Gist')}</label>
                        <span class="tooltip label" title="${_('Public Gists are accessible to anyone and listed in Gists page.')}">${_('Public Gist')}</span>
                        </div>
                    </fieldset>
                  </div>
                </div>

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

    setGistId = function(gistType) {
        if (gistType === 'private') {
            $('#gistid').removeAttr('disabled');
        }
        else {
            $('#gistid').val('');
            $('#gistid').attr('disabled', 'disabled')
        }
    }
</script>
</%def>
