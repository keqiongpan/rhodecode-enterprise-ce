// # Copyright (C) 2016-2019 RhodeCode GmbH
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


var CommitsController = function () {
    var self = this;
    this.$graphCanvas = $('#graph_canvas');
    this.$commitCounter = $('#commit-counter');

    this.getCurrentGraphData = function () {
        // raw form
        return self.$graphCanvas.data('commits');
    };

    this.setLabelText = function (graphData) {
        var shown = $('.commit_hash').length;
        var total = self.$commitCounter.data('total');

        if (shown == 1) {
            var text = _gettext('showing {0} out of {1} commit').format(shown, total);
        } else {
            var text = _gettext('showing {0} out of {1} commits').format(shown, total);
        }
        self.$commitCounter.html(text)
    };

    this.reloadGraph = function (chunk) {
        chunk = chunk || 'next';

        // reset state on re-render !
        self.$graphCanvas.html('');

        var edgeData = $("[data-graph]").data('graph') || this.$graphCanvas.data('graph') || [];
        var prev_link = $('.load-more-commits').find('.prev-commits').get(0);
        var next_link = $('.load-more-commits').find('.next-commits').get(0);

        // Determine max number of edges per row in graph
        var edgeCount = 1;
        $.each(edgeData, function (i, item) {
            $.each(item[2], function (key, value) {
                if (value[1] > edgeCount) {
                    edgeCount = value[1];
                }
            });
        });

        if (prev_link && next_link) {
            var graph_padding = -64;
        }
        else if (next_link) {
            var graph_padding = -32;
        } else {
            var graph_padding = 0;
        }

        var x_step = Math.min(10, Math.floor(86 / edgeCount));
        var height = $('#changesets').find('.commits-range').height() + graph_padding;
        var graph_options = {
            width: 100,
            height: height,
            x_step: x_step,
            y_step: 42,
            dotRadius: 3.5,
            lineWidth: 2.5
        };

        var prevCommitsData = this.$graphCanvas.data('commits') || [];
        var nextCommitsData = $("[data-graph]").data('commits') || [];

        if (chunk == 'next') {
            var commitData = $.merge(prevCommitsData, nextCommitsData);
        } else {
            var commitData = $.merge(nextCommitsData, prevCommitsData);
        }

        this.$graphCanvas.data('graph', edgeData);
        this.$graphCanvas.data('commits', commitData);

        // destroy dynamic loaded graph
        $("[data-graph]").remove();

        this.$graphCanvas.commits(graph_options);

        this.setLabelText(edgeData);

        var padding = 90;
        if (prev_link) {
            padding += 34;

        }
        $('#graph_nodes').css({'padding-top': padding});

        $.each($('.message.truncate'), function(idx, value) {
            if(!(value.offsetWidth < value.scrollWidth)){
                var expandTd = $(this).closest('td').siblings('.expand_commit');
                expandTd.find('i').hide();
                expandTd.removeAttr('title');
                expandTd.removeClass('expand_commit');
            }
        });

    };

    this.getChunkUrl = function (page, chunk, branch, commit_id, f_path) {
        var urlData = {
            'repo_name': templateContext.repo_name,
            'page': page,
            'chunk': chunk
        };

        if (branch !== undefined && branch !== '') {
            urlData['branch'] = branch;
        }
        if (commit_id !== undefined && commit_id !== '') {
            urlData['commit_id'] = commit_id;
        }
        if (f_path !== undefined && f_path !== '') {
            urlData['f_path'] = f_path;
        }

        if (urlData['commit_id'] && urlData['f_path']) {
            return pyroutes.url('repo_commits_elements_file', urlData);
        }
        else {
            return pyroutes.url('repo_commits_elements', urlData);
        }

    };

    this.loadNext = function (node, page, branch, commit_id, f_path) {
        var loadUrl = this.getChunkUrl(page, 'next', branch, commit_id, f_path);
        var postData = {'graph': JSON.stringify(this.getCurrentGraphData())};
        $(node).html('loading...').addClass('disabled').css({'cursor':'default'});
        $.post(loadUrl, postData, function (data) {
            $(node).closest('tbody').append(data);
            $(node).closest('td').remove();
            self.reloadGraph('next');
        })
    };

    this.loadPrev = function (node, page, branch, commit_id, f_path) {
        var loadUrl = this.getChunkUrl(page, 'prev', branch, commit_id, f_path);
        var postData = {'graph': JSON.stringify(this.getCurrentGraphData())};
        $(node).html('loading...').addClass('disabled').css({'cursor':'default'});
        $.post(loadUrl, postData, function (data) {
            $(node).closest('tbody').prepend(data);
            $(node).closest('td').remove();
            self.reloadGraph('prev');
        })
    };

    this.expandCommit = function (node, reloadGraph) {
        reloadGraph = reloadGraph || false;

        var target_expand = $(node);
        var cid = target_expand.data('commitId');

        if (target_expand.hasClass('open')) {
            $('#c-' + cid).css({
                'height': '1.5em',
                'white-space': 'nowrap',
                'text-overflow': 'ellipsis',
                'overflow': 'hidden'
            });
            $('#t-' + cid).css({
                'height': 'auto',
                'line-height': '.9em',
                'text-overflow': 'ellipsis',
                'overflow': 'hidden',
                'white-space': 'nowrap'
            });
            target_expand.removeClass('open');
        }
        else {
            $('#c-' + cid).css({
                'height': 'auto',
                'white-space': 'pre-line',
                'text-overflow': 'initial',
                'overflow': 'visible'
            });
            $('#t-' + cid).css({
                'height': 'auto',
                'max-height': 'none',
                'text-overflow': 'initial',
                'overflow': 'visible',
                'white-space': 'normal'
            });
            target_expand.addClass('open');
        }

        if (reloadGraph) {
            // redraw the graph
            self.reloadGraph();
        }
    }
};
