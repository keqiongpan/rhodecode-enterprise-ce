// # Copyright (C) 2010-2019 RhodeCode GmbH
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
 * Code Mirror
 */
// global code-mirror logger;, to enable run
// Logger.get('CodeMirror').setLevel(Logger.DEBUG)

cmLog = Logger.get('CodeMirror');
cmLog.setLevel(Logger.OFF);


//global cache for inline forms
var userHintsCache = {};

// global timer, used to cancel async loading
var CodeMirrorLoadUserHintTimer;

var escapeRegExChars = function(value) {
  return value.replace(/[\-\[\]\/\{\}\(\)\*\+\?\.\\\^\$\|]/g, "\\$&");
};

/**
 * Load hints from external source returns an array of objects in a format
 * that hinting lib requires
 * @returns {Array}
 */
var CodeMirrorLoadUserHints = function(query, triggerHints) {
  cmLog.debug('Loading mentions users via AJAX');
  var _users = [];
  $.ajax({
    type: 'GET',
    data: {query: query},
    url: pyroutes.url('user_autocomplete_data'),
    headers: {'X-PARTIAL-XHR': true},
    async: true
  })
  .done(function(data) {
    var tmpl = '<img class="gravatar" src="{0}"/>{1}';
    $.each(data.suggestions, function(i) {
      var userObj = data.suggestions[i];

      if (userObj.username !== "default") {
        _users.push({
          text: userObj.username + " ",
          org_text: userObj.username,
          displayText: userObj.value_display, // search that field
          // internal caches
          _icon_link: userObj.icon_link,
          _text: userObj.value_display,

          render: function(elt, data, completion) {
            var el = document.createElement('div');
            el.className = "CodeMirror-hint-entry";
            el.innerHTML = tmpl.format(
                completion._icon_link, completion._text);
            elt.appendChild(el);
          }
        });
      }
    });
    cmLog.debug('Mention users loaded');
    // set to global cache
    userHintsCache[query] = _users;
    triggerHints(userHintsCache[query]);
  })
  .fail(function(data, textStatus, xhr) {
      alert("error processing request. \n" +
            "Error code {0} ({1}).".format(data.status, data.statusText));
  });
};

/**
 * filters the results based on the current context
 * @param users
 * @param context
 * @returns {Array}
 */
var CodeMirrorFilterUsers = function(users, context) {
  var MAX_LIMIT = 10;
  var filtered_users = [];
  var curWord = context.string;

  cmLog.debug('Filtering users based on query:', curWord);
  $.each(users, function(i) {
    var match = users[i];
    var searchText = match.displayText;

    if (!curWord ||
        searchText.toLowerCase().lastIndexOf(curWord) !== -1) {
      // reset state
      match._text = match.displayText;
      if (curWord) {
        // do highlighting
        var pattern = '(' + escapeRegExChars(curWord) + ')';
        match._text = searchText.replace(
            new RegExp(pattern, 'gi'), '<strong>$1<\/strong>');
      }

      filtered_users.push(match);
    }
    // to not return to many results, use limit of filtered results
    if (filtered_users.length > MAX_LIMIT) {
      return false;
    }
  });

  return filtered_users;
};

var CodeMirrorMentionHint = function(editor, callback, options) {
  var cur = editor.getCursor();
  var curLine = editor.getLine(cur.line).slice(0, cur.ch);

  // match on @ +1char
  var tokenMatch = new RegExp(
      '(^@| @)([a-zA-Z0-9]{1}[a-zA-Z0-9\-\_\.]*)$').exec(curLine);

  var tokenStr = '';
  if (tokenMatch !== null && tokenMatch.length > 0){
    tokenStr = tokenMatch[0].strip();
  } else {
    // skip if we didn't match our token
    return;
  }

  var context = {
    start: (cur.ch - tokenStr.length) + 1,
    end: cur.ch,
    string: tokenStr.slice(1),
    type: null
  };

  // case when we put the @sign in fron of a string,
  // eg <@ we put it here>sometext then we need to prepend to text
  if (context.end > cur.ch) {
    context.start = context.start + 1; // we add to the @ sign
    context.end = cur.ch; // don't eat front part just append
    context.string = context.string.slice(1, cur.ch - context.start);
  }

  cmLog.debug('Mention context', context);

  var triggerHints = function(userHints){
    return callback({
      list: CodeMirrorFilterUsers(userHints, context),
      from: CodeMirror.Pos(cur.line, context.start),
      to: CodeMirror.Pos(cur.line, context.end)
    });
  };

  var queryBasedHintsCache = undefined;
  // if we have something in the cache, try to fetch the query based cache
  if (userHintsCache !== {}){
    queryBasedHintsCache = userHintsCache[context.string];
  }

  if (queryBasedHintsCache !== undefined) {
    cmLog.debug('Users loaded from cache');
    triggerHints(queryBasedHintsCache);
  } else {
    // this takes care for async loading, and then displaying results
    // and also propagates the userHintsCache
    window.clearTimeout(CodeMirrorLoadUserHintTimer);
    CodeMirrorLoadUserHintTimer = setTimeout(function() {
      CodeMirrorLoadUserHints(context.string, triggerHints);
    }, 300);
  }
};

