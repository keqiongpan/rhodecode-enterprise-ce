// # Copyright (C) 2010-2017 RhodeCode GmbH
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

/**
 * Pull request reviewers
 */
var removeReviewMember = function(reviewer_id, mark_delete){
    var reviewer = $('#reviewer_{0}'.format(reviewer_id));

    if(typeof(mark_delete) === undefined){
        mark_delete = false;
    }

    if(mark_delete === true){
        if (reviewer){
            // mark as to-remove
            var obj = $('#reviewer_{0}_name'.format(reviewer_id));
            obj.addClass('to-delete');
            // now delete the input
            $('#reviewer_{0} input'.format(reviewer_id)).remove();
        }
    }
    else{
        $('#reviewer_{0}'.format(reviewer_id)).remove();
    }
};

var addReviewMember = function(id, fname, lname, nname, gravatar_link, reasons) {
    var members = $('#review_members').get(0);
    var reasons_html = '';
    var reasons_inputs = '';
    var reasons = reasons || [];
    if (reasons) {
        for (var i = 0; i < reasons.length; i++) {
            reasons_html += '<div class="reviewer_reason">- {0}</div>'.format(reasons[i]);
            reasons_inputs += '<input type="hidden" name="reason" value="' + escapeHtml(reasons[i]) + '">';
        }
    }
    var tmpl = '<li id="reviewer_{2}">'+
       '<input type="hidden" name="__start__" value="reviewer:mapping">'+
       '<div class="reviewer_status">'+
          '<div class="flag_status not_reviewed pull-left reviewer_member_status"></div>'+
       '</div>'+
      '<img alt="gravatar" class="gravatar" src="{0}"/>'+
      '<span class="reviewer_name user">{1}</span>'+
      reasons_html +
      '<input type="hidden" name="user_id" value="{2}">'+
       '<input type="hidden" name="__start__" value="reasons:sequence">'+
       '{3}'+
       '<input type="hidden" name="__end__" value="reasons:sequence">'+
      '<div class="reviewer_member_remove action_button" onclick="removeReviewMember({2})">' +
      '<i class="icon-remove-sign"></i>'+
        '</div>'+
    '</div>'+
    '<input type="hidden" name="__end__" value="reviewer:mapping">'+
    '</li>' ;

    var displayname = "{0} ({1} {2})".format(
            nname, escapeHtml(fname), escapeHtml(lname));
    var element = tmpl.format(gravatar_link,displayname,id,reasons_inputs);
    // check if we don't have this ID already in
    var ids = [];
    var _els = $('#review_members li').toArray();
    for (el in _els){
        ids.push(_els[el].id)
    }
    if(ids.indexOf('reviewer_'+id) == -1){
        // only add if it's not there
        members.innerHTML += element;
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
        window.location.reload();
    };
    ajaxPOST(url, postData, success);
};

var updateReviewers = function(reviewers_ids, repo_name, pull_request_id){
    if (reviewers_ids === undefined){
      var postData = '_method=put&' + $('#reviewers input').serialize();
      _updatePullRequest(repo_name, pull_request_id, postData);
    }
};

/**
 * PULL REQUEST reject & close
 */
var closePullRequest = function(repo_name, pull_request_id) {
    var postData = {
        '_method': 'put',
        'close_pull_request': true};
    _updatePullRequest(repo_name, pull_request_id, postData);
};

/**
 * PULL REQUEST update commits
 */
var updateCommits = function(repo_name, pull_request_id) {
    var postData = {
        '_method': 'put',
        'update_commits': true};
    _updatePullRequest(repo_name, pull_request_id, postData);
};


/**
 * PULL REQUEST edit info
 */
var editPullRequest = function(repo_name, pull_request_id, title, description) {
    var url = pyroutes.url(
        'pullrequest_update',
        {"repo_name": repo_name, "pull_request_id": pull_request_id});

    var postData = {
        '_method': 'put',
        'title': title,
        'description': description,
        'edit_pull_request': true,
        'csrf_token': CSRF_TOKEN
    };
    var success = function(o) {
        window.location.reload();
    };
    ajaxPOST(url, postData, success);
};

var initPullRequestsCodeMirror = function (textAreaId) {
    var ta = $(textAreaId).get(0);
    var initialHeight = '100px';

    // default options
    var codeMirrorOptions = {
        mode: "text",
        lineNumbers: false,
        indentUnit: 4,
        theme: 'rc-input'
    };

    var codeMirrorInstance = CodeMirror.fromTextArea(ta, codeMirrorOptions);
    // marker for manually set description
    codeMirrorInstance._userDefinedDesc = false;
    codeMirrorInstance.setSize(null, initialHeight);
    codeMirrorInstance.on("change", function(instance, changeObj) {
        var height = initialHeight;
        var lines = instance.lineCount();
        if (lines > 6 && lines < 20) {
            height = "auto"
        }
        else if (lines >= 20) {
            height = 20 * 15;
        }
        instance.setSize(null, height);

        // detect if the change was trigger by auto desc, or user input
        changeOrigin = changeObj.origin;

        if (changeOrigin === "setValue") {
            cmLog.debug('Change triggered by setValue');
        }
        else {
            cmLog.debug('user triggered change !');
            // set special marker to indicate user has created an input.
            instance._userDefinedDesc = true;
        }

    });

    return codeMirrorInstance
};

/**
 * Reviewer autocomplete
 */
var ReviewerAutoComplete = function(input_id) {
  $('#'+input_id).autocomplete({
    serviceUrl: pyroutes.url('user_autocomplete_data'),
    minChars:2,
    maxHeight:400,
    deferRequestBy: 300, //miliseconds
    showNoSuggestionNotice: true,
    tabDisabled: true,
    autoSelectFirst: true,
    formatResult: autocompleteFormatResult,
    lookupFilter: autocompleteFilterResult,
    onSelect: function(suggestion, data){
      var msg = _gettext('added manually by "{0}"');
      var reasons = [msg.format(templateContext.rhodecode_user.username)];
      addReviewMember(data.id, data.first_name, data.last_name,
                      data.username, data.icon_link, reasons);
      $('#'+input_id).val('');
    }
  });
};


VersionController = function () {
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
    }

};