// # Copyright (C) 2010-2020 RhodeCode GmbH
// #
// # This program is free software: you can redistribute it and/or modify
// # it under the terms of the GNU Affero General Public License, version 3
// # (only), as published by the Free Software Foundation.
// #
// # This program is distributed in the hope that it will be useful,
// # but WITHOUT ANY WARRANTY; without even the implied warranty of
// # MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// # GNU General Public License for more details.
// #
// # You should have received a copy of the GNU Affero General Public License
// # along with this program.  If not, see <http://www.gnu.org/licenses/>.
// #
// # This program is dual-licensed. If you wish to learn more about the
// # RhodeCode Enterprise Edition, including its added features, Support services,
// # and proprietary license terms, please see https://rhodecode.com/licenses/


var prButtonLockChecks = {
  'compare': false,
  'reviewers': false
};

/**
 * lock button until all checks and loads are made. E.g reviewer calculation
 * should prevent from submitting a PR
 * @param lockEnabled
 * @param msg
 * @param scope
 */
var prButtonLock = function(lockEnabled, msg, scope) {
      scope = scope || 'all';
      if (scope == 'all'){
          prButtonLockChecks['compare'] = !lockEnabled;
          prButtonLockChecks['reviewers'] = !lockEnabled;
      } else if (scope == 'compare') {
          prButtonLockChecks['compare'] = !lockEnabled;
      } else if (scope == 'reviewers'){
          prButtonLockChecks['reviewers'] = !lockEnabled;
      }
      var checksMeet = prButtonLockChecks.compare && prButtonLockChecks.reviewers;
      if (lockEnabled) {
          $('#pr_submit').attr('disabled', 'disabled');
      }
      else if (checksMeet) {
          $('#pr_submit').removeAttr('disabled');
      }

      if (msg) {
          $('#pr_open_message').html(msg);
      }
};


/**
Generate Title and Description for a PullRequest.
In case of 1 commits, the title and description is that one commit
in case of multiple commits, we iterate on them with max N number of commits,
and build description in a form
- commitN
- commitN+1
...

Title is then constructed from branch names, or other references,
replacing '-' and '_' into spaces

* @param sourceRef
* @param elements
* @param limit
* @returns {*[]}
*/
var getTitleAndDescription = function(sourceRefType, sourceRef, elements, limit) {
  var title = '';
  var desc = '';

  $.each($(elements).get().reverse().slice(0, limit), function(idx, value) {
      var rawMessage = value['message'];
      desc += '- ' + rawMessage.split('\n')[0].replace(/\n+$/, "") + '\n';
  });
  // only 1 commit, use commit message as title
  if (elements.length === 1) {
      var rawMessage = elements[0]['message'];
      title = rawMessage.split('\n')[0];
  }
  else {
      // use reference name
      var normalizedRef = sourceRef.replace(/-/g, ' ').replace(/_/g, ' ').capitalizeFirstLetter()
      var refType = sourceRefType;
      title = 'Changes from {0}: {1}'.format(refType, normalizedRef);
  }

  return [title, desc]
};


