## -*- coding: utf-8 -*-
<%namespace name="base" file="/base/base.mako"/>

<div class="panel panel-default">
    <div class="panel-heading">
        <h3 class="panel-title">${_('Settings for Repository Group: %s') % c.repo_group.name}</h3>
    </div>
    <div class="panel-body">
        ${h.secure_form(h.route_path('edit_repo_group', repo_group_name=c.repo_group.group_name), request=request)}
        <div class="form">
            <!-- fields -->
            <div class="fields">
                <div class="field">
                    <div class="label">
                        <label for="group_name">${_('Group Name')}:</label>
                    </div>
                    <div class="input">
                        ${c.form['repo_group_name'].render(css_class='medium', oid='group_name')|n}
                        ${c.form.render_error(request, c.form['repo_group_name'])|n}
                    </div>
                </div>

                <div class="field">
                    <div class="label">
                        <label for="repo_group">${_('Group parent')}:</label>
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
                        <span class="help-block">${_('Plain text format with support of {metatags}').format(metatags=metatags_url)|n}</span>
                        <span id="meta-tags-desc" style="display: none">
                            <%namespace name="dt" file="/data_table/_dt_elements.mako"/>
                            ${dt.metatags_help()}
                        </span>
                    </div>
                </div>

                <div class="field">
                    <div class="label label-checkbox">
                        <label for="repo_group_enable_locking">${_('Enable Repository Locking')}:</label>
                    </div>
                    <div class="checkboxes">
                        ${c.form['repo_group_enable_locking'].render(css_class='medium', oid='repo_group_enable_locking')|n}
                        ${c.form.render_error(request, c.form['repo_group_enable_locking'])|n}

                        <span class="help-block">${_('Repository locking will be enabled on all subgroups and repositories inside this repository group. Pulling from a repository locks it, and it is unlocked by pushing back by the same user.')}</span>
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
