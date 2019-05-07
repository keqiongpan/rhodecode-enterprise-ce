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
RhodeCode JS Files
**/

if (typeof console == "undefined" || typeof console.log == "undefined"){
    console = { log: function() {} }
}

// TODO: move the following function to submodules

/**
 * show more
 */
var show_more_event = function(){
  $('table .show_more').click(function(e) {
    var cid = e.target.id.substring(1);
    var button = $(this);
    if (button.hasClass('open')) {
      $('#'+cid).hide();
      button.removeClass('open');
    } else {
      $('#'+cid).show();
      button.addClass('open one');
    }
  });
};

var compare_radio_buttons = function(repo_name, compare_ref_type){
    $('#compare_action').on('click', function(e){
        e.preventDefault();

        var source = $('input[name=compare_source]:checked').val();
        var target = $('input[name=compare_target]:checked').val();
        if(source && target){
            var url_data = {
                repo_name: repo_name,
                source_ref: source,
                source_ref_type: compare_ref_type,
                target_ref: target,
                target_ref_type: compare_ref_type,
                merge: 1
            };
            window.location = pyroutes.url('repo_compare', url_data);
        }
    });
    $('.compare-radio-button').on('click', function(e){
        var source = $('input[name=compare_source]:checked').val();
        var target = $('input[name=compare_target]:checked').val();
        if(source && target){
            $('#compare_action').removeAttr("disabled");
            $('#compare_action').removeClass("disabled");
        }
    })
};

var showRepoSize = function(target, repo_name, commit_id, callback) {
    var container = $('#' + target);
    var url = pyroutes.url('repo_stats',
      {"repo_name": repo_name, "commit_id": commit_id});

    container.show();
    if (!container.hasClass('loaded')) {
        $.ajax({url: url})
            .complete(function (data) {
                var responseJSON = data.responseJSON;
                container.addClass('loaded');
                container.html(responseJSON.size);
                callback(responseJSON.code_stats)
            })
            .fail(function (data) {
                console.log('failed to load repo stats');
            });
    }

};

var showRepoStats = function(target, data){
    var container = $('#' + target);

    if (container.hasClass('loaded')) {
        return
    }

    var total = 0;
    var no_data = true;
    var tbl = document.createElement('table');
    tbl.setAttribute('class', 'trending_language_tbl rctable');

    $.each(data, function(key, val){
        total += val.count;
    });

    var sortedStats = [];
    for (var obj in data){
        sortedStats.push([obj, data[obj]])
    }
    var sortedData = sortedStats.sort(function (a, b) {
        return b[1].count - a[1].count
    });
    var cnt = 0;
    $.each(sortedData, function(idx, val){
        cnt += 1;
        no_data = false;

        var tr = document.createElement('tr');

        var key = val[0];
        var obj = {"desc": val[1].desc, "count": val[1].count};

        // meta language names
        var td1 = document.createElement('td');
        var trending_language_label = document.createElement('div');
        trending_language_label.innerHTML = obj.desc;
        td1.appendChild(trending_language_label);

        // extensions
        var td2 = document.createElement('td');
        var extension = document.createElement('div');
        extension.innerHTML = ".{0}".format(key)
        td2.appendChild(extension);

        // number of files
        var td3 = document.createElement('td');
        var file_count = document.createElement('div');
        var percentage_num = Math.round((obj.count / total * 100), 2);
        var label = _ngettext('file', 'files', obj.count);
        file_count.innerHTML = "{0} {1} ({2}%)".format(obj.count, label, percentage_num) ;
        td3.appendChild(file_count);

        // percentage
        var td4 = document.createElement('td');
        td4.setAttribute("class", 'trending_language');

        var percentage = document.createElement('div');
        percentage.setAttribute('class', 'lang-bar');
        percentage.innerHTML = "&nbsp;";
        percentage.style.width = percentage_num + '%';
        td4.appendChild(percentage);

        tr.appendChild(td1);
        tr.appendChild(td2);
        tr.appendChild(td3);
        tr.appendChild(td4);
        tbl.appendChild(tr);

    });

    $(container).html(tbl);
    $(container).addClass('loaded');

    $('#code_stats_show_more').on('click', function (e) {
        e.preventDefault();
        $('.stats_hidden').each(function (idx) {
            $(this).css("display", "");
        });
        $('#code_stats_show_more').hide();
    });

};