window.ReviewersController = function () {
    var self = this;
    this.$loadingIndicator = $('.calculate-reviewers');
    this.$reviewRulesContainer = $('#review_rules');
    this.$rulesList = this.$reviewRulesContainer.find('.pr-reviewer-rules');
    this.$userRule = $('.pr-user-rule-container');
    this.$reviewMembers = $('#review_members');
    this.$observerMembers = $('#observer_members');

    this.currentRequest = null;
    this.diffData = null;
    this.enabledRules = [];
    // sync with db.py entries
    this.ROLE_REVIEWER = 'reviewer';
    this.ROLE_OBSERVER = 'observer'

    //dummy handler, we might register our own later
    this.diffDataHandler = function (data) {};

    this.defaultForbidUsers = function () {
        return [
            {
                'username': 'default',
                'user_id': templateContext.default_user.user_id
            }
        ];
    };

    // init default forbidden users
    this.forbidUsers = this.defaultForbidUsers();

    this.hideReviewRules = function () {
        self.$reviewRulesContainer.hide();
        $(self.$userRule.selector).hide();
    };

    this.showReviewRules = function () {
        self.$reviewRulesContainer.show();
        $(self.$userRule.selector).show();
    };

    this.addRule = function (ruleText) {
        self.showReviewRules();
        self.enabledRules.push(ruleText);
        return '<div>- {0}</div>'.format(ruleText)
    };

    this.increaseCounter = function(role) {
        if (role === self.ROLE_REVIEWER) {
            var $elem = $('#reviewers-cnt')
            var cnt = parseInt($elem.data('count') || 0)
            cnt +=1
            $elem.html(cnt);
            $elem.data('count', cnt);
        }
        else if (role === self.ROLE_OBSERVER) {
            var $elem = $('#observers-cnt');
            var cnt = parseInt($elem.data('count') || 0)
            cnt +=1
            $elem.html(cnt);
            $elem.data('count', cnt);
        }
    }

    this.resetCounter = function () {
        var $elem = $('#reviewers-cnt');

        $elem.data('count', 0);
        $elem.html(0);

        var $elem = $('#observers-cnt');

        $elem.data('count', 0);
        $elem.html(0);
    }

    this.loadReviewRules = function (data) {
        self.diffData = data;

        // reset forbidden Users
        this.forbidUsers = self.defaultForbidUsers();

        // reset state of review rules
        self.$rulesList.html('');

        if (!data || data.rules === undefined || $.isEmptyObject(data.rules)) {
            // default rule, case for older repo that don't have any rules stored
            self.$rulesList.append(
                self.addRule(
                    _gettext('All reviewers must vote.'))
            );
            return self.forbidUsers
        }

        if (data.rules.voting !== undefined) {
            if (data.rules.voting < 0) {
                self.$rulesList.append(
                    self.addRule(
                        _gettext('All individual reviewers must vote.'))
                )
            } else if (data.rules.voting === 1) {
                self.$rulesList.append(
                    self.addRule(
                        _gettext('At least {0} reviewer must vote.').format(data.rules.voting))
                )

            } else {
                self.$rulesList.append(
                    self.addRule(
                        _gettext('At least {0} reviewers must vote.').format(data.rules.voting))
                )
            }
        }

        if (data.rules.voting_groups !== undefined) {
            $.each(data.rules.voting_groups, function (index, rule_data) {
                self.$rulesList.append(
                    self.addRule(rule_data.text)
                )
            });
        }

        if (data.rules.use_code_authors_for_review) {
            self.$rulesList.append(
                self.addRule(
                    _gettext('Reviewers picked from source code changes.'))
            )
        }

        if (data.rules.forbid_adding_reviewers) {
            $('#add_reviewer_input').remove();
            self.$rulesList.append(
                self.addRule(
                    _gettext('Adding new reviewers is forbidden.'))
            )
        }

        if (data.rules.forbid_author_to_review) {
            self.forbidUsers.push(data.rules_data.pr_author);
            self.$rulesList.append(
                self.addRule(
                    _gettext('Author is not allowed to be a reviewer.'))
            )
        }

        if (data.rules.forbid_commit_author_to_review) {

            if (data.rules_data.forbidden_users) {
                $.each(data.rules_data.forbidden_users, function (index, member_data) {
                    self.forbidUsers.push(member_data)
                });
            }

            self.$rulesList.append(
                self.addRule(
                    _gettext('Commit Authors are not allowed to be a reviewer.'))
            )
        }

        // we don't have any rules set, so we inform users about it
        if (self.enabledRules.length === 0) {
            self.addRule(
                _gettext('No review rules set.'))
        }

        return self.forbidUsers
    };

    this.emptyTables = function () {
        self.emptyReviewersTable();
        self.emptyObserversTable();

        // Also reset counters.
        self.resetCounter();
    }

    this.emptyReviewersTable = function (withText) {
        self.$reviewMembers.empty();
        if (withText !== undefined) {
            self.$reviewMembers.html(withText)
        }
    };

    this.emptyObserversTable = function (withText) {
        self.$observerMembers.empty();
        if (withText !== undefined) {
            self.$observerMembers.html(withText)
        }
    }

    this.loadDefaultReviewers = function (sourceRepo, sourceRef, targetRepo, targetRef) {

        if (self.currentRequest) {
            // make sure we cleanup old running requests before triggering this again
            self.currentRequest.abort();
        }

        self.$loadingIndicator.show();

        // reset reviewer/observe members
        self.emptyTables();

        prButtonLock(true, null, 'reviewers');
        $('#user').hide(); // hide user autocomplete before load
        $('#observer').hide(); //hide observer autocomplete before load

        // lock PR button, so we cannot send PR before it's calculated
        prButtonLock(true, _gettext('Loading diff ...'), 'compare');

        if (sourceRef.length !== 3 || targetRef.length !== 3) {
            // don't load defaults in case we're missing some refs...
            self.$loadingIndicator.hide();
            return
        }

        var url = pyroutes.url('repo_default_reviewers_data',
            {
                'repo_name': templateContext.repo_name,
                'source_repo': sourceRepo,
                'source_ref': sourceRef[2],
                'target_repo': targetRepo,
                'target_ref': targetRef[2]
            });

        self.currentRequest = $.ajax({
            url: url,
            headers: {'X-PARTIAL-XHR': true},
            type: 'GET',
            success: function (data) {

                self.currentRequest = null;

                // review rules
                self.loadReviewRules(data);
                self.handleDiffData(data["diff_info"]);

                for (var i = 0; i < data.reviewers.length; i++) {
                    var reviewer = data.reviewers[i];
                    // load reviewer rules from the repo data
                    self.addMember(reviewer, reviewer.reasons, reviewer.mandatory, reviewer.role);
                }


                self.$loadingIndicator.hide();
                prButtonLock(false, null, 'reviewers');

                $('#user').show(); // show user autocomplete before load
                $('#observer').show(); // show observer autocomplete before load

                var commitElements = data["diff_info"]['commits'];

                if (commitElements.length === 0) {
                    var noCommitsMsg = '<span class="alert-text-warning">{0}</span>'.format(
                        _gettext('There are no commits to merge.'));
                    prButtonLock(true, noCommitsMsg, 'all');

                } else {
                    // un-lock PR button, so we cannot send PR before it's calculated
                    prButtonLock(false, null, 'compare');
                }

            },
            error: function (jqXHR, textStatus, errorThrown) {
                var prefix = "Loading diff and reviewers/observers failed\n"
                var message = formatErrorMessage(jqXHR, textStatus, errorThrown, prefix);
                ajaxErrorSwal(message);
            }
        });

    };

    // check those, refactor
    this.removeMember = function (reviewer_id, mark_delete) {
        var reviewer = $('#reviewer_{0}'.format(reviewer_id));

        if (typeof (mark_delete) === undefined) {
            mark_delete = false;
        }

        if (mark_delete === true) {
            if (reviewer) {
                // now delete the input
                $('#reviewer_{0} input'.format(reviewer_id)).remove();
                $('#reviewer_{0}_rules input'.format(reviewer_id)).remove();
                // mark as to-delete
                var obj = $('#reviewer_{0}_name'.format(reviewer_id));
                obj.addClass('to-delete');
                obj.css({"text-decoration": "line-through", "opacity": 0.5});
            }
        } else {
            $('#reviewer_{0}'.format(reviewer_id)).remove();
        }
    };

    this.addMember = function (reviewer_obj, reasons, mandatory, role) {

        var id = reviewer_obj.user_id;
        var username = reviewer_obj.username;

        reasons = reasons || [];
        mandatory = mandatory || false;
        role = role || self.ROLE_REVIEWER

        // register current set IDS to check if we don't have this ID already in
        // and prevent duplicates
        var currentIds = [];

        $.each($('.reviewer_entry'), function (index, value) {
            currentIds.push($(value).data('reviewerUserId'))
        })

        var userAllowedReview = function (userId) {
            var allowed = true;
            $.each(self.forbidUsers, function (index, member_data) {
                if (parseInt(userId) === member_data['user_id']) {
                    allowed = false;
                    return false // breaks the loop
                }
            });
            return allowed
        };

        var userAllowed = userAllowedReview(id);

        if (!userAllowed) {
            alert(_gettext('User `{0}` not allowed to be a reviewer').format(username));
        } else {
            // only add if it's not there
            var alreadyReviewer = currentIds.indexOf(id) != -1;

            if (alreadyReviewer) {
                alert(_gettext('User `{0}` already in reviewers/observers').format(username));
            } else {

                var reviewerEntry = renderTemplate('reviewMemberEntry', {
                    'member': reviewer_obj,
                    'mandatory': mandatory,
                    'role': role,
                    'reasons': reasons,
                    'allowed_to_update': true,
                    'review_status': 'not_reviewed',
                    'review_status_label': _gettext('Not Reviewed'),
                    'user_group': reviewer_obj.user_group,
                    'create': true,
                    'rule_show': true,
                })

                if (role === self.ROLE_REVIEWER) {
                    $(self.$reviewMembers.selector).append(reviewerEntry);
                    self.increaseCounter(self.ROLE_REVIEWER);
                    $('#reviewer-empty-msg').remove()
                }
                else if (role === self.ROLE_OBSERVER) {
                    $(self.$observerMembers.selector).append(reviewerEntry);
                    self.increaseCounter(self.ROLE_OBSERVER);
                    $('#observer-empty-msg').remove();
                }

                tooltipActivate();
            }
        }

    };

    this.updateReviewers = function (repo_name, pull_request_id, role) {
        if (role === 'reviewer') {
            var postData = $('#reviewers input').serialize();
            _updatePullRequest(repo_name, pull_request_id, postData);
        } else if (role === 'observer') {
            var postData = $('#observers input').serialize();
            _updatePullRequest(repo_name, pull_request_id, postData);
        }
    };

    this.handleDiffData = function (data) {
        self.diffDataHandler(data)
    }
};


