<div class="panel panel-default">
    <div class="panel-heading">
      <h3 class="panel-title">${_('Authentication Tokens')}</h3>
    </div>
    <div class="panel-body">
        <div class="apikeys_wrap">
          <p>
             ${_('Each token can have a role. Token with a role can be used only in given context, '
             'e.g. VCS tokens can be used together with the authtoken auth plugin for git/hg/svn operations only.')}
          </p>
          <table class="rctable auth_tokens">
            <tr>
                <th>${_('Token')}</th>
                <th>${_('Scope')}</th>
                <th>${_('Description')}</th>
                <th>${_('Role')}</th>
                <th>${_('Expiration')}</th>
                <th>${_('Action')}</th>
            </tr>
            %if c.user_auth_tokens:
                %for auth_token in c.user_auth_tokens:
                  <tr class="${'expired' if auth_token.expired else ''}">
                    <td class="truncate-wrap td-authtoken"><div class="user_auth_tokens truncate autoexpand"><code>${auth_token.api_key}</code></div></td>
                    <td class="td">${auth_token.scope_humanized}</td>
                    <td class="td-wrap">${auth_token.description}</td>
                    <td class="td-tags">
                        <span class="tag disabled">${auth_token.role_humanized}</span>
                    </td>
                    <td class="td-exp">
                         %if auth_token.expires == -1:
                          ${_('never')}
                         %else:
                            %if auth_token.expired:
                                <span style="text-decoration: line-through">${h.age_component(h.time_to_utcdatetime(auth_token.expires))}</span>
                            %else:
                                ${h.age_component(h.time_to_utcdatetime(auth_token.expires))}
                            %endif
                         %endif
                    </td>
                    <td class="td-action">
                        ${h.secure_form(h.route_path('edit_user_auth_tokens_delete', user_id=c.user.user_id), method='POST', request=request)}
                            ${h.hidden('del_auth_token', auth_token.user_api_key_id)}
                            <button class="btn btn-link btn-danger" type="submit"
                                    onclick="return confirm('${_('Confirm to remove this auth token: %s') % auth_token.token_obfuscated}');">
                                ${_('Delete')}
                            </button>
                        ${h.end_form()}
                    </td>
                  </tr>
                %endfor
            %else:
            <tr><td><div class="ip">${_('No additional auth tokens specified')}</div></td></tr>
            %endif
          </table>
        </div>

        <div class="user_auth_tokens">
            ${h.secure_form(h.route_path('edit_user_auth_tokens_add', user_id=c.user.user_id), method='POST', request=request)}
            <div class="form form-vertical">
                <!-- fields -->
                <div class="fields">
                     <div class="field">
                        <div class="label">
                            <label for="new_email">${_('New authentication token')}:</label>
                        </div>
                        <div class="input">
                            ${h.text('description', class_='medium', placeholder=_('Description'))}
                            ${h.hidden('lifetime')}
                            ${h.select('role', '', c.role_options)}

                            % if c.allow_scoped_tokens:
                                ${h.hidden('scope_repo_id')}
                            % else:
                                ${h.select('scope_repo_id_disabled', '', ['Scopes available in EE edition'], disabled='disabled')}
                            % endif
                        </div>
                        <p class="help-block">
                          ${_('Repository scope works only with tokens with VCS type.')}
                        </p>
                     </div>
                    <div class="buttons">
                      ${h.submit('save',_('Add'),class_="btn")}
                      ${h.reset('reset',_('Reset'),class_="btn")}
                    </div>
                </div>
            </div>
            ${h.end_form()}
        </div>
    </div>
</div>

<script>

$(document).ready(function(){
var select2Options = {
    'containerCssClass': "drop-menu",
    'dropdownCssClass': "drop-menu-dropdown",
    'dropdownAutoWidth': true
};
$("#role").select2(select2Options);

var preloadData = {
    results: [
        % for entry in c.lifetime_values:
            {id:${entry[0]}, text:"${entry[1]}"}${'' if loop.last else ','}
        % endfor
    ]
};

$("#lifetime").select2({
    containerCssClass: "drop-menu",
    dropdownCssClass: "drop-menu-dropdown",
    dropdownAutoWidth: true,
    data: preloadData,
    placeholder: "${_('Select or enter expiration date')}",
    query: function(query) {
        feedLifetimeOptions(query, preloadData);
    }
});


var repoFilter = function(data) {
    var results = [];

    if (!data.results[0]) {
        return data
    }

    $.each(data.results[0].children, function() {
        // replace name to ID for submision
        this.id = this.obj.repo_id;
        results.push(this);
    });

    data.results[0].children = results;
    return data;
};

$("#scope_repo_id_disabled").select2(select2Options);

$("#scope_repo_id").select2({
    cachedDataSource: {},
    minimumInputLength: 2,
    placeholder: "${_('repository scope')}",
    dropdownAutoWidth: true,
    containerCssClass: "drop-menu",
    dropdownCssClass: "drop-menu-dropdown",
    formatResult: formatResult,
    query: $.debounce(250, function(query){
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
                success: function(data) {
                    data = repoFilter(data);
                    self.cachedDataSource[cacheKey] = data;
                    query.callback({results: data.results});
                },
                error: function(data, textStatus, errorThrown) {
                    alert("Error while fetching entries.\nError code {0} ({1}).".format(data.status, data.statusText));
                }
})
        }
    })
});

});
</script>
