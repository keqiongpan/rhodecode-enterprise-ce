<%inherit file="/base/base.mako"/>
<%namespace name="dt" file="/data_table/_dt_elements.mako"/>

<%def name="title()">
    ${c.repo_name} ${_('New pull request')}
</%def>

<%def name="breadcrumbs_links()"></%def>

<%def name="menu_bar_nav()">
    ${self.menu_items(active='repositories')}
</%def>

<%def name="menu_bar_subnav()">
    ${self.repo_menu(active='showpullrequest')}
</%def>

<%def name="main()">
<div class="box">
    ${h.secure_form(h.route_path('pullrequest_create', repo_name=c.repo_name, _query=request.GET.mixed()), id='pull_request_form', request=request)}

        <div class="box">

            <div class="summary-details block-left">

                <div class="form" style="padding-top: 10px">

                    <div class="fields" >

                        ## COMMIT FLOW
                        <div class="field">
                            <div class="label label-textarea">
                                <label for="commit_flow">${_('Commit flow')}:</label>
                            </div>

                            <div class="content">
                                <div class="flex-container">
                                    <div style="width: 45%;">
                                        <div class="panel panel-default source-panel">
                                            <div class="panel-heading">
                                                <h3 class="panel-title">${_('Source repository')}</h3>
                                            </div>
                                            <div class="panel-body">
                                                <div style="display:none">${c.rhodecode_db_repo.description}</div>
                                                ${h.hidden('source_repo')}
                                                ${h.hidden('source_ref')}

                                                <div id="pr_open_message"></div>
                                            </div>
                                        </div>
                                    </div>

                                    <div style="width: 90px; text-align: center; padding-top: 30px">
                                    <div>
                                        <i class="icon-right" style="font-size: 2.2em"></i>
                                    </div>
                                    <div style="position: relative; top: 10px">
                                    <span class="tag tag">
                                        <span id="switch_base"></span>
                                    </span>
                                    </div>

                                </div>

                                    <div style="width: 45%;">

                                    <div class="panel panel-default target-panel">
                                        <div class="panel-heading">
                                            <h3 class="panel-title">${_('Target repository')}</h3>
                                        </div>
                                        <div class="panel-body">
                                          <div style="display:none" id="target_repo_desc"></div>
                                          ${h.hidden('target_repo')}
                                          ${h.hidden('target_ref')}
                                          <span id="target_ref_loading" style="display: none">
                                              ${_('Loading refs...')}
                                          </span>
                                        </div>
                                    </div>

                                </div>
                                </div>

                            </div>

                        </div>

                        ## TITLE
                        <div class="field">
                            <div class="label">
                                <label for="pullrequest_title">${_('Title')}:</label>
                            </div>
                            <div class="input">
                                ${h.text('pullrequest_title', c.default_title, class_="medium autogenerated-title")}
                            </div>
                            <p class="help-block">
                                Start the title with WIP: to prevent accidental merge of Work In Progress pull request before it's ready.
                            </p>
                        </div>

                        ## DESC
                        <div class="field">
                            <div class="label label-textarea">
                                <label for="pullrequest_desc">${_('Description')}:</label>
                            </div>
                            <div class="textarea text-area">
                                <input id="pr-renderer-input" type="hidden" name="description_renderer" value="${c.visual.default_renderer}">
                                ${dt.markup_form('pullrequest_desc')}
                            </div>
                        </div>

                        ## REVIEWERS
                        <div class="field">
                            <div class="label label-textarea">
                                <label for="pullrequest_reviewers">${_('Reviewers / Observers')}:</label>
                            </div>
                            <div class="content">
                                ## REVIEW RULES
                                <div id="review_rules" style="display: none" class="reviewers-title">
                                    <div class="pr-details-title">
                                        ${_('Reviewer rules')}
                                    </div>
                                    <div class="pr-reviewer-rules">
                                        ## review rules will be appended here, by default reviewers logic
                                    </div>
                                </div>

                                ## REVIEWERS / OBSERVERS
                                <div class="reviewers-title">

                                    <ul class="nav-links clearfix">

                                        ## TAB1 MANDATORY REVIEWERS
                                        <li class="active">
                                            <a id="reviewers-btn" href="#showReviewers" tabindex="-1">
                                                Reviewers
                                                <span id="reviewers-cnt" data-count="0" class="menulink-counter">0</span>
                                            </a>
                                        </li>

                                        ## TAB2 OBSERVERS
                                        <li class="">
                                            <a id="observers-btn" href="#showObservers" tabindex="-1">
                                                Observers
                                                <span id="observers-cnt"  data-count="0" class="menulink-counter">0</span>
                                            </a>
                                        </li>

                                    </ul>

                                    ## TAB1 MANDATORY REVIEWERS
                                    <div id="reviewers-container">
                                        <span class="calculate-reviewers">
                                            <h4>${_('loading...')}</h4>
                                        </span>

                                        <div id="reviewers" class="pr-details-content reviewers">
                                            ## members goes here, filled via JS based on initial selection !
                                            <input type="hidden" name="__start__" value="review_members:sequence">
                                            <table id="review_members" class="group_members">
                                            ## This content is loaded via JS and ReviewersPanel, an sets reviewer_entry class on each element
                                            </table>
                                            <input type="hidden" name="__end__" value="review_members:sequence">

                                            <div id="add_reviewer_input" class='ac'>
                                                <div class="reviewer_ac">
                                                    ${h.text('user', class_='ac-input', placeholder=_('Add reviewer or reviewer group'))}
                                                    <div id="reviewers_container"></div>
                                                </div>
                                            </div>

                                        </div>
                                    </div>

                                    ## TAB2 OBSERVERS
                                    <div id="observers-container" style="display: none">
                                        <span class="calculate-reviewers">
                                            <h4>${_('loading...')}</h4>
                                        </span>
                                        % if c.rhodecode_edition_id == 'EE':
                                        <div id="observers" class="pr-details-content observers">
                                            ## members goes here, filled via JS based on initial selection !
                                            <input type="hidden" name="__start__" value="observer_members:sequence">
                                            <table id="observer_members" class="group_members">
                                            ## This content is loaded via JS and ReviewersPanel, an sets reviewer_entry class on each element
                                            </table>
                                            <input type="hidden" name="__end__" value="observer_members:sequence">

                                            <div id="add_observer_input" class='ac'>
                                                <div class="observer_ac">
                                                    ${h.text('observer', class_='ac-input', placeholder=_('Add observer or observer group'))}
                                                    <div id="observers_container"></div>
                                                </div>
                                            </div>
                                        </div>
                                        % else:
                                            <h4>${_('This feature is available in RhodeCode EE edition only. Contact {sales_email} to obtain a trial license.').format(sales_email='<a href="mailto:sales@rhodecode.com">sales@rhodecode.com</a>')|n}</h4>
                                            <p>
                                                Pull request observers allows adding users who don't need to leave mandatory votes, but need to be aware about certain changes.
                                            </p>
                                        % endif
                                    </div>

                                </div>

                            </div>
                        </div>

                        ## SUBMIT
                        <div class="field">
                            <div class="label label-textarea">
                                <label for="pullrequest_submit"></label>
                            </div>
                            <div class="input">
                                <div class="pr-submit-button">
                                    <input id="pr_submit" class="btn" name="save" type="submit" value="${_('Submit Pull Request')}">
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

        </div>

    ${h.end_form()}
