## -*- coding: utf-8 -*-

${h.secure_form(h.route_path('repo_create'), request=request)}
<div class="form">
    <!-- fields -->
    <div class="fields">
        <div class="field">
            <div class="label">
                <label for="repo_name">${_('Repository name')}:</label>
            </div>
            <div class="input">
                ${h.text('repo_name', class_="medium")}
                <div class="info-block">
                    <a id="remote_clone_toggle" href="#">${_('Import Existing Repository ?')}</a>
                </div>
                %if not c.rhodecode_user.is_admin:
                    ${h.hidden('user_created',True)}
                %endif
            </div>
         </div>
        <div id="remote_clone" class="field" style="display: none;">
            <div class="label">
                <label for="clone_uri">${_('Clone from')}:</label>
            </div>
            <div class="input">
                ${h.text('clone_uri', class_="medium")}
                <span class="help-block">
                    <pre>
- The repository must be accessible over http:// or https://
- For Git projects it's recommended appending .git to the end of clone url.
- Make sure to select proper repository type from the below selector before importing it.
- If your HTTP[S] repository is not publicly accessible,
  add authentication information to the URL: https://username:password@server.company.com/repo-name.
- The Git LFS/Mercurial Largefiles objects will not be imported.
- For very large repositories, it's recommended to manually copy them into the
  RhodeCode <a href="${h.route_path('admin_settings_vcs', _anchor='vcs-storage-options')}">storage location</a> and run <a href="${h.route_path('admin_settings_mapping')}">Remap and Rescan</a>.
                    </pre>
                </span>
            </div>
        </div>
        <div class="field">
             <div class="label">
                 <label for="repo_group">${_('Repository group')}:</label>
             </div>
             <div class="select">
                 ${h.select('repo_group',request.GET.get('parent_group'),c.repo_groups,class_="medium")}
                 % if c.personal_repo_group:
                     <a class="btn" href="#" id="select_my_group" data-personal-group-id="${c.personal_repo_group.group_id}">
                         ${_('Select my personal group (%(repo_group_name)s)') % {'repo_group_name': c.personal_repo_group.group_name}}
                     </a>
                 % endif
                 <span class="help-block">${_('Optionally select a group to put this repository into.')}</span>
             </div>
        </div>
        <div class="field">
            <div class="label">
                <label for="repo_type">${_('Type')}:</label>
            </div>
            <div class="select">
                ${h.select('repo_type','hg',c.backends)}
                <span class="help-block">${_('Set the type of repository to create.')}</span>
            </div>
        </div>
        <div class="field">
            <div class="label">
                <label for="repo_description">${_('Description')}:</label>
            </div>
            <div class="textarea editor">
                ${h.textarea('repo_description',cols=23,rows=5,class_="medium")}
                <% metatags_url = h.literal('''<a href="#metatagsShow" onclick="$('#meta-tags-desc').toggle();return false">meta-tags</a>''') %>
                <span class="help-block">
                    % if c.visual.stylify_metatags:
                        ${_('Plain text format with {metatags} support.').format(metatags=metatags_url)|n}
                    % else:
                        ${_('Plain text format.')}
                    % endif
                    ${_('Add a README file for longer descriptions')}
                </span>
                <span id="meta-tags-desc" style="display: none">
                    <%namespace name="dt" file="/data_table/_dt_elements.mako"/>
                    ${dt.metatags_help()}
                </span>
            </div>
        </div>
        <div id="copy_perms" class="field">
            <div class="label label-checkbox">
                <label for="repo_copy_permissions">${_('Copy Parent Group Permissions')}:</label>
            </div>
            <div class="checkboxes">
                ${h.checkbox('repo_copy_permissions', value="True", checked="checked")}
                <span class="help-block">${_('Copy permissions from parent repository group.')}</span>
            </div>
        </div>
        <div class="field">
            <div class="label label-checkbox">
                <label for="repo_private">${_('Private Repository')}:</label>
            </div>
            <div class="checkboxes">
                ${h.checkbox('repo_private',value="True")}
                <span class="help-block">${_('Private repositories are only visible to people explicitly added as collaborators.')}</span>
            </div>
        </div>
        <div class="buttons">
          ${h.submit('save',_('Create Repository'),class_="btn")}
        </div>
    </div>
</div>
<script>
    $(document).ready(function(){
        var setCopyPermsOption = function(group_val){
            if(group_val != "-1"){
                $('#copy_perms').show()
            }
            else{
                $('#copy_perms').hide();
            }
        };

        $('#remote_clone_toggle').on('click', function(e){
            $('#remote_clone').show();
            e.preventDefault();
        });

        if($('#remote_clone input').hasClass('error')){
            $('#remote_clone').show();
        }
        if($('#remote_clone input').val()){
            $('#remote_clone').show();
        }

        $("#repo_group").select2({
            'containerCssClass': "drop-menu",
            'dropdownCssClass': "drop-menu-dropdown",
            'dropdownAutoWidth': true,
            'width': "resolve"
        });

        setCopyPermsOption($('#repo_group').val());
        $("#repo_group").on("change", function(e) {
            setCopyPermsOption(e.val)
        });

        $("#repo_type").select2({
            'containerCssClass': "drop-menu",
            'dropdownCssClass': "drop-menu-dropdown",
            'minimumResultsForSearch': -1,
        });

        $('#repo_name').focus();

        $('#select_my_group').on('click', function(e){
            e.preventDefault();
            $("#repo_group").val($(this).data('personalGroupId')).trigger("change");
        })

    })
</script>
${h.end_form()}
