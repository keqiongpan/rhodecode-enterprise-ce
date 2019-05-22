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
 * Search file list
 */

var NodeFilter = {};

var fileBrowserListeners = function (node_list_url, url_base) {
    var $filterInput = $('#node_filter');
    var n_filter = $filterInput.get(0);

    NodeFilter.filterTimeout = null;
    var nodes = null;

    NodeFilter.focus = function () {
        $filterInput.focus()
    };

    NodeFilter.fetchNodes = function (callback) {
        $.ajax(
            {url: node_list_url, headers: {'X-PARTIAL-XHR': true}})
            .done(function (data) {
                nodes = data.nodes;
                if (callback) {
                    callback();
                }
            })
            .fail(function (data) {
                console.log('failed to load');
            });
    };

    NodeFilter.initFilter = function (e) {
        if ($filterInput.hasClass('loading')) {
            return
        }

        // in case we are already loaded, do nothing
        if (!$filterInput.hasClass('init')) {
            return NodeFilter.handleKey(e);
        }

        var org = $('.files-filter-box-path .tag').html();
        $('.files-filter-box-path .tag').html('loading...');
        $filterInput.addClass('loading');

        var callback = function (org) {
            return function () {
                if ($filterInput.hasClass('init')) {
                    $filterInput.removeClass('init');
                    $filterInput.removeClass('loading');
                }
                $('.files-filter-box-path .tag').html(org);

                // auto re-filter if we filled in the input
                if (n_filter.value !== "") {
                    NodeFilter.updateFilter(n_filter, e)()
                }

            }
        };
        // load node data
        NodeFilter.fetchNodes(callback(org));

    };

    NodeFilter.resetFilter = function () {
        $('#tbody').show();
        $('#tbody_filtered').hide();
        $filterInput.val('');
    };

    NodeFilter.handleKey = function (e) {
        var scrollDown = function (element) {
            var elementBottom = element.offset().top + $(element).outerHeight();
            var windowBottom = window.innerHeight + $(window).scrollTop();
            if (elementBottom > windowBottom) {
                var offset = elementBottom - window.innerHeight;
                $('html,body').scrollTop(offset);
                return false;
            }
            return true;
        };

        var scrollUp = function (element) {
            if (element.offset().top < $(window).scrollTop()) {
                $('html,body').scrollTop(element.offset().top);
                return false;
            }
            return true;
        };
        var $hlElem = $('.browser-highlight');

        if (e.keyCode === 40) { // Down
            if ($hlElem.length === 0) {
                $('.browser-result').first().addClass('browser-highlight');
            } else {
                var next = $hlElem.next();
                if (next.length !== 0) {
                    $hlElem.removeClass('browser-highlight');
                    next.addClass('browser-highlight');
                }
            }

            if ($hlElem.get(0) !== undefined){
                scrollDown($hlElem);
            }
        }
        if (e.keyCode === 38) { // Up
            e.preventDefault();
            if ($hlElem.length !== 0) {
                var next = $hlElem.prev();
                if (next.length !== 0) {
                    $('.browser-highlight').removeClass('browser-highlight');
                    next.addClass('browser-highlight');
                }
            }

            if ($hlElem.get(0) !== undefined){
                scrollUp($hlElem);
            }

        }
        if (e.keyCode === 13) { // Enter
            if ($('.browser-highlight').length !== 0) {
                var url = $('.browser-highlight').find('.match-link').attr('href');
                window.location = url;
            }
        }
        if (e.keyCode === 27) { // Esc
            NodeFilter.resetFilter();
            $('html,body').scrollTop(0);
        }

        var capture_keys = [
            40, // ArrowDown
            38, // ArrowUp
            39, // ArrowRight
            37, // ArrowLeft
            13, // Enter
            27  // Esc
        ];

        if ($.inArray(e.keyCode, capture_keys) === -1) {
            clearTimeout(NodeFilter.filterTimeout);
            NodeFilter.filterTimeout = setTimeout(NodeFilter.updateFilter(n_filter, e), 200);
        }

    };

    NodeFilter.fuzzy_match = function (filepath, query) {
        var highlight = [];
        var order = 0;
        for (var i = 0; i < query.length; i++) {
            var match_position = filepath.indexOf(query[i]);
            if (match_position !== -1) {
                var prev_match_position = highlight[highlight.length - 1];
                if (prev_match_position === undefined) {
                    highlight.push(match_position);
                } else {
                    var current_match_position = prev_match_position + match_position + 1;
                    highlight.push(current_match_position);
                    order = order + current_match_position - prev_match_position;
                }
                filepath = filepath.substring(match_position + 1);
            } else {
                return false;
            }
        }
        return {
            'order': order,
            'highlight': highlight
        };
    };

    NodeFilter.sortPredicate = function (a, b) {
        if (a.order < b.order) return -1;
        if (a.order > b.order) return 1;
        if (a.filepath < b.filepath) return -1;
        if (a.filepath > b.filepath) return 1;
        return 0;
    };

    NodeFilter.updateFilter = function (elem, e) {
        return function () {
            // Reset timeout
            NodeFilter.filterTimeout = null;
            var query = elem.value.toLowerCase();
            var match = [];
            var matches_max = 20;
            if (query !== "") {
                var results = [];
                for (var k = 0; k < nodes.length; k++) {
                    var result = NodeFilter.fuzzy_match(
                            nodes[k].name.toLowerCase(), query);
                    if (result) {
                        result.type = nodes[k].type;
                        result.filepath = nodes[k].name;
                        results.push(result);
                    }
                }
                results = results.sort(NodeFilter.sortPredicate);
                var limit = matches_max;
                if (results.length < matches_max) {
                    limit = results.length;
                }
                for (var i = 0; i < limit; i++) {
                    if (query && results.length > 0) {
                        var n = results[i].filepath;
                        var t = results[i].type;
                        var n_hl = n.split("");
                        var pos = results[i].highlight;
                        for (var j = 0; j < pos.length; j++) {
                            n_hl[pos[j]] = "<em>" + n_hl[pos[j]] + "</em>";
                        }
                        n_hl = n_hl.join("");
                        var new_url = url_base.replace('__FPATH__', n);

                        var typeObj = {
                            dir: 'icon-directory browser-dir',
                            file: 'icon-file-text browser-file'
                        };

                        var typeIcon = '<i class="{0}"></i>'.format(typeObj[t]);
                        match.push('<tr class="browser-result"><td><a class="match-link" href="{0}">{1}{2}</a></td><td colspan="5"></td></tr>'.format(new_url, typeIcon, n_hl));
                    }
                }
                if (results.length > limit) {
                    var truncated_count = results.length - matches_max;
                    if (truncated_count === 1) {
                        match.push('<tr><td>{0} {1}</td><td colspan="5"></td></tr>'.format(truncated_count, _gettext('truncated result')));
                    } else {
                        match.push('<tr><td>{0} {1}</td><td colspan="5"></td></tr>'.format(truncated_count, _gettext('truncated results')));
                    }
                }
            }
            if (query !== "") {
                $('#tbody').hide();
                $('#tbody_filtered').show();

                if (match.length === 0) {
                    match.push('<tr><td>{0}</td><td colspan="5"></td></tr>'.format(_gettext('No matching files')));
                }
                $('#tbody_filtered').html(match.join(""));
            } else {
                $('#tbody').show();
                $('#tbody_filtered').hide();
            }

        };
    };

};