var _updatePullRequest = function(repo_name, pull_request_id, postData) {
    var url = pyroutes.url(
        'pullrequest_update',
        {"repo_name": repo_name, "pull_request_id": pull_request_id});
    if (typeof postData === 'string' ) {
        postData += '&csrf_token=' + CSRF_TOKEN;
    } else {
        postData.csrf_token = CSRF_TOKEN;
    }

    var success = function(o) {
        var redirectUrl = o['redirect_url'];
        if (redirectUrl !== undefined && redirectUrl !== null && redirectUrl !== '') {
            window.location = redirectUrl;
        } else {
            window.location.reload();
        }
    };

    ajaxPOST(url, postData, success);
};

/**
 * PULL REQUEST update commits
 */
var updateCommits = function(repo_name, pull_request_id, force) {
    var postData = {
        'update_commits': true
    };
    if (force !== undefined && force === true) {
        postData['force_refresh'] = true
    }
    _updatePullRequest(repo_name, pull_request_id, postData);
};


/**
 * PULL REQUEST edit info
 */
var editPullRequest = function(repo_name, pull_request_id, title, description, renderer) {
    var url = pyroutes.url(
        'pullrequest_update',
        {"repo_name": repo_name, "pull_request_id": pull_request_id});

    var postData = {
        'title': title,
        'description': description,
        'description_renderer': renderer,
        'edit_pull_request': true,
        'csrf_token': CSRF_TOKEN
    };
    var success = function(o) {
        window.location.reload();
    };
    ajaxPOST(url, postData, success);
};


