.. _repo-methods-ref:

repo methods
============

add_field_to_repo 
-----------------

.. py:function:: add_field_to_repo(apiuser, repoid, key, label=<Optional:''>, description=<Optional:''>)

   Adds an extra field to a repository.

   This command can only be run using an |authtoken| with at least
   write permissions to the |repo|.

   :param apiuser: This is filled automatically from the |authtoken|.
   :type apiuser: AuthUser
   :param repoid: Set the repository name or repository id.
   :type repoid: str or int
   :param key: Create a unique field key for this repository.
   :type key: str
   :param label:
   :type label: Optional(str)
   :param description:
   :type description: Optional(str)


comment_commit 
--------------

.. py:function:: comment_commit(apiuser, repoid, commit_id, message, status=<Optional:None>, comment_type=<Optional:u'note'>, resolves_comment_id=<Optional:None>, userid=<Optional:<OptionalAttr:apiuser>>)

   Set a commit comment, and optionally change the status of the commit.

   :param apiuser: This is filled automatically from the |authtoken|.
   :type apiuser: AuthUser
   :param repoid: Set the repository name or repository ID.
   :type repoid: str or int
   :param commit_id: Specify the commit_id for which to set a comment.
   :type commit_id: str
   :param message: The comment text.
   :type message: str
   :param status: (**Optional**) status of commit, one of: 'not_reviewed',
       'approved', 'rejected', 'under_review'
   :type status: str
   :param comment_type: Comment type, one of: 'note', 'todo'
   :type comment_type: Optional(str), default: 'note'
   :param userid: Set the user name of the comment creator.
   :type userid: Optional(str or int)

   Example error output:

   .. code-block:: bash

       {
           "id" : <id_given_in_input>,
           "result" : {
               "msg": "Commented on commit `<commit_id>` for repository `<repoid>`",
               "status_change": null or <status>,
               "success": true
           },
           "error" :  null
       }


create_repo 
-----------

.. py:function:: create_repo(apiuser, repo_name, repo_type, owner=<Optional:<OptionalAttr:apiuser>>, description=<Optional:''>, private=<Optional:False>, clone_uri=<Optional:None>, push_uri=<Optional:None>, landing_rev=<Optional:'rev:tip'>, enable_statistics=<Optional:False>, enable_locking=<Optional:False>, enable_downloads=<Optional:False>, copy_permissions=<Optional:False>)

   Creates a repository.

   * If the repository name contains "/", repository will be created inside
     a repository group or nested repository groups

     For example "foo/bar/repo1" will create |repo| called "repo1" inside
     group "foo/bar". You have to have permissions to access and write to
     the last repository group ("bar" in this example)

   This command can only be run using an |authtoken| with at least
   permissions to create repositories, or write permissions to
   parent repository groups.

   :param apiuser: This is filled automatically from the |authtoken|.
   :type apiuser: AuthUser
   :param repo_name: Set the repository name.
   :type repo_name: str
   :param repo_type: Set the repository type; 'hg','git', or 'svn'.
   :type repo_type: str
   :param owner: user_id or username
   :type owner: Optional(str)
   :param description: Set the repository description.
   :type description: Optional(str)
   :param private: set repository as private
   :type private: bool
   :param clone_uri: set clone_uri
   :type clone_uri: str
   :param push_uri: set push_uri
   :type push_uri: str
   :param landing_rev: <rev_type>:<rev>
   :type landing_rev: str
   :param enable_locking:
   :type enable_locking: bool
   :param enable_downloads:
   :type enable_downloads: bool
   :param enable_statistics:
   :type enable_statistics: bool
   :param copy_permissions: Copy permission from group in which the
       repository is being created.
   :type copy_permissions: bool


   Example output:

   .. code-block:: bash

       id : <id_given_in_input>
       result: {
                 "msg": "Created new repository `<reponame>`",
                 "success": true,
                 "task": "<celery task id or None if done sync>"
               }
       error:  null


   Example error output:

   .. code-block:: bash

     id : <id_given_in_input>
     result : null
     error :  {
        'failed to create repository `<repo_name>`'
     }