var CodeMirrorCompleteAfter = function(cm, pred) {
  var options = {
    completeSingle: false,
    async: true,
    closeOnUnfocus: true
  };
  var cur = cm.getCursor();
  setTimeout(function() {
    if (!cm.state.completionActive) {
      cmLog.debug('Trigger mentions hinting');
      CodeMirror.showHint(cm, CodeMirror.hint.mentions, options);
    }
  }, 100);

  // tell CodeMirror we didn't handle the key
  // trick to trigger on a char but still complete it
  return CodeMirror.Pass;
};

var initCodeMirror = function(textAreadId, resetUrl, focus, options) {
  if (textAreadId.substr(0,1) === "#"){
    var ta = $(textAreadId).get(0);
  }else {
    var ta = $('#' + textAreadId).get(0);
  }

  if (focus === undefined) {
      focus = true;
  }

  // default options
  var codeMirrorOptions = {
    mode: "null",
    lineNumbers: true,
    indentUnit: 4,
    autofocus: focus
  };

  if (options !== undefined) {
    // extend with custom options
    codeMirrorOptions = $.extend(true, codeMirrorOptions, options);
  }

  var myCodeMirror = CodeMirror.fromTextArea(ta, codeMirrorOptions);

  $('#reset').on('click', function(e) {
    window.location = resetUrl;
  });

  return myCodeMirror;
};


var initMarkupCodeMirror = function(textAreadId, focus, options) {
  var initialHeight = 100;

  var ta = $(textAreadId).get(0);
  if (focus === undefined) {
      focus = true;
  }

  // default options
  var codeMirrorOptions = {
    lineNumbers: false,
    indentUnit: 4,
    viewportMargin: 30,
    // this is a trick to trigger some logic behind codemirror placeholder
    // it influences styling and behaviour.
    placeholder: " ",
    lineWrapping: true,
    autofocus: focus
  };

  if (options !== undefined) {
    // extend with custom options
    codeMirrorOptions = $.extend(true, codeMirrorOptions, options);
  }

  var cm = CodeMirror.fromTextArea(ta, codeMirrorOptions);
  cm.setSize(null, initialHeight);
  cm.setOption("mode", DEFAULT_RENDERER);
  CodeMirror.autoLoadMode(cm, DEFAULT_RENDERER); // load rst or markdown mode
  cmLog.debug('Loading codemirror mode', DEFAULT_RENDERER);

  // start listening on changes to make auto-expanded editor
  cm.on("change", function(instance, changeObj) {
    var height = initialHeight;
    var lines = instance.lineCount();
    if ( lines > 6 && lines < 20) {
      height = "auto";
    }
    else if (lines >= 20){
      zheight = 20*15;
    }
    instance.setSize(null, height);

    // detect if the change was trigger by auto desc, or user input
    var changeOrigin = changeObj.origin;

    if (changeOrigin === "setValue") {
        cmLog.debug('Change triggered by setValue');
    }
    else {
        cmLog.debug('user triggered change !');
        // set special marker to indicate user has created an input.
        instance._userDefinedValue = true;
    }

  });

  return cm;
};


