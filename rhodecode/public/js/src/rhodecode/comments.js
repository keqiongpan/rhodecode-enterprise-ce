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

var firefoxAnchorFix = function() {
  // hack to make anchor links behave properly on firefox, in our inline
  // comments generation when comments are injected firefox is misbehaving
  // when jumping to anchor links
  if (location.href.indexOf('#') > -1) {
    location.href += '';
  }
};

var linkifyComments = function(comments) {
  var firstCommentId = null;
  if (comments) {
      firstCommentId = $(comments[0]).data('comment-id');
  }

  if (firstCommentId){
    $('#inline-comments-counter').attr('href', '#comment-' + firstCommentId);
  }
};

var bindToggleButtons = function() {
  $('.comment-toggle').on('click', function() {
        $(this).parent().nextUntil('tr.line').toggle('inline-comments');
  });
};



var _submitAjaxPOST = function(url, postData, successHandler, failHandler) {
    failHandler = failHandler || function() {};
    postData = toQueryString(postData);
    var request = $.ajax({
        url: url,
        type: 'POST',
        data: postData,
        headers: {'X-PARTIAL-XHR': true}
    })
    .done(function (data) {
        successHandler(data);
    })
    .fail(function (data, textStatus, errorThrown) {
        failHandler(data, textStatus, errorThrown)
    });
    return request;
};