delete_repo 
-----------

.. py:function:: delete_repo(apiuser, repoid, forks=<Optional:''>)

   Deletes a repository.

   * When the `forks` parameter is set it's possible to detach or delete
     forks of deleted repository.

   This command can only be run using an |authtoken| with admin
   permissions on the |repo|.

   :param apiuser: This is filled automatically from the |authtoken|.
   :type apiuser: AuthUser
   :param repoid: Set the repository name or repository ID.
   :type repoid: str or int
   :param forks: Set to `detach` or `delete` forks from the |repo|.
   :type forks: Optional(str)

   Example error output:

   .. code-block:: bash

       id : <id_given_in_input>
       result: {
                 "msg": "Deleted repository `<reponame>`",
                 "success": true
               }
       error:  null


fork_repo 
---------

.. py:function:: fork_repo(apiuser, repoid, fork_name, owner=<Optional:<OptionalAttr:apiuser>>, description=<Optional:''>, private=<Optional:False>, clone_uri=<Optional:None>, landing_rev=<Optional:'rev:tip'>, copy_permissions=<Optional:False>)

   Creates a fork of the specified |repo|.

   * If the fork_name contains "/", fork will be created inside
     a repository group or nested repository groups

     For example "foo/bar/fork-repo" will create fork called "fork-repo"
     inside group "foo/bar". You have to have permissions to access and
     write to the last repository group ("bar" in this example)

   This command can only be run using an |authtoken| with minimum
   read permissions of the forked repo, create fork permissions for an user.

   :param apiuser: This is filled automatically from the |authtoken|.
   :type apiuser: AuthUser
   :param repoid: Set repository name or repository ID.
   :type repoid: str or int
   :param fork_name: Set the fork name, including it's repository group membership.
   :type fork_name: str
   :param owner: Set the fork owner.
   :type owner: str
   :param description: Set the fork description.
   :type description: str
   :param copy_permissions: Copy permissions from parent |repo|. The
       default is False.
   :type copy_permissions: bool
   :param private: Make the fork private. The default is False.
   :type private: bool
   :param landing_rev: Set the landing revision. The default is tip.

   Example output:

   .. code-block:: bash

       id : <id_for_response>
       api_key : "<api_key>"
       args:     {
                   "repoid" :          "<reponame or repo_id>",
                   "fork_name":        "<forkname>",
                   "owner":            "<username or user_id = Optional(=apiuser)>",
                   "description":      "<description>",
                   "copy_permissions": "<bool>",
                   "private":          "<bool>",
                   "landing_rev":      "<landing_rev>"
                 }

   Example error output:

   .. code-block:: bash

       id : <id_given_in_input>
       result: {
                 "msg": "Created fork of `<reponame>` as `<forkname>`",
                 "success": true,
                 "task": "<celery task id or None if done sync>"
               }
       error:  null


get_repo 
--------

