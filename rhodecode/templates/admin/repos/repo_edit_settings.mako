## -*- coding: utf-8 -*-
<%namespace name="base" file="/base/base.mako"/>

<div class="panel panel-default">
    <div class="panel-heading">
        <h3 class="panel-title">${_('Settings for Repository: %s') % c.rhodecode_db_repo.repo_name}</h3>
    </div>
    <div class="panel-body">
    ${h.secure_form(h.route_path('edit_repo', repo_name=c.rhodecode_db_repo.repo_name), request=request)}
    <div class="form">
        <!-- fields -->
        <div class="fields">

            <div class="field">
                <div class="label">
                    <label for="repo_name">${_('Name')}:</label>
                </div>
                <div class="input">
                    ${c.form['repo_name'].render(css_class='medium', oid='repo_name')|n}
                    ${c.form.render_error(request, c.form['repo_name'])|n}

                    <p class="help-block">${_('permalink id')}: `_${c.rhodecode_db_repo.repo_id}` <span><a href="#" onclick="$('#clone_id').toggle();return false">${_('what is that ?')}</a></span></p>
                    <p id="clone_id" style="display:none;">
                        ${_('URL by id')}: `${c.rhodecode_db_repo.clone_url(with_id=True)}` <br/>
                        ${_('''In case this repository is renamed or moved into another group the repository url changes.
                               Using above url guarantees that this repository will always be accessible under such url.
                               Useful for CI systems, or any other cases that you need to hardcode the url into 3rd party service.''')}</p>
                </div>
           </div>

           <div class="field">
                <div class="label">
                    <label for="repo_group">${_('Repository group')}:</label>
                </div>
                <div class="select">
                    ${c.form['repo_group'].render(css_class='medium', oid='repo_group')|n}
                    ${c.form.render_error(request, c.form['repo_group'])|n}

                    % if c.personal_repo_group:
                         <a class="btn" href="#" data-personal-group-name="${c.personal_repo_group.group_name}" data-personal-group-id="${c.personal_repo_group.group_id}" onclick="selectMyGroup(this); return false">
                             ${_('Select my personal group (`%(repo_group_name)s`)') % {'repo_group_name': c.personal_repo_group.group_name}}
                         </a>
                    % endif
                    <p class="help-block">${_('Optional select a group to put this repository into.')}</p>
                </div>
           </div>

           % if c.rhodecode_db_repo.repo_type != 'svn':
           <% sync_link = h.literal(h.link_to('remote sync', h.route_path('edit_repo_remote', repo_name=c.repo_name))) %>
           <div class="field">
               <div class="label">
                   <label for="clone_uri">${_('Remote pull uri')}:</label>
               </div>
               <div class="input">
                   %if c.rhodecode_db_repo.clone_uri:
                    ## display, if we don't have any errors
                    % if not c.form['repo_clone_uri'].error:
                    <div id="clone_uri_hidden" class='text-as-placeholder'>
                        <span id="clone_uri_hidden_value">${c.rhodecode_db_repo.clone_uri_hidden}</span>
                        <span class="link" id="edit_clone_uri">${_('edit')}</span>
                    </div>
                    % endif

                    ## alter field
                    <div id="alter_clone_uri" style="${'' if c.form['repo_clone_uri'].error else 'display: none'}">
                        ${c.form['repo_clone_uri'].render(css_class='medium', oid='clone_uri', placeholder=_('enter new value, or leave empty to remove'))|n}
                        ${c.form.render_error(request, c.form['repo_clone_uri'])|n}
                        % if c.form['repo_clone_uri'].error:
                            ## we got error from form subit, means we modify the url
                            ${h.hidden('repo_clone_uri_change', 'MOD')}
                        % else:
                            ${h.hidden('repo_clone_uri_change', 'OLD')}
                        % endif

                        % if not c.form['repo_clone_uri'].error:
                        <span class="link" id="cancel_edit_clone_uri">${_('cancel')}</span>
                        % endif

                    </div>
                   %else:
                    ## not set yet, display form to set it
                    ${c.form['repo_clone_uri'].render(css_class='medium', oid='clone_uri')|n}
                    ${c.form.render_error(request, c.form['repo_clone_uri'])|n}
                    ${h.hidden('repo_clone_uri_change', 'NEW')}
                   %endif
                 <p id="alter_clone_uri_help_block" class="help-block">
                     ${_('http[s] url where from repository was imported. This field can used for doing {sync_link}.').format(sync_link=sync_link)|n} <br/>
                     ${_('This field is stored encrypted inside Database, a format of http://user:password@server.com/repo_name can be used and will be hidden from display.')}
                 </p>
               </div>
            </div>
           <div class="field">
               <div class="label">
                   <label for="push_uri">${_('Remote push uri')}:</label>
               </div>
               <div class="input">
                   %if c.rhodecode_db_repo.push_uri:
                    ## display, if we don't have any errors
                    % if not c.form['repo_push_uri'].error:
                    <div id="push_uri_hidden" class='text-as-placeholder'>
                        <span id="push_uri_hidden_value">${c.rhodecode_db_repo.push_uri_hidden}</span>
                        <span class="link" id="edit_push_uri">${_('edit')}</span>
                    </div>
                    % endif

                    ## alter field
                    <div id="alter_push_uri" style="${'' if c.form['repo_push_uri'].error else 'display: none'}">
                        ${c.form['repo_push_uri'].render(css_class='medium', oid='push_uri', placeholder=_('enter new value, or leave empty to remove'))|n}
                        ${c.form.render_error(request, c.form['repo_push_uri'])|n}
                        % if c.form['repo_push_uri'].error:
                            ## we got error from form subit, means we modify the url
                            ${h.hidden('repo_push_uri_change', 'MOD')}
                        % else:
                            ${h.hidden('repo_push_uri_change', 'OLD')}
                        % endif

                        % if not c.form['repo_push_uri'].error:
                        <span class="link" id="cancel_edit_push_uri">${_('cancel')}</span>
                        % endif

                    </div>
                   %else:
                    ## not set yet, display form to set it
                    ${c.form['repo_push_uri'].render(css_class='medium', oid='push_uri')|n}
                    ${c.form.render_error(request, c.form['repo_push_uri'])|n}
                    ${h.hidden('repo_push_uri_change', 'NEW')}
                   %endif
                 <p id="alter_push_uri_help_block" class="help-block">
                     ${_('http[s] url to sync data back. This field can used for doing {sync_link}.').format(sync_link=sync_link)|n} <br/>
                     ${_('This field is stored encrypted inside Database, a format of http://user:password@server.com/repo_name can be used and will be hidden from display.')}
                 </p>
               </div>
            </div>
           % else:
           ${h.hidden('repo_clone_uri', '')}
           ${h.hidden('repo_push_uri', '')}
           % endif

            <div class="field">
                <div class="label">
                    <label for="repo_landing_commit_ref">${_('Landing commit')}:</label>
                </div>
                <div class="select">
                    ${c.form['repo_landing_commit_ref'].render(css_class='medium', oid='repo_landing_commit_ref')|n}
                    ${c.form.render_error(request, c.form['repo_landing_commit_ref'])|n}
                    <p class="help-block">${_('The default commit for file pages, downloads, full text search index, and README generation.')}</p>
                </div>
            </div>

            <div class="field badged-field">
                <div class="label">
                    <label for="repo_owner">${_('Owner')}:</label>
                </div>
                <div class="input">
                    <div class="badge-input-container">
                        <div class="user-badge">
                            ${base.gravatar_with_user(c.rhodecode_db_repo.user.email or c.rhodecode_db_repo.user.username, show_disabled=not c.rhodecode_db_repo.user.active)}
                        </div>
                        <div class="badge-input-wrap">
                            ${c.form['repo_owner'].render(css_class='medium', oid='repo_owner')|n}
                        </div>
                    </div>
                    ${c.form.render_error(request, c.form['repo_owner'])|n}
                    <p class="help-block">${_('Change owner of this repository.')}</p>
                </div>
            </div>

            <div class="field">
                <div class="label label-textarea">
                    <label for="repo_description">${_('Description')}:</label>
                </div>
                <div class="textarea text-area editor">
                    ${c.form['repo_description'].render(css_class='medium', oid='repo_description')|n}
                    ${c.form.render_error(request, c.form['repo_description'])|n}

                    <% metatags_url = h.literal('''<a href="#metatagsShow" onclick="$('#meta-tags-desc').toggle();return false">meta-tags</a>''') %>
                    <span class="help-block">${_('Plain text format with support of {metatags}. Add a README file for longer descriptions').format(metatags=metatags_url)|n}</span>
                    <span id="meta-tags-desc" style="display: none">
                        <%namespace name="dt" file="/data_table/_dt_elements.mako"/>
                        ${dt.metatags_help()}
                    </span>
                </div>
            </div>

            <div class="field">
                <div class="label label-checkbox">
                    <label for="${c.form['repo_private'].oid}">${_('Private repository')}:</label>
                </div>
                <div class="checkboxes">
                    ${c.form['repo_private'].render(css_class='medium')|n}
                    ${c.form.render_error(request, c.form['repo_private'])|n}
                    <span class="help-block">${_('Private repositories are only visible to people explicitly added as collaborators.')}</span>
                </div>
            </div>
            <div class="field">
                <div class="label label-checkbox">
                    <label for="${c.form['repo_enable_statistics'].oid}">${_('Enable statistics')}:</label>
                </div>
                <div class="checkboxes">
                    ${c.form['repo_enable_statistics'].render(css_class='medium')|n}
                    ${c.form.render_error(request, c.form['repo_enable_statistics'])|n}
                    <span class="help-block">${_('Enable statistics window on summary page.')}</span>
                </div>
            </div>
            <div class="field">
                <div class="label label-checkbox">
                    <label for="${c.form['repo_enable_downloads'].oid}">${_('Enable downloads')}:</label>
                </div>
                <div class="checkboxes">
                    ${c.form['repo_enable_downloads'].render(css_class='medium')|n}
                    ${c.form.render_error(request, c.form['repo_enable_downloads'])|n}
                    <span class="help-block">${_('Enable download menu on summary page.')}</span>
                </div>
            </div>
            <div class="field">
                <div class="label label-checkbox">
                    <label for="${c.form['repo_enable_locking'].oid}">${_('Enable automatic locking')}:</label>
                </div>
                <div class="checkboxes">
                    ${c.form['repo_enable_locking'].render(css_class='medium')|n}
                    ${c.form.render_error(request, c.form['repo_enable_locking'])|n}
                    <span class="help-block">${_('Enable automatic locking on repository. Pulling from this repository creates a lock that can be released by pushing back by the same user')}</span>
                </div>
            </div>

            %if c.visual.repository_fields:
              ## EXTRA FIELDS
              %for field in c.repo_fields:
                <div class="field">
                    <div class="label">
                        <label for="${field.field_key_prefixed}">${field.field_label} (${field.field_key}):</label>
                    </div>
                    <div class="input input-medium">
                        ${h.text(field.field_key_prefixed, field.field_value, class_='medium')}
                        %if field.field_desc:
                          <span class="help-block">${field.field_desc}</span>
                        %endif
                    </div>
                 </div>
              %endfor
            %endif
            <div class="buttons">
              ${h.submit('save',_('Save'),class_="btn")}
              ${h.reset('reset',_('Reset'),class_="btn")}
            </div>
        </div>
    </div>
    ${h.end_form()}
  </div>