/**
 * autocomplete handler for reviewers/observers
 */
var autoCompleteHandler = function (inputId, controller, role) {

    return function (element, data) {
        var mandatory = false;
        var reasons = [_gettext('added manually by "{0}"').format(
            templateContext.rhodecode_user.username)];

        // add whole user groups
        if (data.value_type == 'user_group') {
            reasons.push(_gettext('member of "{0}"').format(data.value_display));

            $.each(data.members, function (index, member_data) {
                var reviewer = member_data;
                reviewer['user_id'] = member_data['id'];
                reviewer['gravatar_link'] = member_data['icon_link'];
                reviewer['user_link'] = member_data['profile_link'];
                reviewer['rules'] = [];
                controller.addMember(reviewer, reasons, mandatory, role);
            })
        }
        // add single user
        else {
            var reviewer = data;
            reviewer['user_id'] = data['id'];
            reviewer['gravatar_link'] = data['icon_link'];
            reviewer['user_link'] = data['profile_link'];
            reviewer['rules'] = [];
            controller.addMember(reviewer, reasons, mandatory, role);
        }

        $(inputId).val('');
    }
}

/**
 * Reviewer autocomplete
 */
var ReviewerAutoComplete = function (inputId, controller) {
    var self = this;
    self.controller = controller;
    self.inputId = inputId;
    var handler = autoCompleteHandler(inputId, controller, controller.ROLE_REVIEWER);

    $(inputId).autocomplete({
        serviceUrl: pyroutes.url('user_autocomplete_data'),
        minChars: 2,
        maxHeight: 400,
        deferRequestBy: 300, //miliseconds
        showNoSuggestionNotice: true,
        tabDisabled: true,
        autoSelectFirst: true,
        params: {
            user_id: templateContext.rhodecode_user.user_id,
            user_groups: true,
            user_groups_expand: true,
            skip_default_user: true
        },
        formatResult: autocompleteFormatResult,
        lookupFilter: autocompleteFilterResult,
        onSelect: handler
    });
};

