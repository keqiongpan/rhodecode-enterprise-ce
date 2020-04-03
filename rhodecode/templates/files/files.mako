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
    <script type="text/javascript">
        var fileSourcePage = ${c.file_source_page};
        var atRef = '${request.GET.get('at', '')}';

        // global state for fetching metadata
        metadataRequest = null;

        // global metadata about URL
        filesUrlData = ${h.files_url_data(request)|n};
    </script>

    <div>
        <div>
            <%include file='files_pjax.mako'/>
        </div>
    </div>

    <script type="text/javascript">

        var initFileJS = function () {
            var state = getFileState();

            // select code link event
            $("#hlcode").mouseup(getSelectionLink);

            // file history select2 used for history of file, and switch to
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

            var loadUrl = pyroutes.url('repo_file_history', {'repo_name': templateContext.repo_name, 'commit_id': state.commit_id,'f_path': state.f_path});
            var cacheKey = '__SINGLE_FILE_REFS__';
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

                query.callback(data);
            };

            var select2FileHistorySwitcher = function (targetElement, loadUrl, initialData) {
                var formatResult = function (result, container, query) {
                    return formatSelect2SelectionRefs(result);
                };

                var formatSelection = function (data, container) {
                    var commit_ref = data;

                    var tmpl = '';
                    if (commit_ref.type === 'sha') {
                        tmpl = (commit_ref.raw_id || "").substr(0,8);
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
                    var idx = commit_ref.idx || 0;
                    if (idx !== 0) {
                        tmpl = tmpl.concat('<span class="select-index-number">r{0}</span>'.format(idx));
                    }
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

            select2FileHistorySwitcher('#file_refs_filter', loadUrl, initialCommitData);

            // switcher for files
            $('#file_refs_filter').on('change', function(e) {
                var data = $('#file_refs_filter').select2('data');
                var commit_id = data.id;
                var params = {
                    'repo_name': templateContext.repo_name,
                    'commit_id': commit_id,
                    'f_path': state.f_path
                };

                if(data.at_rev !== undefined && data.at_rev !== "") {
                    params['at'] = data.at_rev;
                }

                if ("${c.annotate}" === "True") {
                    var url = pyroutes.url('repo_files:annotated', params);
                } else {
                    var url = pyroutes.url('repo_files', params);
                }
                window.location = url;

            });

            // load file short history
            $('#file_history_overview').on('click', function(e) {
                e.preventDefault();
                path = state.f_path;
                if (path.indexOf("#") >= 0) {
                    path = path.slice(0, path.indexOf("#"));
                }
                var url = pyroutes.url('repo_commits_file',
                        {'repo_name': templateContext.repo_name,
                         'commit_id': state.commit_id, 'f_path': path, 'limit': 6});
                $('#file_history_container').show();
                $('#file_history_container').html('<div class="file-history-inner">{0}</div>'.format(_gettext('Loading ...')));

                $.pjax({
                    url: url,
                    container: '#file_history_container',
                    push: false,
                    timeout: 5000
                }).complete(function () {
                    tooltipActivate();
                });
            });

        };

        var initTreeJS = function () {
            var state = getFileState();
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
                        tmpl = (commit_ref.raw_id || "").substr(0,8);
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

                    var idx = commit_ref.idx || 0;
                    if (idx !== 0) {
                        tmpl = tmpl.concat('<span class="select-index-number">r{0}</span>'.format(idx));
                    }
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

            // switcher for file tree
            $('#refs_filter').on('change', function(e) {
                var data = $('#refs_filter').select2('data');
                window.location = data.files_url
            });

        };

        $(document).ready(function() {
            timeagoActivate();
            tooltipActivate();

            if ($('#trimmed_message_box').height() < 50) {
                $('#message_expand').hide();
            }

            $('#message_expand').on('click', function(e) {
                $('#trimmed_message_box').css('max-height', 'none');
                $(this).hide();
            });

            if (fileSourcePage) {
                initFileJS()
            } else {
                initTreeJS()
            }

            var search_GET = "${request.GET.get('search','')}";
            if (search_GET === "1") {
                NodeFilter.initFilter();
                NodeFilter.focus();
            }
        });

    </script>

</%def>