</div>

<script>
    $(document).ready(function () {
        var cloneUrl = function (
            alterButton, editButton, cancelEditButton,
            hiddenUrl, hiddenUrlValue, input, helpBlock, changedFlag) {

          var originalText = helpBlock.html();
          var obfuscatedUrl = hiddenUrlValue.html();

          var edit = function(e) {
            alterButton.show();
            editButton.hide();
            hiddenUrl.hide();

            //add the old value next to input for verification
            helpBlock.html("(" + obfuscatedUrl + ")" + "<br\>" + originalText);
            changedFlag.val('MOD');
          };

          var cancelEdit = function(e) {
            alterButton.hide();
            editButton.show();
            hiddenUrl.show();

            helpBlock.html(originalText);
            changedFlag.val('OLD');
            input.val('');
          };

          var initEvents = function() {
            editButton.on('click', edit);
            cancelEditButton.on('click', cancelEdit);
          };

          var setInitialState = function() {
            if (input.hasClass('error')) {
              alterButton.show();
              editButton.hide();
              hiddenUrl.hide();
            }
          };

          setInitialState();
          initEvents();
        };


        var alterButton = $('#alter_clone_uri');
        var editButton = $('#edit_clone_uri');
        var cancelEditButton = $('#cancel_edit_clone_uri');
        var hiddenUrl = $('#clone_uri_hidden');
        var hiddenUrlValue = $('#clone_uri_hidden_value');
        var input = $('#clone_uri');
        var helpBlock = $('#alter_clone_uri_help_block');
        var changedFlag = $('#repo_clone_uri_change');
        cloneUrl(
            alterButton, editButton, cancelEditButton, hiddenUrl,
            hiddenUrlValue, input, helpBlock, changedFlag);

        var alterButton = $('#alter_push_uri');
        var editButton = $('#edit_push_uri');
        var cancelEditButton = $('#cancel_edit_push_uri');
        var hiddenUrl = $('#push_uri_hidden');
        var hiddenUrlValue = $('#push_uri_hidden_value');
        var input = $('#push_uri');
        var helpBlock = $('#alter_push_uri_help_block');
        var changedFlag = $('#repo_push_uri_change');
        cloneUrl(
            alterButton, editButton, cancelEditButton, hiddenUrl,
            hiddenUrlValue, input, helpBlock, changedFlag);

        selectMyGroup = function(element) {
            $("#repo_group").val($(element).data('personalGroupId')).trigger("change");
        };

        UsersAutoComplete('repo_owner', '${c.rhodecode_user.user_id}');
    });
</script>
