<%namespace name="dt" file="/data_table/_dt_elements.mako"/>

<%def name="form_item(count, position=None, title=None, redirect_url=None, repo=None, repo_group=None)">
    <tr>
        <td class="td-align-top" >
            <div class="label">
                <label for="position">${_('Position')}:</label>
            </div>
            <div class="input">
                <input type="text" name="position" value="${position or count}" style="width: 40px"/>
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

            <div class="label">
                <label for="redirect_url">${_('Redirect URL')}:</label>
            </div>
            <div class="input">
                <input type="text" name="redirect_url" value="${redirect_url}" style="width: 600px"/>
            </div>


            <div class="select">
                % if repo:
                    <div class="label">
                        <label for="redirect_url">${_('Repository template')}:</label>
                    </div>
                    ${dt.repo_name(name=repo.repo_name, rtype=repo.repo_type,rstate=None,private=None,archived=False,fork_of=False)}
                    ${h.hidden('bookmark_repo', repo.repo_id)}
                % elif repo_group:
                    <div class="label">
                        <label for="redirect_url">${_('Repository group template')}:</label>
                    </div>
                    ${dt.repo_group_name(repo_group.group_name)}
                    ${h.hidden('bookmark_repo_group', repo_group.group_id)}
                % else:
                    <div class="label">
                        <label for="redirect_url">${_('Template Repository or Repository group')}:</label>
                    </div>
                    ${h.hidden('bookmark_repo', class_='bookmark_repo')}
                    <span style="padding-right:15px">OR</span>
                    ${h.hidden('bookmark_repo_group', class_='bookmark_repo_group')}
                % endif
            </div>

            <p class="help-block help-block-inline" >
            % if repo:
                ${_('Available as ${repo_url}  e.g. Redirect url: ${repo_url}/changelog')}
            % elif repo_group:
                ${_('Available as ${repo_group_url} e.g. Redirect url: ${repo_group_url}')}
            % else:
                ${_('Available as full url variables in redirect url. i.e: ${repo_url}, ${repo_group_url}.')}
            % endif
            </p>
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
        % for cnt, item in enumerate((c.bookmark_items + [None for i in range(10)])[:10]):
            <input type="hidden" name="__start__" value="bookmark:mapping"/>
            % if item is None:
                ## empty placehodlder
                ${form_item(cnt)}
            % else:
                ## actual entry
                ${form_item(cnt, position=item.position, title=item.title, redirect_url=item.redirect_url, repo=item.repository, repo_group=item.repository_group)}
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