/**
 * Observers autocomplete
 */
var ObserverAutoComplete = function(inputId, controller) {
    var self = this;
    self.controller = controller;
    self.inputId = inputId;
    var handler = autoCompleteHandler(inputId, controller, controller.ROLE_OBSERVER);

    $(inputId).autocomplete({
        serviceUrl: pyroutes.url('user_autocomplete_data'),
        minChars: 2,
        maxHeight: 400,
        deferRequestBy: 300, //miliseconds
        showNoSuggestionNotice: true,
        tabDisabled: true,
        autoSelectFirst: true,
        params: {
            user_id: templateContext.rhodecode_user.user_id,
            user_groups: true,
            user_groups_expand: true,
            skip_default_user: true
        },
        formatResult: autocompleteFormatResult,
        lookupFilter: autocompleteFilterResult,
        onSelect: handler
    });
}


window.VersionController = function () {
    var self = this;
    this.$verSource = $('input[name=ver_source]');
    this.$verTarget = $('input[name=ver_target]');
    this.$showVersionDiff = $('#show-version-diff');

    this.adjustRadioSelectors = function (curNode) {
        var getVal = function (item) {
            if (item === 'latest') {
                return Number.MAX_SAFE_INTEGER
            }
            else {
                return parseInt(item)
            }
        };

        var curVal = getVal($(curNode).val());
        var cleared = false;

        $.each(self.$verSource, function (index, value) {
            var elVal = getVal($(value).val());

            if (elVal > curVal) {
                if ($(value).is(':checked')) {
                    cleared = true;
                }
                $(value).attr('disabled', 'disabled');
                $(value).removeAttr('checked');
                $(value).css({'opacity': 0.1});
            }
            else {
                $(value).css({'opacity': 1});
                $(value).removeAttr('disabled');
            }
        });

        if (cleared) {
            // if we unchecked an active, set the next one to same loc.
            $(this.$verSource).filter('[value={0}]'.format(
                curVal)).attr('checked', 'checked');
        }

        self.setLockAction(false,
            $(curNode).data('verPos'),
            $(this.$verSource).filter(':checked').data('verPos')
        );
    };


    this.attachVersionListener = function () {
        self.$verTarget.change(function (e) {
            self.adjustRadioSelectors(this)
        });
        self.$verSource.change(function (e) {
            self.adjustRadioSelectors(self.$verTarget.filter(':checked'))
        });
    };

    this.init = function () {

        var curNode = self.$verTarget.filter(':checked');
        self.adjustRadioSelectors(curNode);
        self.setLockAction(true);
        self.attachVersionListener();

    };

    this.setLockAction = function (state, selectedVersion, otherVersion) {
        var $showVersionDiff = this.$showVersionDiff;

        if (state) {
            $showVersionDiff.attr('disabled', 'disabled');
            $showVersionDiff.addClass('disabled');
            $showVersionDiff.html($showVersionDiff.data('labelTextLocked'));
        }
        else {
            $showVersionDiff.removeAttr('disabled');
            $showVersionDiff.removeClass('disabled');

            if (selectedVersion == otherVersion) {
                $showVersionDiff.html($showVersionDiff.data('labelTextShow'));
            } else {
                $showVersionDiff.html($showVersionDiff.data('labelTextDiff'));
            }
        }

    };

    this.showVersionDiff = function () {
        var target = self.$verTarget.filter(':checked');
        var source = self.$verSource.filter(':checked');

        if (target.val() && source.val()) {
            var params = {
                'pull_request_id': templateContext.pull_request_data.pull_request_id,
                'repo_name': templateContext.repo_name,
                'version': target.val(),
                'from_version': source.val()
            };
            window.location = pyroutes.url('pullrequest_show', params)
        }

        return false;
    };

    this.toggleVersionView = function (elem) {

        if (this.$showVersionDiff.is(':visible')) {
            $('.version-pr').hide();
            this.$showVersionDiff.hide();
            $(elem).html($(elem).data('toggleOn'))
        } else {
            $('.version-pr').show();
            this.$showVersionDiff.show();
            $(elem).html($(elem).data('toggleOff'))
        }

        return false
    };

};


