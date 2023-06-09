## snippet for displaying vcs settings
## usage:
##    <%namespace name="vcss" file="/base/vcssettings.mako"/>
##    ${vcss.vcs_settings_fields()}

<%def name="vcs_settings_fields(suffix='', svn_branch_patterns=None, svn_tag_patterns=None, repo_type=None, display_globals=False, allow_repo_location_change=False, **kwargs)">
    % if display_globals:
        <div class="panel panel-default">
            <div class="panel-heading" id="general">
                <h3 class="panel-title">${_('General')}<a class="permalink" href="#general"> ¶</a></h3>
            </div>
            <div class="panel-body">
                <div class="field">
                    <div class="checkbox">
                        ${h.checkbox('web_push_ssl' + suffix, 'True')}
                        <label for="web_push_ssl${suffix}">${_('Require SSL for vcs operations')}</label>
                    </div>
                    <div class="label">
                        <span class="help-block">${_('Activate to set RhodeCode to require SSL for pushing or pulling. If SSL certificate is missing it will return a HTTP Error 406: Not Acceptable.')}</span>
                    </div>
                 </div>
            </div>
        </div>
    % endif

    % if display_globals:
        <div class="panel panel-default">
            <div class="panel-heading" id="vcs-storage-options">
                <h3 class="panel-title">${_('Main Storage Location')}<a class="permalink" href="#vcs-storage-options"> ¶</a></h3>
            </div>
            <div class="panel-body">
                <div class="field">
                    <div class="inputx locked_input">
                        %if allow_repo_location_change:
                            ${h.text('paths_root_path',size=59,readonly="readonly", class_="disabled")}
                            <span id="path_unlock" class="tooltip"
                                    title="${h.tooltip(_('Click to unlock. You must restart RhodeCode in order to make this setting take effect.'))}">
                                <div class="btn btn-default lock_input_button"><i id="path_unlock_icon" class="icon-lock"></i></div>
                            </span>
                        %else:
                            ${_('Repository location change is disabled. You can enable this by changing the `allow_repo_location_change` inside .ini file.')}
                            ## form still requires this but we cannot internally change it anyway
                            ${h.hidden('paths_root_path',size=30,readonly="readonly", class_="disabled")}
                        %endif
                    </div>
                </div>
                <div class="label">
                    <span class="help-block">${_('Filesystem location where repositories should be stored. After changing this value a restart and rescan of the repository folder are required.')}</span>
                </div>
            </div>
        </div>
    % endif

    % if display_globals or repo_type in ['git', 'hg']:
        <div class="panel panel-default">
            <div class="panel-heading" id="vcs-hooks-options">
                <h3 class="panel-title">${_('Internal Hooks')}<a class="permalink" href="#vcs-hooks-options"> ¶</a></h3>
            </div>
            <div class="panel-body">
                <div class="field">
                    <div class="checkbox">
                        ${h.checkbox('hooks_changegroup_repo_size' + suffix, 'True', **kwargs)}
                        <label for="hooks_changegroup_repo_size${suffix}">${_('Show repository size after push')}</label>
                    </div>

                    <div class="label">
                        <span class="help-block">${_('Trigger a hook that calculates repository size after each push.')}</span>
                    </div>
                    <div class="checkbox">
                        ${h.checkbox('hooks_changegroup_push_logger' + suffix, 'True', **kwargs)}
                        <label for="hooks_changegroup_push_logger${suffix}">${_('Execute pre/post push hooks')}</label>
                    </div>
                    <div class="label">
                        <span class="help-block">${_('Execute Built in pre/post push hooks. This also executes rcextensions hooks.')}</span>
                    </div>
                    <div class="checkbox">
                        ${h.checkbox('hooks_outgoing_pull_logger' + suffix, 'True', **kwargs)}
                        <label for="hooks_outgoing_pull_logger${suffix}">${_('Execute pre/post pull hooks')}</label>
                    </div>
                    <div class="label">
                        <span class="help-block">${_('Execute Built in pre/post pull hooks. This also executes rcextensions hooks.')}</span>
                    </div>
                </div>
            </div>
        </div>
    % endif

    % if display_globals or repo_type in ['hg']:
        <div class="panel panel-default">
            <div class="panel-heading" id="vcs-hg-options">
                <h3 class="panel-title">${_('Mercurial Settings')}<a class="permalink" href="#vcs-hg-options"> ¶</a></h3>
            </div>
            <div class="panel-body">
                <div class="checkbox">
                    ${h.checkbox('extensions_largefiles' + suffix, 'True', **kwargs)}
                    <label for="extensions_largefiles${suffix}">${_('Enable largefiles extension')}</label>
                </div>
                <div class="label">
                    % if display_globals:
                        <span class="help-block">${_('Enable Largefiles extensions for all repositories.')}</span>
                    % else:
                        <span class="help-block">${_('Enable Largefiles extensions for this repository.')}</span>
                    % endif
                </div>

                % if display_globals:
                <div class="field">
                    <div class="input">
                        ${h.text('largefiles_usercache' + suffix, size=59)}
                    </div>
                </div>
                <div class="label">
                    <span class="help-block">${_('Filesystem location where Mercurial largefile objects should be stored.')}</span>
                </div>
                % endif

                <div class="checkbox">
                    ${h.checkbox('phases_publish' + suffix, 'True', **kwargs)}
                    <label for="phases_publish${suffix}">${_('Set repositories as publishing') if display_globals else _('Set repository as publishing')}</label>
                </div>
                <div class="label">
                    <span class="help-block">${_('When this is enabled all commits in the repository are seen as public commits by clients.')}</span>
                </div>
                % if display_globals:
                    <div class="checkbox">
                        ${h.checkbox('extensions_hgsubversion' + suffix,'True')}
                        <label for="extensions_hgsubversion${suffix}">${_('Enable hgsubversion extension')}</label>
                    </div>
                    <div class="label">
                        <span class="help-block">${_('Requires hgsubversion library to be installed. Allows cloning remote SVN repositories and migrates them to Mercurial type.')}</span>
                    </div>
                % endif

                <div class="checkbox">
                    ${h.checkbox('extensions_evolve' + suffix, 'True', **kwargs)}
                    <label for="extensions_evolve${suffix}">${_('Enable Evolve and Topic extension')}</label>
                </div>
                <div class="label">
                    % if display_globals:
                        <span class="help-block">${_('Enable Evolve and Topic extensions for all repositories.')}</span>
                    % else:
                        <span class="help-block">${_('Enable Evolve and Topic extensions for this repository.')}</span>
                    % endif
                </div>

            </div>
        </div>
    % endif

    % if display_globals or repo_type in ['git']:
        <div class="panel panel-default">
            <div class="panel-heading" id="vcs-git-options">
                <h3 class="panel-title">${_('Git Settings')}<a class="permalink" href="#vcs-git-options"> ¶</a></h3>
            </div>
            <div class="panel-body">
                <div class="checkbox">
                    ${h.checkbox('vcs_git_lfs_enabled' + suffix, 'True', **kwargs)}
                    <label for="vcs_git_lfs_enabled${suffix}">${_('Enable lfs extension')}</label>
                </div>
                <div class="label">
                    % if display_globals:
                        <span class="help-block">${_('Enable lfs extensions for all repositories.')}</span>
                    % else:
                        <span class="help-block">${_('Enable lfs extensions for this repository.')}</span>
                    % endif
                </div>

                % if display_globals:
                <div class="field">
                    <div class="input">
                        ${h.text('vcs_git_lfs_store_location' + suffix, size=59)}
                    </div>
                </div>
                <div class="label">
                    <span class="help-block">${_('Filesystem location where Git lfs objects should be stored.')}</span>
                </div>
                % endif
            </div>
        </div>
    % endif


    % if display_globals:
        <div class="panel panel-default">
            <div class="panel-heading" id="vcs-global-svn-options">
                <h3 class="panel-title">${_('Global Subversion Settings')}<a class="permalink" href="#vcs-global-svn-options"> ¶</a></h3>
            </div>
            <div class="panel-body">
                <div class="field">
                    <div class="checkbox">
                        ${h.checkbox('vcs_svn_proxy_http_requests_enabled' + suffix, 'True', **kwargs)}
                        <label for="vcs_svn_proxy_http_requests_enabled${suffix}">${_('Proxy subversion HTTP requests')}</label>
                    </div>
                    <div class="label">
                        <span class="help-block">
                            ${_('Subversion HTTP Support. Enables communication with SVN over HTTP protocol.')}
                            <a href="${h.route_url('enterprise_svn_setup')}" target="_blank">${_('SVN Protocol setup Documentation')}</a>.
                        </span>
                    </div>
                </div>
                <div class="field">
                    <div class="label">
                        <label for="vcs_svn_proxy_http_server_url">${_('Subversion HTTP Server URL')}</label><br/>
                    </div>
                    <div class="input">
                        ${h.text('vcs_svn_proxy_http_server_url',size=59)}
                        % if c.svn_proxy_generate_config:
                            <span class="buttons">
                                <button class="btn btn-primary" id="vcs_svn_generate_cfg">${_('Generate Apache Config')}</button>
                            </span>
                        % endif
                    </div>
                </div>
            </div>
        </div>
    % endif

    % if display_globals or repo_type in ['svn']:
        <div class="panel panel-default">
            <div class="panel-heading" id="vcs-svn-options">
                <h3 class="panel-title">${_('Subversion Settings')}<a class="permalink" href="#vcs-svn-options"> ¶</a></h3>
            </div>
            <div class="panel-body">
                <div class="field">
                    <div class="content" >
                        <label>${_('Repository patterns')}</label><br/>
                    </div>
                </div>
                <div class="label">
                    <span class="help-block">${_('Patterns for identifying SVN branches and tags. For recursive search, use "*". Eg.: "/branches/*"')}</span>
                </div>

                <div class="field branch_patterns">
                    <div class="input" >
                        <label>${_('Branches')}:</label><br/>
                    </div>
                    % if svn_branch_patterns:
                        % for branch in svn_branch_patterns:
                        <div class="input adjacent"   id="${'id%s' % branch.ui_id}">
                            ${h.hidden('branch_ui_key' + suffix, branch.ui_key)}
                            ${h.text('branch_value_%d' % branch.ui_id + suffix, branch.ui_value, size=59, readonly="readonly", class_='disabled')}
                            % if kwargs.get('disabled') != 'disabled':
                                <span class="btn btn-x" onclick="ajaxDeletePattern(${branch.ui_id},'${'id%s' % branch.ui_id}')">
                                    ${_('Delete')}
                                </span>
                            % endif
                        </div>
                        % endfor
                    %endif
                </div>
                % if kwargs.get('disabled') != 'disabled':
                    <div class="field branch_patterns">
                        <div class="input" >
                            ${h.text('new_svn_branch',size=59,placeholder='New branch pattern')}
                        </div>
                    </div>
                % endif
                <div class="field tag_patterns">
                    <div class="input" >
                        <label>${_('Tags')}:</label><br/>
                    </div>
                    % if svn_tag_patterns:
                        % for tag in svn_tag_patterns:
                        <div class="input"  id="${'id%s' % tag.ui_id + suffix}">
                            ${h.hidden('tag_ui_key' + suffix, tag.ui_key)}
                            ${h.text('tag_ui_value_new_%d' % tag.ui_id + suffix, tag.ui_value, size=59, readonly="readonly", class_='disabled tag_input')}
                            % if kwargs.get('disabled') != 'disabled':
                                <span class="btn btn-x" onclick="ajaxDeletePattern(${tag.ui_id},'${'id%s' % tag.ui_id}')">
                                    ${_('Delete')}
                                </span>
                            %endif
                        </div>
                        % endfor
                    % endif
                </div>
                % if kwargs.get('disabled') != 'disabled':
                    <div class="field tag_patterns">
                        <div class="input" >
                            ${h.text('new_svn_tag' + suffix, size=59, placeholder='New tag pattern')}
                        </div>
                    </div>
                %endif
            </div>
        </div>
    % else:
        ${h.hidden('new_svn_branch' + suffix, '')}
        ${h.hidden('new_svn_tag' + suffix, '')}
    % endif


    % if display_globals or repo_type in ['hg', 'git']:
        <div class="panel panel-default">
            <div class="panel-heading" id="vcs-pull-requests-options">
                <h3 class="panel-title">${_('Pull Request Settings')}<a class="permalink" href="#vcs-pull-requests-options"> ¶</a></h3>
            </div>
            <div class="panel-body">
                <div class="checkbox">
                    ${h.checkbox('rhodecode_pr_merge_enabled' + suffix, 'True', **kwargs)}
                    <label for="rhodecode_pr_merge_enabled${suffix}">${_('Enable server-side merge for pull requests')}</label>
                </div>
                <div class="label">
                    <span class="help-block">${_('Note: when this feature is enabled, it only runs hooks defined in the rcextension package. Custom hooks added on the Admin -> Settings -> Hooks page will not be run when pull requests are automatically merged from the web interface.')}</span>
                </div>
                <div class="checkbox">
                    ${h.checkbox('rhodecode_use_outdated_comments' + suffix, 'True', **kwargs)}
                    <label for="rhodecode_use_outdated_comments${suffix}">${_('Invalidate and relocate inline comments during update')}</label>
                </div>
                <div class="label">
                    <span class="help-block">${_('During the update of a pull request, the position of inline comments will be updated and outdated inline comments will be hidden.')}</span>
                </div>
            </div>
        </div>
    % endif

    % if display_globals or repo_type in ['hg', 'git', 'svn']:
        <div class="panel panel-default">
            <div class="panel-heading" id="vcs-pull-requests-options">
                <h3 class="panel-title">${_('Diff cache')}<a class="permalink" href="#vcs-pull-requests-options"> ¶</a></h3>
            </div>
            <div class="panel-body">
                <div class="checkbox">
                    ${h.checkbox('rhodecode_diff_cache' + suffix, 'True', **kwargs)}
                    <label for="rhodecode_diff_cache${suffix}">${_('Enable caching diffs for pull requests cache and commits')}</label>
                </div>
            </div>
        </div>
    % endif

    % if display_globals or repo_type in ['hg',]:
        <div class="panel panel-default">
            <div class="panel-heading" id="vcs-pull-requests-options">
                <h3 class="panel-title">${_('Mercurial Pull Request Settings')}<a class="permalink" href="#vcs-hg-pull-requests-options"> ¶</a></h3>
            </div>
            <div class="panel-body">
                ## Specific HG settings
                <div class="checkbox">
                    ${h.checkbox('rhodecode_hg_use_rebase_for_merging' + suffix, 'True', **kwargs)}
                    <label for="rhodecode_hg_use_rebase_for_merging${suffix}">${_('Use rebase as merge strategy')}</label>
                </div>
                <div class="label">
                    <span class="help-block">${_('Use rebase instead of creating a merge commit when merging via web interface.')}</span>
                </div>

                <div class="checkbox">
                    ${h.checkbox('rhodecode_hg_close_branch_before_merging' + suffix, 'True', **kwargs)}
                    <label for="rhodecode_hg_close_branch_before_merging{suffix}">${_('Close branch before merging it')}</label>
                </div>
                <div class="label">
                    <span class="help-block">${_('Close branch before merging it into destination branch. No effect when rebase strategy is use.')}</span>
                </div>


            </div>
        </div>
    % endif