var initCommentBoxCodeMirror = function(CommentForm, textAreaId, triggerActions){
  var initialHeight = 100;

  if (typeof userHintsCache === "undefined") {
    userHintsCache = {};
    cmLog.debug('Init empty cache for mentions');
  }
  if (!$(textAreaId).get(0)) {
    cmLog.debug('Element for textarea not found', textAreaId);
    return;
  }
    /**
     * Filter action based on typed in text
     * @param actions
     * @param context
     * @returns {Array}
     */

    var filterActions = function(actions, context){

      var MAX_LIMIT = 10;
      var filtered_actions = [];
      var curWord = context.string;

      cmLog.debug('Filtering actions based on query:', curWord);
      $.each(actions, function(i) {
        var match = actions[i];
        var searchText = match.searchText;

        if (!curWord ||
          searchText.toLowerCase().lastIndexOf(curWord) !== -1) {
          // reset state
          match._text = match.displayText;
          if (curWord) {
            // do highlighting
            var pattern = '(' + escapeRegExChars(curWord) + ')';
            match._text = searchText.replace(
              new RegExp(pattern, 'gi'), '<strong>$1<\/strong>');
          }

          filtered_actions.push(match);
        }
        // to not return to many results, use limit of filtered results
        if (filtered_actions.length > MAX_LIMIT) {
            return false;
        }
      });

      return filtered_actions;
    };

    var submitForm = function(cm, pred) {
      $(cm.display.input.textarea.form).submit();
      return CodeMirror.Pass;
    };

    var completeActions = function(actions){

        var registeredActions = [];
        var allActions = [
        {
          text: "approve",
          searchText: "status approved",
          displayText: _gettext('Set status to Approved'),
          hint: function(CodeMirror, data, completion) {
            CodeMirror.replaceRange("", completion.from || data.from,
                        completion.to || data.to, "complete");
            $(CommentForm.statusChange).select2("val", 'approved').trigger('change');
          },
          render: function(elt, data, completion) {
            var el = document.createElement('i');

            el.className = "icon-circle review-status-approved";
            elt.appendChild(el);

            el = document.createElement('span');
            el.innerHTML = completion.displayText;
            elt.appendChild(el);
          }
        },
        {
          text: "reject",
          searchText: "status rejected",
          displayText: _gettext('Set status to Rejected'),
          hint: function(CodeMirror, data, completion) {
              CodeMirror.replaceRange("", completion.from || data.from,
                          completion.to || data.to, "complete");
              $(CommentForm.statusChange).select2("val", 'rejected').trigger('change');
          },
          render: function(elt, data, completion) {
              var el = document.createElement('i');
              el.className = "icon-circle review-status-rejected";
              elt.appendChild(el);

              el = document.createElement('span');
              el.innerHTML = completion.displayText;
              elt.appendChild(el);
          }
        },
        {
          text: "as_todo",
          searchText: "todo comment",
          displayText: _gettext('TODO comment'),
          hint: function(CodeMirror, data, completion) {
              CodeMirror.replaceRange("", completion.from || data.from,
                          completion.to || data.to, "complete");

              $(CommentForm.commentType).val('todo');
          },
          render: function(elt, data, completion) {
              var el = document.createElement('div');
              el.className = "pull-left";
              elt.appendChild(el);

              el = document.createElement('span');
              el.innerHTML = completion.displayText;
              elt.appendChild(el);
          }
        },
        {
          text: "as_note",
          searchText: "note comment",
          displayText: _gettext('Note Comment'),
          hint: function(CodeMirror, data, completion) {
              CodeMirror.replaceRange("", completion.from || data.from,
                          completion.to || data.to, "complete");

              $(CommentForm.commentType).val('note');
          },
          render: function(elt, data, completion) {
              var el = document.createElement('div');
              el.className = "pull-left";
              elt.appendChild(el);

              el = document.createElement('span');
              el.innerHTML = completion.displayText;
              elt.appendChild(el);
          }
        }
        ];

        $.each(allActions, function(index, value){
            var actionData = allActions[index];
            if (actions.indexOf(actionData['text']) != -1) {
                registeredActions.push(actionData);
            }
        });

        return function(cm, pred) {
            var cur = cm.getCursor();
            var options = {
                closeOnUnfocus: true,
                registeredActions: registeredActions
            };
            setTimeout(function() {
                if (!cm.state.completionActive) {
                    cmLog.debug('Trigger actions hinting');
                    CodeMirror.showHint(cm, CodeMirror.hint.actions, options);
                }
            }, 100);

            // tell CodeMirror we didn't handle the key
            // trick to trigger on a char but still complete it
            return CodeMirror.Pass;
        }
    };

    var extraKeys = {
      "'@'": CodeMirrorCompleteAfter,
      Tab: function(cm) {
        // space indent instead of TABS
        var spaces = new Array(cm.getOption("indentUnit") + 1).join(" ");
        cm.replaceSelection(spaces);
      }
    };
    // submit form on Meta-Enter
    if (OSType === "mac") {
      extraKeys["Cmd-Enter"] = submitForm;
    }
    else {
      extraKeys["Ctrl-Enter"] = submitForm;
    }

    if (triggerActions) {
      // register triggerActions for this instance
      extraKeys["'/'"] = completeActions(triggerActions);
    }

    var cm = CodeMirror.fromTextArea($(textAreaId).get(0), {
      lineNumbers: false,
      indentUnit: 4,
      viewportMargin: 30,
      // this is a trick to trigger some logic behind codemirror placeholder
      // it influences styling and behaviour.
      placeholder: " ",
      extraKeys: extraKeys,
      lineWrapping: true
    });

    cm.setSize(null, initialHeight);
    cm.setOption("mode", DEFAULT_RENDERER);
    CodeMirror.autoLoadMode(cm, DEFAULT_RENDERER); // load rst or markdown mode
    cmLog.debug('Loading codemirror mode', DEFAULT_RENDERER);
    // start listening on changes to make auto-expanded editor
    cm.on("change", function(self) {
      var height = initialHeight;
      var lines = self.lineCount();
      if ( lines > 6 && lines < 20) {
        height = "auto";
      }
      else if (lines >= 20){
        zheight = 20*15;
      }
      self.setSize(null, height);
    });

    var actionHint = function(editor, options) {

      var cur = editor.getCursor();
      var curLine = editor.getLine(cur.line).slice(0, cur.ch);

      // match  only on /+1 character minimum
      var tokenMatch = new RegExp('(^/\|/\)([a-zA-Z]*)$').exec(curLine);

      var tokenStr = '';
      if (tokenMatch !== null && tokenMatch.length > 0){
        tokenStr = tokenMatch[2].strip();
      }

      var context = {
        start: (cur.ch - tokenStr.length) - 1,
        end: cur.ch,
        string: tokenStr,
        type: null
      };

      return {
        list: filterActions(options.registeredActions, context),
        from: CodeMirror.Pos(cur.line, context.start),
        to: CodeMirror.Pos(cur.line, context.end)
      };

    };
    CodeMirror.registerHelper("hint", "mentions", CodeMirrorMentionHint);
    CodeMirror.registerHelper("hint", "actions", actionHint);
    return cm;
};

