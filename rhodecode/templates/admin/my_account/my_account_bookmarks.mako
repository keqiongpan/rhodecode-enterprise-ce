<%namespace name="dt" file="/data_table/_dt_elements.mako"/>

<%def name="form_item(position=None, title=None, redirect_url=None, repo=None, repo_group=None)">
    <tr>
        <td class="td-align-top" >
            <div class="label">
                <label for="position">${_('Position')}:</label>
            </div>
            <div class="input">
                <input type="text" name="position" value="${position}" style="width: 40px"/>
                ${h.hidden('cur_position', position)}
            </div>
        </td>

        <td>
            <div class="label">
                <label for="title">${_('Bookmark title (max 30 characters, optional)')}:</label>
            </div>
            <div class="input">
                <input type="text" name="title" value="${title}" style="width: 300px" maxlength="30"/>

                <div class="field pull-right">
                    <div>
                        <label class="btn-link btn-danger">${_('Clear')}:</label>
                        ${h.checkbox('remove', value=True)}
                    </div>
                </div>
            </div>

            <div class="label" style="margin-top:10px">
                <label for="redirect_url">${_('Redirect URL')}:</label>
            </div>
            <div class="input">
                <input type="text" name="redirect_url" value="${redirect_url}" style="width: 600px"/>
            </div>
            <p class="help-block help-block-inline">
                ${_('Server URL is available as ${server_url} variable. E.g. Redirect url: ${server_url}/_admin/exception_tracker')}
            </p>

            <div class="select" style="margin-top:5px">
                <div class="label">
                    <label for="redirect_url">${_('Templates')}:</label>
                </div>

                % if repo:
                    ${dt.repo_name(name=repo.repo_name, rtype=repo.repo_type,rstate=None,private=None,archived=False,fork_of=False)}
                    ${h.hidden('bookmark_repo', repo.repo_id)}
                % elif repo_group:
                    ${dt.repo_group_name(repo_group.group_name)}
                    ${h.hidden('bookmark_repo_group', repo_group.group_id)}
                % else:
                    <div>
                        ${h.hidden('bookmark_repo', class_='bookmark_repo')}
                        <p class="help-block help-block-inline">${_('Available as ${repo_url}  e.g. Redirect url: ${repo_url}/changelog')}</p>
                    </div>
                    <div style="margin-top:5px">
                        ${h.hidden('bookmark_repo_group', class_='bookmark_repo_group')}
                        <p class="help-block help-block-inline">${_('Available as ${repo_group_url} e.g. Redirect url: ${repo_group_url}')}</p>
                    </div>

                % endif
            </div>

        </td>

    </tr>
</%def>

<div class="panel panel-default">
    <div class="panel-heading">
        <h3 class="panel-title">${_('Your Bookmarks')}</h3>
    </div>

    <div class="panel-body">
        <p>
            ${_('Store upto 10 bookmark links to favorite repositories, external issue tracker or CI server. ')}
            <br/>
            ${_('Bookmarks are accessible from your username dropdown or by keyboard shortcut `g 0-9`')}
        </p>

        ${h.secure_form(h.route_path('my_account_bookmarks_update'), request=request)}
        <div class="form-vertical">
        <table class="rctable">
        ## generate always 10 entries
        <input type="hidden" name="__start__" value="bookmarks:sequence"/>
        % for item in (c.bookmark_items + [None for i in range(10)])[:10]:
            <input type="hidden" name="__start__" value="bookmark:mapping"/>
            % if item is None:
                ## empty placehodlder
                ${form_item()}
            % else:
                ## actual entry
                ${form_item(position=item.position, title=item.title, redirect_url=item.redirect_url, repo=item.repository, repo_group=item.repository_group)}
            % endif
            <input type="hidden" name="__end__" value="bookmark:mapping"/>
        % endfor
        <input type="hidden" name="__end__" value="bookmarks:sequence"/>
        </table>
        <div class="buttons">
          ${h.submit('save',_('Save'),class_="btn")}
        </div>
        </div>
        ${h.end_form()}
    </div>
</div>

<script>
$(document).ready(function(){


    var repoFilter = function (data) {
        var results = [];

        if (!data.results[0]) {
            return data
        }

        $.each(data.results[0].children, function () {
            // replace name to ID for submision
            this.id = this.repo_id;
            results.push(this);
        });

        data.results[0].children = results;
        return data;
    };


    $(".bookmark_repo").select2({
        cachedDataSource: {},
        minimumInputLength: 2,
        placeholder: "${_('repository')}",
        dropdownAutoWidth: true,
        containerCssClass: "drop-menu",
        dropdownCssClass: "drop-menu-dropdown",
        formatResult: formatRepoResult,
        query: $.debounce(250, function (query) {
            self = this;
            var cacheKey = query.term;
            var cachedData = self.cachedDataSource[cacheKey];

            if (cachedData) {
                query.callback({results: cachedData.results});
            } else {
                $.ajax({
                    url: pyroutes.url('repo_list_data'),
                    data: {'query': query.term},
                    dataType: 'json',
                    type: 'GET',
                    success: function (data) {
                        data = repoFilter(data);
                        self.cachedDataSource[cacheKey] = data;
                        query.callback({results: data.results});
                    },
                    error: function (data, textStatus, errorThrown) {
                        alert("Error while fetching entries.\nError code {0} ({1}).".format(data.status, data.statusText));
                    }
                })
            }
        }),
    });

    var repoGroupFilter = function (data) {
        var results = [];

        if (!data.results[0]) {
            return data
        }

        $.each(data.results[0].children, function () {
            // replace name to ID for submision
            this.id = this.repo_group_id;
            results.push(this);
        });

        data.results[0].children = results;
        return data;
    };

    $(".bookmark_repo_group").select2({
        cachedDataSource: {},
        minimumInputLength: 2,
        placeholder: "${_('repository group')}",
        dropdownAutoWidth: true,
        containerCssClass: "drop-menu",
        dropdownCssClass: "drop-menu-dropdown",
        formatResult: formatRepoGroupResult,
        query: $.debounce(250, function (query) {
            self = this;
            var cacheKey = query.term;
            var cachedData = self.cachedDataSource[cacheKey];

            if (cachedData) {
                query.callback({results: cachedData.results});
            } else {
                $.ajax({
                    url: pyroutes.url('repo_group_list_data'),
                    data: {'query': query.term},
                    dataType: 'json',
                    type: 'GET',
                    success: function (data) {
                        data = repoGroupFilter(data);
                        self.cachedDataSource[cacheKey] = data;
                        query.callback({results: data.results});
                    },
                    error: function (data, textStatus, errorThrown) {
                        alert("Error while fetching entries.\nError code {0} ({1}).".format(data.status, data.statusText));
                    }
                })
            }
        })
    });


});

</script>