// returns a node from given html;
var fromHTML = function(html){
  var _html = document.createElement('element');
  _html.innerHTML = html;
  return _html;
};

// Toggle Collapsable Content
function collapsableContent() {

    $('.collapsable-content').not('.no-hide').hide();

    $('.btn-collapse').unbind(); //in case we've been here before
    $('.btn-collapse').click(function() {
        var button = $(this);
        var togglename = $(this).data("toggle");
        $('.collapsable-content[data-toggle='+togglename+']').toggle();
        if ($(this).html()=="Show Less")
            $(this).html("Show More");
        else
            $(this).html("Show Less");
    });
};

var timeagoActivate = function() {
    $("time.timeago").timeago();
};


var clipboardActivate = function() {
    /*
    *
    * <i class="tooltip icon-plus clipboard-action" data-clipboard-text="${commit.raw_id}" title="${_('Copy the full commit id')}"></i>
    * */
    var clipboard = new ClipboardJS('.clipboard-action');

    clipboard.on('success', function(e) {
        var callback = function () {
            $(e.trigger).animate({'opacity': 1.00}, 200)
        };
        $(e.trigger).animate({'opacity': 0.15}, 200, callback);
        e.clearSelection();
    });
};


// Formatting values in a Select2 dropdown of commit references
var formatSelect2SelectionRefs = function(commit_ref){
  var tmpl = '';
  if (!commit_ref.text || commit_ref.type === 'sha'){
    return commit_ref.text;
  }
  if (commit_ref.type === 'branch'){
    tmpl = tmpl.concat('<i class="icon-branch"></i> ');
  } else if (commit_ref.type === 'tag'){
    tmpl = tmpl.concat('<i class="icon-tag"></i> ');
  } else if (commit_ref.type === 'book'){
    tmpl = tmpl.concat('<i class="icon-bookmark"></i> ');
  }
  return tmpl.concat(escapeHtml(commit_ref.text));
};

// takes a given html element and scrolls it down offset pixels
function offsetScroll(element, offset) {
    setTimeout(function() {
        var location = element.offset().top;
        // some browsers use body, some use html
        $('html, body').animate({ scrollTop: (location - offset) });
    }, 100);
}

// scroll an element `percent`% from the top of page in `time` ms
function scrollToElement(element, percent, time) {
    percent = (percent === undefined ? 25 : percent);
    time = (time === undefined ? 100 : time);

    var $element = $(element);
    if ($element.length == 0) {
        throw('Cannot scroll to {0}'.format(element))
    }
    var elOffset = $element.offset().top;
    var elHeight = $element.height();
    var windowHeight = $(window).height();
    var offset = elOffset;
    if (elHeight < windowHeight) {
        offset = elOffset - ((windowHeight / (100 / percent)) - (elHeight / 2));
    }
    setTimeout(function() {
        $('html, body').animate({ scrollTop: offset});
    }, time);
}

/**
 * global hooks after DOM is loaded
 */