.. py:function:: get_repo(apiuser, repoid, cache=<Optional:True>)

   Gets an existing repository by its name or repository_id.

   The members section so the output returns users groups or users
   associated with that repository.

   This command can only be run using an |authtoken| with admin rights,
   or users with at least read rights to the |repo|.

   :param apiuser: This is filled automatically from the |authtoken|.
   :type apiuser: AuthUser
   :param repoid: The repository name or repository id.
   :type repoid: str or int
   :param cache: use the cached value for last changeset
   :type: cache: Optional(bool)

   Example output:

   .. code-block:: bash

       {
         "error": null,
         "id": <repo_id>,
         "result": {
           "clone_uri": null,
           "created_on": "timestamp",
           "description": "repo description",
           "enable_downloads": false,
           "enable_locking": false,
           "enable_statistics": false,
           "followers": [
             {
               "active": true,
               "admin": false,
               "api_key": "****************************************",
               "api_keys": [
                 "****************************************"
               ],
               "email": "user@example.com",
               "emails": [
                 "user@example.com"
               ],
               "extern_name": "rhodecode",
               "extern_type": "rhodecode",
               "firstname": "username",
               "ip_addresses": [],
               "language": null,
               "last_login": "2015-09-16T17:16:35.854",
               "lastname": "surname",
               "user_id": <user_id>,
               "username": "name"
             }
           ],
           "fork_of": "parent-repo",
           "landing_rev": [
             "rev",
             "tip"
           ],
           "last_changeset": {
             "author": "User <user@example.com>",
             "branch": "default",
             "date": "timestamp",
             "message": "last commit message",
             "parents": [
               {
                 "raw_id": "commit-id"
               }
             ],
             "raw_id": "commit-id",
             "revision": <revision number>,
             "short_id": "short id"
           },
           "lock_reason": null,
           "locked_by": null,
           "locked_date": null,
           "owner": "owner-name",
           "permissions": [
             {
               "name": "super-admin-name",
               "origin": "super-admin",
               "permission": "repository.admin",
               "type": "user"
             },
             {
               "name": "owner-name",
               "origin": "owner",
               "permission": "repository.admin",
               "type": "user"
             },
             {
               "name": "user-group-name",
               "origin": "permission",
               "permission": "repository.write",
               "type": "user_group"
             }
           ],
           "private": true,
           "repo_id": 676,
           "repo_name": "user-group/repo-name",
           "repo_type": "hg"
         }
       }


get_repo_changeset 
------------------

.. py:function:: get_repo_changeset(apiuser, repoid, revision, details=<Optional:'basic'>)

   Returns information about a changeset.

   Additionally parameters define the amount of details returned by
   this function.

   This command can only be run using an |authtoken| with admin rights,
   or users with at least read rights to the |repo|.

   :param apiuser: This is filled automatically from the |authtoken|.
   :type apiuser: AuthUser
   :param repoid: The repository name or repository id
   :type repoid: str or int
   :param revision: revision for which listing should be done
   :type revision: str
   :param details: details can be 'basic|extended|full' full gives diff
       info details like the diff itself, and number of changed files etc.
   :type details: Optional(str)


get_repo_changesets 
-------------------

.. py:function:: get_repo_changesets(apiuser, repoid, start_rev, limit, details=<Optional:'basic'>)

   Returns a set of commits limited by the number starting
   from the `start_rev` option.

   Additional parameters define the amount of details returned by this
   function.

   This command can only be run using an |authtoken| with admin rights,
   or users with at least read rights to |repos|.

   :param apiuser: This is filled automatically from the |authtoken|.
   :type apiuser: AuthUser
   :param repoid: The repository name or repository ID.
   :type repoid: str or int
   :param start_rev: The starting revision from where to get changesets.
   :type start_rev: str
   :param limit: Limit the number of commits to this amount
   :type limit: str or int
   :param details: Set the level of detail returned. Valid option are:
       ``basic``, ``extended`` and ``full``.
   :type details: Optional(str)

   .. note::

      Setting the parameter `details` to the value ``full`` is extensive
      and returns details like the diff itself, and the number
      of changed files.


get_repo_nodes 
--------------

.. py:function:: get_repo_nodes(apiuser, repoid, revision, root_path, ret_type=<Optional:'all'>, details=<Optional:'basic'>, max_file_bytes=<Optional:None>)

   Returns a list of nodes and children in a flat list for a given
   path at given revision.

   It's possible to specify ret_type to show only `files` or `dirs`.

   This command can only be run using an |authtoken| with admin rights,
   or users with at least read rights to |repos|.

   :param apiuser: This is filled automatically from the |authtoken|.
   :type apiuser: AuthUser
   :param repoid: The repository name or repository ID.
   :type repoid: str or int
   :param revision: The revision for which listing should be done.
   :type revision: str
   :param root_path: The path from which to start displaying.
   :type root_path: str
   :param ret_type: Set the return type. Valid options are
       ``all`` (default), ``files`` and ``dirs``.
   :type ret_type: Optional(str)
   :param details: Returns extended information about nodes, such as
       md5, binary, and or content.  The valid options are ``basic`` and
       ``full``.
   :type details: Optional(str)
   :param max_file_bytes: Only return file content under this file size bytes
   :type details: Optional(int)

   Example output:

   .. code-block:: bash

       id : <id_given_in_input>
       result: [
                 {
                   "name" : "<name>"
                   "type" : "<type>",
                   "binary": "<true|false>" (only in extended mode)
                   "md5"  : "<md5 of file content>" (only in extended mode)
                 },
                 ...
               ]
       error:  null


