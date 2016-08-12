.. _user-group-methods-ref:

user_group methods
=================

add_user_to_user_group 
----------------------

.. py:function:: add_user_to_user_group(apiuser, usergroupid, userid)

   Adds a user to a `user group`. If the user already exists in the group
   this command will return false.

   This command can only be run using an |authtoken| with admin rights to
   the specified user group.

   This command takes the following options:

   :param apiuser: This is filled automatically from the |authtoken|.
   :type apiuser: AuthUser
   :param usergroupid: Set the name of the `user group` to which a
       user will be added.
   :type usergroupid: int
   :param userid: Set the `user_id` of the user to add to the group.
   :type userid: int

   Example output:

   .. code-block:: bash

     id : <id_given_in_input>
     result : {
         "success": True|False # depends on if member is in group
         "msg": "added member `<username>` to user group `<groupname>` |
                 User is already in that group"

     }
     error :  null

   Example error output:

   .. code-block:: bash

     id : <id_given_in_input>
     result : null
     error :  {
       "failed to add member to user group `<user_group_name>`"
     }


create_user_group 
-----------------

.. py:function:: create_user_group(apiuser, group_name, description=<Optional:''>, owner=<Optional:<OptionalAttr:apiuser>>, active=<Optional:True>)

   Creates a new user group.

   This command can only be run using an |authtoken| with admin rights to
   the specified repository.

   This command takes the following options:

   :param apiuser: This is filled automatically from the |authtoken|.
   :type apiuser: AuthUser
   :param group_name: Set the name of the new user group.
   :type group_name: str
   :param description: Give a description of the new user group.
   :type description: str
   :param owner: Set the owner of the new user group.
       If not set, the owner is the |authtoken| user.
   :type owner: Optional(str or int)
   :param active: Set this group as active.
   :type active: Optional(``True`` | ``False``)

   Example output:

   .. code-block:: bash

       id : <id_given_in_input>
       result: {
                 "msg": "created new user group `<groupname>`",
                 "user_group": <user_group_object>
               }
       error:  null

   Example error output:

   .. code-block:: bash

     id : <id_given_in_input>
     result : null
     error :  {
       "user group `<group name>` already exist"
       or
       "failed to create group `<group name>`"
     }


delete_user_group 
-----------------

.. py:function:: delete_user_group(apiuser, usergroupid)

   Deletes the specified `user group`.

   This command can only be run using an |authtoken| with admin rights to
   the specified repository.

   This command takes the following options:

   :param apiuser: filled automatically from apikey
   :type apiuser: AuthUser
   :param usergroupid:
   :type usergroupid: int

   Example output:

   .. code-block:: bash

     id : <id_given_in_input>
     result : {
       "msg": "deleted user group ID:<user_group_id> <user_group_name>"
     }
     error :  null

   Example error output:

   .. code-block:: bash

     id : <id_given_in_input>
     result : null
     error :  {
       "failed to delete user group ID:<user_group_id> <user_group_name>"
       or
       "RepoGroup assigned to <repo_groups_list>"
     }


get_user_group 
--------------