$(document).ready(function() {
    firefoxAnchorFix();

    $('.navigation a.menulink').on('click', function(e){
        var menuitem = $(this).parent('li');
        if (menuitem.hasClass('open')) {
            menuitem.removeClass('open');
        } else {
            menuitem.addClass('open');
            $(document).on('click', function(event) {
                if (!$(event.target).closest(menuitem).length) {
                    menuitem.removeClass('open');
                }
            });
        }
    });

    $('body').on('click', '.cb-lineno a', function(event) {
        function sortNumber(a,b) {
            return a - b;
        }

        var lineNo = $(this).data('lineNo');
        var lineName = $(this).attr('name');

        if (lineNo) {
            var prevLine = $('.cb-line-selected a').data('lineNo');

            // on shift, we do a range selection, if we got previous line
            if (event.shiftKey && prevLine !== undefined) {
                var prevLine = parseInt(prevLine);
                var nextLine = parseInt(lineNo);
                var pos = [prevLine, nextLine].sort(sortNumber);
                var anchor = '#L{0}-{1}'.format(pos[0], pos[1]);

            // single click
            } else {
                var nextLine = parseInt(lineNo);
                var pos = [nextLine, nextLine];
                var anchor = '#L{0}'.format(pos[0]);

            }
            // highlight
            var range = [];
            for (var i = pos[0]; i <= pos[1]; i++) {
                range.push(i);
            }
            // clear old selected lines
            $('.cb-line-selected').removeClass('cb-line-selected');

            $.each(range, function (i, lineNo) {
                var line_td = $('td.cb-lineno#L' + lineNo);

                if (line_td.length) {
                    line_td.addClass('cb-line-selected'); // line number td
                    line_td.prev().addClass('cb-line-selected'); // line data
                    line_td.next().addClass('cb-line-selected'); // line content
                }
            });

        } else if (lineName !== undefined) { // lineName only occurs in diffs
            // clear old selected lines
            $('td.cb-line-selected').removeClass('cb-line-selected');
            var anchor = '#{0}'.format(lineName);
            var diffmode = templateContext.session_attrs.diffmode || "sideside";

            if (diffmode === "unified") {
                $(this).closest('tr').find('td').addClass('cb-line-selected');
            } else {
                var activeTd = $(this).closest('td');
                activeTd.addClass('cb-line-selected');
                activeTd.next('td').addClass('cb-line-selected');
            }

        }

        // Replace URL without jumping to it if browser supports.
        // Default otherwise
        if (history.pushState && anchor !== undefined) {
            var new_location = location.href.rstrip('#');
            if (location.hash) {
                // location without hash
                new_location = new_location.replace(location.hash, "");
            }

            // Make new anchor url
            new_location = new_location + anchor;
            history.pushState(true, document.title, new_location);

            return false;
        }

    });

    $('.collapse_file').on('click', function(e) {
        e.stopPropagation();
        if ($(e.target).is('a')) { return; }
        var node = $(e.delegateTarget).first();
        var icon = $($(node.children().first()).children().first());
        var id = node.attr('fid');
        var target = $('#'+id);
        var tr = $('#tr_'+id);
        var diff = $('#diff_'+id);
        if(node.hasClass('expand_file')){
            node.removeClass('expand_file');
            icon.removeClass('expand_file_icon');
            node.addClass('collapse_file');
            icon.addClass('collapse_file_icon');
            diff.show();
            tr.show();
            target.show();
        } else {
            node.removeClass('collapse_file');
            icon.removeClass('collapse_file_icon');
            node.addClass('expand_file');
            icon.addClass('expand_file_icon');
            diff.hide();
            tr.hide();
            target.hide();
        }
    });

    $('#expand_all_files').click(function() {
        $('.expand_file').each(function() {
            var node = $(this);
            var icon = $($(node.children().first()).children().first());
            var id = $(this).attr('fid');
            var target = $('#'+id);
            var tr = $('#tr_'+id);
            var diff = $('#diff_'+id);
            node.removeClass('expand_file');
            icon.removeClass('expand_file_icon');
            node.addClass('collapse_file');
            icon.addClass('collapse_file_icon');
            diff.show();
            tr.show();
            target.show();
        });
    });

    $('#collapse_all_files').click(function() {
        $('.collapse_file').each(function() {
            var node = $(this);
            var icon = $($(node.children().first()).children().first());
            var id = $(this).attr('fid');
            var target = $('#'+id);
            var tr = $('#tr_'+id);
            var diff = $('#diff_'+id);
            node.removeClass('collapse_file');
            icon.removeClass('collapse_file_icon');
            node.addClass('expand_file');
            icon.addClass('expand_file_icon');
            diff.hide();
            tr.hide();
            target.hide();
        });
    });

    // Mouse over behavior for comments and line selection

    // Select the line that comes from the url anchor
    // At the time of development, Chrome didn't seem to support jquery's :target
    // element, so I had to scroll manually

    if (location.hash) {
        var result = splitDelimitedHash(location.hash);
        var loc  = result.loc;
        if (loc.length > 1) {

            var highlightable_line_tds = [];

            // source code line format
            var page_highlights = loc.substring(
                loc.indexOf('#') + 1).split('L');

            if (page_highlights.length > 1) {
                var highlight_ranges = page_highlights[1].split(",");
                var h_lines = [];
                for (var pos in highlight_ranges) {
                    var _range = highlight_ranges[pos].split('-');
                    if (_range.length === 2) {
                        var start = parseInt(_range[0]);
                        var end = parseInt(_range[1]);
                        if (start < end) {
                            for (var i = start; i <= end; i++) {
                                h_lines.push(i);
                            }
                        }
                    }
                    else {
                        h_lines.push(parseInt(highlight_ranges[pos]));
                    }
                }
                for (pos in h_lines) {
                    var line_td = $('td.cb-lineno#L' + h_lines[pos]);
                    if (line_td.length) {
                        highlightable_line_tds.push(line_td);
                    }
                }
            }

            // now check a direct id reference (diff page)
            if ($(loc).length && $(loc).hasClass('cb-lineno')) {
                highlightable_line_tds.push($(loc));
            }
            $.each(highlightable_line_tds, function (i, $td) {
                $td.addClass('cb-line-selected'); // line number td
                $td.prev().addClass('cb-line-selected'); // line data
                $td.next().addClass('cb-line-selected'); // line content
            });

            if (highlightable_line_tds.length) {
                var $first_line_td = highlightable_line_tds[0];
                scrollToElement($first_line_td);
                $.Topic('/ui/plugins/code/anchor_focus').prepareOrPublish({
                    td: $first_line_td,
                    remainder: result.remainder
                });
            }
        }
    }
    collapsableContent();
});