/* Comment form for main and inline comments */
(function(mod) {

    if (typeof exports == "object" && typeof module == "object") {
        // CommonJS
        module.exports = mod();
    }
    else {
        // Plain browser env
        (this || window).CommentForm = mod();
    }

})(function() {
    "use strict";

    function CommentForm(formElement, commitId, pullRequestId, lineNo, initAutocompleteActions, resolvesCommentId, edit, comment_id) {

        if (!(this instanceof CommentForm)) {
            return new CommentForm(formElement, commitId, pullRequestId, lineNo, initAutocompleteActions, resolvesCommentId, edit, comment_id);
        }

        // bind the element instance to our Form
        $(formElement).get(0).CommentForm = this;

        this.withLineNo = function(selector) {
            var lineNo = this.lineNo;
            if (lineNo === undefined) {
                return selector
            } else {
                return selector + '_' + lineNo;
            }
        };

        this.commitId = commitId;
        this.pullRequestId = pullRequestId;
        this.lineNo = lineNo;
        this.initAutocompleteActions = initAutocompleteActions;

        this.previewButton = this.withLineNo('#preview-btn');
        this.previewContainer = this.withLineNo('#preview-container');

        this.previewBoxSelector = this.withLineNo('#preview-box');

        this.editButton = this.withLineNo('#edit-btn');
        this.editContainer = this.withLineNo('#edit-container');
        this.cancelButton = this.withLineNo('#cancel-btn');
        this.commentType = this.withLineNo('#comment_type');

        this.resolvesId = null;
        this.resolvesActionId = null;

        this.closesPr = '#close_pull_request';

        this.cmBox = this.withLineNo('#text');
        this.cm = initCommentBoxCodeMirror(this, this.cmBox, this.initAutocompleteActions);

        this.statusChange = this.withLineNo('#change_status');

        this.submitForm = formElement;

        this.submitButton = $(this.submitForm).find('.submit-comment-action');
        this.submitButtonText = this.submitButton.val();

        this.submitDraftButton = $(this.submitForm).find('.submit-draft-action');
        this.submitDraftButtonText = this.submitDraftButton.val();

        this.previewUrl = pyroutes.url('repo_commit_comment_preview',
            {'repo_name': templateContext.repo_name,
             'commit_id': templateContext.commit_data.commit_id});

        if (edit){
            this.submitDraftButton.hide();
            this.submitButtonText = _gettext('Update Comment');
            $(this.commentType).prop('disabled', true);
            $(this.commentType).addClass('disabled');
            var editInfo =
                '';
            $(editInfo).insertBefore($(this.editButton).parent());
        }

        if (resolvesCommentId){
            this.resolvesId = '#resolve_comment_{0}'.format(resolvesCommentId);
            this.resolvesActionId = '#resolve_comment_action_{0}'.format(resolvesCommentId);
            $(this.commentType).prop('disabled', true);
            $(this.commentType).addClass('disabled');

            // disable select
            setTimeout(function() {
                $(self.statusChange).select2('readonly', true);
            }, 10);

            var resolvedInfo = (
                '<li class="resolve-action">' +
                '<input type="hidden" id="resolve_comment_{0}" name="resolve_comment_{0}" value="{0}">' +
                '<button id="resolve_comment_action_{0}" class="resolve-text btn btn-sm" onclick="return Rhodecode.comments.submitResolution({0})">{1} #{0}</button>' +
                '</li>'
            ).format(resolvesCommentId, _gettext('resolve comment'));
            $(resolvedInfo).insertAfter($(this.commentType).parent());
        }

        // based on commitId, or pullRequestId decide where do we submit
        // out data
        if (this.commitId){
            var pyurl = 'repo_commit_comment_create';
            if(edit){
                pyurl = 'repo_commit_comment_edit';
            }
            this.submitUrl = pyroutes.url(pyurl,
                {'repo_name': templateContext.repo_name,
                 'commit_id': this.commitId,
                 'comment_id': comment_id});
            this.selfUrl = pyroutes.url('repo_commit',
                {'repo_name': templateContext.repo_name,
                 'commit_id': this.commitId});

        } else if (this.pullRequestId) {
            var pyurl = 'pullrequest_comment_create';
            if(edit){
                pyurl = 'pullrequest_comment_edit';
            }
            this.submitUrl = pyroutes.url(pyurl,
                {'repo_name': templateContext.repo_name,
                 'pull_request_id': this.pullRequestId,
                 'comment_id': comment_id});
            this.selfUrl = pyroutes.url('pullrequest_show',
                {'repo_name': templateContext.repo_name,
                 'pull_request_id': this.pullRequestId});

        } else {
            throw new Error(
                'CommentForm requires pullRequestId, or commitId to be specified.')
        }

        // FUNCTIONS and helpers
        var self = this;

        this.isInline = function(){
            return this.lineNo && this.lineNo != 'general';
        };

        this.getCmInstance = function(){
            return this.cm
        };

        this.setPlaceholder = function(placeholder) {
            var cm = this.getCmInstance();
            if (cm){
                cm.setOption('placeholder', placeholder);
            }
        };

        this.getCommentStatus = function() {
          return $(this.submitForm).find(this.statusChange).val();
        };

        this.getCommentType = function() {
          return $(this.submitForm).find(this.commentType).val();
        };

        this.getDraftState = function () {
            var submitterElem = $(this.submitForm).find('input[type="submit"].submitter');
            var data = $(submitterElem).data('isDraft');
            return data
        }

        this.getResolvesId = function() {
            return $(this.submitForm).find(this.resolvesId).val() || null;
        };

        this.getClosePr = function() {
            return $(this.submitForm).find(this.closesPr).val() || null;
        };

        this.markCommentResolved = function(resolvedCommentId){
            $('#comment-label-{0}'.format(resolvedCommentId)).find('.resolved').show();
            $('#comment-label-{0}'.format(resolvedCommentId)).find('.resolve').hide();
        };

        this.isAllowedToSubmit = function() {
            var commentDisabled = $(this.submitButton).prop('disabled');
            var draftDisabled = $(this.submitDraftButton).prop('disabled');
            return !commentDisabled && !draftDisabled;
        };

        this.initStatusChangeSelector = function(){
            var formatChangeStatus = function(state, escapeMarkup) {
                var originalOption = state.element;
                var tmpl = '<i class="icon-circle review-status-{0}"></i><span>{1}</span>'.format($(originalOption).data('status'), escapeMarkup(state.text));
                return tmpl
            };
            var formatResult = function(result, container, query, escapeMarkup) {
                return formatChangeStatus(result, escapeMarkup);
            };

            var formatSelection = function(data, container, escapeMarkup) {
                return formatChangeStatus(data, escapeMarkup);
            };

            $(this.submitForm).find(this.statusChange).select2({
                placeholder: _gettext('Status Review'),
                formatResult: formatResult,
                formatSelection: formatSelection,
                containerCssClass: "drop-menu status_box_menu",
                dropdownCssClass: "drop-menu-dropdown",
                dropdownAutoWidth: true,
                minimumResultsForSearch: -1
            });

            $(this.submitForm).find(this.statusChange).on('change', function() {
                var status = self.getCommentStatus();

                if (status && !self.isInline()) {
                    $(self.submitButton).prop('disabled', false);
                    $(self.submitDraftButton).prop('disabled', false);
                }

                var placeholderText = _gettext('Comment text will be set automatically based on currently selected status ({0}) ...').format(status);
                self.setPlaceholder(placeholderText)
            })
        };

        // reset the comment form into it's original state
        this.resetCommentFormState = function(content) {
            content = content || '';

            $(this.editContainer).show();
            $(this.editButton).parent().addClass('active');

            $(this.previewContainer).hide();
            $(this.previewButton).parent().removeClass('active');

            this.setActionButtonsDisabled(true);
            self.cm.setValue(content);
            self.cm.setOption("readOnly", false);

            if (this.resolvesId) {
                // destroy the resolve action
                $(this.resolvesId).parent().remove();
            }
            // reset closingPR flag
            $('.close-pr-input').remove();

            $(this.statusChange).select2('readonly', false);
        };

        this.globalSubmitSuccessCallback = function(comment){
            // default behaviour is to call GLOBAL hook, if it's registered.
            if (window.commentFormGlobalSubmitSuccessCallback !== undefined){
                commentFormGlobalSubmitSuccessCallback(comment);
            }
        };

        this.submitAjaxPOST = function(url, postData, successHandler, failHandler) {
            return _submitAjaxPOST(url, postData, successHandler, failHandler);
        };

        // overwrite a submitHandler, we need to do it for inline comments
        this.setHandleFormSubmit = function(callback) {
            this.handleFormSubmit = callback;
        };

        // overwrite a submitSuccessHandler
        this.setGlobalSubmitSuccessCallback = function(callback) {
            this.globalSubmitSuccessCallback = callback;
        };

        // default handler for for submit for main comments
        this.handleFormSubmit = function() {
            var text = self.cm.getValue();
            var status = self.getCommentStatus();
            var commentType = self.getCommentType();
            var isDraft = self.getDraftState();
            var resolvesCommentId = self.getResolvesId();
            var closePullRequest = self.getClosePr();

            if (text === "" && !status) {
                return;
            }

            var excludeCancelBtn = false;
            var submitEvent = true;
            self.setActionButtonsDisabled(true, excludeCancelBtn, submitEvent);
            self.cm.setOption("readOnly", true);

            var postData = {
                'text': text,
                'changeset_status': status,
                'comment_type': commentType,
                'csrf_token': CSRF_TOKEN
            };

            if (resolvesCommentId) {
                postData['resolves_comment_id'] = resolvesCommentId;
            }

            if (closePullRequest) {
                postData['close_pull_request'] = true;
            }

            // submitSuccess for general comments
            var submitSuccessCallback = function(json_data) {
                // reload page if we change status for single commit.
                if (status && self.commitId) {
                    location.reload(true);
                } else {
                    // inject newly created comments, json_data is {<comment_id>: {}}
                    self.attachGeneralComment(json_data)

                    self.resetCommentFormState();
                    timeagoActivate();
                    tooltipActivate();

                    // mark visually which comment was resolved
                    if (resolvesCommentId) {
                        self.markCommentResolved(resolvesCommentId);
                    }
                }

                // run global callback on submit
                self.globalSubmitSuccessCallback({draft: isDraft, comment_id: comment_id});

            };
            var submitFailCallback = function(jqXHR, textStatus, errorThrown) {
                var prefix = "Error while submitting comment.\n"
                var message = formatErrorMessage(jqXHR, textStatus, errorThrown, prefix);
                ajaxErrorSwal(message);
                self.resetCommentFormState(text);
            };
            self.submitAjaxPOST(
                self.submitUrl, postData, submitSuccessCallback, submitFailCallback);
        };

        this.previewSuccessCallback = function(o) {
            $(self.previewBoxSelector).html(o);
            $(self.previewBoxSelector).removeClass('unloaded');

            // swap buttons, making preview active
            $(self.previewButton).parent().addClass('active');
            $(self.editButton).parent().removeClass('active');

            // unlock buttons
            self.setActionButtonsDisabled(false);
        };

        this.setActionButtonsDisabled = function(state, excludeCancelBtn, submitEvent) {
            excludeCancelBtn = excludeCancelBtn || false;
            submitEvent = submitEvent || false;

            $(this.editButton).prop('disabled', state);
            $(this.previewButton).prop('disabled', state);

            if (!excludeCancelBtn) {
                $(this.cancelButton).prop('disabled', state);
            }

            var submitState = state;
            if (!submitEvent && this.getCommentStatus() && !self.isInline()) {
                // if the value of commit review status is set, we allow
                // submit button, but only on Main form, isInline means inline
                submitState = false
            }

            $(this.submitButton).prop('disabled', submitState);
            $(this.submitDraftButton).prop('disabled', submitState);

            if (submitEvent) {
              var isDraft = self.getDraftState();

              if (isDraft) {
                $(this.submitDraftButton).val(_gettext('Saving Draft...'));
              }  else {
                $(this.submitButton).val(_gettext('Submitting...'));
              }

            } else {
              $(this.submitButton).val(this.submitButtonText);
              $(this.submitDraftButton).val(this.submitDraftButtonText);
            }

        };

        // lock preview/edit/submit buttons on load, but exclude cancel button
        var excludeCancelBtn = true;
        this.setActionButtonsDisabled(true, excludeCancelBtn);

        // anonymous users don't have access to initialized CM instance
        if (this.cm !== undefined){
            this.cm.on('change', function(cMirror) {
                if (cMirror.getValue() === "") {
                    self.setActionButtonsDisabled(true, excludeCancelBtn)
                } else {
                    self.setActionButtonsDisabled(false, excludeCancelBtn)
                }
            });
        }

        $(this.editButton).on('click', function(e) {
            e.preventDefault();

            $(self.previewButton).parent().removeClass('active');
            $(self.previewContainer).hide();

            $(self.editButton).parent().addClass('active');
            $(self.editContainer).show();

        });

        $(this.previewButton).on('click', function(e) {
            e.preventDefault();
            var text = self.cm.getValue();

            if (text === "") {
                return;
            }

            var postData = {
                'text': text,
                'renderer': templateContext.visual.default_renderer,
                'csrf_token': CSRF_TOKEN
            };

            // lock ALL buttons on preview
            self.setActionButtonsDisabled(true);

            $(self.previewBoxSelector).addClass('unloaded');
            $(self.previewBoxSelector).html(_gettext('Loading ...'));

            $(self.editContainer).hide();
            $(self.previewContainer).show();

            // by default we reset state of comment preserving the text
            var previewFailCallback = function(jqXHR, textStatus, errorThrown) {
                var prefix = "Error while preview of comment.\n"
                var message = formatErrorMessage(jqXHR, textStatus, errorThrown, prefix);
                ajaxErrorSwal(message);

                self.resetCommentFormState(text)
            };
            self.submitAjaxPOST(
                self.previewUrl, postData, self.previewSuccessCallback,
                previewFailCallback);

            $(self.previewButton).parent().addClass('active');
            $(self.editButton).parent().removeClass('active');
        });

        $(this.submitForm).submit(function(e) {
            e.preventDefault();
            var allowedToSubmit = self.isAllowedToSubmit();
            if (!allowedToSubmit){
               return false;
            }

            self.handleFormSubmit();
        });

    }

    return CommentForm;
});