var setCodeMirrorMode = function(codeMirrorInstance, mode) {
  CodeMirror.autoLoadMode(codeMirrorInstance, mode);
  codeMirrorInstance.setOption("mode", mode);
};

var setCodeMirrorLineWrap = function(codeMirrorInstance, line_wrap) {
  codeMirrorInstance.setOption("lineWrapping", line_wrap);
};

var setCodeMirrorModeFromSelect = function(
  targetSelect, targetFileInput, codeMirrorInstance, callback){

  $(targetSelect).on('change', function(e) {
    cmLog.debug('codemirror select2 mode change event !');
    var selected = e.currentTarget;
    var node = selected.options[selected.selectedIndex];
    var mimetype = node.value;
    cmLog.debug('picked mimetype', mimetype);
    var new_mode = $(node).attr('mode');
    setCodeMirrorMode(codeMirrorInstance, new_mode);
    cmLog.debug('set new mode', new_mode);

    //propose filename from picked mode
    cmLog.debug('setting mimetype', mimetype);
    var proposed_ext = getExtFromMimeType(mimetype);
    cmLog.debug('file input', $(targetFileInput).val());
    var file_data = getFilenameAndExt($(targetFileInput).val());
    var filename = file_data.filename || 'filename1';
    $(targetFileInput).val(filename + proposed_ext);
    cmLog.debug('proposed file', filename + proposed_ext);


    if (typeof(callback) === 'function') {
      try {
        cmLog.debug('running callback', callback);
        callback(filename, mimetype, new_mode);
      } catch (err) {
        console.log('failed to run callback', callback, err);
      }
    }
    cmLog.debug('finish iteration...');
  });
};

