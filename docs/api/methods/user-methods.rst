.. _user-methods-ref:

user methods
============

create_user 
-----------

.. py:function:: create_user(apiuser, username, email, password=<Optional:''>, firstname=<Optional:''>, lastname=<Optional:''>, description=<Optional:''>, active=<Optional:True>, admin=<Optional:False>, extern_name=<Optional:'rhodecode'>, extern_type=<Optional:'rhodecode'>, force_password_change=<Optional:False>, create_personal_repo_group=<Optional:None>)

   Creates a new user and returns the new user object.

   This command can only be run using an |authtoken| with admin rights to
   the specified repository.

   This command takes the following options:

   :param apiuser: This is filled automatically from the |authtoken|.
   :type apiuser: AuthUser
   :param username: Set the new username.
   :type username: str or int
   :param email: Set the user email address.
   :type email: str
   :param password: Set the new user password.
   :type password: Optional(str)
   :param firstname: Set the new user firstname.
   :type firstname: Optional(str)
   :param lastname: Set the new user surname.
   :type lastname: Optional(str)
   :param description: Set user description, or short bio. Metatags are allowed.
   :type description: Optional(str)
   :param active: Set the user as active.
   :type active: Optional(``True`` | ``False``)
   :param admin: Give the new user admin rights.
   :type admin: Optional(``True`` | ``False``)
   :param extern_name: Set the authentication plugin name.
       Using LDAP this is filled with LDAP UID.
   :type extern_name: Optional(str)
   :param extern_type: Set the new user authentication plugin.
   :type extern_type: Optional(str)
   :param force_password_change: Force the new user to change password
       on next login.
   :type force_password_change: Optional(``True`` | ``False``)
   :param create_personal_repo_group: Create personal repo group for this user
   :type create_personal_repo_group: Optional(``True`` | ``False``)

   Example output:

   .. code-block:: bash

       id : <id_given_in_input>
       result: {
           "msg" : "created new user `<username>`",
           "user": <user_obj>
       }
       error:  null

   Example error output:

   .. code-block:: bash

     id : <id_given_in_input>
     result : null
     error :  {
       "user `<username>` already exist"
       or
       "email `<email>` already exist"
       or
       "failed to create user `<username>`"
     }


delete_user 
-----------

.. py:function:: delete_user(apiuser, userid)

   Deletes the specified user from the |RCE| user database.

   This command can only be run using an |authtoken| with admin rights to
   the specified repository.

   .. important::

      Ensure all open pull requests and open code review
      requests to this user are close.

      Also ensure all repositories, or repository groups owned by this
      user are reassigned before deletion.

   This command takes the following options:

   :param apiuser: This is filled automatically from the |authtoken|.
   :type apiuser: AuthUser
   :param userid: Set the user to delete.
   :type userid: str or int

   Example output:

   .. code-block:: bash

       id : <id_given_in_input>
       result: {
           "msg" : "deleted user ID:<userid> <username>",
           "user": null
       }
       error:  null

   Example error output:

   .. code-block:: bash

     id : <id_given_in_input>
     result : null
     error :  {
       "failed to delete user ID:<userid> <username>"
     }


get_user 
--------

.. py:function:: get_user(apiuser, userid=<Optional:<OptionalAttr:apiuser>>)

   Returns the information associated with a username or userid.

   * If the ``userid`` is not set, this command returns the information
     for the ``userid`` calling the method.

   .. note::

      Normal users may only run this command against their ``userid``. For
      full privileges you must run this command using an |authtoken| with
      admin rights.

   :param apiuser: This is filled automatically from the |authtoken|.
   :type apiuser: AuthUser
   :param userid: Sets the userid for which data will be returned.
   :type userid: Optional(str or int)

   Example output:

   .. code-block:: bash

       {
         "error": null,
         "id": <id>,
         "result": {
           "active": true,
           "admin": false,
           "api_keys": [ list of keys ],
           "auth_tokens": [ list of tokens with details ],
           "email": "user@example.com",
           "emails": [
             "user@example.com"
           ],
           "extern_name": "rhodecode",
           "extern_type": "rhodecode",
           "firstname": "username",
           "description": "user description",
           "ip_addresses": [],
           "language": null,
           "last_login": "Timestamp",
           "last_activity": "Timestamp",
           "lastname": "surnae",
           "permissions": <deprecated>,
           "permissions_summary": {
             "global": [
               "hg.inherit_default_perms.true",
               "usergroup.read",
               "hg.repogroup.create.false",
               "hg.create.none",
               "hg.password_reset.enabled",
               "hg.extern_activate.manual",
               "hg.create.write_on_repogroup.false",
               "hg.usergroup.create.false",
               "group.none",
               "repository.none",
               "hg.register.none",
               "hg.fork.repository"
             ],
             "repositories": { "username/example": "repository.write"},
             "repositories_groups": { "user-group/repo": "group.none" },
             "user_groups": { "user_group_name": "usergroup.read" }
           }
           "user_id": 32,
           "username": "username"
         }
       }