get_repo_refs 
-------------

.. py:function:: get_repo_refs(apiuser, repoid)

   Returns a dictionary of current references. It returns
   bookmarks, branches, closed_branches, and tags for given repository

   It's possible to specify ret_type to show only `files` or `dirs`.

   This command can only be run using an |authtoken| with admin rights,
   or users with at least read rights to |repos|.

   :param apiuser: This is filled automatically from the |authtoken|.
   :type apiuser: AuthUser
   :param repoid: The repository name or repository ID.
   :type repoid: str or int

   Example output:

   .. code-block:: bash

       id : <id_given_in_input>
       "result": {
           "bookmarks": {
             "dev": "5611d30200f4040ba2ab4f3d64e5b06408a02188",
             "master": "367f590445081d8ec8c2ea0456e73ae1f1c3d6cf"
           },
           "branches": {
             "default": "5611d30200f4040ba2ab4f3d64e5b06408a02188",
             "stable": "367f590445081d8ec8c2ea0456e73ae1f1c3d6cf"
           },
           "branches_closed": {},
           "tags": {
             "tip": "5611d30200f4040ba2ab4f3d64e5b06408a02188",
             "v4.4.0": "1232313f9e6adac5ce5399c2a891dc1e72b79022",
             "v4.4.1": "cbb9f1d329ae5768379cdec55a62ebdd546c4e27",
             "v4.4.2": "24ffe44a27fcd1c5b6936144e176b9f6dd2f3a17",
           }
       }
       error:  null


get_repo_settings 
-----------------

.. py:function:: get_repo_settings(apiuser, repoid, key=<Optional:None>)

   Returns all settings for a repository. If key is given it only returns the
   setting identified by the key or null.

   :param apiuser: This is filled automatically from the |authtoken|.
   :type apiuser: AuthUser
   :param repoid: The repository name or repository id.
   :type repoid: str or int
   :param key: Key of the setting to return.
   :type: key: Optional(str)

   Example output:

   .. code-block:: bash

       {
           "error": null,
           "id": 237,
           "result": {
               "extensions_largefiles": true,
               "extensions_evolve": true,
               "hooks_changegroup_push_logger": true,
               "hooks_changegroup_repo_size": false,
               "hooks_outgoing_pull_logger": true,
               "phases_publish": "True",
               "rhodecode_hg_use_rebase_for_merging": true,
               "rhodecode_pr_merge_enabled": true,
               "rhodecode_use_outdated_comments": true
           }
       }


get_repos 
---------

.. py:function:: get_repos(apiuser, root=<Optional:None>, traverse=<Optional:True>)

   Lists all existing repositories.

   This command can only be run using an |authtoken| with admin rights,
   or users with at least read rights to |repos|.

   :param apiuser: This is filled automatically from the |authtoken|.
   :type apiuser: AuthUser
   :param root: specify root repository group to fetch repositories.
       filters the returned repositories to be members of given root group.
   :type root: Optional(None)
   :param traverse: traverse given root into subrepositories. With this flag
       set to False, it will only return top-level repositories from `root`.
       if root is empty it will return just top-level repositories.
   :type traverse: Optional(True)


   Example output:

   .. code-block:: bash

       id : <id_given_in_input>
       result: [
                 {
                   "repo_id" :          "<repo_id>",
                   "repo_name" :        "<reponame>"
                   "repo_type" :        "<repo_type>",
                   "clone_uri" :        "<clone_uri>",
                   "private": :         "<bool>",
                   "created_on" :       "<datetimecreated>",
                   "description" :      "<description>",
                   "landing_rev":       "<landing_rev>",
                   "owner":             "<repo_owner>",
                   "fork_of":           "<name_of_fork_parent>",
                   "enable_downloads":  "<bool>",
                   "enable_locking":    "<bool>",
                   "enable_statistics": "<bool>",
                 },
                 ...
               ]
       error:  null


