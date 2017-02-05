.. _pull-request-methods-ref:

pull_request methods
====================

close_pull_request 
------------------

.. py:function:: close_pull_request(apiuser, repoid, pullrequestid, userid=<Optional:<OptionalAttr:apiuser>>)

   Close the pull request specified by `pullrequestid`.

   :param apiuser: This is filled automatically from the |authtoken|.
   :type apiuser: AuthUser
   :param repoid: Repository name or repository ID to which the pull
       request belongs.
   :type repoid: str or int
   :param pullrequestid: ID of the pull request to be closed.
   :type pullrequestid: int
   :param userid: Close the pull request as this user.
   :type userid: Optional(str or int)

   Example output:

   .. code-block:: bash

     "id": <id_given_in_input>,
     "result":
       {
           "pull_request_id":  "<int>",
           "closed":           "<bool>"
       },
     "error": null


comment_pull_request 
--------------------

.. py:function:: comment_pull_request(apiuser, repoid, pullrequestid, message=<Optional:None>, commit_id=<Optional:None>, status=<Optional:None>, comment_type=<Optional:u'note'>, resolves_comment_id=<Optional:None>, userid=<Optional:<OptionalAttr:apiuser>>)

   Comment on the pull request specified with the `pullrequestid`,
   in the |repo| specified by the `repoid`, and optionally change the
   review status.

   :param apiuser: This is filled automatically from the |authtoken|.
   :type apiuser: AuthUser
   :param repoid: The repository name or repository ID.
   :type repoid: str or int
   :param pullrequestid: The pull request ID.
   :type pullrequestid: int
   :param commit_id: Specify the commit_id for which to set a comment. If
       given commit_id is different than latest in the PR status
       change won't be performed.
   :type commit_id: str
   :param message: The text content of the comment.
   :type message: str
   :param status: (**Optional**) Set the approval status of the pull
       request. One of: 'not_reviewed', 'approved', 'rejected',
       'under_review'
   :type status: str
   :param comment_type: Comment type, one of: 'note', 'todo'
   :type comment_type: Optional(str), default: 'note'
   :param userid: Comment on the pull request as this user
   :type userid: Optional(str or int)

   Example output:

   .. code-block:: bash

     id : <id_given_in_input>
     result :
       {
           "pull_request_id":  "<Integer>",
           "comment_id":       "<Integer>",
           "status": {"given": <given_status>,
                      "was_changed": <bool status_was_actually_changed> },
       }
     error :  null


create_pull_request 
-------------------

.. py:function:: create_pull_request(apiuser, source_repo, target_repo, source_ref, target_ref, title, description=<Optional:''>, reviewers=<Optional:None>)

   Creates a new pull request.

   Accepts refs in the following formats:

       * branch:<branch_name>:<sha>
       * branch:<branch_name>
       * bookmark:<bookmark_name>:<sha> (Mercurial only)
       * bookmark:<bookmark_name> (Mercurial only)

   :param apiuser: This is filled automatically from the |authtoken|.
   :type apiuser: AuthUser
   :param source_repo: Set the source repository name.
   :type source_repo: str
   :param target_repo: Set the target repository name.
   :type target_repo: str
   :param source_ref: Set the source ref name.
   :type source_ref: str
   :param target_ref: Set the target ref name.
   :type target_ref: str
   :param title: Set the pull request title.
   :type title: str
   :param description: Set the pull request description.
   :type description: Optional(str)
   :param reviewers: Set the new pull request reviewers list.
   :type reviewers: Optional(list)
       Accepts username strings or objects of the format:
       {
           'username': 'nick', 'reasons': ['original author']
       }


get_pull_request 
----------------

.. py:function:: get_pull_request(apiuser, repoid, pullrequestid)

   Get a pull request based on the given ID.

   :param apiuser: This is filled automatically from the |authtoken|.
   :type apiuser: AuthUser
   :param repoid: Repository name or repository ID from where the pull
       request was opened.
   :type repoid: str or int
   :param pullrequestid: ID of the requested pull request.
   :type pullrequestid: int

   Example output:

   .. code-block:: bash

     "id": <id_given_in_input>,
     "result":
       {
           "pull_request_id":   "<pull_request_id>",
           "url":               "<url>",
           "title":             "<title>",
           "description":       "<description>",
           "status" :           "<status>",
           "created_on":        "<date_time_created>",
           "updated_on":        "<date_time_updated>",
           "commit_ids":        [
                                    ...
                                    "<commit_id>",
                                    "<commit_id>",
                                    ...
                                ],
           "review_status":    "<review_status>",
           "mergeable":         {
                                    "status":  "<bool>",
                                    "message": "<message>",
                                },
           "source":            {
                                    "clone_url":     "<clone_url>",
                                    "repository":    "<repository_name>",
                                    "reference":
                                    {
                                        "name":      "<name>",
                                        "type":      "<type>",
                                        "commit_id": "<commit_id>",
                                    }
                                },
           "target":            {
                                    "clone_url":   "<clone_url>",
                                    "repository":    "<repository_name>",
                                    "reference":
                                    {
                                        "name":      "<name>",
                                        "type":      "<type>",
                                        "commit_id": "<commit_id>",
                                    }
                                },
           "merge":             {
                                    "clone_url":   "<clone_url>",
                                    "reference":
                                    {
                                        "name":      "<name>",
                                        "type":      "<type>",
                                        "commit_id": "<commit_id>",
                                    }
                                },
          "author":             <user_obj>,
          "reviewers":          [
                                    ...
                                    {
                                       "user":          "<user_obj>",
                                       "review_status": "<review_status>",
                                    }
                                    ...
                                ]
       },
      "error": null