get_user_audit_logs 
-------------------

.. py:function:: get_user_audit_logs(apiuser, userid=<Optional:<OptionalAttr:apiuser>>)

   Fetches all action logs made by the specified user.

   This command takes the following options:

   :param apiuser: This is filled automatically from the |authtoken|.
   :type apiuser: AuthUser
   :param userid: Sets the userid whose list of locked |repos| will be
       displayed.
   :type userid: Optional(str or int)

   Example output:

   .. code-block:: bash

       id : <id_given_in_input>
       result : {
           [action, action,...]
       }
       error :  null


get_user_locks 
--------------

.. py:function:: get_user_locks(apiuser, userid=<Optional:<OptionalAttr:apiuser>>)

   Displays all repositories locked by the specified user.

   * If this command is run by a non-admin user, it returns
     a list of |repos| locked by that user.

   This command takes the following options:

   :param apiuser: This is filled automatically from the |authtoken|.
   :type apiuser: AuthUser
   :param userid: Sets the userid whose list of locked |repos| will be
       displayed.
   :type userid: Optional(str or int)

   Example output:

   .. code-block:: bash

       id : <id_given_in_input>
       result : {
           [repo_object, repo_object,...]
       }
       error :  null


get_users 
---------

.. py:function:: get_users(apiuser)

   Lists all users in the |RCE| user database.

   This command can only be run using an |authtoken| with admin rights to
   the specified repository.

   This command takes the following options:

   :param apiuser: This is filled automatically from the |authtoken|.
   :type apiuser: AuthUser

   Example output:

   .. code-block:: bash

       id : <id_given_in_input>
       result: [<user_object>, ...]
       error:  null


update_user 
-----------

.. py:function:: update_user(apiuser, userid, username=<Optional:None>, email=<Optional:None>, password=<Optional:None>, firstname=<Optional:None>, lastname=<Optional:None>, description=<Optional:None>, active=<Optional:None>, admin=<Optional:None>, extern_type=<Optional:None>, extern_name=<Optional:None>)

   Updates the details for the specified user, if that user exists.

   This command can only be run using an |authtoken| with admin rights to
   the specified repository.

   This command takes the following options:

   :param apiuser: This is filled automatically from |authtoken|.
   :type apiuser: AuthUser
   :param userid: Set the ``userid`` to update.
   :type userid: str or int
   :param username: Set the new username.
   :type username: str or int
   :param email: Set the new email.
   :type email: str
   :param password: Set the new password.
   :type password: Optional(str)
   :param firstname: Set the new first name.
   :type firstname: Optional(str)
   :param lastname: Set the new surname.
   :type lastname: Optional(str)
   :param description: Set user description, or short bio. Metatags are allowed.
   :type description: Optional(str)
   :param active: Set the new user as active.
   :type active: Optional(``True`` | ``False``)
   :param admin: Give the user admin rights.
   :type admin: Optional(``True`` | ``False``)
   :param extern_name: Set the authentication plugin user name.
       Using LDAP this is filled with LDAP UID.
   :type extern_name: Optional(str)
   :param extern_type: Set the authentication plugin type.
   :type extern_type: Optional(str)


   Example output:

   .. code-block:: bash

       id : <id_given_in_input>
       result: {
           "msg" : "updated user ID:<userid> <username>",
           "user": <user_object>,
       }
       error:  null

   Example error output:

   .. code-block:: bash

     id : <id_given_in_input>
     result : null
     error :  {
       "failed to update user `<username>`"
     }