grant_user_group_permission 
---------------------------

.. py:function:: grant_user_group_permission(apiuser, repoid, usergroupid, perm)

   Grant permission for a user group on the specified repository,
   or update existing permissions.

   This command can only be run using an |authtoken| with admin
   permissions on the |repo|.

   :param apiuser: This is filled automatically from the |authtoken|.
   :type apiuser: AuthUser
   :param repoid: Set the repository name or repository ID.
   :type repoid: str or int
   :param usergroupid: Specify the ID of the user group.
   :type usergroupid: str or int
   :param perm: Set the user group permissions using the following
       format: (repository.(none|read|write|admin))
   :type perm: str

   Example output:

   .. code-block:: bash

     id : <id_given_in_input>
     result : {
       "msg" : "Granted perm: `<perm>` for group: `<usersgroupname>` in repo: `<reponame>`",
       "success": true

     }
     error :  null

   Example error output:

   .. code-block:: bash

     id : <id_given_in_input>
     result : null
     error :  {
       "failed to edit permission for user group: `<usergroup>` in repo `<repo>`'
     }


grant_user_permission 
---------------------

.. py:function:: grant_user_permission(apiuser, repoid, userid, perm)

   Grant permissions for the specified user on the given repository,
   or update existing permissions if found.

   This command can only be run using an |authtoken| with admin
   permissions on the |repo|.

   :param apiuser: This is filled automatically from the |authtoken|.
   :type apiuser: AuthUser
   :param repoid: Set the repository name or repository ID.
   :type repoid: str or int
   :param userid: Set the user name.
   :type userid: str
   :param perm: Set the user permissions, using the following format
       ``(repository.(none|read|write|admin))``
   :type perm: str

   Example output:

   .. code-block:: bash

       id : <id_given_in_input>
       result: {
                 "msg" : "Granted perm: `<perm>` for user: `<username>` in repo: `<reponame>`",
                 "success": true
               }
       error:  null


invalidate_cache 
----------------

.. py:function:: invalidate_cache(apiuser, repoid, delete_keys=<Optional:False>)

   Invalidates the cache for the specified repository.

   This command can only be run using an |authtoken| with admin rights to
   the specified repository.

   This command takes the following options:

   :param apiuser: This is filled automatically from |authtoken|.
   :type apiuser: AuthUser
   :param repoid: Sets the repository name or repository ID.
   :type repoid: str or int
   :param delete_keys: This deletes the invalidated keys instead of
       just flagging them.
   :type delete_keys: Optional(``True`` | ``False``)

   Example output:

   .. code-block:: bash

     id : <id_given_in_input>
     result : {
       'msg': Cache for repository `<repository name>` was invalidated,
       'repository': <repository name>
     }
     error :  null

   Example error output:

   .. code-block:: bash

     id : <id_given_in_input>
     result : null
     error : {
        'Error occurred during cache invalidation action'
     }


lock 
----

.. py:function:: lock(apiuser, repoid, locked=<Optional:None>, userid=<Optional:<OptionalAttr:apiuser>>)

   Sets the lock state of the specified |repo| by the given user.
   From more information, see :ref:`repo-locking`.

   * If the ``userid`` option is not set, the repository is locked to the
     user who called the method.
   * If the ``locked`` parameter is not set, the current lock state of the
     repository is displayed.

   This command can only be run using an |authtoken| with admin rights to
   the specified repository.

   This command takes the following options:

   :param apiuser: This is filled automatically from the |authtoken|.
   :type apiuser: AuthUser
   :param repoid: Sets the repository name or repository ID.
   :type repoid: str or int
   :param locked: Sets the lock state.
   :type locked: Optional(``True`` | ``False``)
   :param userid: Set the repository lock to this user.
   :type userid: Optional(str or int)

   Example error output:

   .. code-block:: bash

     id : <id_given_in_input>
     result : {
       'repo': '<reponame>',
       'locked': <bool: lock state>,
       'locked_since': <int: lock timestamp>,
       'locked_by': <username of person who made the lock>,
       'lock_reason': <str: reason for locking>,
       'lock_state_changed': <bool: True if lock state has been changed in this request>,
       'msg': 'Repo `<reponame>` locked by `<username>` on <timestamp>.'
       or
       'msg': 'Repo `<repository name>` not locked.'
       or
       'msg': 'User `<user name>` set lock state for repo `<repository name>` to `<new lock state>`'
     }
     error :  null

   Example error output:

   .. code-block:: bash

     id : <id_given_in_input>
     result : null
     error :  {
       'Error occurred locking repository `<reponame>`'
     }


