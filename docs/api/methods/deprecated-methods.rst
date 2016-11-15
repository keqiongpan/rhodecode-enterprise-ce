.. _deprecated-methods-ref:

deprecated methods
==================

changeset_comment 
-----------------

.. py:function:: changeset_comment(apiuser, repoid, revision, message, userid=<Optional:<OptionalAttr:apiuser>>, status=<Optional:None>)

   .. deprecated:: 3.4.0

          Please use method `comment_commit` instead.


   Set a changeset comment, and optionally change the status of the
   changeset.

   This command can only be run using an |authtoken| with admin
   permissions on the |repo|.

   :param apiuser: This is filled automatically from the |authtoken|.
   :type apiuser: AuthUser
   :param repoid: Set the repository name or repository ID.
   :type repoid: str or int
   :param revision: Specify the revision for which to set a comment.
   :type revision: str
   :param message: The comment text.
   :type message: str
   :param userid: Set the user name of the comment creator.
   :type userid: Optional(str or int)
   :param status: Set the comment status. The following are valid options:
       * not_reviewed
       * approved
       * rejected
       * under_review
   :type status: str

   Example error output:

   .. code-block:: bash

       {
           "id" : <id_given_in_input>,
           "result" : {
               "msg": "Commented on commit `<revision>` for repository `<repoid>`",
               "status_change": null or <status>,
               "success": true
           },
           "error" : null
       }


get_locks 
---------

.. py:function:: get_locks(apiuser, userid=<Optional:<OptionalAttr:apiuser>>)

   .. deprecated:: 4.0.0

      Please use method `get_user_locks` instead.

   None


show_ip 
-------

.. py:function:: show_ip(apiuser, userid=<Optional:<OptionalAttr:apiuser>>)

   .. deprecated:: 4.0.0

      Please use method `get_ip` instead.

   None


