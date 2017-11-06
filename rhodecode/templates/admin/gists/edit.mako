## -*- coding: utf-8 -*-
<%inherit file="/base/base.mako"/>

<%def name="title()">
    ${_('Edit Gist')} &middot; ${c.gist.gist_access_id}
    %if c.rhodecode_name:
        &middot; ${h.branding(c.rhodecode_name)}
    %endif
</%def>

<%def name="breadcrumbs_links()">
    ${_('Edit Gist')} &middot; ${c.gist.gist_access_id}
</%def>

<%def name="menu_bar_nav()">
    ${self.menu_items(active='gists')}
</%def>

<%def name="main()">
<div class="box">
    <!-- box / title -->
    <div class="title">
        ${self.breadcrumbs()}
    </div>

    <div class="table">

        <div id="files_data">
          ${h.secure_form(h.route_path('gist_update', gist_id=c.gist.gist_access_id), id='eform', request=request)}
            <div>
                <input type="hidden" value="${c.file_last_commit.raw_id}" name="parent_hash">
                <textarea id="description" name="description"
                          placeholder="${_('Gist description ...')}">${c.gist.gist_description}</textarea>
                <div>
                    <span class="gist-gravatar">
                      ${self.gravatar(h.email_or_none(c.rhodecode_user.full_contact), 30)}
                    </span>
                    <label for='lifetime'>${_('Gist lifetime')}</label>
                    ${h.dropdownmenu('lifetime', '0', c.lifetime_options)}

                    <label for='gist_acl_level'>${_('Gist access level')}</label>
                    ${h.dropdownmenu('gist_acl_level', c.gist.acl_level, c.acl_options)}
                </div>
            </div>

            ## peppercorn schema
            <input type="hidden" name="__start__" value="nodes:sequence"/>
            % for cnt, file in enumerate(c.files):
                <input type="hidden" name="__start__" value="file:mapping"/>
                <div id="codeblock" class="codeblock" >
                  <div class="code-header">
                    <div class="form">
                      <div class="fields">
                        <input type="hidden" name="filename_org" value="${file.path}" >
                        <input id="filename_${h.FID('f',file.path)}" name="filename" size="30" type="text" value="${file.path}">
                          ${h.dropdownmenu('mimetype' ,'plain',[('plain',_('plain'))],enable_filter=True, id='mimetype_'+h.FID('f',file.path))}
                      </div>
                    </div>
                  </div>
                  <div class="editor_container">
                      <pre id="editor_pre"></pre>
                      <textarea id="editor_${h.FID('f',file.path)}" name="content" >${file.content}</textarea>
                  </div>
                </div>
                <input type="hidden" name="__end__" />

                ## dynamic edit box.
                <script type="text/javascript">
                $(document).ready(function(){
                    var myCodeMirror = initCodeMirror(
                            "editor_${h.FID('f',file.path)}", '');

                    var modes_select = $("#mimetype_${h.FID('f',file.path)}");
                    fillCodeMirrorOptions(modes_select);

                    // try to detect the mode based on the file we edit
                    var mimetype = "${file.mimetype}";
                    var detected_mode = detectCodeMirrorMode(
                            "${file.path}", mimetype);

                    if(detected_mode){
                        $(modes_select).select2("val", mimetype);
                        $(modes_select).change();
                        setCodeMirrorMode(myCodeMirror, detected_mode);
                    }

                    var filename_selector = "#filename_${h.FID('f',file.path)}";
                    // on change of select field set mode
                    setCodeMirrorModeFromSelect(
                            modes_select, filename_selector, myCodeMirror, null);

                    // on entering the new filename set mode, from given extension
                    setCodeMirrorModeFromInput(
                        modes_select, filename_selector, myCodeMirror, null);
                });
                </script>
            %endfor
            <input type="hidden" name="__end__" />

            <div class="pull-right">
            ${h.submit('update',_('Update Gist'),class_="btn btn-success")}
            <a class="btn" href="${h.route_path('gist_show', gist_id=c.gist.gist_access_id)}">${_('Cancel')}</a>
            </div>
          ${h.end_form()}
        </div>
    </div>

</div>
<script>
  $('#update').on('click', function(e){
      e.preventDefault();

      $(this).val('Updating...');
      $(this).attr('disabled', 'disabled');
      // check for newer version.
      $.ajax({
        url: "${h.route_path('gist_edit_check_revision', gist_id=c.gist.gist_access_id)}",
        data: {
            'revision': '${c.file_last_commit.raw_id}'
        },
        dataType: 'json',
        type: 'GET',
        success: function(data) {
          if(data.success === false){
            message = '${h.literal(_('Gist was updated since you started editing. Copy your changes and click %(here)s to reload the new version.')
              % {'here': h.link_to('here', h.route_path('gist_edit', gist_id=c.gist.gist_access_id))})}'
            alertMessage = [{"message": {
              "message": message, "force": "true", "level": "warning"}}];
            $.Topic('/notifications').publish(alertMessage[0]);
          }
          else{
            $('#eform').submit();
          }
        }
      });
  })

</script>
</%def>
