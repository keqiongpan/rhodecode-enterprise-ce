${h.secure_form(h.route_path('admin_settings_visual_update'), request=request)}

<div class="panel panel-default">
    <div class="panel-heading" id="general">
        <h3 class="panel-title">${_('General')}</h3>
    </div>
    <div class="panel-body">
        <div class="checkbox">
            ${h.checkbox('rhodecode_repository_fields','True')}
            <label for="rhodecode_repository_fields">${_('Use repository extra fields')}</label>
        </div>
        <span class="help-block">${_('Allows storing additional customized fields per repository.')}</span>

        <div></div>
        <div class="checkbox">
            ${h.checkbox('rhodecode_show_version','True')}
            <label for="rhodecode_show_version">${_('Show RhodeCode version')}</label>
        </div>
        <span class="help-block">${_('Shows or hides a version number of RhodeCode displayed in the footer.')}</span>
    </div>
</div>


<div class="panel panel-default">
    <div class="panel-heading" id="gravatars">
        <h3 class="panel-title">${_('Gravatars')}</h3>
    </div>
    <div class="panel-body">
        <div class="checkbox">
            ${h.checkbox('rhodecode_use_gravatar','True')}
            <label for="rhodecode_use_gravatar">${_('Use Gravatars based avatars')}</label>
        </div>
        <span class="help-block">${_('Use gravatar.com as avatar system for RhodeCode accounts. If this is disabled avatars are generated based on initials and email.')}</span>

        <div class="label">
            <label for="rhodecode_gravatar_url">${_('Gravatar URL')}</label>
        </div>
        <div class="input">
            <div class="field">
                ${h.text('rhodecode_gravatar_url', size='100%')}
            </div>

            <div class="field">
            <span class="help-block">${_('''Gravatar url allows you to use other avatar server application.
                                            Following variables of the URL will be replaced accordingly.
                                            {scheme}    'http' or 'https' sent from running RhodeCode server,
                                            {email}     user email,
                                            {md5email}  md5 hash of the user email (like at gravatar.com),
                                            {size}      size of the image that is expected from the server application,
                                            {netloc}    network location/server host of running RhodeCode server''')}</span>
            </div>
        </div>
    </div>
</div>


<div class="panel panel-default">
    <div class="panel-heading" id="meta-tagging">
        <h3 class="panel-title">${_('Meta-Tagging')}</h3>
    </div>
    <div class="panel-body">
        <div class="checkbox">
            ${h.checkbox('rhodecode_stylify_metatags','True')}
            <label for="rhodecode_stylify_metatags">${_('Stylify recognised meta tags')}</label>
        </div>
        <span class="help-block">${_('Parses meta tags from repository or repository group description fields and turns them into colored tags.')}</span>
        <div>
            <%namespace name="dt" file="/data_table/_dt_elements.mako"/>
            ${dt.metatags_help()}
        </div>
    </div>
</div>


<div class="panel panel-default">
    <div class="panel-heading">
        <h3 class="panel-title">${_('Dashboard Items')}</h3>
    </div>
    <div class="panel-body">
        <div class="label">
            <label for="rhodecode_dashboard_items">${_('Main page dashboard items')}</label>
        </div>
        <div class="field input">
            ${h.text('rhodecode_dashboard_items',size=5)}
        </div>
        <div class="field">
            <span class="help-block">${_('Number of items displayed in the main page dashboard before pagination is shown.')}</span>
        </div>

        <div class="label">
            <label for="rhodecode_admin_grid_items">${_('Admin pages items')}</label>
        </div>
        <div class="field input">
            ${h.text('rhodecode_admin_grid_items',size=5)}
        </div>
        <div class="field">
            <span class="help-block">${_('Number of items displayed in the admin pages grids before pagination is shown.')}</span>
        </div>
    </div>
</div>



