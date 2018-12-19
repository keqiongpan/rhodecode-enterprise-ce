<%inherit file="/base/base.mako"/>

<%def name="title(*args)">
    ${_('%s Files') % c.repo_name}
    %if hasattr(c,'file'):
        &middot; ${h.safe_unicode(c.file.path) or '\\'}
    %endif

    %if c.rhodecode_name:
        &middot; ${h.branding(c.rhodecode_name)}
    %endif
</%def>

<%def name="breadcrumbs_links()">
    ${_('Files')}
    %if c.file:
        @ ${h.show_id(c.commit)}
    %endif
</%def>

<%def name="menu_bar_nav()">
    ${self.menu_items(active='repositories')}
</%def>

<%def name="menu_bar_subnav()">
    ${self.repo_menu(active='files')}
</%def>

<%def name="main()">
    <div class="title">
        ${self.repo_page_title(c.rhodecode_db_repo)}
    </div>

    <div id="pjax-container" class="summary">
        <div id="files_data">
            <%include file='files_pjax.mako'/>
        </div>
    </div>
    <script>
        var curState = {
            commit_id: "${c.commit.raw_id}"
        };

        var getState = function(context) {
            var url = $(location).attr('href');
            var _base_url = '${h.route_path("repo_files",repo_name=c.repo_name,commit_id='',f_path='')}';
            var _annotate_url = '${h.route_path("repo_files:annotated",repo_name=c.repo_name,commit_id='',f_path='')}';
            _base_url = _base_url.replace('//', '/');
            _annotate_url = _annotate_url.replace('//', '/');

            //extract f_path from url.
            var parts = url.split(_base_url);
            if (parts.length != 2) {
                parts = url.split(_annotate_url);
                if (parts.length != 2) {
                    var rev = "tip";
                    var f_path = "";
                } else {
                    var parts2 = parts[1].split('/');
                    var rev = parts2.shift(); // pop the first element which is the revision
                    var f_path = parts2.join('/');
                }

            } else {
                var parts2 = parts[1].split('/');
                var rev = parts2.shift(); // pop the first element which is the revision
                var f_path = parts2.join('/');
            }

            var _node_list_url = pyroutes.url('repo_files_nodelist',
                    {repo_name: templateContext.repo_name,
                     commit_id: rev, f_path: f_path});
            var _url_base = pyroutes.url('repo_files',
                    {repo_name: templateContext.repo_name,
                     commit_id: rev, f_path:'__FPATH__'});
            return {
                url: url,
                f_path: f_path,
                rev: rev,
                commit_id: curState.commit_id,
                node_list_url: _node_list_url,
                url_base: _url_base
            };
        };

        var metadataRequest = null;
        var getFilesMetadata = function() {
            if (metadataRequest && metadataRequest.readyState != 4) {
                metadataRequest.abort();
            }
            if (fileSourcePage) {
                return false;
            }

            if ($('#file-tree-wrapper').hasClass('full-load')) {
                // in case our HTML wrapper has full-load class we don't
                // trigger the async load of metadata
                return false;
            }

            var state = getState('metadata');
            var url_data = {
                'repo_name': templateContext.repo_name,
                'commit_id': state.commit_id,
                'f_path': state.f_path
            };

            var url = pyroutes.url('repo_nodetree_full', url_data);

            metadataRequest = $.ajax({url: url});

            metadataRequest.done(function(data) {
                $('#file-tree').html(data);
                timeagoActivate();
            });
            metadataRequest.fail(function (data, textStatus, errorThrown) {
                console.log(data);
                if (data.status != 0) {
                    alert("Error while fetching metadata.\nError code {0} ({1}).Please consider reloading the page".format(data.status,data.statusText));
                }
            });
        };

        var callbacks = function() {
            var state = getState('callbacks');
            timeagoActivate();

            // used for history, and switch to
            var initialCommitData = {
                id: null,
                text: '${_("Pick Commit")}',
                type: 'sha',
                raw_id: null,
                files_url: null
            };

            if ($('#trimmed_message_box').height() < 50) {
                $('#message_expand').hide();
            }

            $('#message_expand').on('click', function(e) {
                $('#trimmed_message_box').css('max-height', 'none');
                $(this).hide();
            });

            if (fileSourcePage) {
                // variants for with source code, not tree view

                // select code link event
                $("#hlcode").mouseup(getSelectionLink);

                // file history select2
                select2FileHistorySwitcher('#diff1', initialCommitData, state);

                // show at, diff to actions handlers
                $('#diff1').on('change', function(e) {
                    $('#diff_to_commit').removeClass('disabled').removeAttr("disabled");
                    $('#diff_to_commit').val(_gettext('Diff to Commit ') + e.val.truncateAfter(8, '...'));

                    $('#show_at_commit').removeClass('disabled').removeAttr("disabled");
                    $('#show_at_commit').val(_gettext('Show at Commit ') + e.val.truncateAfter(8, '...'));
                });

                $('#diff_to_commit').on('click', function(e) {
                    var diff1 = $('#diff1').val();
                    var diff2 = $('#diff2').val();

                    var url_data = {
                        repo_name: templateContext.repo_name,
                        source_ref: diff1,
                        source_ref_type: 'rev',
                        target_ref: diff2,
                        target_ref_type: 'rev',
                        merge: 1,
                        f_path: state.f_path
                    };
                    window.location = pyroutes.url('repo_compare', url_data);
                });

                $('#show_at_commit').on('click', function(e) {
                    var diff1 = $('#diff1').val();

                    var annotate = $('#annotate').val();
                    if (annotate === "True") {
                        var url = pyroutes.url('repo_files:annotated',
                                {'repo_name': templateContext.repo_name,
                                 'commit_id': diff1, 'f_path': state.f_path});
                    } else {
                        var url = pyroutes.url('repo_files',
                                {'repo_name': templateContext.repo_name,
                                 'commit_id': diff1, 'f_path': state.f_path});
                    }
                    window.location = url;

                });

                // show more authors
                $('#show_authors').on('click', function(e) {
                    e.preventDefault();
                    var url = pyroutes.url('repo_file_authors',
                                {'repo_name': templateContext.repo_name,
                                 'commit_id': state.rev, 'f_path': state.f_path});

                    $.pjax({
                        url: url,
                        data: 'annotate=${"1" if c.annotate else "0"}',
                        container: '#file_authors',
                        push: false,
                        timeout: pjaxTimeout
                    }).complete(function(){
                        $('#show_authors').hide();
                    })
                });

                // load file short history
                $('#file_history_overview').on('click', function(e) {
                    e.preventDefault();
                    path = state.f_path;
                    if (path.indexOf("#") >= 0) {
                        path = path.slice(0, path.indexOf("#"));
                    }
                    var url = pyroutes.url('repo_changelog_file',
                            {'repo_name': templateContext.repo_name,
                             'commit_id': state.rev, 'f_path': path, 'limit': 6});
                    $('#file_history_container').show();
                    $('#file_history_container').html('<div class="file-history-inner">{0}</div>'.format(_gettext('Loading ...')));

                    $.pjax({
                        url: url,
                        container: '#file_history_container',
                        push: false,
                        timeout: pjaxTimeout
                    })
                });

            }
            else {
                getFilesMetadata();

                // fuzzy file filter
                fileBrowserListeners(state.node_list_url, state.url_base);

                // switch to widget
                select2RefSwitcher('#refs_filter', initialCommitData);
                $('#refs_filter').on('change', function(e) {
                    var data = $('#refs_filter').select2('data');
                    curState.commit_id = data.raw_id;
                    $.pjax({url: data.files_url, container: '#pjax-container', timeout: pjaxTimeout});
                });

                $("#prev_commit_link").on('click', function(e) {
                    var data = $(this).data();
                    curState.commit_id = data.commitId;
                });

                $("#next_commit_link").on('click', function(e) {
                    var data = $(this).data();
                    curState.commit_id = data.commitId;
                });

                $('#at_rev').on("keypress", function(e) {
                    /* ENTER PRESSED */
                    if (e.keyCode === 13) {
                        var rev = $('#at_rev').val();
                        // explicit reload page here. with pjax entering bad input
                        // produces not so nice results
                        window.location = pyroutes.url('repo_files',
                                {'repo_name': templateContext.repo_name,
                                 'commit_id': rev, 'f_path': state.f_path});
                    }
                });
            }
        };

        var pjaxTimeout = 5000;

        $(document).pjax(".pjax-link", "#pjax-container", {
            "fragment": "#pjax-content",
            "maxCacheLength": 1000,
            "timeout": pjaxTimeout
        });

        // define global back/forward states
        var isPjaxPopState = false;
        $(document).on('pjax:popstate', function() {
            isPjaxPopState = true;
        });

        $(document).on('pjax:end', function(xhr, options) {
            if (isPjaxPopState) {
                isPjaxPopState = false;
                callbacks();
                _NODEFILTER.resetFilter();
            }

            // run callback for tracking if defined for google analytics etc.
            // this is used to trigger tracking on pjax
            if (typeof window.rhodecode_statechange_callback !== 'undefined') {
                var state = getState('statechange');
                rhodecode_statechange_callback(state.url, null)
            }
        });

        $(document).on('pjax:success', function(event, xhr, options) {
            if (event.target.id == "file_history_container") {
                $('#file_history_overview').hide();
                $('#file_history_overview_full').show();
                timeagoActivate();
            } else {
                callbacks();
            }
        });

        $(document).ready(function() {
            callbacks();
            var search_GET = "${request.GET.get('search','')}";
            if (search_GET === "1") {
                _NODEFILTER.initFilter();
            }
        });

    </script>

</%def>