get_pull_requests 
-----------------

.. py:function:: get_pull_requests(apiuser, repoid, status=<Optional:'new'>)

   Get all pull requests from the repository specified in `repoid`.

   :param apiuser: This is filled automatically from the |authtoken|.
   :type apiuser: AuthUser
   :param repoid: Repository name or repository ID.
   :type repoid: str or int
   :param status: Only return pull requests with the specified status.
       Valid options are.
       * ``new`` (default)
       * ``open``
       * ``closed``
   :type status: str

   Example output:

   .. code-block:: bash

     "id": <id_given_in_input>,
     "result":
       [
           ...
           {
               "pull_request_id":   "<pull_request_id>",
               "url":               "<url>",
               "title" :            "<title>",
               "description":       "<description>",
               "status":            "<status>",
               "created_on":        "<date_time_created>",
               "updated_on":        "<date_time_updated>",
               "commit_ids":        [
                                        ...
                                        "<commit_id>",
                                        "<commit_id>",
                                        ...
                                    ],
               "review_status":    "<review_status>",
               "mergeable":         {
                                       "status":      "<bool>",
                                       "message:      "<message>",
                                    },
               "source":            {
                                        "clone_url":     "<clone_url>",
                                        "reference":
                                        {
                                            "name":      "<name>",
                                            "type":      "<type>",
                                            "commit_id": "<commit_id>",
                                        }
                                    },
               "target":            {
                                        "clone_url":   "<clone_url>",
                                        "reference":
                                        {
                                            "name":      "<name>",
                                            "type":      "<type>",
                                            "commit_id": "<commit_id>",
                                        }
                                    },
               "merge":             {
                                        "clone_url":   "<clone_url>",
                                        "reference":
                                        {
                                            "name":      "<name>",
                                            "type":      "<type>",
                                            "commit_id": "<commit_id>",
                                        }
                                    },
              "author":             <user_obj>,
              "reviewers":          [
                                        ...
                                        {
                                           "user":          "<user_obj>",
                                           "review_status": "<review_status>",
                                        }
                                        ...
                                    ]
           }
           ...
       ],
     "error": null


merge_pull_request 
------------------

.. py:function:: merge_pull_request(apiuser, repoid, pullrequestid, userid=<Optional:<OptionalAttr:apiuser>>)

   Merge the pull request specified by `pullrequestid` into its target
   repository.

   :param apiuser: This is filled automatically from the |authtoken|.
   :type apiuser: AuthUser
   :param repoid: The Repository name or repository ID of the
       target repository to which the |pr| is to be merged.
   :type repoid: str or int
   :param pullrequestid: ID of the pull request which shall be merged.
   :type pullrequestid: int
   :param userid: Merge the pull request as this user.
   :type userid: Optional(str or int)

   Example output:

   .. code-block:: bash

     "id": <id_given_in_input>,
     "result":
       {
           "executed":         "<bool>",
           "failure_reason":   "<int>",
           "merge_commit_id":  "<merge_commit_id>",
           "possible":         "<bool>",
           "merge_ref":        {
                                   "commit_id": "<commit_id>",
                                   "type":      "<type>",
                                   "name":      "<name>"
                               }
       },
     "error": null


update_pull_request 
-------------------

.. py:function:: update_pull_request(apiuser, repoid, pullrequestid, title=<Optional:''>, description=<Optional:''>, reviewers=<Optional:None>, update_commits=<Optional:None>, close_pull_request=<Optional:None>)

   Updates a pull request.

   :param apiuser: This is filled automatically from the |authtoken|.
   :type apiuser: AuthUser
   :param repoid: The repository name or repository ID.
   :type repoid: str or int
   :param pullrequestid: The pull request ID.
   :type pullrequestid: int
   :param title: Set the pull request title.
   :type title: str
   :param description: Update pull request description.
   :type description: Optional(str)
   :param reviewers: Update pull request reviewers list with new value.
   :type reviewers: Optional(list)
   :param update_commits: Trigger update of commits for this pull request
   :type: update_commits: Optional(bool)
   :param close_pull_request: Close this pull request with rejected state
   :type: close_pull_request: Optional(bool)

   Example output:

   .. code-block:: bash

     id : <id_given_in_input>
     result :
       {
           "msg": "Updated pull request `63`",
           "pull_request": <pull_request_object>,
           "updated_reviewers": {
             "added": [
               "username"
             ],
             "removed": []
           },
           "updated_commits": {
             "added": [
               "<sha1_hash>"
             ],
             "common": [
               "<sha1_hash>",
               "<sha1_hash>",
             ],
             "removed": []
           }
       }
     error :  null