window.UpdatePrController = function () {
    var self = this;
    this.$updateCommits = $('#update_commits');
    this.$updateCommitsSwitcher = $('#update_commits_switcher');

    this.lockUpdateButton = function (label) {
        self.$updateCommits.attr('disabled', 'disabled');
        self.$updateCommitsSwitcher.attr('disabled', 'disabled');

        self.$updateCommits.addClass('disabled');
        self.$updateCommitsSwitcher.addClass('disabled');

        self.$updateCommits.removeClass('btn-primary');
        self.$updateCommitsSwitcher.removeClass('btn-primary');

        self.$updateCommits.text(_gettext(label));
    };

    this.isUpdateLocked = function () {
        return self.$updateCommits.attr('disabled') !== undefined;
    };

    this.updateCommits = function (curNode) {
        if (self.isUpdateLocked()) {
            return
        }
        self.lockUpdateButton(_gettext('Updating...'));
        updateCommits(
            templateContext.repo_name,
            templateContext.pull_request_data.pull_request_id);
    };

    this.forceUpdateCommits = function () {
        if (self.isUpdateLocked()) {
            return
        }
        self.lockUpdateButton(_gettext('Force updating...'));
        var force = true;
        updateCommits(
            templateContext.repo_name,
            templateContext.pull_request_data.pull_request_id, force);
    };
};


/**
 * Reviewer display panel
 */
window.ReviewersPanel = {
    editButton: null,
    closeButton: null,
    addButton: null,
    removeButtons: null,
    reviewRules: null,
    setReviewers: null,
    controller: null,

    setSelectors: function () {
        var self = this;
        self.editButton = $('#open_edit_reviewers');
        self.closeButton =$('#close_edit_reviewers');
        self.addButton = $('#add_reviewer');
        self.removeButtons = $('.reviewer_member_remove,.reviewer_member_mandatory_remove');
    },

    init: function (controller, reviewRules, setReviewers) {
        var self = this;
        self.setSelectors();

        self.controller = controller;
        self.reviewRules = reviewRules;
        self.setReviewers = setReviewers;

        self.editButton.on('click', function (e) {
            self.edit();
        });
        self.closeButton.on('click', function (e) {
            self.close();
            self.renderReviewers();
        });

        self.renderReviewers();

    },

    renderReviewers: function () {
        var self = this;

        if (self.setReviewers.reviewers === undefined) {
            return
        }
        if (self.setReviewers.reviewers.length === 0) {
            self.controller.emptyReviewersTable('<tr id="reviewer-empty-msg"><td colspan="6">No reviewers</td></tr>');
            return
        }

        self.controller.emptyReviewersTable();

        $.each(self.setReviewers.reviewers, function (key, val) {

            var member = val;
            if (member.role === self.controller.ROLE_REVIEWER) {
                var entry = renderTemplate('reviewMemberEntry', {
                    'member': member,
                    'mandatory': member.mandatory,
                    'role': member.role,
                    'reasons': member.reasons,
                    'allowed_to_update': member.allowed_to_update,
                    'review_status': member.review_status,
                    'review_status_label': member.review_status_label,
                    'user_group': member.user_group,
                    'create': false
                });

                $(self.controller.$reviewMembers.selector).append(entry)
            }
        });

        tooltipActivate();
    },

    edit: function (event) {
        var self = this;
        self.editButton.hide();
        self.closeButton.show();
        self.addButton.show();
        $(self.removeButtons.selector).css('visibility', 'visible');
        // review rules
        self.controller.loadReviewRules(this.reviewRules);
    },

    close: function (event) {
        var self = this;
        this.editButton.show();
        this.closeButton.hide();
        this.addButton.hide();
        $(this.removeButtons.selector).css('visibility', 'hidden');
        // hide review rules
        self.controller.hideReviewRules();
    }
};