.. py:function:: get_user_group(apiuser, usergroupid)

   Returns the data of an existing user group.

   This command can only be run using an |authtoken| with admin rights to
   the specified repository.

   :param apiuser: This is filled automatically from the |authtoken|.
   :type apiuser: AuthUser
   :param usergroupid: Set the user group from which to return data.
   :type usergroupid: str or int

   Example error output:

   .. code-block:: bash

       {
         "error": null,
         "id": <id>,
         "result": {
           "active": true,
           "group_description": "group description",
           "group_name": "group name",
           "members": [
             {
               "name": "owner-name",
               "origin": "owner",
               "permission": "usergroup.admin",
               "type": "user"
             },
             {
             {
               "name": "user name",
               "origin": "permission",
               "permission": "usergroup.admin",
               "type": "user"
             },
             {
               "name": "user group name",
               "origin": "permission",
               "permission": "usergroup.write",
               "type": "user_group"
             }
           ],
           "owner": "owner name",
           "users": [],
           "users_group_id": 2
         }
       }


get_user_groups 
---------------

.. py:function:: get_user_groups(apiuser)

   Lists all the existing user groups within RhodeCode.

   This command can only be run using an |authtoken| with admin rights to
   the specified repository.

   This command takes the following options:

   :param apiuser: This is filled automatically from the |authtoken|.
   :type apiuser: AuthUser

   Example error output:

   .. code-block:: bash

       id : <id_given_in_input>
       result : [<user_group_obj>,...]
       error : null


grant_user_group_permission_to_user_group 
-----------------------------------------

.. py:function:: grant_user_group_permission_to_user_group(apiuser, usergroupid, sourceusergroupid, perm)

   Give one user group permissions to another user group.

   :param apiuser: This is filled automatically from the |authtoken|.
   :type apiuser: AuthUser
   :param usergroupid: Set the user group on which to edit permissions.
   :type usergroupid: str or int
   :param sourceusergroupid: Set the source user group to which
       access/permissions will be granted.
   :type sourceusergroupid: str or int
   :param perm: (usergroup.(none|read|write|admin))
   :type perm: str

   Example output:

   .. code-block:: bash

     id : <id_given_in_input>
     result : {
       "msg": "Granted perm: `<perm_name>` for user group: `<source_user_group_name>` in user group: `<user_group_name>`",
       "success": true
     }
     error :  null


grant_user_permission_to_user_group 
-----------------------------------

.. py:function:: grant_user_permission_to_user_group(apiuser, usergroupid, userid, perm)

   Set permissions for a user in a user group.

   :param apiuser: This is filled automatically from the |authtoken|.
   :type apiuser: AuthUser
   :param usergroupid: Set the user group to edit permissions on.
   :type usergroupid: str or int
   :param userid: Set the user from whom you wish to set permissions.
   :type userid: str
   :param perm: (usergroup.(none|read|write|admin))
   :type perm: str

   Example output:

   .. code-block:: bash

     id : <id_given_in_input>
     result : {
       "msg": "Granted perm: `<perm_name>` for user: `<username>` in user group: `<user_group_name>`",
       "success": true
     }
     error :  null


remove_user_from_user_group 
---------------------------

.. py:function:: remove_user_from_user_group(apiuser, usergroupid, userid)

   Removes a user from a user group.

   * If the specified user is not in the group, this command will return
     `false`.

   This command can only be run using an |authtoken| with admin rights to
   the specified user group.

   :param apiuser: This is filled automatically from the |authtoken|.
   :type apiuser: AuthUser
   :param usergroupid: Sets the user group name.
   :type usergroupid: str or int
   :param userid: The user you wish to remove from |RCE|.
   :type userid: str or int

   Example output:

   .. code-block:: bash

       id : <id_given_in_input>
       result: {
                 "success":  True|False,  # depends on if member is in group
                 "msg": "removed member <username> from user group <groupname> |
                         User wasn't in group"
               }
       error:  null


revoke_user_group_permission_from_user_group 
--------------------------------------------

.. py:function:: revoke_user_group_permission_from_user_group(apiuser, usergroupid, sourceusergroupid)

   Revoke the permissions that one user group has to another.

   :param apiuser: This is filled automatically from the |authtoken|.
   :type apiuser: AuthUser
   :param usergroupid: Set the user group on which to edit permissions.
   :type usergroupid: str or int
   :param sourceusergroupid: Set the user group from which permissions
       are revoked.
   :type sourceusergroupid: str or int

   Example output:

   .. code-block:: bash

     id : <id_given_in_input>
     result : {
       "msg": "Revoked perm for user group: `<user_group_name>` in user group: `<target_user_group_name>`",
       "success": true
     }
     error :  null


revoke_user_permission_from_user_group 
--------------------------------------

.. py:function:: revoke_user_permission_from_user_group(apiuser, usergroupid, userid)

   Revoke a users permissions in a user group.

   :param apiuser: This is filled automatically from the |authtoken|.
   :type apiuser: AuthUser
   :param usergroupid: Set the user group from which to revoke the user
       permissions.
   :type: usergroupid: str or int
   :param userid: Set the userid of the user whose permissions will be
       revoked.
   :type userid: str

   Example output:

   .. code-block:: bash

     id : <id_given_in_input>
     result : {
       "msg": "Revoked perm for user: `<username>` in user group: `<user_group_name>`",
       "success": true
     }
     error :  null


update_user_group 
-----------------

.. py:function:: update_user_group(apiuser, usergroupid, group_name=<Optional:''>, description=<Optional:''>, owner=<Optional:None>, active=<Optional:True>)

   Updates the specified `user group` with the details provided.

   This command can only be run using an |authtoken| with admin rights to
   the specified repository.

   :param apiuser: This is filled automatically from the |authtoken|.
   :type apiuser: AuthUser
   :param usergroupid: Set the id of the `user group` to update.
   :type usergroupid: str or int
   :param group_name: Set the new name the `user group`
   :type group_name: str
   :param description: Give a description for the `user group`
   :type description: str
   :param owner: Set the owner of the `user group`.
   :type owner: Optional(str or int)
   :param active: Set the group as active.
   :type active: Optional(``True`` | ``False``)

   Example output:

   .. code-block:: bash

     id : <id_given_in_input>
     result : {
       "msg": 'updated user group ID:<user group id> <user group name>',
       "user_group": <user_group_object>
     }
     error :  null

   Example error output:

   .. code-block:: bash

     id : <id_given_in_input>
     result : null
     error :  {
       "failed to update user group `<user group name>`"
     }