var getIdentNode = function(n){
  // iterate through nodes until matched interesting node
  if (typeof n === 'undefined'){
    return -1;
  }
  if(typeof n.id !== "undefined" && n.id.match('L[0-9]+')){
    return n;
  }
  else{
    return getIdentNode(n.parentNode);
  }
};

var getSelectionLink = function(e) {
  // get selection from start/to nodes
  if (typeof window.getSelection !== "undefined") {
    s = window.getSelection();

    from = getIdentNode(s.anchorNode);
    till = getIdentNode(s.focusNode);

    f_int = parseInt(from.id.replace('L',''));
    t_int = parseInt(till.id.replace('L',''));

    if (f_int > t_int){
      // highlight from bottom
      offset = -35;
      ranges = [t_int,f_int];
    }
    else{
      // highligth from top
      offset = 35;
      ranges = [f_int,t_int];
    }
    // if we select more than 2 lines
    if (ranges[0] !== ranges[1]){
      if($('#linktt').length === 0){
        hl_div = document.createElement('div');
        hl_div.id = 'linktt';
      }
      hl_div.innerHTML = '';

      anchor = '#L'+ranges[0]+'-'+ranges[1];
      var link = document.createElement('a');
      link.href = location.href.substring(0,location.href.indexOf('#'))+anchor;
      link.innerHTML = _gettext('Selection link');
      hl_div.appendChild(link);
      $('#codeblock').append(hl_div);

      var xy = $(till).offset();
      $('#linktt').addClass('hl-tip-box tip-box');
      $('#linktt').offset({top: xy.top + offset, left: xy.left});
      $('#linktt').css('visibility','visible');
    }
    else{
      $('#linktt').css('visibility','hidden');
    }
  }
};