maintenance 
-----------

.. py:function:: maintenance(apiuser, repoid)

   Triggers a maintenance on the given repository.

   This command can only be run using an |authtoken| with admin
   rights to the specified repository. For more information,
   see :ref:`config-token-ref`.

   This command takes the following options:

   :param apiuser: This is filled automatically from the |authtoken|.
   :type apiuser: AuthUser
   :param repoid: The repository name or repository ID.
   :type repoid: str or int

   Example output:

   .. code-block:: bash

     id : <id_given_in_input>
     result : {
       "msg": "executed maintenance command",
       "executed_actions": [
          <action_message>, <action_message2>...
       ],
       "repository": "<repository name>"
     }
     error :  null

   Example error output:

   .. code-block:: bash

     id : <id_given_in_input>
     result : null
     error :  {
       "Unable to execute maintenance on `<reponame>`"
     }


pull 
----

.. py:function:: pull(apiuser, repoid, remote_uri=<Optional:None>)

   Triggers a pull on the given repository from a remote location. You
   can use this to keep remote repositories up-to-date.

   This command can only be run using an |authtoken| with admin
   rights to the specified repository. For more information,
   see :ref:`config-token-ref`.

   This command takes the following options:

   :param apiuser: This is filled automatically from the |authtoken|.
   :type apiuser: AuthUser
   :param repoid: The repository name or repository ID.
   :type repoid: str or int
   :param remote_uri: Optional remote URI to pass in for pull
   :type remote_uri: str

   Example output:

   .. code-block:: bash

     id : <id_given_in_input>
     result : {
       "msg": "Pulled from url `<remote_url>` on repo `<repository name>`"
       "repository": "<repository name>"
     }
     error :  null

   Example error output:

   .. code-block:: bash

     id : <id_given_in_input>
     result : null
     error :  {
       "Unable to push changes from `<remote_url>`"
     }


remove_field_from_repo 
----------------------

.. py:function:: remove_field_from_repo(apiuser, repoid, key)

   Removes an extra field from a repository.

   This command can only be run using an |authtoken| with at least
   write permissions to the |repo|.

   :param apiuser: This is filled automatically from the |authtoken|.
   :type apiuser: AuthUser
   :param repoid: Set the repository name or repository ID.
   :type repoid: str or int
   :param key: Set the unique field key for this repository.
   :type key: str


revoke_user_group_permission 
----------------------------

.. py:function:: revoke_user_group_permission(apiuser, repoid, usergroupid)

   Revoke the permissions of a user group on a given repository.

   This command can only be run using an |authtoken| with admin
   permissions on the |repo|.

   :param apiuser: This is filled automatically from the |authtoken|.
   :type apiuser: AuthUser
   :param repoid: Set the repository name or repository ID.
   :type repoid: str or int
   :param usergroupid: Specify the user group ID.
   :type usergroupid: str or int

   Example output:

   .. code-block:: bash

       id : <id_given_in_input>
       result: {
                 "msg" : "Revoked perm for group: `<usersgroupname>` in repo: `<reponame>`",
                 "success": true
               }
       error:  null


revoke_user_permission 
----------------------

