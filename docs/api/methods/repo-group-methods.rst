.. _repo-group-methods-ref:

repo_group methods
==================

create_repo_group 
-----------------

.. py:function:: create_repo_group(apiuser, group_name, description=<Optional:''>, owner=<Optional:<OptionalAttr:apiuser>>, copy_permissions=<Optional:False>)

   Creates a repository group.

   * If the repository group name contains "/", all the required repository
     groups will be created.

     For example "foo/bar/baz" will create |repo| groups "foo" and "bar"
     (with "foo" as parent). It will also create the "baz" repository
     with "bar" as |repo| group.

   This command can only be run using an |authtoken| with admin
   permissions.

   :param apiuser: This is filled automatically from the |authtoken|.
   :type apiuser: AuthUser
   :param group_name: Set the repository group name.
   :type group_name: str
   :param description: Set the |repo| group description.
   :type description: str
   :param owner: Set the |repo| group owner.
   :type owner: str
   :param copy_permissions:
   :type copy_permissions:

   Example output:

   .. code-block:: bash

     id : <id_given_in_input>
     result : {
         "msg": "Created new repo group `<repo_group_name>`"
         "repo_group": <repogroup_object>
     }
     error :  null


   Example error output:

   .. code-block:: bash

     id : <id_given_in_input>
     result : null
     error :  {
       failed to create repo group `<repogroupid>`
     }


delete_repo_group 
-----------------

.. py:function:: delete_repo_group(apiuser, repogroupid)

   Deletes a |repo| group.

   :param apiuser: This is filled automatically from the |authtoken|.
   :type apiuser: AuthUser
   :param repogroupid: Set the name or ID of repository group to be
       deleted.
   :type repogroupid: str or int

   Example output:

   .. code-block:: bash

     id : <id_given_in_input>
     result : {
       'msg': 'deleted repo group ID:<repogroupid> <repogroupname>
       'repo_group': null
     }
     error :  null

   Example error output:

   .. code-block:: bash

     id : <id_given_in_input>
     result : null
     error :  {
       "failed to delete repo group ID:<repogroupid> <repogroupname>"
     }


get_repo_group 
--------------

.. py:function:: get_repo_group(apiuser, repogroupid)

   Return the specified |repo| group, along with permissions,
   and repositories inside the group

   :param apiuser: This is filled automatically from the |authtoken|.
   :type apiuser: AuthUser
   :param repogroupid: Specify the name of ID of the repository group.
   :type repogroupid: str or int


   Example output:

   .. code-block:: bash

       {
         "error": null,
         "id": repo-group-id,
         "result": {
           "group_description": "repo group description",
           "group_id": 14,
           "group_name": "group name",
           "members": [
             {
               "name": "super-admin-username",
               "origin": "super-admin",
               "permission": "group.admin",
               "type": "user"
             },
             {
               "name": "owner-name",
               "origin": "owner",
               "permission": "group.admin",
               "type": "user"
             },
             {
               "name": "user-group-name",
               "origin": "permission",
               "permission": "group.write",
               "type": "user_group"
             }
           ],
           "owner": "owner-name",
           "parent_group": null,
           "repositories": [ repo-list ]
         }
       }


get_repo_groups 
---------------

.. py:function:: get_repo_groups(apiuser)

   Returns all repository groups.

   :param apiuser: This is filled automatically from the |authtoken|.
   :type apiuser: AuthUser


grant_user_group_permission_to_repo_group 
-----------------------------------------

.. py:function:: grant_user_group_permission_to_repo_group(apiuser, repogroupid, usergroupid, perm, apply_to_children=<Optional:'none'>)

   Grant permission for a user group on given repository group, or update
   existing permissions if found.

   This command can only be run using an |authtoken| with admin
   permissions on the |repo| group.

   :param apiuser: This is filled automatically from the |authtoken|.
   :type apiuser: AuthUser
   :param repogroupid: Set the name or id of repository group
   :type repogroupid: str or int
   :param usergroupid: id of usergroup
   :type usergroupid: str or int
   :param perm: (group.(none|read|write|admin))
   :type perm: str
   :param apply_to_children: 'none', 'repos', 'groups', 'all'
   :type apply_to_children: str

   Example output:

   .. code-block:: bash

     id : <id_given_in_input>
     result : {
       "msg" : "Granted perm: `<perm>` (recursive:<apply_to_children>) for user group: `<usersgroupname>` in repo group: `<repo_group_name>`",
       "success": true

     }
     error :  null

   Example error output:

   .. code-block:: bash

     id : <id_given_in_input>
     result : null
     error :  {
       "failed to edit permission for user group: `<usergroup>` in repo group: `<repo_group_name>`"
     }


