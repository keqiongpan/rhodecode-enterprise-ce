## -*- coding: utf-8 -*-
<%namespace name="base" file="/base/base.mako"/>

<div class="panel panel-default">
    <div class="panel-heading">
        <h3 class="panel-title">${_('User Group: %s') % c.user_group.users_group_name}</h3>
    </div>
    <div class="panel-body">
    ${h.secure_form(h.url('update_users_group', user_group_id=c.user_group.users_group_id),method='put', id='edit_users_group')}
        <div class="form">
            <!-- fields -->
                <div class="fields">
                     <div class="field">
                        <div class="label">
                            <label for="users_group_name">${_('Group name')}:</label>
                        </div>
                        <div class="input">
                            ${h.text('users_group_name',class_='medium')}
                        </div>
                     </div>

                    <div class="field badged-field">
                        <div class="label">
                            <label for="user">${_('Owner')}:</label>
                        </div>
                        <div class="input">
                            <div class="badge-input-container">
                                <div class="user-badge">
                                    ${base.gravatar_with_user(c.user_group.user.email, show_disabled=not c.user_group.user.active)}
                                </div>
                                <div class="badge-input-wrap">
                                    ${h.text('user', class_="medium", autocomplete="off")}
                                </div>
                            </div>
                            <form:error name="user"/>
                            <p class="help-block">${_('Change owner of this user group.')}</p>
                        </div>
                    </div>

                     <div class="field">
                        <div class="label label-textarea">
                            <label for="user_group_description">${_('Description')}:</label>
                        </div>
                        <div class="textarea textarea-small editor">
                            ${h.textarea('user_group_description',cols=23,rows=5,class_="medium")}
                            <span class="help-block">${_('Short, optional description for this user group.')}</span>
                        </div>
                     </div>
                     <div class="field">
                        <div class="label label-checkbox">
                            <label for="users_group_active">${_('Active')}:</label>
                        </div>
                        <div class="checkboxes">
                            ${h.checkbox('users_group_active',value=True)}
                        </div>
                     </div>

                     <div class="field">
                        <div class="label label-checkbox">
                            <label for="users_group_active">${_('Add members')}:</label>
                        </div>
                        <div class="input">
                            ${h.text('user_group_add_members', placeholder="user/usergroup", class_="medium")}
                        </div>
                     </div>

                    <input type="hidden" name="__start__" value="user_group_members:sequence"/>
                    <table id="group_members_placeholder" class="rctable group_members">
                        <tr>
                          <th>${_('Username')}</th>
                          <th>${_('Action')}</th>
                        </tr>

                        % if c.group_members_obj:
                          % for user in c.group_members_obj:
                            <tr>
                              <td id="member_user_${user.user_id}" class="td-author">
                                <div class="group_member">
                                  ${base.gravatar(user.email, 16)}
                                  <span class="username user">${h.link_to(h.person(user), h.url( 'edit_user',user_id=user.user_id))}</span>
                                  <input type="hidden" name="__start__" value="member:mapping">
                                  <input type="hidden" name="member_user_id" value="${user.user_id}">
                                  <input type="hidden" name="type" value="existing" id="member_${user.user_id}">
                                  <input type="hidden" name="__end__" value="member:mapping">
                                </div>
                              </td>
                              <td class="">
                                <div class="usergroup_member_remove action_button" onclick="removeUserGroupMember(${user.user_id}, true)" style="visibility: visible;">
                                    <i class="icon-remove-sign"></i>
                                </div>
                              </td>
                            </tr>
                          % endfor

                        % else:
                          <tr><td colspan="2">${_('No members yet')}</td></tr>
                        % endif
                     </table>
                    <input type="hidden" name="__end__" value="user_group_members:sequence"/>

                     <div class="buttons">
                       ${h.submit('Save',_('Save'),class_="btn")}
                     </div>
                </div>
        </div>
    ${h.end_form()}
    </div>
</div>
<script>
    $(document).ready(function(){
        $("#group_parent_id").select2({
            'containerCssClass': "drop-menu",
            'dropdownCssClass': "drop-menu-dropdown",
            'dropdownAutoWidth': true
        });

        removeUserGroupMember = function(userId){
            $('#member_'+userId).val('remove');
            $('#member_user_'+userId).addClass('to-delete');
        };

        $('#user_group_add_members').autocomplete({
            serviceUrl: pyroutes.url('user_autocomplete_data'),
            minChars:2,
            maxHeight:400,
            width:300,
            deferRequestBy: 300, //miliseconds
            showNoSuggestionNotice: true,
            params: { user_groups:true },
            formatResult: autocompleteFormatResult,
            lookupFilter: autocompleteFilterResult,
            onSelect: function(element, suggestion){

                function addMember(user, fromUserGroup) {
                    var gravatar = user.icon_link;
                    var username = user.value_display;
                    var userLink = pyroutes.url('edit_user', {"user_id": user.id});
                    var uid = user.id;

                    if (fromUserGroup) {
                        username = username +" "+ _gettext('(from usergroup {0})'.format(fromUserGroup))
                    }

                    var elem = $(
                        ('<tr>'+
                          '<td id="member_user_{6}" class="td-author td-author-new-entry">'+
                            '<div class="group_member">'+
                              '<img class="gravatar" src="{0}" height="16" width="16">'+
                              '<span class="username user"><a href="{1}">{2}</a></span>'+
                              '<input type="hidden" name="__start__" value="member:mapping">'+
                              '<input type="hidden" name="member_user_id" value="{3}">'+
                              '<input type="hidden" name="type" value="new" id="member_{4}">'+
                              '<input type="hidden" name="__end__" value="member:mapping">'+
                            '</div>'+
                          '</td>'+
                          '<td class="td-author-new-entry">'+
                            '<div class="usergroup_member_remove action_button" onclick="removeUserGroupMember({5}, true)" style="visibility: visible;">'+
                                '<i class="icon-remove-sign"></i>'+
                            '</div>'+
                          '</td>'+
                        '</tr>').format(gravatar, userLink, username,
                                uid, uid, uid, uid)
                    );
                    $('#group_members_placeholder').append(elem)
                }

                if (suggestion.value_type == 'user_group') {
                    $.getJSON(
                        pyroutes.url('edit_user_group_members',
                                    {'user_group_id': suggestion.id}),
                        function(data) {
                            $.each(data.members, function(idx, user) {
                                addMember(user, suggestion.value)
                            });
                        }
                    );
                } else if (suggestion.value_type == 'user') {
                    addMember(suggestion, null);
                }
            }
        });


        UsersAutoComplete('user', '${c.rhodecode_user.user_id}');
    })
</script>