/**
 * Reviewer display panel
 */
window.ObserversPanel = {
    editButton: null,
    closeButton: null,
    addButton: null,
    removeButtons: null,
    reviewRules: null,
    setReviewers: null,
    controller: null,

    setSelectors: function () {
        var self = this;
        self.editButton = $('#open_edit_observers');
        self.closeButton =$('#close_edit_observers');
        self.addButton = $('#add_observer');
        self.removeButtons = $('.observer_member_remove,.observer_member_mandatory_remove');
    },

    init: function (controller, reviewRules, setReviewers) {
        var self = this;
        self.setSelectors();

        self.controller = controller;
        self.reviewRules = reviewRules;
        self.setReviewers = setReviewers;

        self.editButton.on('click', function (e) {
            self.edit();
        });
        self.closeButton.on('click', function (e) {
            self.close();
            self.renderObservers();
        });

        self.renderObservers();

    },

    renderObservers: function () {
        var self = this;
        if (self.setReviewers.observers === undefined) {
            return
        }
        if (self.setReviewers.observers.length === 0) {
            self.controller.emptyObserversTable('<tr id="observer-empty-msg"><td colspan="6">No observers</td></tr>');
            return
        }

        self.controller.emptyObserversTable();

        $.each(self.setReviewers.observers, function (key, val) {
            var member = val;
            if (member.role === self.controller.ROLE_OBSERVER) {
                var entry = renderTemplate('reviewMemberEntry', {
                    'member': member,
                    'mandatory': member.mandatory,
                    'role': member.role,
                    'reasons': member.reasons,
                    'allowed_to_update': member.allowed_to_update,
                    'review_status': member.review_status,
                    'review_status_label': member.review_status_label,
                    'user_group': member.user_group,
                    'create': false
                });

                $(self.controller.$observerMembers.selector).append(entry)
            }
        });

        tooltipActivate();
    },

    edit: function (event) {
        this.editButton.hide();
        this.closeButton.show();
        this.addButton.show();
        $(this.removeButtons.selector).css('visibility', 'visible');
    },

    close: function (event) {
        this.editButton.show();
        this.closeButton.hide();
        this.addButton.hide();
        $(this.removeButtons.selector).css('visibility', 'hidden');
    }

};

window.PRDetails = {
    editButton: null,
    closeButton: null,
    deleteButton: null,
    viewFields: null,
    editFields: null,

    setSelectors: function () {
        var self = this;
        self.editButton = $('#open_edit_pullrequest')
        self.closeButton = $('#close_edit_pullrequest')
        self.deleteButton = $('#delete_pullrequest')
        self.viewFields = $('#pr-desc, #pr-title')
        self.editFields = $('#pr-desc-edit, #pr-title-edit, .pr-save')
    },

    init: function () {
        var self = this;
        self.setSelectors();
        self.editButton.on('click', function (e) {
            self.edit();
        });
        self.closeButton.on('click', function (e) {
            self.view();
        });
    },

    edit: function (event) {
        var cmInstance = $('#pr-description-input').get(0).MarkupForm.cm;
        this.viewFields.hide();
        this.editButton.hide();
        this.deleteButton.hide();
        this.closeButton.show();
        this.editFields.show();
        cmInstance.refresh();
    },

    view: function (event) {
        this.editButton.show();
        this.deleteButton.show();
        this.editFields.hide();
        this.closeButton.hide();
        this.viewFields.show();
    }
};

/**
 * OnLine presence using channelstream
 */