.. py:function:: revoke_user_permission(apiuser, repoid, userid)

   Revoke permission for a user on the specified repository.

   This command can only be run using an |authtoken| with admin
   permissions on the |repo|.

   :param apiuser: This is filled automatically from the |authtoken|.
   :type apiuser: AuthUser
   :param repoid: Set the repository name or repository ID.
   :type repoid: str or int
   :param userid: Set the user name of revoked user.
   :type userid: str or int

   Example error output:

   .. code-block:: bash

       id : <id_given_in_input>
       result: {
                 "msg" : "Revoked perm for user: `<username>` in repo: `<reponame>`",
                 "success": true
               }
       error:  null


set_repo_settings 
-----------------

.. py:function:: set_repo_settings(apiuser, repoid, settings)

   Update repository settings. Returns true on success.

   :param apiuser: This is filled automatically from the |authtoken|.
   :type apiuser: AuthUser
   :param repoid: The repository name or repository id.
   :type repoid: str or int
   :param settings: The new settings for the repository.
   :type: settings: dict

   Example output:

   .. code-block:: bash

       {
           "error": null,
           "id": 237,
           "result": true
       }


strip 
-----

.. py:function:: strip(apiuser, repoid, revision, branch)

   Strips the given revision from the specified repository.

   * This will remove the revision and all of its decendants.

   This command can only be run using an |authtoken| with admin rights to
   the specified repository.

   This command takes the following options:

   :param apiuser: This is filled automatically from the |authtoken|.
   :type apiuser: AuthUser
   :param repoid: The repository name or repository ID.
   :type repoid: str or int
   :param revision: The revision you wish to strip.
   :type revision: str
   :param branch: The branch from which to strip the revision.
   :type branch: str

   Example output:

   .. code-block:: bash

     id : <id_given_in_input>
     result : {
       "msg": "'Stripped commit <commit_hash> from repo `<repository name>`'"
       "repository": "<repository name>"
     }
     error :  null

   Example error output:

   .. code-block:: bash

     id : <id_given_in_input>
     result : null
     error :  {
       "Unable to strip commit <commit_hash> from repo `<repository name>`"
     }


update_repo 
-----------

.. py:function:: update_repo(apiuser, repoid, repo_name=<Optional:None>, owner=<Optional:<OptionalAttr:apiuser>>, description=<Optional:''>, private=<Optional:False>, clone_uri=<Optional:None>, push_uri=<Optional:None>, landing_rev=<Optional:'rev:tip'>, fork_of=<Optional:None>, enable_statistics=<Optional:False>, enable_locking=<Optional:False>, enable_downloads=<Optional:False>, fields=<Optional:''>)

   Updates a repository with the given information.

   This command can only be run using an |authtoken| with at least
   admin permissions to the |repo|.

   * If the repository name contains "/", repository will be updated
     accordingly with a repository group or nested repository groups

     For example repoid=repo-test name="foo/bar/repo-test" will update |repo|
     called "repo-test" and place it inside group "foo/bar".
     You have to have permissions to access and write to the last repository
     group ("bar" in this example)

   :param apiuser: This is filled automatically from the |authtoken|.
   :type apiuser: AuthUser
   :param repoid: repository name or repository ID.
   :type repoid: str or int
   :param repo_name: Update the |repo| name, including the
       repository group it's in.
   :type repo_name: str
   :param owner: Set the |repo| owner.
   :type owner: str
   :param fork_of: Set the |repo| as fork of another |repo|.
   :type fork_of: str
   :param description: Update the |repo| description.
   :type description: str
   :param private: Set the |repo| as private. (True | False)
   :type private: bool
   :param clone_uri: Update the |repo| clone URI.
   :type clone_uri: str
   :param landing_rev: Set the |repo| landing revision. Default is ``rev:tip``.
   :type landing_rev: str
   :param enable_statistics: Enable statistics on the |repo|, (True | False).
   :type enable_statistics: bool
   :param enable_locking: Enable |repo| locking.
   :type enable_locking: bool
   :param enable_downloads: Enable downloads from the |repo|, (True | False).
   :type enable_downloads: bool
   :param fields: Add extra fields to the |repo|. Use the following
       example format: ``field_key=field_val,field_key2=fieldval2``.
       Escape ', ' with \,
   :type fields: str