## DISABLED FOR GIT FOR NOW as the rebase/close is not supported yet
##     % if display_globals or repo_type in ['git']:
##         <div class="panel panel-default">
##             <div class="panel-heading" id="vcs-pull-requests-options">
##                 <h3 class="panel-title">${_('Git Pull Request Settings')}<a class="permalink" href="#vcs-git-pull-requests-options"> ¶</a></h3>
##             </div>
##             <div class="panel-body">
##                 <div class="checkbox">
##                     ${h.checkbox('rhodecode_git_use_rebase_for_merging' + suffix, 'True', **kwargs)}
##                     <label for="rhodecode_git_use_rebase_for_merging${suffix}">${_('Use rebase as merge strategy')}</label>
##                 </div>
##                 <div class="label">
##                     <span class="help-block">${_('Use rebase instead of creating a merge commit when merging via web interface.')}</span>
##                 </div>
##
##                 <div class="checkbox">
##                     ${h.checkbox('rhodecode_git_close_branch_before_merging' + suffix, 'True', **kwargs)}
##                     <label for="rhodecode_git_close_branch_before_merging{suffix}">${_('Delete branch after merging it')}</label>
##                 </div>
##                 <div class="label">
##                     <span class="help-block">${_('Delete branch after merging it into destination branch. No effect when rebase strategy is use.')}</span>
##                 </div>
##             </div>
##         </div>
##     % endif


</%def>
