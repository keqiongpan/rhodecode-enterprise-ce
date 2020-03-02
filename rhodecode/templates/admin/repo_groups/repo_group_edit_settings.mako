## -*- coding: utf-8 -*-
<%namespace name="base" file="/base/base.mako"/>

<div class="panel panel-default">
    <div class="panel-heading">
        <h3 class="panel-title">${_('Repository Group Settings: {}').format(c.repo_group.name)}</h3>
    </div>
    <div class="panel-body">
        ${h.secure_form(h.route_path('edit_repo_group', repo_group_name=c.repo_group.group_name), request=request)}
        <div class="form">
            <!-- fields -->
            <div class="fields">
                <div class="field">
                    <div class="label">
                        <label for="group_name">${_('Group name')}:</label>
                    </div>
                    <div class="input">
                        ${c.form['repo_group_name'].render(css_class='medium', oid='group_name')|n}
                        ${c.form.render_error(request, c.form['repo_group_name'])|n}
                    </div>
                </div>

                <div class="field">
                    <div class="label">
                        <label for="repo_group">${_('Repository group')}:</label>
                    </div>
                    <div class="select">
                        ${c.form['repo_group'].render(css_class='medium', oid='repo_group')|n}
                        ${c.form.render_error(request, c.form['repo_group'])|n}

                        <p class="help-block">${_('Optional select a parent group to move this repository group into.')}</p>
                    </div>
                </div>

                <div class="field badged-field">
                    <div class="label">
                        <label for="repo_group_owner">${_('Owner')}:</label>
                    </div>
                    <div class="input">
                        <div class="badge-input-container">
                            <div class="user-badge">
                                ${base.gravatar_with_user(c.repo_group.user.email, show_disabled=not c.repo_group.user.active)}
                            </div>
                            <div class="badge-input-wrap">
                                ${c.form['repo_group_owner'].render(css_class='medium', oid='repo_group_owner')|n}
                            </div>
                        </div>
                        ${c.form.render_error(request, c.form['repo_group_owner'])|n}
                        <p class="help-block">${_('Change owner of this repository group.')}</p>
                    </div>
                </div>

                <div class="field">
                    <div class="label label-textarea">
                        <label for="repo_group_description">${_('Description')}:</label>
                    </div>
                    <div class="textarea text-area editor">
                        ${c.form['repo_group_description'].render(css_class='medium', oid='repo_group_description')|n}
                        ${c.form.render_error(request, c.form['repo_group_description'])|n}

                        <% metatags_url = h.literal('''<a href="#metatagsShow" onclick="$('#meta-tags-desc').toggle();return false">meta-tags</a>''') %>
                        <span class="help-block">
                            % if c.visual.stylify_metatags:
                                ${_('Plain text format with {metatags} support.').format(metatags=metatags_url)|n}
                            % else:
                                ${_('Plain text format.')}
                            % endif
                        </span>
                        <span id="meta-tags-desc" style="display: none">
                            <%namespace name="dt" file="/data_table/_dt_elements.mako"/>
                            ${dt.metatags_help()}
                        </span>
                    </div>
                </div>

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
    $(document).ready(function(){
        UsersAutoComplete('repo_group_owner', '${c.rhodecode_user.user_id}');
    })
</script>
