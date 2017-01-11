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

    function CommentForm(formElement, commitId, pullRequestId, lineNo, initAutocompleteActions, resolvesCommentId) {
        if (!(this instanceof CommentForm)) {
            return new CommentForm(formElement, commitId, pullRequestId, lineNo, initAutocompleteActions, resolvesCommentId);
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

        this.cmBox = this.withLineNo('#text');
        this.cm = initCommentBoxCodeMirror(this.cmBox, this.initAutocompleteActions);

        this.statusChange = this.withLineNo('#change_status');

        this.submitForm = formElement;
        this.submitButton = $(this.submitForm).find('input[type="submit"]');
        this.submitButtonText = this.submitButton.val();

        this.previewUrl = pyroutes.url('changeset_comment_preview',
            {'repo_name': templateContext.repo_name});

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
                '<li class="">' +
                '<input type="hidden" id="resolve_comment_{0}" name="resolve_comment_{0}" value="{0}">' +
                '<button id="resolve_comment_action_{0}" class="resolve-text btn btn-sm" onclick="return Rhodecode.comments.submitResolution({0})">{1} #{0}</button>' +
                '</li>'
            ).format(resolvesCommentId, _gettext('resolve comment'));
            $(resolvedInfo).insertAfter($(this.commentType).parent());
        }

        // based on commitId, or pullRequestId decide where do we submit
        // out data
        if (this.commitId){
            this.submitUrl = pyroutes.url('changeset_comment',
                {'repo_name': templateContext.repo_name,
                 'revision': this.commitId});
            this.selfUrl = pyroutes.url('changeset_home',
                {'repo_name': templateContext.repo_name,
                 'revision': this.commitId});

        } else if (this.pullRequestId) {
            this.submitUrl = pyroutes.url('pullrequest_comment',
                {'repo_name': templateContext.repo_name,
                 'pull_request_id': this.pullRequestId});
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

        this.getResolvesId = function() {
            return $(this.submitForm).find(this.resolvesId).val() || null;
        };
        this.markCommentResolved = function(resolvedCommentId){
            $('#comment-label-{0}'.format(resolvedCommentId)).find('.resolved').show();
            $('#comment-label-{0}'.format(resolvedCommentId)).find('.resolve').hide();
        };

        this.isAllowedToSubmit = function() {
          return !$(this.submitButton).prop('disabled');
        };

        this.initStatusChangeSelector = function(){
            var formatChangeStatus = function(state, escapeMarkup) {
                var originalOption = state.element;
                return '<div class="flag_status ' + $(originalOption).data('status') + ' pull-left"></div>' +
                       '<span>' + escapeMarkup(state.text) + '</span>';
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

            $(this.statusChange).select2('readonly', false);
        };

        this.globalSubmitSuccessCallback = function(){};

        this.submitAjaxPOST = function(url, postData, successHandler, failHandler) {
            failHandler = failHandler || function() {};
            var postData = toQueryString(postData);
            var request = $.ajax({
                    url: url,
                    type: 'POST',
                    data: postData,
                    headers: {'X-PARTIAL-XHR': true}
                })
                .done(function(data) {
                    successHandler(data);
                })
                .fail(function(data, textStatus, errorThrown){
                    alert(
                        "Error while submitting comment.\n" +
                        "Error code {0} ({1}).".format(data.status, data.statusText));
                    failHandler()
                });
            return request;
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
            var resolvesCommentId = self.getResolvesId();

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
            if (resolvesCommentId){
                postData['resolves_comment_id'] = resolvesCommentId;
            }

            var submitSuccessCallback = function(o) {
                if (status) {
                    location.reload(true);
                } else {
                    $('#injected_page_comments').append(o.rendered_text);
                    self.resetCommentFormState();
                    timeagoActivate();

                    // mark visually which comment was resolved
                    if (resolvesCommentId) {
                        self.markCommentResolved(resolvesCommentId);
                    }
                }

                // run global callback on submit
                self.globalSubmitSuccessCallback();

            };
            var submitFailCallback = function(){
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
            if (!submitEvent && this.getCommentStatus() && !this.lineNo) {
                // if the value of commit review status is set, we allow
                // submit button, but only on Main form, lineNo means inline
                submitState = false
            }
            $(this.submitButton).prop('disabled', submitState);
            if (submitEvent) {
              $(this.submitButton).val(_gettext('Submitting...'));
            } else {
              $(this.submitButton).val(this.submitButtonText);
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
            var previewFailCallback = function(){
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

/* comments controller */
var CommentsController = function() {
  var mainComment = '#text';
  var self = this;

  this.cancelComment = function(node) {
      var $node = $(node);
      var $td = $node.closest('td');
      $node.closest('.comment-inline-form').remove();
      return false;
  };

  this.getLineNumber = function(node) {
      var $node = $(node);
      return $node.closest('td').attr('data-line-number');
  };

  this.scrollToComment = function(node, offset, outdated) {
    var outdated = outdated || false;
    var klass = outdated ? 'div.comment-outdated' : 'div.comment-current';

    if (!node) {
      node = $('.comment-selected');
      if (!node.length) {
        node = $('comment-current')
      }
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

  this.deleteComment = function(node) {
      if (!confirm(_gettext('Delete this comment?'))) {
        return false;
      }
      var $node = $(node);
      var $td = $node.closest('td');
      var $comment = $node.closest('.comment');
      var comment_id = $comment.attr('data-comment-id');
      var url = AJAX_COMMENT_DELETE_URL.replace('__COMMENT_ID__', comment_id);
      var postData = {
        '_method': 'delete',
        'csrf_token': CSRF_TOKEN
      };

      $comment.addClass('comment-deleting');
      $comment.hide('fast');

      var success = function(response) {
        $comment.remove();
        return false;
      };
      var failure = function(data, textStatus, xhr) {
        alert("error processing request: " + textStatus);
        $comment.show('fast');
        $comment.removeClass('comment-deleting');
        return false;
      };
      ajaxPOST(url, postData, success, failure);
  };

  this.toggleWideMode = function (node) {
      if ($('#content').hasClass('wrapper')) {
          $('#content').removeClass("wrapper");
          $('#content').addClass("wide-mode-wrapper");
          $(node).addClass('btn-success');
      } else {
          $('#content').removeClass("wide-mode-wrapper");
          $('#content').addClass("wrapper");
          $(node).removeClass('btn-success');
      }
      return false;
  };

  this.toggleComments = function(node, show) {
    var $filediff = $(node).closest('.filediff');
    if (show === true) {
      $filediff.removeClass('hide-comments');
    } else if (show === false) {
      $filediff.find('.hide-line-comments').removeClass('hide-line-comments');
      $filediff.addClass('hide-comments');
    } else {
      $filediff.find('.hide-line-comments').removeClass('hide-line-comments');
      $filediff.toggleClass('hide-comments');
    }
    return false;
  };

  this.toggleLineComments = function(node) {
    self.toggleComments(node, true);
    var $node = $(node);
    $node.closest('tr').toggleClass('hide-line-comments');
  };

  this.createCommentForm = function(formElement, lineno, placeholderText, initAutocompleteActions, resolvesCommentId){
      var pullRequestId = templateContext.pull_request_data.pull_request_id;
      var commitId = templateContext.commit_data.commit_id;

      var commentForm = new CommentForm(
          formElement, commitId, pullRequestId, lineno, initAutocompleteActions, resolvesCommentId);
      var cm = commentForm.getCmInstance();

      if (resolvesCommentId){
        var placeholderText = _gettext('Leave a comment, or click resolve button to resolve TODO comment #{0}').format(resolvesCommentId);
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
      var commentForm = this.createCommentForm(
          _form, lineNo, placeholderText, true, resolvesCommentId);
      commentForm.initStatusChangeSelector();

      return commentForm;
  };

  this.createComment = function(node, resolutionComment) {
      var resolvesCommentId = resolutionComment || null;
      var $node = $(node);
      var $td = $node.closest('td');
      var $form = $td.find('.comment-inline-form');

      if (!$form.length) {

          var $filediff = $node.closest('.filediff');
          $filediff.removeClass('hide-comments');
          var f_path = $filediff.attr('data-f-path');
          var lineno = self.getLineNumber(node);
          // create a new HTML from template
          var tmpl = $('#cb-comment-inline-form-template').html();
          tmpl = tmpl.format(f_path, lineno);
          $form = $(tmpl);

          var $comments = $td.find('.inline-comments');
          if (!$comments.length) {
            $comments = $(
              $('#cb-comments-inline-container-template').html());
            $td.append($comments);
          }

          $td.find('.cb-comment-add-button').before($form);

          var placeholderText = _gettext('Leave a comment on line {0}.').format(lineno);
          var _form = $($form[0]).find('form');

          var commentForm = this.createCommentForm(
              _form, lineno, placeholderText, false, resolvesCommentId);

          $.Topic('/ui/plugins/code/comment_form_built').prepareOrPublish({
              form: _form,
              parent: $td[0],
              lineno: lineno,
              f_path: f_path}
          );

          // set a CUSTOM submit handler for inline comments.
          commentForm.setHandleFormSubmit(function(o) {
            var text = commentForm.cm.getValue();
            var commentType = commentForm.getCommentType();
            var resolvesCommentId = commentForm.getResolvesId();

            if (text === "") {
              return;
            }

            if (lineno === undefined) {
              alert('missing line !');
              return;
            }
            if (f_path === undefined) {
              alert('missing file path !');
              return;
            }

            var excludeCancelBtn = false;
            var submitEvent = true;
            commentForm.setActionButtonsDisabled(true, excludeCancelBtn, submitEvent);
            commentForm.cm.setOption("readOnly", true);
            var postData = {
                'text': text,
                'f_path': f_path,
                'line': lineno,
                'comment_type': commentType,
                'csrf_token': CSRF_TOKEN
            };
            if (resolvesCommentId){
                postData['resolves_comment_id'] = resolvesCommentId;
            }

            var submitSuccessCallback = function(json_data) {
              $form.remove();
              try {
                var html = json_data.rendered_text;
                var lineno = json_data.line_no;
                var target_id = json_data.target_id;

                $comments.find('.cb-comment-add-button').before(html);

                //mark visually which comment was resolved
                if (resolvesCommentId) {
                    commentForm.markCommentResolved(resolvesCommentId);
                }

                // run global callback on submit
                commentForm.globalSubmitSuccessCallback();

              } catch (e) {
                console.error(e);
              }

              // re trigger the linkification of next/prev navigation
              linkifyComments($('.inline-comment-injected'));
              timeagoActivate();
              commentForm.setActionButtonsDisabled(false);

            };
            var submitFailCallback = function(){
                commentForm.resetCommentFormState(text)
            };
            commentForm.submitAjaxPOST(
                commentForm.submitUrl, postData, submitSuccessCallback, submitFailCallback);
          });
      }

      $form.addClass('comment-inline-form-open');
  };

  this.createResolutionComment = function(commentId){
    // hide the trigger text
    $('#resolve-comment-{0}'.format(commentId)).hide();

    var comment = $('#comment-'+commentId);
    var commentData = comment.data();
    if (commentData.commentInline) {
        this.createComment(comment, commentId)
    } else {
        Rhodecode.comments.createGeneralComment('general', "$placeholder", commentId)
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

  this.renderInlineComments = function(file_comments) {
    show_add_button = typeof show_add_button !== 'undefined' ? show_add_button : true;

    for (var i = 0; i < file_comments.length; i++) {
      var box = file_comments[i];

      var target_id = $(box).attr('target_id');

      // actually comments with line numbers
      var comments = box.children;

      for (var j = 0; j < comments.length; j++) {
        var data = {
          'rendered_text': comments[j].outerHTML,
          'line_no': $(comments[j]).attr('line'),
          'target_id': target_id
        };
      }
    }

    // since order of injection is random, we're now re-iterating
    // from correct order and filling in links
    linkifyComments($('.inline-comment-injected'));
    firefoxAnchorFix();
  };

};
