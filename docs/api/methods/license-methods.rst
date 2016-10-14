.. _license-methods-ref:

license methods
===============

get_license_info (EE only)
----------------

.. py:function:: get_license_info(apiuser)

   Returns the |RCE| license information.

   :param apiuser: This is filled automatically from the |authtoken|.
   :type apiuser: AuthUser

   Example output:

   .. code-block:: bash

     id : <id_given_in_input>
     result : {
       'rhodecode_version': <rhodecode version>,
       'token': <license token>,
       'issued_to': <license owner>,
       'issued_on': <license issue date>,
       'expires_on': <license expiration date>,
       'type': <license type>,
       'users_limit': <license users limit>,
       'key': <license key>
     }
     error :  null


set_license_key (EE only)
---------------

.. py:function:: set_license_key(apiuser, key)

   Sets the |RCE| license key.

   :param apiuser: This is filled automatically from the |authtoken|.
   :type apiuser: AuthUser
   :param key: This is the license key to be set.
   :type key: str

   Example output:

   .. code-block:: bash

       id : <id_given_in_input>
       result: {
                 "msg" : "updated license information",
                 "key": <key>
               }
       error:  null

   Example error output:

   .. code-block:: bash

     id : <id_given_in_input>
     result : null
     error :  {
       "license key is not valid"
       or
       "trial licenses cannot be uploaded"
       or
       "error occurred while updating license"
     }


