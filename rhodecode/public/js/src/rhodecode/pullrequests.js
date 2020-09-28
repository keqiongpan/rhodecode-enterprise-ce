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


ReviewersController = function () {
    var self = this;
    this.$reviewRulesContainer = $('#review_rules');
    this.$rulesList = this.$reviewRulesContainer.find('.pr-reviewer-rules');
    this.$userRule = $('.pr-user-rule-container');
    this.forbidReviewUsers = undefined;
    this.$reviewMembers = $('#review_members');
    this.currentRequest = null;
    this.diffData = null;
    this.enabledRules = [];

    //dummy handler, we might register our own later
    this.diffDataHandler = function(data){};

    this.defaultForbidReviewUsers = function () {
        return [
            {
                'username': 'default',
                'user_id': templateContext.default_user.user_id
            }
        ];
    };

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

    this.loadReviewRules = function (data) {
        self.diffData = data;

        // reset forbidden Users
        this.forbidReviewUsers = self.defaultForbidReviewUsers();

        // reset state of review rules
        self.$rulesList.html('');

        if (!data || data.rules === undefined || $.isEmptyObject(data.rules)) {
            // default rule, case for older repo that don't have any rules stored
            self.$rulesList.append(
                self.addRule(
                    _gettext('All reviewers must vote.'))
            );
            return self.forbidReviewUsers
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
            self.forbidReviewUsers.push(data.rules_data.pr_author);
            self.$rulesList.append(
                self.addRule(
                    _gettext('Author is not allowed to be a reviewer.'))
            )
        }

        if (data.rules.forbid_commit_author_to_review) {

            if (data.rules_data.forbidden_users) {
                $.each(data.rules_data.forbidden_users, function (index, member_data) {
                    self.forbidReviewUsers.push(member_data)
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

        return self.forbidReviewUsers
    };

    this.loadDefaultReviewers = function (sourceRepo, sourceRef, targetRepo, targetRef) {

        if (self.currentRequest) {
            // make sure we cleanup old running requests before triggering this again
            self.currentRequest.abort();
        }

        $('.calculate-reviewers').show();
        // reset reviewer members
        self.$reviewMembers.empty();

        prButtonLock(true, null, 'reviewers');
        $('#user').hide(); // hide user autocomplete before load

        // lock PR button, so we cannot send PR before it's calculated
        prButtonLock(true, _gettext('Loading diff ...'), 'compare');

        if (sourceRef.length !== 3 || targetRef.length !== 3) {
            // don't load defaults in case we're missing some refs...
            $('.calculate-reviewers').hide();
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
                    self.addReviewMember(reviewer, reviewer.reasons, reviewer.mandatory);
                }
                $('.calculate-reviewers').hide();
                prButtonLock(false, null, 'reviewers');
                $('#user').show(); // show user autocomplete after load

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
                var prefix = "Loading diff and reviewers failed\n"
                var message = formatErrorMessage(jqXHR, textStatus, errorThrown, prefix);
                ajaxErrorSwal(message);
            }
        });

    };

    // check those, refactor
    this.removeReviewMember = function (reviewer_id, mark_delete) {
        var reviewer = $('#reviewer_{0}'.format(reviewer_id));

        if (typeof (mark_delete) === undefined) {
            mark_delete = false;
        }

        if (mark_delete === true) {
            if (reviewer) {
                // now delete the input
                $('#reviewer_{0} input'.format(reviewer_id)).remove();
                // mark as to-delete
                var obj = $('#reviewer_{0}_name'.format(reviewer_id));
                obj.addClass('to-delete');
                obj.css({"text-decoration": "line-through", "opacity": 0.5});
            }
        } else {
            $('#reviewer_{0}'.format(reviewer_id)).remove();
        }
    };

    this.reviewMemberEntry = function () {

    };

    this.addReviewMember = function (reviewer_obj, reasons, mandatory) {
        var id = reviewer_obj.user_id;
        var username = reviewer_obj.username;

        var reasons = reasons || [];
        var mandatory = mandatory || false;

        // register IDS to check if we don't have this ID already in
        var currentIds = [];

        $.each(self.$reviewMembers.find('.reviewer_entry'), function (index, value) {
            currentIds.push($(value).data('reviewerUserId'))
        })

        var userAllowedReview = function (userId) {
            var allowed = true;
            $.each(self.forbidReviewUsers, function (index, member_data) {
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
                alert(_gettext('User `{0}` already in reviewers').format(username));
            } else {
                var reviewerEntry = renderTemplate('reviewMemberEntry', {
                    'member': reviewer_obj,
                    'mandatory': mandatory,
                    'reasons': reasons,
                    'allowed_to_update': true,
                    'review_status': 'not_reviewed',
                    'review_status_label': _gettext('Not Reviewed'),
                    'user_group': reviewer_obj.user_group,
                    'create': true,
                    'rule_show': true,
                })
                $(self.$reviewMembers.selector).append(reviewerEntry);
                tooltipActivate();
            }
        }

    };

    this.updateReviewers = function (repo_name, pull_request_id) {
        var postData = $('#reviewers input').serialize();
        _updatePullRequest(repo_name, pull_request_id, postData);
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
 * Reviewer autocomplete
 */
var ReviewerAutoComplete = function(inputId) {
  $(inputId).autocomplete({
    serviceUrl: pyroutes.url('user_autocomplete_data'),
    minChars:2,
    maxHeight:400,
    deferRequestBy: 300, //miliseconds
    showNoSuggestionNotice: true,
    tabDisabled: true,
    autoSelectFirst: true,
    params: { user_id: templateContext.rhodecode_user.user_id, user_groups:true, user_groups_expand:true, skip_default_user:true },
    formatResult: autocompleteFormatResult,
    lookupFilter: autocompleteFilterResult,
    onSelect: function(element, data) {
        var mandatory = false;
        var reasons = [_gettext('added manually by "{0}"').format(templateContext.rhodecode_user.username)];

        // add whole user groups
        if (data.value_type == 'user_group') {
            reasons.push(_gettext('member of "{0}"').format(data.value_display));

            $.each(data.members, function(index, member_data) {
                var reviewer = member_data;
                reviewer['user_id'] = member_data['id'];
                reviewer['gravatar_link'] = member_data['icon_link'];
                reviewer['user_link'] = member_data['profile_link'];
                reviewer['rules'] = [];
                reviewersController.addReviewMember(reviewer, reasons, mandatory);
            })
        }
        // add single user
        else {
            var reviewer = data;
            reviewer['user_id'] = data['id'];
            reviewer['gravatar_link'] = data['icon_link'];
            reviewer['user_link'] = data['profile_link'];
            reviewer['rules'] = [];
            reviewersController.addReviewMember(reviewer, reasons, mandatory);
        }

      $(inputId).val('');
    }
  });
};


window.VersionController = function () {
    var self = this;
    this.$verSource = $('input[name=ver_source]');
    this.$verTarget = $('input[name=ver_target]');
    this.$showVersionDiff = $('#show-version-diff');

    this.adjustRadioSelectors = function (curNode) {
        var getVal = function (item) {
            if (item == 'latest') {
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

    setSelectors: function () {
        var self = this;
        self.editButton = $('#open_edit_reviewers');
        self.closeButton =$('#close_edit_reviewers');
        self.addButton = $('#add_reviewer');
        self.removeButtons = $('.reviewer_member_remove,.reviewer_member_mandatory_remove');
    },

    init: function (reviewRules, setReviewers) {
        var self = this;
        self.setSelectors();

        this.reviewRules = reviewRules;
        this.setReviewers = setReviewers;

        this.editButton.on('click', function (e) {
            self.edit();
        });
        this.closeButton.on('click', function (e) {
            self.close();
            self.renderReviewers();
        });

        self.renderReviewers();

    },

    renderReviewers: function () {

        $('#review_members').html('')
        $.each(this.setReviewers.reviewers, function (key, val) {
            var member = val;

            var entry = renderTemplate('reviewMemberEntry', {
                'member': member,
                'mandatory': member.mandatory,
                'reasons': member.reasons,
                'allowed_to_update': member.allowed_to_update,
                'review_status': member.review_status,
                'review_status_label': member.review_status_label,
                'user_group': member.user_group,
                'create': false
            });

            $('#review_members').append(entry)
        });
        tooltipActivate();

    },

    edit: function (event) {
        this.editButton.hide();
        this.closeButton.show();
        this.addButton.show();
        $(this.removeButtons.selector).css('visibility', 'visible');
        // review rules
        reviewersController.loadReviewRules(this.reviewRules);
    },

    close: function (event) {
        this.editButton.show();
        this.closeButton.hide();
        this.addButton.hide();
        $(this.removeButtons.selector).css('visibility', 'hidden');
        // hide review rules
        reviewersController.hideReviewRules()
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
    var data = {"comments[]": currentIDs};

    var $targetElem = $('.comments-content-table');
    $targetElem.css('opacity', 0.3);
    $targetElem.load(
        loadUrl, data, function (responseText, textStatus, jqXHR) {
            if (jqXHR.status !== 200) {
                return false;
            }
            var $counterElem = $('#comments-count');
            var newCount = $(responseText).data('counter');
            if (newCount !== undefined) {
                var callback = function () {
                    $counterElem.animate({'opacity': 1.00}, 200)
                    $counterElem.html(newCount);
                };
                $counterElem.animate({'opacity': 0.15}, 200, callback);
            }

            $targetElem.css('opacity', 1);
            tooltipActivate();
        }
    );
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

    var data = {"comments[]": currentIDs};
    var $targetElem = $('.todos-content-table');
    $targetElem.css('opacity', 0.3);
    $targetElem.load(
        loadUrl, data, function (responseText, textStatus, jqXHR) {
            if (jqXHR.status !== 200) {
                return false;
            }
            var $counterElem = $('#todos-count')
            var newCount = $(responseText).data('counter');
            if (newCount !== undefined) {
                var callback = function () {
                    $counterElem.animate({'opacity': 1.00}, 200)
                    $counterElem.html(newCount);
                };
                $counterElem.animate({'opacity': 0.15}, 200, callback);
            }

            $targetElem.css('opacity', 1);
            tooltipActivate();
        }
    );
}

window.refreshAllComments = function (version) {
    version = version || templateContext.pull_request_data.pull_request_version || '';

    refreshComments(version);
    refreshTODOs(version);
};