window.ReviewerPresenceController = function (channel) {
    var self = this;
    this.channel = channel;
    this.users = {};

    this.storeUsers = function (users) {
        self.users = {}
        $.each(users, function (index, value) {
            var userId = value.state.id;
            self.users[userId] = value.state;
        })
    }

    this.render = function () {
        $.each($('.reviewer_entry'), function (index, value) {
            var userData = $(value).data();
            if (self.users[userData.reviewerUserId] !== undefined) {
                $(value).find('.presence-state').show();
            } else {
                $(value).find('.presence-state').hide();
            }
        })
    };

    this.handlePresence = function (data) {
        if (data.type == 'presence' && data.channel === self.channel) {
            this.storeUsers(data.users);
            this.render()
        }
    };

    this.handleChannelUpdate = function (data) {
        if (data.channel === this.channel) {
            this.storeUsers(data.state.users);
            this.render()
        }

    };

    /* subscribe to the current presence */
    $.Topic('/connection_controller/presence').subscribe(this.handlePresence.bind(this));
    /* subscribe to updates e.g connect/disconnect */
    $.Topic('/connection_controller/channel_update').subscribe(this.handleChannelUpdate.bind(this));

};

window.refreshComments = function (version) {
    version = version || templateContext.pull_request_data.pull_request_version || '';

    // Pull request case
    if (templateContext.pull_request_data.pull_request_id !== null) {
        var params = {
            'pull_request_id': templateContext.pull_request_data.pull_request_id,
            'repo_name': templateContext.repo_name,
            'version': version,
        };
        var loadUrl = pyroutes.url('pullrequest_comments', params);
    } // commit case
    else {
        return
    }

    var currentIDs = []
    $.each($('.comment'), function (idx, element) {
        currentIDs.push($(element).data('commentId'));
    });
    var data = {"comments": currentIDs};

    var $targetElem = $('.comments-content-table');
    $targetElem.css('opacity', 0.3);

    var success = function (data) {
        var $counterElem = $('#comments-count');
        var newCount = $(data).data('counter');
        if (newCount !== undefined) {
            var callback = function () {
                $counterElem.animate({'opacity': 1.00}, 200)
                $counterElem.html(newCount);
            };
            $counterElem.animate({'opacity': 0.15}, 200, callback);
        }

        $targetElem.css('opacity', 1);
        $targetElem.html(data);
        tooltipActivate();
    }

    ajaxPOST(loadUrl, data, success, null, {})

}

window.refreshTODOs = function (version) {
    version = version || templateContext.pull_request_data.pull_request_version || '';
    // Pull request case
    if (templateContext.pull_request_data.pull_request_id !== null) {
        var params = {
            'pull_request_id': templateContext.pull_request_data.pull_request_id,
            'repo_name': templateContext.repo_name,
            'version': version,
        };
        var loadUrl = pyroutes.url('pullrequest_comments', params);
    } // commit case
    else {
        return
    }

    var currentIDs = []
    $.each($('.comment'), function (idx, element) {
        currentIDs.push($(element).data('commentId'));
    });

    var data = {"comments": currentIDs};
    var $targetElem = $('.todos-content-table');
    $targetElem.css('opacity', 0.3);

    var success = function (data) {
        var $counterElem = $('#todos-count')
        var newCount = $(data).data('counter');
        if (newCount !== undefined) {
            var callback = function () {
                $counterElem.animate({'opacity': 1.00}, 200)
                $counterElem.html(newCount);
            };
            $counterElem.animate({'opacity': 0.15}, 200, callback);
        }

        $targetElem.css('opacity', 1);
        $targetElem.html(data);
        tooltipActivate();
    }

    ajaxPOST(loadUrl, data, success, null, {})

}

window.refreshAllComments = function (version) {
    version = version || templateContext.pull_request_data.pull_request_version || '';

    refreshComments(version);
    refreshTODOs(version);
};

window.sidebarComment = function (commentId) {
    var jsonData = $('#commentHovercard{0}'.format(commentId)).data('commentJsonB64');
    if (!jsonData) {
        return 'Failed to load comment {0}'.format(commentId)
    }
    var funcData = JSON.parse(atob(jsonData));
    return renderTemplate('sideBarCommentHovercard', funcData)
};
