.. _store-methods-ref:

store methods
=============

file_store_add (EE only)
------------------------

.. py:function:: file_store_add(apiuser, filename, content)

   Upload API for the file_store

   Example usage from CLI::
       rhodecode-api --instance-name=enterprise-1 upload_file "{"content": "$(cat image.jpg | base64)", "filename":"image.jpg"}"

   This command takes the following options:

   :param apiuser: This is filled automatically from the |authtoken|.
   :type apiuser: AuthUser
   :param filename: name of the file uploaded
   :type filename: str
   :param content: base64 encoded content of the uploaded file
   :type content: str

   Example output:

   .. code-block:: bash

     id : <id_given_in_input>
     result: {
       "access_path": "/_file_store/download/84d156f7-8323-4ad3-9fce-4a8e88e1deaf-0.jpg",
       "access_path_fqn": "http://server.domain.com/_file_store/download/84d156f7-8323-4ad3-9fce-4a8e88e1deaf-0.jpg",
       "store_fid": "84d156f7-8323-4ad3-9fce-4a8e88e1deaf-0.jpg"
     }
     error :  null


