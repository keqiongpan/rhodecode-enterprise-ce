.. _store-methods-ref:

store methods
=============

file_store_add (EE only)
------------------------

.. py:function:: file_store_add(apiuser, filename, content, description=<Optional:''>)

   Upload API for the file_store

   Example usage from CLI::
       rhodecode-api --instance-name=enterprise-1 upload_file "{"content": "$(cat image.jpg | base64)", "filename":"image.jpg"}"

   This command takes the following options:

   :param apiuser: This is filled automatically from the |authtoken|.
   :type apiuser: AuthUser
   :param filename: name of the file uploaded
   :type filename: str
   :param description: Optional description for added file
   :type description: str
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


file_store_add_with_acl (EE only)
---------------------------------

.. py:function:: file_store_add_with_acl(apiuser, filename, content, description=<Optional:''>, scope_user_id=<Optional:None>, scope_repo_id=<Optional:None>, scope_repo_group_id=<Optional:None>)

   Upload API for the file_store

   Example usage from CLI::
       rhodecode-api --instance-name=enterprise-1 upload_file "{"content": "$(cat image.jpg | base64)", "filename":"image.jpg", "scope_repo_id":101}"

   This command takes the following options:

   :param apiuser: This is filled automatically from the |authtoken|.
   :type apiuser: AuthUser
   :param filename: name of the file uploaded
   :type filename: str
   :param description: Optional description for added file
   :type description: str
   :param content: base64 encoded content of the uploaded file
   :type content: str

   :param scope_user_id: Optionally bind this file to user.
       This will check ACL in such way only this user can access the file.
   :type scope_user_id: int
   :param scope_repo_id: Optionally bind this file to repository.
       This will check ACL in such way only user with proper access to such
       repository can access the file.
   :type scope_repo_id: int
   :param scope_repo_group_id:  Optionally bind this file to repository group.
       This will check ACL in such way only user with proper access to such
       repository group can access the file.
   :type scope_repo_group_id: int

   Example output:

   .. code-block:: bash

     id : <id_given_in_input>
     result: {
       "access_path": "/_file_store/download/84d156f7-8323-4ad3-9fce-4a8e88e1deaf-0.jpg",
       "access_path_fqn": "http://server.domain.com/_file_store/download/84d156f7-8323-4ad3-9fce-4a8e88e1deaf-0.jpg",
       "store_fid": "84d156f7-8323-4ad3-9fce-4a8e88e1deaf-0.jpg"
     }
     error :  null


file_store_get_info (EE only)
-----------------------------

.. py:function:: file_store_get_info(apiuser, store_fid)

   Get artifact data.

   Example output:

   .. code-block:: bash

     id : <id_given_in_input>
     result: {
         "artifact": {
           "access_path_fqn": "https://rhodecode.example.com/_file_store/download/0-031c2aa0-0d56-49a7-9ba3-b570bdd342ab.jpg",
           "created_on": "2019-10-15T16:25:35.491",
           "description": "my upload",
           "downloaded_times": 1,
           "file_uid": "0-031c2aa0-0d56-49a7-9ba3-b570bdd342ab.jpg",
           "filename": "example.jpg",
           "filename_org": "0-031c2aa0-0d56-49a7-9ba3-b570bdd342ab.jpg",
           "hidden": false,
           "metadata": [
             {
               "artifact": "0-031c2aa0-0d56-49a7-9ba3-b570bdd342ab.jpg",
               "key": "yellow",
               "section": "tags",
               "value": "bar"
             }
           ],
           "sha256": "818dff0f44574dfb6814d38e6bf3c60c5943d1d13653398ecddaedf2f6a5b04d",
           "size": 18599,
           "uploaded_by": {
             "email": "admin@rhodecode.com",
             "emails": [
               "admin@rhodecode.com"
             ],
             "firstname": "Admin",
             "lastname": "LastName",
             "user_id": 2,
             "username": "admin"
           }
         }
     }
     error :  null


file_store_add_metadata (EE only)
---------------------------------

.. py:function:: file_store_add_metadata(apiuser, store_fid, section, key, value, value_type=<Optional:'unicode'>)

   Add metadata into artifact. The metadata consist of section, key, value. eg.
   section='tags', 'key'='tag_name', value='1'

   :param apiuser: This is filled automatically from the |authtoken|.
   :type apiuser: AuthUser

   :param store_fid: file uid, e.g 0-d054cb71-91ab-44e2-9e4b-23fe14b4d74a.mp4
   :type store_fid: str

   :param section: Section name to add metadata
   :type section: str

   :param key: Key to add as metadata
   :type key: str

   :param value: Value to add as metadata
   :type value: str

   :param value_type: Optional type, default is 'unicode' other types are:
       int, list, bool, unicode, str

   :type value_type: str

   Example output:

   .. code-block:: bash

     id : <id_given_in_input>
     result: {
           "metadata": [
             {
               "artifact": "0-d054cb71-91ab-44e2-9e4b-23fe14b4d74a.mp4",
               "key": "secret",
               "section": "tags",
               "value": "1"
             },
             {
               "artifact": "0-d054cb71-91ab-44e2-9e4b-23fe14b4d74a.mp4",
               "key": "video",
               "section": "tags",
               "value": "1"
             }
           ]
     }
     error :  null


