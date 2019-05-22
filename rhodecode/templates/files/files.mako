<%inherit file="/base/base.mako"/>

<%def name="title(*args)">
    ${_('{} Files').format(c.repo_name)}
    %if hasattr(c,'file'):
        &middot; ${(h.safe_unicode(c.file.path) or '\\')}
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
    <div>
        <div id="files_data">
            <%include file='files_pjax.mako'/>
        </div>
    </div>
    <script>

        var metadataRequest = null;
        var fileSourcePage = ${c.file_source_page};
        var atRef = '${request.GET.get('at', '')}';

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

            var url_params = {
                repo_name: templateContext.repo_name,
                commit_id: rev,
                f_path:'__FPATH__'
            };
            if (atRef !== '') {
                url_params['at'] = atRef
            }

            var _url_base = pyroutes.url('repo_files', url_params);
            var _node_list_url = pyroutes.url('repo_files_nodelist',
                    {repo_name: templateContext.repo_name,
                     commit_id: rev, f_path: f_path});

            return {
                url: url,
                f_path: f_path,
                rev: rev,
                commit_id: "${c.commit.raw_id}",
                node_list_url: _node_list_url,
                url_base: _url_base
            };
        };

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
            timeagoActivate();

            if ($('#trimmed_message_box').height() < 50) {
                $('#message_expand').hide();
            }

            $('#message_expand').on('click', function(e) {
                $('#trimmed_message_box').css('max-height', 'none');
                $(this).hide();
            });

            var state = getState('callbacks');

            // VIEW FOR FILE SOURCE
            if (fileSourcePage) {
                // variants for with source code, not tree view

                // select code link event
                $("#hlcode").mouseup(getSelectionLink);

                // file history select2 used for history, and switch to
                var initialCommitData = {
                    id: null,
                    text: '${_("Pick Commit")}',
                    type: 'sha',
                    raw_id: null,
                    files_url: null
                };

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
                        data: 'annotate=${("1" if c.annotate else "0")}',
                        container: '#file_authors',
                        push: false,
                        timeout: 5000
                    }).complete(function(){
                        $('#show_authors').hide();
                        $('#file_authors_title').html(_gettext('All Authors'))
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
                        timeout: 5000
                    })
                });

            }
            // VIEW FOR FILE TREE BROWSER
            else {
                getFilesMetadata();

                // fuzzy file filter
                fileBrowserListeners(state.node_list_url, state.url_base);

                // switch to widget
                var initialCommitData = {
                    at_ref: atRef,
                    id: null,
                    text: '${c.commit.raw_id}',
                    type: 'sha',
                    raw_id: '${c.commit.raw_id}',
                    idx: ${c.commit.idx},
                    files_url: null,
                };

                // check if we have ref info.
                var selectedRef =  fileTreeRefs[atRef];
                if (selectedRef !== undefined) {
                    $.extend(initialCommitData, selectedRef)
                }

                var loadUrl = pyroutes.url('repo_refs_data', {'repo_name': templateContext.repo_name});
                var cacheKey = '__ALL_FILE_REFS__';
                var cachedDataSource = {};

                var loadRefsData = function (query) {
                    $.ajax({
                        url: loadUrl,
                        data: {},
                        dataType: 'json',
                        type: 'GET',
                        success: function (data) {
                            cachedDataSource[cacheKey] = data;
                            query.callback({results: data.results});
                        }
                    });
                };

                var feedRefsData = function (query, cachedData) {
                    var data = {results: []};
                    //filter results
                    $.each(cachedData.results, function () {
                        var section = this.text;
                        var children = [];
                        $.each(this.children, function () {
                            if (query.term.length === 0 || this.text.toUpperCase().indexOf(query.term.toUpperCase()) >= 0) {
                                children.push(this)
                            }
                        });
                        data.results.push({
                            'text': section,
                            'children': children
                        })
                    });

                    //push the typed in commit idx
                    if (!isNaN(query.term)) {
                        var files_url = pyroutes.url('repo_files',
                                    {'repo_name': templateContext.repo_name,
                                     'commit_id': query.term, 'f_path': state.f_path});

                        data.results.push({
                            'text': _gettext('go to numeric commit'),
                            'children': [{
                                at_ref: null,
                                id: null,
                                text: 'r{0}'.format(query.term),
                                type: 'sha',
                                raw_id: query.term,
                                idx: query.term,
                                files_url: files_url,
                            }]
                        });
                    }
                    query.callback(data);
                };

                var select2RefFileSwitcher = function (targetElement, loadUrl, initialData) {
                    var formatResult = function (result, container, query) {
                        return formatSelect2SelectionRefs(result);
                    };

                    var formatSelection = function (data, container) {
                        var commit_ref = data;

                        var tmpl = '';
                        if (commit_ref.type === 'sha') {
                            tmpl = commit_ref.raw_id.substr(0,8);
                        } else if (commit_ref.type === 'branch') {
                            tmpl = tmpl.concat('<i class="icon-branch"></i> ');
                            tmpl = tmpl.concat(escapeHtml(commit_ref.text));
                        } else if (commit_ref.type === 'tag') {
                            tmpl = tmpl.concat('<i class="icon-tag"></i> ');
                            tmpl = tmpl.concat(escapeHtml(commit_ref.text));
                        } else if (commit_ref.type === 'book') {
                            tmpl = tmpl.concat('<i class="icon-bookmark"></i> ');
                            tmpl = tmpl.concat(escapeHtml(commit_ref.text));
                        }

                        tmpl = tmpl.concat('<span class="select-index-number">r{0}</span>'.format(commit_ref.idx));
                        return tmpl
                    };

                  $(targetElement).select2({
                    dropdownAutoWidth: true,
                    width: "resolve",
                    containerCssClass: "drop-menu",
                    dropdownCssClass: "drop-menu-dropdown",
                    query: function(query) {

                      var cachedData = cachedDataSource[cacheKey];
                      if (cachedData) {
                        feedRefsData(query, cachedData)
                      } else {
                        loadRefsData(query)
                      }
                    },
                    initSelection: function(element, callback) {
                      callback(initialData);
                    },
                    formatResult: formatResult,
                    formatSelection: formatSelection
                  });

                };

                select2RefFileSwitcher('#refs_filter', loadUrl, initialCommitData);

                $('#refs_filter').on('change', function(e) {
                    var data = $('#refs_filter').select2('data');
                    window.location = data.files_url
                });

            }
        };

        $(document).ready(function() {
            callbacks();
            var search_GET = "${request.GET.get('search','')}";
            if (search_GET === "1") {
                NodeFilter.initFilter();
                NodeFilter.focus();
            }
        });

    </script>

</%def>