var setCodeMirrorModeFromInput = function(
  targetSelect, targetFileInput, codeMirrorInstance, callback) {

  // on type the new filename set mode
  $(targetFileInput).on('keyup', function(e) {
    var file_data = getFilenameAndExt(this.value);
    if (file_data.ext === null) {
      return;
    }

    var mimetypes = getMimeTypeFromExt(file_data.ext, true);
    cmLog.debug('mimetype from file', file_data, mimetypes);
    var detected_mode;
    var detected_option;
    for (var i in mimetypes) {
      var mt = mimetypes[i];
      if (!detected_mode) {
        detected_mode = detectCodeMirrorMode(this.value, mt);
      }

      if (!detected_option) {
        cmLog.debug('#mimetype option[value="{0}"]'.format(mt));
        if ($(targetSelect).find('option[value="{0}"]'.format(mt)).length) {
          detected_option = mt;
        }
      }
    }

    cmLog.debug('detected mode', detected_mode);
    cmLog.debug('detected option', detected_option);
    if (detected_mode && detected_option){

      $(targetSelect).select2("val", detected_option);
      setCodeMirrorMode(codeMirrorInstance, detected_mode);

      if(typeof(callback) === 'function'){
        try{
          cmLog.debug('running callback', callback);
          var filename = file_data.filename + "." + file_data.ext;
          callback(filename, detected_option, detected_mode);
        }catch (err){
          console.log('failed to run callback', callback, err);
        }
      }
    }

  });
};

var fillCodeMirrorOptions = function(targetSelect) {
  //inject new modes, based on codeMirrors modeInfo object
  var modes_select = $(targetSelect);
  for (var i = 0; i < CodeMirror.modeInfo.length; i++) {
    var m = CodeMirror.modeInfo[i];
    var opt = new Option(m.name, m.mime);
    $(opt).attr('mode', m.mode);
    modes_select.append(opt);
  }
};


 /* markup form */
(function(mod) {

    if (typeof exports == "object" && typeof module == "object") {
        // CommonJS
        module.exports = mod();
    }
    else {
        // Plain browser env
        (this || window).MarkupForm = mod();
    }

})(function() {
    "use strict";

    function MarkupForm(textareaId) {
        if (!(this instanceof MarkupForm)) {
            return new MarkupForm(textareaId);
        }

        // bind the element instance to our Form
        $('#' + textareaId).get(0).MarkupForm = this;

        this.withSelectorId = function(selector) {
            var selectorId = textareaId;
            return selector + '_' + selectorId;
        };

        this.previewButton = this.withSelectorId('#preview-btn');
        this.previewContainer = this.withSelectorId('#preview-container');

        this.previewBoxSelector = this.withSelectorId('#preview-box');

        this.editButton = this.withSelectorId('#edit-btn');
        this.editContainer = this.withSelectorId('#edit-container');

        this.cmBox = textareaId;
        this.cm = initMarkupCodeMirror('#' + textareaId);

        this.previewUrl = pyroutes.url('markup_preview');

        // FUNCTIONS and helpers
        var self = this;

        this.getCmInstance = function(){
            return this.cm
        };

        this.setPlaceholder = function(placeholder) {
            var cm = this.getCmInstance();
            if (cm){
                cm.setOption('placeholder', placeholder);
            }
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
                }

                var placeholderText = _gettext('Comment text will be set automatically based on currently selected status ({0}) ...').format(status);
                self.setPlaceholder(placeholderText)
            })
        };

        // reset the text area into it's original state
        this.resetMarkupFormState = function(content) {
            content = content || '';

            $(this.editContainer).show();
            $(this.editButton).parent().addClass('active');

            $(this.previewContainer).hide();
            $(this.previewButton).parent().removeClass('active');

            this.setActionButtonsDisabled(true);
            self.cm.setValue(content);
            self.cm.setOption("readOnly", false);
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

        this.setActionButtonsDisabled = function(state) {
            $(this.editButton).prop('disabled', state);
            $(this.previewButton).prop('disabled', state);
        };

        // lock preview/edit/submit buttons on load, but exclude cancel button
        var excludeCancelBtn = true;
        this.setActionButtonsDisabled(true);

        // anonymous users don't have access to initialized CM instance
        if (this.cm !== undefined){
            this.cm.on('change', function(cMirror) {
                if (cMirror.getValue() === "") {
                    self.setActionButtonsDisabled(true)
                } else {
                    self.setActionButtonsDisabled(false)
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
            var previewFailCallback = function(data){
                alert(
                "Error while submitting preview.\n" +
                "Error code {0} ({1}).".format(data.status, data.statusText)
                );
                self.resetMarkupFormState(text)
            };
            _submitAjaxPOST(
                self.previewUrl, postData, self.previewSuccessCallback,
                previewFailCallback);

            $(self.previewButton).parent().addClass('active');
            $(self.editButton).parent().removeClass('active');
        });

    }

    return MarkupForm;
});
