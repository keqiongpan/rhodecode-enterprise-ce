.. _views-ref:

views
=====

push (EE only)
--------------

.. py:function:: push(apiuser, repoid, remote_uri=<Optional:None>)

   Triggers a push on the given repository from a remote location. You
   can use this to keep remote repositories up-to-date.

   This command can only be run using an |authtoken| with admin
   rights to the specified repository. For more information,
   see :ref:`config-token-ref`.

   This command takes the following options:

   :param apiuser: This is filled automatically from the |authtoken|.
   :type apiuser: AuthUser
   :param repoid: The repository name or repository ID.
   :type repoid: str or int
   :param remote_uri: Optional remote URI to pass in for push
   :type remote_uri: str

   Example output:

   .. code-block:: bash

     id : <id_given_in_input>
     result : {
       "msg": "Pushed to url `<remote_url>` on repo `<repository name>`"
       "repository": "<repository name>"
     }
     error :  null

   Example error output:

   .. code-block:: bash

     id : <id_given_in_input>
     result : null
     error :  {
       "Unable to push changes to `<remote_url>`"
     }