grant_user_permission_to_repo_group 
-----------------------------------

.. py:function:: grant_user_permission_to_repo_group(apiuser, repogroupid, userid, perm, apply_to_children=<Optional:'none'>)

   Grant permission for a user on the given repository group, or update
   existing permissions if found.

   This command can only be run using an |authtoken| with admin
   permissions.

   :param apiuser: This is filled automatically from the |authtoken|.
   :type apiuser: AuthUser
   :param repogroupid: Set the name or ID of repository group.
   :type repogroupid: str or int
   :param userid: Set the user name.
   :type userid: str
   :param perm: (group.(none|read|write|admin))
   :type perm: str
   :param apply_to_children: 'none', 'repos', 'groups', 'all'
   :type apply_to_children: str

   Example output:

   .. code-block:: bash

       id : <id_given_in_input>
       result: {
                 "msg" : "Granted perm: `<perm>` (recursive:<apply_to_children>) for user: `<username>` in repo group: `<repo_group_name>`",
                 "success": true
               }
       error:  null

   Example error output:

   .. code-block:: bash

     id : <id_given_in_input>
     result : null
     error :  {
       "failed to edit permission for user: `<userid>` in repo group: `<repo_group_name>`"
     }


revoke_user_group_permission_from_repo_group 
--------------------------------------------

.. py:function:: revoke_user_group_permission_from_repo_group(apiuser, repogroupid, usergroupid, apply_to_children=<Optional:'none'>)

   Revoke permission for user group on given repository.

   This command can only be run using an |authtoken| with admin
   permissions on the |repo| group.

   :param apiuser: This is filled automatically from the |authtoken|.
   :type apiuser: AuthUser
   :param repogroupid: name or id of repository group
   :type repogroupid: str or int
   :param usergroupid:
   :param apply_to_children: 'none', 'repos', 'groups', 'all'
   :type apply_to_children: str

   Example output:

   .. code-block:: bash

       id : <id_given_in_input>
       result: {
                 "msg" : "Revoked perm (recursive:<apply_to_children>) for user group: `<usersgroupname>` in repo group: `<repo_group_name>`",
                 "success": true
               }
       error:  null

   Example error output:

   .. code-block:: bash

     id : <id_given_in_input>
     result : null
     error :  {
       "failed to edit permission for user group: `<usergroup>` in repo group: `<repo_group_name>`"
     }


revoke_user_permission_from_repo_group 
--------------------------------------

.. py:function:: revoke_user_permission_from_repo_group(apiuser, repogroupid, userid, apply_to_children=<Optional:'none'>)

   Revoke permission for a user in a given repository group.

   This command can only be run using an |authtoken| with admin
   permissions on the |repo| group.

   :param apiuser: This is filled automatically from the |authtoken|.
   :type apiuser: AuthUser
   :param repogroupid: Set the name or ID of the repository group.
   :type repogroupid: str or int
   :param userid: Set the user name to revoke.
   :type userid: str
   :param apply_to_children: 'none', 'repos', 'groups', 'all'
   :type apply_to_children: str

   Example output:

   .. code-block:: bash

       id : <id_given_in_input>
       result: {
                 "msg" : "Revoked perm (recursive:<apply_to_children>) for user: `<username>` in repo group: `<repo_group_name>`",
                 "success": true
               }
       error:  null

   Example error output:

   .. code-block:: bash

     id : <id_given_in_input>
     result : null
     error :  {
       "failed to edit permission for user: `<userid>` in repo group: `<repo_group_name>`"
     }


update_repo_group 
-----------------

.. py:function:: update_repo_group(apiuser, repogroupid, group_name=<Optional:''>, description=<Optional:''>, owner=<Optional:<OptionalAttr:apiuser>>, parent=<Optional:None>, enable_locking=<Optional:False>)

   Updates repository group with the details given.

   This command can only be run using an |authtoken| with admin
   permissions.

   :param apiuser: This is filled automatically from the |authtoken|.
   :type apiuser: AuthUser
   :param repogroupid: Set the ID of repository group.
   :type repogroupid: str or int
   :param group_name: Set the name of the |repo| group.
   :type group_name: str
   :param description: Set a description for the group.
   :type description: str
   :param owner: Set the |repo| group owner.
   :type owner: str
   :param parent: Set the |repo| group parent.
   :type parent: str or int
   :param enable_locking: Enable |repo| locking. The default is false.
   :type enable_locking: bool