</div>

<script type="text/javascript">
 $(function(){
   var defaultSourceRepo = '${c.default_repo_data['source_repo_name']}';
   var defaultSourceRepoData = ${c.default_repo_data['source_refs_json']|n};
   var defaultTargetRepo = '${c.default_repo_data['target_repo_name']}';
   var defaultTargetRepoData = ${c.default_repo_data['target_refs_json']|n};

   var $pullRequestForm = $('#pull_request_form');
   var $pullRequestSubmit = $('#pr_submit', $pullRequestForm);
   var $sourceRepo = $('#source_repo', $pullRequestForm);
   var $targetRepo = $('#target_repo', $pullRequestForm);
   var $sourceRef = $('#source_ref', $pullRequestForm);
   var $targetRef = $('#target_ref', $pullRequestForm);

   var sourceRepo = function() { return $sourceRepo.eq(0).val() };
   var sourceRef = function() { return $sourceRef.eq(0).val().split(':') };

   var targetRepo = function() { return $targetRepo.eq(0).val() };
   var targetRef = function() { return $targetRef.eq(0).val().split(':') };

   var calculateContainerWidth = function() {
       var maxWidth = 0;
       var repoSelect2Containers = ['#source_repo', '#target_repo'];
       $.each(repoSelect2Containers, function(idx, value) {
           $(value).select2('container').width('auto');
           var curWidth = $(value).select2('container').width();
           if (maxWidth <= curWidth) {
               maxWidth = curWidth;
           }
           $.each(repoSelect2Containers, function(idx, value) {
               $(value).select2('container').width(maxWidth + 10);
           });
       });
   };

   var initRefSelection = function(selectedRef) {
       return function(element, callback) {
           // translate our select2 id into a text, it's a mapping to show
           // simple label when selecting by internal ID.
           var id, refData;
           if (selectedRef === undefined || selectedRef === null) {
             id = element.val();
             refData = element.val().split(':');

             if (refData.length !== 3){
                 refData = ["", "", ""]
             }
           } else {
             id = selectedRef;
             refData = selectedRef.split(':');
           }

           var text = refData[1];
           if (refData[0] === 'rev') {
               text = text.substring(0, 12);
           }

           var data = {id: id, text: text};
           callback(data);
       };
   };

   var formatRefSelection = function(data, container, escapeMarkup) {
       var prefix = '';
       var refData = data.id.split(':');
       if (refData[0] === 'branch') {
           prefix = '<i class="icon-branch"></i>';
       }
       else if (refData[0] === 'book') {
           prefix = '<i class="icon-bookmark"></i>';
       }
       else if (refData[0] === 'tag') {
           prefix = '<i class="icon-tag"></i>';
       }

       var originalOption = data.element;
       return prefix + escapeMarkup(data.text);
   };

   // custom code mirror
   var codeMirrorInstance = $('#pullrequest_desc').get(0).MarkupForm.cm;

   var diffDataHandler = function(data) {

       var commitElements = data['commits'];
       var files = data['files'];
       var added = data['stats'][0]
       var deleted = data['stats'][1]
       var commonAncestorId = data['ancestor'];
       var _sourceRefType = sourceRef()[0];
       var _sourceRefName = sourceRef()[1];
       var prTitleAndDesc = getTitleAndDescription(_sourceRefType, _sourceRefName, commitElements, 5);

       var title = prTitleAndDesc[0];
       var proposedDescription = prTitleAndDesc[1];

       var useGeneratedTitle = (
            $('#pullrequest_title').hasClass('autogenerated-title') ||
            $('#pullrequest_title').val() === "");

       if (title && useGeneratedTitle) {
           // use generated title if we haven't specified our own
           $('#pullrequest_title').val(title);
           $('#pullrequest_title').addClass('autogenerated-title');

       }

       var useGeneratedDescription = (
           !codeMirrorInstance._userDefinedValue ||
            codeMirrorInstance.getValue() === "");

       if (proposedDescription && useGeneratedDescription) {
            // set proposed content, if we haven't defined our own,
            // or we don't have description written
            codeMirrorInstance._userDefinedValue = false; // reset state
            codeMirrorInstance.setValue(proposedDescription);
       }

       // refresh our codeMirror so events kicks in and it's change aware
       codeMirrorInstance.refresh();

       var url_data = {
           'repo_name': targetRepo(),
           'target_repo': sourceRepo(),
           'source_ref': targetRef()[2],
           'source_ref_type': 'rev',
           'target_ref': sourceRef()[2],
           'target_ref_type': 'rev',
           'merge': true,
           '_': Date.now() // bypass browser caching
       }; // gather the source/target ref and repo here
       var url = pyroutes.url('repo_compare', url_data);

       var msg = '<input id="common_ancestor" type="hidden" name="common_ancestor" value="{0}">'.format(commonAncestorId);
       msg += '<input type="hidden" name="__start__" value="revisions:sequence">'


       $.each(commitElements, function(idx, value) {
           var commit_id = value["commit_id"]
           msg += '<input type="hidden" name="revisions" value="{0}">'.format(commit_id);
       });

       msg += '<input type="hidden" name="__end__" value="revisions:sequence">'
       msg += _ngettext(
           'Compare summary: <strong>{0} commit</strong>',
           'Compare summary: <strong>{0} commits</strong>',
           commitElements.length).format(commitElements.length)

       msg += '';
       msg += _ngettext(
           '<strong>, and {0} file</strong> changed.',
           '<strong>, and {0} files</strong> changed.',
           files.length).format(files.length)

       msg += '\n Diff: <span class="op-added">{0} lines inserted</span>, <span class="op-deleted">{1} lines deleted </span>.'.format(added, deleted)

       msg += '\n <a class="" id="pull_request_overview_url" href="{0}" target="_blank">${_('Show detailed compare.')}</a>'.format(url);

       if (commitElements.length) {
           var commitsLink = '<a href="#pull_request_overview"><strong>{0}</strong></a>'.format(commitElements.length);
           prButtonLock(false, msg.replace('__COMMITS__', commitsLink), 'compare');
       }
       else {
           var noCommitsMsg = '<span class="alert-text-warning">{0}</span>'.format(
               _gettext('There are no commits to merge.'));
           prButtonLock(true, noCommitsMsg, 'compare');
       }

       //make both panels equal
       $('.target-panel').height($('.source-panel').height())
   };

   reviewersController = new ReviewersController();
   reviewersController.diffDataHandler = diffDataHandler;

   var queryTargetRepo = function(self, query) {
       // cache ALL results if query is empty
       var cacheKey = query.term || '__';
       var cachedData = self.cachedDataSource[cacheKey];

       if (cachedData) {
           query.callback({results: cachedData.results});
       } else {
           $.ajax({
               url: pyroutes.url('pullrequest_repo_targets', {'repo_name': templateContext.repo_name}),
               data: {query: query.term},
               dataType: 'json',
               type: 'GET',
               success: function(data) {
                   self.cachedDataSource[cacheKey] = data;
                   query.callback({results: data.results});
               },
               error: function(jqXHR, textStatus, errorThrown) {
                var prefix = "Error while fetching entries.\n"
                var message = formatErrorMessage(jqXHR, textStatus, errorThrown, prefix);
                ajaxErrorSwal(message);
               }
           });
       }
   };

   var queryTargetRefs = function(initialData, query) {
       var data = {results: []};
       // filter initialData
       $.each(initialData, function() {
           var section = this.text;
           var children = [];
           $.each(this.children, function() {
               if (query.term.length === 0 ||
                   this.text.toUpperCase().indexOf(query.term.toUpperCase()) >= 0 ) {
                   children.push({'id': this.id, 'text': this.text})
               }
           });
           data.results.push({'text': section, 'children': children})
       });
       query.callback({results: data.results});
   };

   var Select2Box = function(element, overrides) {
     var globalDefaults = {
         dropdownAutoWidth: true,
         containerCssClass: "drop-menu",
         dropdownCssClass: "drop-menu-dropdown"
     };

     var initSelect2 = function(defaultOptions) {
       var options = jQuery.extend(globalDefaults, defaultOptions, overrides);
       element.select2(options);
     };

     return {
       initRef: function() {
         var defaultOptions = {
           minimumResultsForSearch: 5,
           formatSelection: formatRefSelection
         };

         initSelect2(defaultOptions);
       },

       initRepo: function(defaultValue, readOnly) {
         var defaultOptions = {
           initSelection : function (element, callback) {
             var data = {id: defaultValue, text: defaultValue};
             callback(data);
           }
         };

         initSelect2(defaultOptions);

         element.select2('val', defaultSourceRepo);
         if (readOnly === true) {
           element.select2('readonly', true);
         }
       }
     };
   };

   var initTargetRefs = function(refsData, selectedRef) {

     Select2Box($targetRef, {
         placeholder: "${_('Select commit reference')}",
       query: function(query) {
         queryTargetRefs(refsData, query);
       },
       initSelection : initRefSelection(selectedRef)
     }).initRef();

     if (!(selectedRef === undefined)) {
         $targetRef.select2('val', selectedRef);
     }
   };

   var targetRepoChanged = function(repoData) {
       // generate new DESC of target repo displayed next to select

       $('#target_repo_desc').html(repoData['description']);

       var prLink = pyroutes.url('pullrequest_new', {'repo_name': repoData['name']});
       var title = _gettext('Switch target repository with the source.')
       $('#switch_base').html("<a class=\"tooltip\" title=\"{0}\" href=\"{1}\">Switch sides</a>".format(title, prLink))

       // generate dynamic select2 for refs.
       initTargetRefs(repoData['refs']['select2_refs'],
                      repoData['refs']['selected_ref']);

   };

   var sourceRefSelect2 = Select2Box($sourceRef, {
       placeholder: "${_('Select commit reference')}",
       query: function(query) {
         var initialData = defaultSourceRepoData['refs']['select2_refs'];
         queryTargetRefs(initialData, query)
       },
       initSelection: initRefSelection()
   });

   var sourceRepoSelect2 = Select2Box($sourceRepo, {
     query: function(query) {}
   });

   var targetRepoSelect2 = Select2Box($targetRepo, {
     cachedDataSource: {},
     query: $.debounce(250, function(query) {
       queryTargetRepo(this, query);
     }),
     formatResult: formatRepoResult
   });

   sourceRefSelect2.initRef();

   sourceRepoSelect2.initRepo(defaultSourceRepo, true);

   targetRepoSelect2.initRepo(defaultTargetRepo, false);

   $sourceRef.on('change', function(e){
     reviewersController.loadDefaultReviewers(
         sourceRepo(), sourceRef(), targetRepo(), targetRef());
   });

   $targetRef.on('change', function(e){
     reviewersController.loadDefaultReviewers(
         sourceRepo(), sourceRef(), targetRepo(), targetRef());
   });

   $targetRepo.on('change', function(e){
       var repoName = $(this).val();
       calculateContainerWidth();
       $targetRef.select2('destroy');
       $('#target_ref_loading').show();

       $.ajax({
           url: pyroutes.url('pullrequest_repo_refs',
             {'repo_name': templateContext.repo_name, 'target_repo_name':repoName}),
           data: {},
           dataType: 'json',
           type: 'GET',
           success: function(data) {
               $('#target_ref_loading').hide();
               targetRepoChanged(data);
           },
           error: function(jqXHR, textStatus, errorThrown) {
                var prefix = "Error while fetching entries.\n"
                var message = formatErrorMessage(jqXHR, textStatus, errorThrown, prefix);
                ajaxErrorSwal(message);
           }
       })

   });

   $pullRequestForm.on('submit', function(e){
       // Flush changes into textarea
       codeMirrorInstance.save();
       prButtonLock(true, null, 'all');
       $pullRequestSubmit.val(_gettext('Please wait creating pull request...'));
   });

   prButtonLock(true, "${_('Please select source and target')}", 'all');

   // auto-load on init, the target refs select2
   calculateContainerWidth();
   targetRepoChanged(defaultTargetRepoData);

   $('#pullrequest_title').on('keyup', function(e){
       $(this).removeClass('autogenerated-title');
   });

   % if c.default_source_ref:
   // in case we have a pre-selected value, use it now
   $sourceRef.select2('val', '${c.default_source_ref}');


   // default reviewers / observers
   reviewersController.loadDefaultReviewers(
       sourceRepo(), sourceRef(), targetRepo(), targetRef());
   % endif

   ReviewerAutoComplete('#user', reviewersController);
   ObserverAutoComplete('#observer', reviewersController);

   // TODO, move this to another handler

   var $reviewersBtn = $('#reviewers-btn');
   var $reviewersContainer = $('#reviewers-container');

   var $observersBtn = $('#observers-btn')
   var $observersContainer = $('#observers-container');

   $reviewersBtn.on('click', function (e) {

       $observersContainer.hide();
       $reviewersContainer.show();

       $observersBtn.parent().removeClass('active');
       $reviewersBtn.parent().addClass('active');
       e.preventDefault();

   })

   $observersBtn.on('click', function (e) {

       $reviewersContainer.hide();
       $observersContainer.show();

       $reviewersBtn.parent().removeClass('active');
       $observersBtn.parent().addClass('active');
       e.preventDefault();

   })

 });
</script>

</%def>