var feedLifetimeOptions = function(query, initialData){
    var data = {results: []};
    var isQuery = typeof query.term !== 'undefined';

    var section = _gettext('Lifetime');
    var children = [];

    //filter results
    $.each(initialData.results, function(idx, value) {

        if (!isQuery || query.term.length === 0 || value.text.toUpperCase().indexOf(query.term.toUpperCase()) >= 0) {
            children.push({
                'id': this.id,
                'text': this.text
            })
        }

    });
    data.results.push({
        'text': section,
        'children': children
    });

    if (isQuery) {

        var now = moment.utc();

        var parseQuery = function(entry, now){
            var fmt = 'DD/MM/YYYY H:mm';
            var parsed = moment.utc(entry, fmt);
            var diffInMin = parsed.diff(now, 'minutes');

            if (diffInMin > 0){
                return {
                    id: diffInMin,
                    text: parsed.format(fmt)
                }
            } else {
                return {
                    id: undefined,
                    text: parsed.format('DD/MM/YYYY') + ' ' + _gettext('date not in future')
                }
            }


        };

        data.results.push({
            'text': _gettext('Specified expiration date'),
            'children': [{
                'id': parseQuery(query.term, now).id,
                'text': parseQuery(query.term, now).text
            }]
        });
    }

    query.callback(data);
};


var storeUserSessionAttr = function (key, val) {

    var postData = {
        'key': key,
        'val': val,
        'csrf_token': CSRF_TOKEN
    };

    var success = function(o) {
        return true
    };

    ajaxPOST(pyroutes.url('store_user_session_value'), postData, success);
    return false;
};