/* selector for comment versions */
var initVersionSelector = function(selector, initialData) {

    var formatResult = function(result, container, query, escapeMarkup) {

        return renderTemplate('commentVersion', {
            show_disabled: true,
            version: result.comment_version,
            user_name: result.comment_author_username,
            gravatar_url: result.comment_author_gravatar,
            size: 16,
            timeago_component: result.comment_created_on,
        })
    };

    $(selector).select2({
        placeholder: "Edited",
        containerCssClass: "drop-menu-comment-history",
        dropdownCssClass: "drop-menu-dropdown",
        dropdownAutoWidth: true,
        minimumResultsForSearch: -1,
        data: initialData,
        formatResult: formatResult,
    });

    $(selector).on('select2-selecting', function (e) {
        // hide the mast as we later do preventDefault()
        $("#select2-drop-mask").click();
        e.preventDefault();
        e.choice.action();
    });

    $(selector).on("select2-open", function() {
        timeagoActivate();
    });
};

/* comments controller */
var CommentsController = function() {
  var mainComment = '#text';
  var self = this;

  this.showVersion = function (comment_id, comment_history_id) {

       var historyViewUrl = pyroutes.url(
           'repo_commit_comment_history_view',
           {
               'repo_name': templateContext.repo_name,
               'commit_id': comment_id,
               'comment_history_id': comment_history_id,
           }
       );
       successRenderCommit = function (data) {
           SwalNoAnimation.fire({
               html: data,
               title: '',
           });
       };
       failRenderCommit = function () {
           SwalNoAnimation.fire({
               html: 'Error while loading comment history',
               title: '',
           });
       };
       _submitAjaxPOST(
           historyViewUrl, {'csrf_token': CSRF_TOKEN},
           successRenderCommit,
           failRenderCommit
       );
  };

  this.getLineNumber = function(node) {
      var $node = $(node);
      var lineNo = $node.closest('td').attr('data-line-no');
      if (lineNo === undefined && $node.data('commentInline')){
          lineNo = $node.data('commentLineNo')
      }

      return lineNo
  };

  this.scrollToComment = function(node, offset, outdated) {
    if (offset === undefined) {
      offset = 0;
    }
    var outdated = outdated || false;
    var klass = outdated ? 'div.comment-outdated' : 'div.comment-current';

    if (!node) {
      node = $('.comment-selected');
      if (!node.length) {
        node = $('comment-current')
      }
    }

    $wrapper = $(node).closest('div.comment');

    // show hidden comment when referenced.
    if (!$wrapper.is(':visible')){
        $wrapper.show();
    }

    $comment = $(node).closest(klass);
    $comments = $(klass);

    $('.comment-selected').removeClass('comment-selected');

    var nextIdx = $(klass).index($comment) + offset;
    if (nextIdx >= $comments.length) {
      nextIdx = 0;
    }
    var $next = $(klass).eq(nextIdx);

    var $cb = $next.closest('.cb');
    $cb.removeClass('cb-collapsed');

    var $filediffCollapseState = $cb.closest('.filediff').prev();
    $filediffCollapseState.prop('checked', false);
    $next.addClass('comment-selected');
    scrollToElement($next);
    return false;
  };

  this.nextComment = function(node) {
    return self.scrollToComment(node, 1);
  };

  this.prevComment = function(node) {
    return self.scrollToComment(node, -1);
  };

  this.nextOutdatedComment = function(node) {
    return self.scrollToComment(node, 1, true);
  };

  this.prevOutdatedComment = function(node) {
    return self.scrollToComment(node, -1, true);
  };

  this.cancelComment = function (node) {
      var $node = $(node);
      var edit = $(this).attr('edit');
      var $inlineComments = $node.closest('div.inline-comments');

      if (edit) {
          var $general_comments = null;
          if (!$inlineComments.length) {
              $general_comments = $('#comments');
              var $comment = $general_comments.parent().find('div.comment:hidden');
              // show hidden general comment form
              $('#cb-comment-general-form-placeholder').show();
          } else {
              var $comment = $inlineComments.find('div.comment:hidden');
          }
          $comment.show();
      }
      var $replyWrapper = $node.closest('.comment-inline-form').closest('.reply-thread-container-wrapper')
      $replyWrapper.removeClass('comment-form-active');

      var lastComment = $inlineComments.find('.comment-inline').last();
      if ($(lastComment).hasClass('comment-outdated')) {
        $replyWrapper.hide();
      }

      $node.closest('.comment-inline-form').remove();
      return false;
  };

  this._deleteComment = function(node) {
      var $node = $(node);
      var $td = $node.closest('td');
      var $comment = $node.closest('.comment');
      var comment_id = $($comment).data('commentId');
      var isDraft = $($comment).data('commentDraft');

      var pullRequestId = templateContext.pull_request_data.pull_request_id;
      var commitId = templateContext.commit_data.commit_id;

      if (pullRequestId) {
          var url = pyroutes.url('pullrequest_comment_delete', {"comment_id": comment_id, "repo_name": templateContext.repo_name, "pull_request_id": pullRequestId})
      } else if (commitId) {
          var url = pyroutes.url('repo_commit_comment_delete', {"comment_id": comment_id, "repo_name": templateContext.repo_name, "commit_id": commitId})
      }

      var postData = {
        'csrf_token': CSRF_TOKEN
      };

      $comment.addClass('comment-deleting');
      $comment.hide('fast');

      var success = function(response) {
        $comment.remove();

        if (window.updateSticky !== undefined) {
            // potentially our comments change the active window size, so we
            // notify sticky elements
            updateSticky()
        }

        if (window.refreshAllComments !== undefined && !isDraft) {
          // if we have this handler, run it, and refresh all comments boxes
          refreshAllComments()
        }
        else if (window.refreshDraftComments !== undefined && isDraft) {
          // if we have this handler, run it, and refresh all comments boxes
          refreshDraftComments();
        }
        return false;
      };

      var failure = function(jqXHR, textStatus, errorThrown) {
        var prefix = "Error while deleting this comment.\n"
        var message = formatErrorMessage(jqXHR, textStatus, errorThrown, prefix);
        ajaxErrorSwal(message);

        $comment.show('fast');
        $comment.removeClass('comment-deleting');
        return false;
      };
      ajaxPOST(url, postData, success, failure);

  }

  this.deleteComment = function(node) {
    var $comment = $(node).closest('.comment');
    var comment_id = $comment.attr('data-comment-id');

    SwalNoAnimation.fire({
      title: 'Delete this comment?',
      icon: 'warning',
      showCancelButton: true,
      confirmButtonText: _gettext('Yes, delete comment #{0}!').format(comment_id),

    }).then(function(result) {
      if (result.value) {
        self._deleteComment(node);
      }
    })
  };

  this._finalizeDrafts = function(commentIds) {

    var pullRequestId = templateContext.pull_request_data.pull_request_id;
    var commitId = templateContext.commit_data.commit_id;

    if (pullRequestId) {
          var url = pyroutes.url('pullrequest_draft_comments_submit', {"repo_name": templateContext.repo_name, "pull_request_id": pullRequestId})
    } else if (commitId) {
          var url = pyroutes.url('commit_draft_comments_submit', {"repo_name": templateContext.repo_name, "commit_id": commitId})
    }

    // remove the drafts so we can lock them before submit.
    $.each(commentIds, function(idx, val){
        $('#comment-{0}'.format(val)).remove();
    })

    var postData = {'comments': commentIds, 'csrf_token': CSRF_TOKEN};

    var submitSuccessCallback = function(json_data) {
        self.attachInlineComment(json_data);

        if (window.refreshDraftComments !== undefined) {
          // if we have this handler, run it, and refresh all comments boxes
          refreshDraftComments()
        }

        return false;
    };

    ajaxPOST(url, postData, submitSuccessCallback)

  }

  this.finalizeDrafts = function(commentIds, callback) {

    SwalNoAnimation.fire({
      title: _ngettext('Submit {0} draft comment.', 'Submit {0} draft comments.', commentIds.length).format(commentIds.length),
      icon: 'warning',
      showCancelButton: true,
      confirmButtonText: _gettext('Yes'),

    }).then(function(result) {
      if (result.value) {
        if (callback !== undefined) {
            callback(result)
        }
        self._finalizeDrafts(commentIds);
      }
    })
  };

  this.toggleWideMode = function (node) {

      if ($('#content').hasClass('wrapper')) {
          $('#content').removeClass("wrapper");
          $('#content').addClass("wide-mode-wrapper");
          $(node).addClass('btn-success');
          return true
      } else {
          $('#content').removeClass("wide-mode-wrapper");
          $('#content').addClass("wrapper");
          $(node).removeClass('btn-success');
          return false
      }

  };

  /**
   * Turn off/on all comments in file diff
   */
  this.toggleDiffComments = function(node) {
    // Find closes filediff container
    var $filediff = $(node).closest('.filediff');
    if ($(node).hasClass('toggle-on')) {
        var show = false;
    } else if ($(node).hasClass('toggle-off')) {
        var show = true;
    }

    // Toggle each individual comment block, so we can un-toggle single ones
    $.each($filediff.find('.toggle-comment-action'), function(idx, val) {
        self.toggleLineComments($(val), show)
    })

    // since we change the height of the diff container that has anchor points for upper
    // sticky header, we need to tell it to re-calculate those
    if (window.updateSticky !== undefined) {
        // potentially our comments change the active window size, so we
        // notify sticky elements
        updateSticky()
    }

    return false;
  }

  this.toggleLineComments = function(node, show) {

    var trElem = $(node).closest('tr')

    if (show === true) {
        // mark outdated comments as visible before the toggle;
        $(trElem).find('.comment-outdated').show();
        $(trElem).removeClass('hide-line-comments');
    } else if (show === false) {
        $(trElem).find('.comment-outdated').hide();
        $(trElem).addClass('hide-line-comments');
    } else {
        // mark outdated comments as visible before the toggle;
        $(trElem).find('.comment-outdated').show();
        $(trElem).toggleClass('hide-line-comments');
    }

    // since we change the height of the diff container that has anchor points for upper
    // sticky header, we need to tell it to re-calculate those
    if (window.updateSticky !== undefined) {
        // potentially our comments change the active window size, so we
        // notify sticky elements
        updateSticky()
    }

  };

  this.createCommentForm = function(formElement, lineno, placeholderText, initAutocompleteActions, resolvesCommentId, edit, comment_id){
      var pullRequestId = templateContext.pull_request_data.pull_request_id;
      var commitId = templateContext.commit_data.commit_id;

      var commentForm = new CommentForm(
          formElement, commitId, pullRequestId, lineno, initAutocompleteActions, resolvesCommentId, edit, comment_id);
      var cm = commentForm.getCmInstance();

      if (resolvesCommentId){
        placeholderText = _gettext('Leave a resolution comment, or click resolve button to resolve TODO comment #{0}').format(resolvesCommentId);
      }

      setTimeout(function() {
          // callbacks
          if (cm !== undefined) {
              commentForm.setPlaceholder(placeholderText);
              if (commentForm.isInline()) {
                cm.focus();
                cm.refresh();
              }
          }
      }, 10);

      // trigger scrolldown to the resolve comment, since it might be away
      // from the clicked
      if (resolvesCommentId){
        var actionNode = $(commentForm.resolvesActionId).offset();

        setTimeout(function() {
            if (actionNode) {
                $('body, html').animate({scrollTop: actionNode.top}, 10);
            }
        }, 100);
      }

        // add dropzone support
        var insertAttachmentText = function (cm, attachmentName, attachmentStoreUrl, isRendered) {
            var renderer = templateContext.visual.default_renderer;
            if (renderer == 'rst') {
                var attachmentUrl = '`#{0} <{1}>`_'.format(attachmentName, attachmentStoreUrl);
                if (isRendered){
                    attachmentUrl = '\n.. image:: {0}'.format(attachmentStoreUrl);
                }
            } else if (renderer == 'markdown') {
                var attachmentUrl = '[{0}]({1})'.format(attachmentName, attachmentStoreUrl);
                if (isRendered){
                    attachmentUrl = '!' + attachmentUrl;
                }
            } else {
                var attachmentUrl = '{}'.format(attachmentStoreUrl);
            }
            cm.replaceRange(attachmentUrl+'\n', CodeMirror.Pos(cm.lastLine()));

            return false;
        };

        //see: https://www.dropzonejs.com/#configuration
        var storeUrl = pyroutes.url('repo_commit_comment_attachment_upload',
            {'repo_name': templateContext.repo_name,
                     'commit_id': templateContext.commit_data.commit_id})

        var previewTmpl = $(formElement).find('.comment-attachment-uploader-template').get(0);
        if (previewTmpl !== undefined){
            var selectLink = $(formElement).find('.pick-attachment').get(0);
            $(formElement).find('.comment-attachment-uploader').dropzone({
                url: storeUrl,
                headers: {"X-CSRF-Token": CSRF_TOKEN},
                paramName: function () {
                    return "attachment"
                }, // The name that will be used to transfer the file
                clickable: selectLink,
                parallelUploads: 1,
                maxFiles: 10,
                maxFilesize: templateContext.attachment_store.max_file_size_mb,
                uploadMultiple: false,
                autoProcessQueue: true, // if false queue will not be processed automatically.
                createImageThumbnails: false,
                previewTemplate: previewTmpl.innerHTML,

                accept: function (file, done) {
                    done();
                },
                init: function () {

                    this.on("sending", function (file, xhr, formData) {
                        $(formElement).find('.comment-attachment-uploader').find('.dropzone-text').hide();
                        $(formElement).find('.comment-attachment-uploader').find('.dropzone-upload').show();
                    });

                    this.on("success", function (file, response) {
                        $(formElement).find('.comment-attachment-uploader').find('.dropzone-text').show();
                        $(formElement).find('.comment-attachment-uploader').find('.dropzone-upload').hide();

                        var isRendered = false;
                        var ext = file.name.split('.').pop();
                        var imageExts = templateContext.attachment_store.image_ext;
                        if (imageExts.indexOf(ext) !== -1){
                            isRendered = true;
                        }

                        insertAttachmentText(cm, file.name, response.repo_fqn_access_path, isRendered)
                    });

                    this.on("error", function (file, errorMessage, xhr) {
                        $(formElement).find('.comment-attachment-uploader').find('.dropzone-upload').hide();

                        var error = null;

                        if (xhr !== undefined){
                            var httpStatus = xhr.status + " " + xhr.statusText;
                            if (xhr !== undefined && xhr.status >= 500) {
                                error = httpStatus;
                            }
                        }

                        if (error === null) {
                            error = errorMessage.error || errorMessage || httpStatus;
                        }
                        $(file.previewElement).find('.dz-error-message').html('ERROR: {0}'.format(error));

                    });
                }
            });
        }
      return commentForm;
  };

  this.createGeneralComment = function (lineNo, placeholderText, resolvesCommentId) {

      var tmpl = $('#cb-comment-general-form-template').html();
      tmpl = tmpl.format(null, 'general');
      var $form = $(tmpl);

      var $formPlaceholder = $('#cb-comment-general-form-placeholder');
      var curForm = $formPlaceholder.find('form');
      if (curForm){
          curForm.remove();
      }
      $formPlaceholder.append($form);

      var _form = $($form[0]);
      var autocompleteActions = ['approve', 'reject', 'as_note', 'as_todo'];
      var edit = false;
      var comment_id = null;
      var commentForm = this.createCommentForm(
          _form, lineNo, placeholderText, autocompleteActions, resolvesCommentId, edit, comment_id);
      commentForm.initStatusChangeSelector();

      return commentForm;
  };

  this.editComment = function(node, line_no, f_path) {
      self.edit = true;
      var $node = $(node);
      var $td = $node.closest('td');

      var $comment = $(node).closest('.comment');
      var comment_id = $($comment).data('commentId');
      var isDraft = $($comment).data('commentDraft');
      var $editForm = null

      var $comments = $node.closest('div.inline-comments');
      var $general_comments = null;

      if($comments.length){
          // inline comments setup
          $editForm = $comments.find('.comment-inline-form');
          line_no = self.getLineNumber(node)
      }
      else{
          // general comments setup
          $comments = $('#comments');
          $editForm = $comments.find('.comment-inline-form');
          line_no = $comment[0].id
          $('#cb-comment-general-form-placeholder').hide();
      }

      if ($editForm.length === 0) {

          // unhide all comments if they are hidden for a proper REPLY mode
          var $filediff = $node.closest('.filediff');
          $filediff.removeClass('hide-comments');

          $editForm = self.createNewFormWrapper(f_path, line_no);
          if(f_path && line_no) {
            $editForm.addClass('comment-inline-form-edit')
          }

          $comment.after($editForm)

          var _form = $($editForm[0]).find('form');
          var autocompleteActions = ['as_note',];
          var commentForm = this.createCommentForm(
              _form, line_no, '', autocompleteActions, resolvesCommentId,
              this.edit, comment_id);
          var old_comment_text_binary = $comment.attr('data-comment-text');
          var old_comment_text = b64DecodeUnicode(old_comment_text_binary);
          commentForm.cm.setValue(old_comment_text);
          $comment.hide();
          tooltipActivate();

           // set a CUSTOM submit handler for inline comment edit action.
           commentForm.setHandleFormSubmit(function(o) {
              var text = commentForm.cm.getValue();
              var commentType = commentForm.getCommentType();

              if (text === "") {
                return;
              }

              if (old_comment_text == text) {
                  SwalNoAnimation.fire({
                      title: 'Unable to edit comment',
                      html: _gettext('Comment body was not changed.'),
                  });
                  return;
              }
              var excludeCancelBtn = false;
              var submitEvent = true;
              commentForm.setActionButtonsDisabled(true, excludeCancelBtn, submitEvent);
              commentForm.cm.setOption("readOnly", true);

              // Read last version known
              var versionSelector = $('#comment_versions_{0}'.format(comment_id));
              var version = versionSelector.data('lastVersion');

              if (!version) {
                version = 0;
              }

              var postData = {
                  'text': text,
                  'f_path': f_path,
                  'line': line_no,
                  'comment_type': commentType,
                  'draft': isDraft,
                  'version': version,
                  'csrf_token': CSRF_TOKEN
              };

              var submitSuccessCallback = function(json_data) {
                $editForm.remove();
                $comment.show();
                var postData = {
                    'text': text,
                    'renderer': $comment.attr('data-comment-renderer'),
                    'csrf_token': CSRF_TOKEN
                };

                /* Inject new edited version selector */
                var updateCommentVersionDropDown = function () {
                    var versionSelectId = '#comment_versions_'+comment_id;
                    var preLoadVersionData = [
                        {
                            id: json_data['comment_version'],
                            text: "v{0}".format(json_data['comment_version']),
                            action: function () {
                                Rhodecode.comments.showVersion(
                                    json_data['comment_id'],
                                    json_data['comment_history_id']
                                )
                            },
                            comment_version: json_data['comment_version'],
                            comment_author_username: json_data['comment_author_username'],
                            comment_author_gravatar: json_data['comment_author_gravatar'],
                            comment_created_on: json_data['comment_created_on'],
                        },
                    ]


                    if ($(versionSelectId).data('select2')) {
                        var oldData = $(versionSelectId).data('select2').opts.data.results;
                        $(versionSelectId).select2("destroy");
                        preLoadVersionData = oldData.concat(preLoadVersionData)
                    }

                    initVersionSelector(versionSelectId, {results: preLoadVersionData});

                    $comment.attr('data-comment-text', utf8ToB64(text));

                    var versionSelector = $('#comment_versions_'+comment_id);

                    // set lastVersion so we know our last edit version
                    versionSelector.data('lastVersion', json_data['comment_version'])
                    versionSelector.parent().show();
                }
                updateCommentVersionDropDown();

                // by default we reset state of comment preserving the text
                var failRenderCommit = function(jqXHR, textStatus, errorThrown) {
                    var prefix = "Error while editing this comment.\n"
                    var message = formatErrorMessage(jqXHR, textStatus, errorThrown, prefix);
                    ajaxErrorSwal(message);
                };

                var successRenderCommit = function(o){
                    $comment.show();
                    $comment[0].lastElementChild.innerHTML = o;
                };

                var previewUrl = pyroutes.url(
                    'repo_commit_comment_preview',
             {'repo_name': templateContext.repo_name,
                    'commit_id': templateContext.commit_data.commit_id});

                _submitAjaxPOST(
                    previewUrl, postData, successRenderCommit, failRenderCommit
                );

                try {
                  var html = json_data.rendered_text;
                  var lineno = json_data.line_no;
                  var target_id = json_data.target_id;

                  $comments.find('.cb-comment-add-button').before(html);

                 //  run global callback on submit
                  commentForm.globalSubmitSuccessCallback({draft: isDraft, comment_id: comment_id});

                } catch (e) {
                  console.error(e);
                }

                // re trigger the linkification of next/prev navigation
                linkifyComments($('.inline-comment-injected'));
                timeagoActivate();
                tooltipActivate();

                if (window.updateSticky !== undefined) {
                    // potentially our comments change the active window size, so we
                    // notify sticky elements
                    updateSticky()
                }

                if (window.refreshAllComments !== undefined && !isDraft) {
                      // if we have this handler, run it, and refresh all comments boxes
                      refreshAllComments()
                }
               else if (window.refreshDraftComments !== undefined && isDraft) {
                  // if we have this handler, run it, and refresh all comments boxes
                  refreshDraftComments();
               }

                commentForm.setActionButtonsDisabled(false);

              };

              var submitFailCallback = function(jqXHR, textStatus, errorThrown) {
                  var prefix = "Error while editing comment.\n"
                  var message = formatErrorMessage(jqXHR, textStatus, errorThrown, prefix);
                  if (jqXHR.status == 409){
                    message = 'This comment was probably changed somewhere else. Please reload the content of this comment.'
                    ajaxErrorSwal(message, 'Comment version mismatch.');
                  } else {
                    ajaxErrorSwal(message);
                  }

                  commentForm.resetCommentFormState(text)
              };
              commentForm.submitAjaxPOST(
                  commentForm.submitUrl, postData,
                  submitSuccessCallback,
                  submitFailCallback);
            });
      }

      $editForm.addClass('comment-inline-form-open');
  };

  this.attachComment = function(json_data) {
    var self = this;
    $.each(json_data, function(idx, val) {
        var json_data_elem = [val]
        var isInline = val.comment_f_path && val.comment_lineno

        if (isInline) {
            self.attachInlineComment(json_data_elem)
        }  else {
            self.attachGeneralComment(json_data_elem)
        }
    })

  }

  this.attachGeneralComment = function(json_data) {
    $.each(json_data, function(idx, val) {
        $('#injected_page_comments').append(val.rendered_text);
    })
  }

  this.attachInlineComment = function(json_data) {

    $.each(json_data, function (idx, val) {
        var line_qry = '*[data-line-no="{0}"]'.format(val.line_no);
        var html = val.rendered_text;
        var $inlineComments = $('#' + val.target_id)
                .find(line_qry)
                .find('.inline-comments');

        var lastComment = $inlineComments.find('.comment-inline').last();

        if (lastComment.length === 0) {
            // first comment, we append simply
            $inlineComments.find('.reply-thread-container-wrapper').before(html);
        } else {
            $(lastComment).after(html)
        }

    })

  };

  this.createNewFormWrapper = function(f_path, line_no) {
      // create a new reply HTML form from template
      var tmpl = $('#cb-comment-inline-form-template').html();
      tmpl = tmpl.format(escapeHtml(f_path), line_no);
      return $(tmpl);
  }

  this.createComment = function(node, f_path, line_no, resolutionComment) {
      self.edit = false;
      var $node = $(node);
      var $td = $node.closest('td');
      var resolvesCommentId = resolutionComment || null;

      var $replyForm = $td.find('.comment-inline-form');

      // if form isn't existing, we're generating a new one and injecting it.
      if ($replyForm.length === 0) {

          // unhide/expand all comments if they are hidden for a proper REPLY mode
          self.toggleLineComments($node, true);

          $replyForm = self.createNewFormWrapper(f_path, line_no);

          var $comments = $td.find('.inline-comments');

          // There aren't any comments, we init the `.inline-comments` with `reply-thread-container` first
          if ($comments.length===0) {
            var replBtn = '<button class="cb-comment-add-button" onclick="return Rhodecode.comments.createComment(this, \'{0}\', \'{1}\', null)">Reply...</button>'.format(f_path, line_no)
            var $reply_container = $('#cb-comments-inline-container-template')
            $reply_container.find('button.cb-comment-add-button').replaceWith(replBtn);
            $td.append($($reply_container).html());
          }

          // default comment button exists, so we prepend the form for leaving initial comment
          $td.find('.cb-comment-add-button').before($replyForm);
          // set marker, that we have a open form
          var $replyWrapper = $td.find('.reply-thread-container-wrapper')
          $replyWrapper.addClass('comment-form-active');

          var lastComment = $comments.find('.comment-inline').last();
          if ($(lastComment).hasClass('comment-outdated')) {
            $replyWrapper.show();
          }

          var _form = $($replyForm[0]).find('form');
          var autocompleteActions = ['as_note', 'as_todo'];
          var comment_id=null;
          var placeholderText = _gettext('Leave a comment on file {0} line {1}.').format(f_path, line_no);
          var commentForm = self.createCommentForm(
              _form, line_no, placeholderText, autocompleteActions, resolvesCommentId,
              self.edit, comment_id);

          // set a CUSTOM submit handler for inline comments.
          commentForm.setHandleFormSubmit(function(o) {
            var text = commentForm.cm.getValue();
            var commentType = commentForm.getCommentType();
            var resolvesCommentId = commentForm.getResolvesId();
            var isDraft = commentForm.getDraftState();

            if (text === "") {
              return;
            }

            if (line_no === undefined) {
              alert('Error: unable to fetch line number for this inline comment !');
              return;
            }

            if (f_path === undefined) {
              alert('Error: unable to fetch file path for this inline comment !');
              return;
            }

            var excludeCancelBtn = false;
            var submitEvent = true;
            commentForm.setActionButtonsDisabled(true, excludeCancelBtn, submitEvent);
            commentForm.cm.setOption("readOnly", true);
            var postData = {
                'text': text,
                'f_path': f_path,
                'line': line_no,
                'comment_type': commentType,
                'draft': isDraft,
                'csrf_token': CSRF_TOKEN
            };
            if (resolvesCommentId){
                postData['resolves_comment_id'] = resolvesCommentId;
            }

            // submitSuccess for inline commits
            var submitSuccessCallback = function(json_data) {

                $replyForm.remove();
                $td.find('.reply-thread-container-wrapper').removeClass('comment-form-active');

                try {

                    // inject newly created comments, json_data is {<comment_id>: {}}
                    self.attachInlineComment(json_data)

                    //mark visually which comment was resolved
                    if (resolvesCommentId) {
                        commentForm.markCommentResolved(resolvesCommentId);
                    }

                    // run global callback on submit
                    commentForm.globalSubmitSuccessCallback({
                        draft: isDraft,
                        comment_id: comment_id
                    });

                } catch (e) {
                    console.error(e);
                }

              if (window.updateSticky !== undefined) {
                  // potentially our comments change the active window size, so we
                  // notify sticky elements
                  updateSticky()
              }

              if (window.refreshAllComments !== undefined && !isDraft) {
                  // if we have this handler, run it, and refresh all comments boxes
                  refreshAllComments()
              }
              else if (window.refreshDraftComments !== undefined && isDraft) {
                  // if we have this handler, run it, and refresh all comments boxes
                  refreshDraftComments();
              }

              commentForm.setActionButtonsDisabled(false);

              // re trigger the linkification of next/prev navigation
              linkifyComments($('.inline-comment-injected'));
              timeagoActivate();
              tooltipActivate();
            };

            var submitFailCallback = function(jqXHR, textStatus, errorThrown) {
                var prefix = "Error while submitting comment.\n"
                var message = formatErrorMessage(jqXHR, textStatus, errorThrown, prefix);
                ajaxErrorSwal(message);
                commentForm.resetCommentFormState(text)
            };

            commentForm.submitAjaxPOST(
                commentForm.submitUrl, postData, submitSuccessCallback, submitFailCallback);
          });
      }

      // Finally "open" our reply form, since we know there are comments and we have the "attached" old form
      $replyForm.addClass('comment-inline-form-open');
      tooltipActivate();
  };

  this.createResolutionComment = function(commentId){
    // hide the trigger text
    $('#resolve-comment-{0}'.format(commentId)).hide();

    var comment = $('#comment-'+commentId);
    var commentData = comment.data();
    console.log(commentData);

    if (commentData.commentInline) {
        var f_path = commentData.commentFPath;
        var line_no = commentData.commentLineNo;
        this.createComment(comment, f_path, line_no, commentId)
    } else {
        this.createGeneralComment('general', "$placeholder", commentId)
    }

    return false;
  };

  this.submitResolution = function(commentId){
    var form = $('#resolve_comment_{0}'.format(commentId)).closest('form');
    var commentForm = form.get(0).CommentForm;

    var cm = commentForm.getCmInstance();
    var renderer = templateContext.visual.default_renderer;
    if (renderer == 'rst'){
        var commentUrl = '`#{0} <{1}#comment-{0}>`_'.format(commentId, commentForm.selfUrl);
    } else if (renderer == 'markdown') {
        var commentUrl = '[#{0}]({1}#comment-{0})'.format(commentId, commentForm.selfUrl);
    } else {
        var commentUrl = '{1}#comment-{0}'.format(commentId, commentForm.selfUrl);
    }

    cm.setValue(_gettext('TODO from comment {0} was fixed.').format(commentUrl));
    form.submit();
    return false;
  };

};

window.commentHelp = function(renderer) {
    var funcData = {'renderer': renderer}
    return renderTemplate('commentHelpHovercard', funcData)
}