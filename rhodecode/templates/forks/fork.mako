## -*- coding: utf-8 -*-
<%inherit file="/base/base.mako"/>

<%def name="title()">
    ${_('Fork repository %s') % c.repo_name}
    %if c.rhodecode_name:
        &middot; ${h.branding(c.rhodecode_name)}
    %endif
</%def>

<%def name="breadcrumbs_links()">
    ${_('New Fork')}
</%def>

<%def name="menu_bar_nav()">
    ${self.menu_items(active='repositories')}
</%def>

<%def name="menu_bar_subnav()">
  ${self.repo_menu(active='options')}
</%def>

<%def name="main()">
<div class="box">
      <div class="title">
          ${self.repo_page_title(c.rhodecode_db_repo)}
          ${self.breadcrumbs()}
      </div>

    ${h.secure_form(h.route_path('repo_fork_create',repo_name=c.rhodecode_db_repo.repo_name), method='POST', request=request)}
    <div class="form">
        <!-- fields -->
        <div class="fields">

            <div class="field">
              <div class="label">
                  <label for="repo_name">${_('Fork name')}:</label>
              </div>
              <div class="input">
                  ${h.text('repo_name', class_="medium")}
                  ${h.hidden('repo_type',c.rhodecode_db_repo.repo_type)}
                  ${h.hidden('fork_parent_id',c.rhodecode_db_repo.repo_id)}
              </div>
            </div>

            <div class="field">
                <div class="label label-textarea">
                    <label for="description">${_('Description')}:</label>
                </div>
                <div class="textarea-repo textarea text-area editor">
                    ${h.textarea('description')}
                    <% metatags_url = h.literal('''<a href="#metatagsShow" onclick="$('#meta-tags-desc').toggle();return false">meta-tags</a>''') %>
                    <span class="help-block">${_('Plain text format with support of {metatags}. Add a README file for longer descriptions').format(metatags=metatags_url)|n}</span>
                    <span id="meta-tags-desc" style="display: none">
                        <%namespace name="dt" file="/data_table/_dt_elements.mako"/>
                        ${dt.metatags_help()}
                    </span>
                </div>
            </div>

            <div class="field">
                 <div class="label">
                     <label for="repo_group">${_('Repository group')}:</label>
                 </div>
                 <div class="select">
                     ${h.select('repo_group','',c.repo_groups,class_="medium")}
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
                    <label for="landing_rev">${_('Landing commit')}:</label>
                </div>
                <div class="select">
                    ${h.select('landing_rev','',c.landing_revs,class_="medium")}
                    <span class="help-block">${_('Default commit for files page, downloads, whoosh and readme')}</span>
                </div>
            </div>

            <div class="field">
                <div class="label label-checkbox">
                    <label for="private">${_('Private')}:</label>
                </div>
                <div class="checkboxes">
                    ${h.checkbox('private',value="True")}
                    <span class="help-block">${_('Private repositories are only visible to people explicitly added as collaborators.')}</span>
                </div>
            </div>

            <div class="field">
                <div class="label label-checkbox">
                    <label for="private">${_('Copy permissions')}:</label>
                </div>
                <div class="checkboxes">
                    ${h.checkbox('copy_permissions',value="True", checked="checked")}
                    <span class="help-block">${_('Copy permissions from forked repository')}</span>
                </div>
            </div>

            <div class="buttons">
                ${h.submit('',_('Fork this Repository'),class_="btn")}
            </div>
        </div>
    </div>
    ${h.end_form()}
</div>
<script>
    $(document).ready(function(){
        $("#repo_group").select2({
            'dropdownAutoWidth': true,
            'containerCssClass': "drop-menu",
            'dropdownCssClass': "drop-menu-dropdown",
            'width': "resolve"
        });
        $("#landing_rev").select2({
            'containerCssClass': "drop-menu",
            'dropdownCssClass': "drop-menu-dropdown",
            'minimumResultsForSearch': -1
        });
        $('#repo_name').focus();

        $('#select_my_group').on('click', function(e){
            e.preventDefault();
            $("#repo_group").val($(this).data('personalGroupId')).trigger("change");
        })
    })
</script>
</%def>
