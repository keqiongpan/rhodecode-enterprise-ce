.. _gist-methods-ref:

gist methods
=================

create_gist 
-----------

.. py:function:: create_gist(apiuser, files, gistid=<Optional:None>, owner=<Optional:<OptionalAttr:apiuser>>, gist_type=<Optional:u'public'>, lifetime=<Optional:-1>, acl_level=<Optional:u'acl_public'>, description=<Optional:''>)

   Creates a new Gist.

   :param apiuser: This is filled automatically from the |authtoken|.
   :type apiuser: AuthUser
   :param files: files to be added to the gist. The data structure has
       to match the following example::

         {'filename1': {'content':'...'}, 'filename2': {'content':'...'}}

   :type files: dict
   :param gistid: Set a custom id for the gist
   :type gistid: Optional(str)
   :param owner: Set the gist owner, defaults to api method caller
   :type owner: Optional(str or int)
   :param gist_type: type of gist ``public`` or ``private``
   :type gist_type: Optional(str)
   :param lifetime: time in minutes of gist lifetime
   :type lifetime: Optional(int)
   :param acl_level: acl level for this gist, can be
       ``acl_public`` or ``acl_private`` If the value is set to
       ``acl_private`` only logged in users are able to access this gist.
       If not set it defaults to ``acl_public``.
   :type acl_level: Optional(str)
   :param description: gist description
   :type description: Optional(str)

   Example  output:

   .. code-block:: bash

     id : <id_given_in_input>
     result : {
       "msg": "created new gist",
       "gist": {}
     }
     error :  null

   Example error output:

   .. code-block:: bash

     id : <id_given_in_input>
     result : null
     error :  {
       "failed to create gist"
     }


delete_gist 
-----------

.. py:function:: delete_gist(apiuser, gistid)

   Deletes existing gist

   :param apiuser: filled automatically from apikey
   :type apiuser: AuthUser
   :param gistid: id of gist to delete
   :type gistid: str

   Example output:

   .. code-block:: bash

     id : <id_given_in_input>
     result : {
       "deleted gist ID: <gist_id>",
       "gist": null
     }
     error :  null

   Example error output:

   .. code-block:: bash

     id : <id_given_in_input>
     result : null
     error :  {
       "failed to delete gist ID:<gist_id>"
     }


get_gist 
--------

.. py:function:: get_gist(apiuser, gistid, content=<Optional:False>)

   Get the specified gist, based on the gist ID.

   :param apiuser: This is filled automatically from the |authtoken|.
   :type apiuser: AuthUser
   :param gistid: Set the id of the private or public gist
   :type gistid: str
   :param content: Return the gist content. Default is false.
   :type content: Optional(bool)


get_gists 
---------

.. py:function:: get_gists(apiuser, userid=<Optional:<OptionalAttr:apiuser>>)

   Get all gists for given user. If userid is empty returned gists
   are for user who called the api

   :param apiuser: This is filled automatically from the |authtoken|.
   :type apiuser: AuthUser
   :param userid: user to get gists for
   :type userid: Optional(str or int)