<div class="panel panel-default">
    <div class="panel-heading" id="commit-id">
        <h3 class="panel-title">${_('Commit ID Style')}</h3>
    </div>
    <div class="panel-body">
        <div class="label">
            <label for="rhodecode_show_sha_length">${_('Commit sha length')}</label>
        </div>
        <div class="input">
            <div class="field">
                ${h.text('rhodecode_show_sha_length',size=5)}
            </div>
            <div class="field">
                <span class="help-block">${_('''Number of chars to show in commit sha displayed in web interface.
                                                By default it's shown as r123:9043a6a4c226 this value defines the
                                                length of the sha after the `r123:` part.''')}</span>
            </div>
        </div>

        <div class="checkbox">
            ${h.checkbox('rhodecode_show_revision_number','True')}
            <label for="rhodecode_show_revision_number">${_('Show commit ID numeric reference')} / ${_('Commit show revision number')}</label>
        </div>
        <span class="help-block">${_('''Show revision number in commit sha displayed in web interface.
                                        By default it's shown as r123:9043a6a4c226 this value defines the
                                        if the `r123:` part is shown.''')}</span>
    </div>
</div>


<div class="panel panel-default">
    <div class="panel-heading" id="icons">
        <h3 class="panel-title">${_('Icons')}</h3>
    </div>
    <div class="panel-body">
        <div class="checkbox">
            ${h.checkbox('rhodecode_show_public_icon','True')}
            <label for="rhodecode_show_public_icon">${_('Show public repo icon on repositories')}</label>
        </div>
        <div></div>

        <div class="checkbox">
            ${h.checkbox('rhodecode_show_private_icon','True')}
            <label for="rhodecode_show_private_icon">${_('Show private repo icon on repositories')}</label>
        </div>
        <span class="help-block">${_('Show public/private icons next to repositories names.')}</span>
    </div>
</div>


<div class="panel panel-default">
    <div class="panel-heading">
        <h3 class="panel-title">${_('Markup Renderer')}</h3>
    </div>
    <div class="panel-body">
        <div class="field select">
            ${h.select('rhodecode_markup_renderer', '', ['rst', 'markdown'])}
        </div>
        <div class="field">
            <span class="help-block">${_('Default renderer used to render comments, pull request descriptions and other description elements. After change old entries will still work correctly.')}</span>
        </div>
    </div>
</div>

<div class="panel panel-default">
    <div class="panel-heading">
        <h3 class="panel-title">${_('Clone URL')}</h3>
    </div>
    <div class="panel-body">
        <div class="field">
            ${h.text('rhodecode_clone_uri_tmpl', size=60)}
        </div>

        <div class="field">
            <span class="help-block">
                ${_('''Schema of clone url construction eg. '{scheme}://{user}@{netloc}/{repo}', available vars:
                       {scheme} 'http' or 'https' sent from running RhodeCode server,
                       {user}   current user username,
                       {netloc} network location/server host of running RhodeCode server,
                       {repo}   full repository name,
                       {repoid} ID of repository, can be used to contruct clone-by-id''')}
            </span>
        </div>
    </div>
</div>

<div class="panel panel-default">
    <div class="panel-heading">
        <h3 class="panel-title">${_('Custom Support Link')}</h3>
    </div>
    <div class="panel-body">
        <div class="field">
            ${h.text('rhodecode_support_url', size=60)}
        </div>
        <div class="field">
            <span class="help-block">
                ${_('''Custom url for the support link located at the bottom.
                    The default is set to %(default_url)s. In case there's a need
                    to change the support link to internal issue tracker, it should be done here.
                    ''') % {'default_url': h.route_url('rhodecode_support')}}
            </span>
        </div>
    </div>
</div>

<div class="buttons">
    ${h.submit('save',_('Save settings'),class_="btn")}
    ${h.reset('reset',_('Reset'),class_="btn")}
</div>


${h.end_form()}

<script>
$(document).ready(function() {
    $('#rhodecode_markup_renderer').select2({
        containerCssClass: 'drop-menu',
        dropdownCssClass: 'drop-menu-dropdown',
        dropdownAutoWidth: true,
        minimumResultsForSearch: -1
    });
});
</script>
