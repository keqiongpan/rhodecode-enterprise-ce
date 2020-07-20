.. _pull-request-methods-ref:

pull_request methods
====================

close_pull_request 
------------------

.. py:function:: close_pull_request(apiuser, pullrequestid, repoid=<Optional:None>, userid=<Optional:<OptionalAttr:apiuser>>, message=<Optional:''>)

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
   :param message: Optional message to close the Pull Request with. If not
       specified it will be generated automatically.
   :type message: Optional(str)

   Example output:

   .. code-block:: bash

       "id": <id_given_in_input>,
       "result": {
           "pull_request_id":  "<int>",
           "close_status":     "<str:status_lbl>,
           "closed":           "<bool>"
       },
       "error": null


comment_pull_request 
--------------------

.. py:function:: comment_pull_request(apiuser, pullrequestid, repoid=<Optional:None>, message=<Optional:None>, commit_id=<Optional:None>, status=<Optional:None>, comment_type=<Optional:u'note'>, resolves_comment_id=<Optional:None>, extra_recipients=<Optional:[]>, userid=<Optional:<OptionalAttr:apiuser>>, send_email=<Optional:True>)

   Comment on the pull request specified with the `pullrequestid`,
   in the |repo| specified by the `repoid`, and optionally change the
   review status.

   :param apiuser: This is filled automatically from the |authtoken|.
   :type apiuser: AuthUser
   :param repoid: Optional repository name or repository ID.
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
   :param resolves_comment_id: id of comment which this one will resolve
   :type resolves_comment_id: Optional(int)
   :param extra_recipients: list of user ids or usernames to add
       notifications for this comment. Acts like a CC for notification
   :type extra_recipients: Optional(list)
   :param userid: Comment on the pull request as this user
   :type userid: Optional(str or int)
   :param send_email: Define if this comment should also send email notification
   :type send_email: Optional(bool)

   Example output:

   .. code-block:: bash

       id : <id_given_in_input>
       result : {
           "pull_request_id":  "<Integer>",
           "comment_id":       "<Integer>",
           "status": {"given": <given_status>,
                      "was_changed": <bool status_was_actually_changed> },
       },
       error :  null


create_pull_request 
-------------------

.. py:function:: create_pull_request(apiuser, source_repo, target_repo, source_ref, target_ref, owner=<Optional:<OptionalAttr:apiuser>>, title=<Optional:''>, description=<Optional:''>, description_renderer=<Optional:''>, reviewers=<Optional:None>)

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
   :param owner: user_id or username
   :type owner: Optional(str)
   :param title: Optionally Set the pull request title, it's generated otherwise
   :type title: str
   :param description: Set the pull request description.
   :type description: Optional(str)
   :type description_renderer: Optional(str)
   :param description_renderer: Set pull request renderer for the description.
       It should be 'rst', 'markdown' or 'plain'. If not give default
       system renderer will be used
   :param reviewers: Set the new pull request reviewers list.
       Reviewer defined by review rules will be added automatically to the
       defined list.
   :type reviewers: Optional(list)
       Accepts username strings or objects of the format:

           [{'username': 'nick', 'reasons': ['original author'], 'mandatory': <bool>}]


get_pull_request 
----------------

.. py:function:: get_pull_request(apiuser, pullrequestid, repoid=<Optional:None>, merge_state=<Optional:False>)

   Get a pull request based on the given ID.

   :param apiuser: This is filled automatically from the |authtoken|.
   :type apiuser: AuthUser
   :param repoid: Optional, repository name or repository ID from where
       the pull request was opened.
   :type repoid: str or int
   :param pullrequestid: ID of the requested pull request.
   :type pullrequestid: int
   :param merge_state: Optional calculate merge state for each repository.
       This could result in longer time to fetch the data
   :type merge_state: bool

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
           "versions":          "<number_or_versions_of_pr>",
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


get_pull_request_comments 
-------------------------

.. py:function:: get_pull_request_comments(apiuser, pullrequestid, repoid=<Optional:None>)

   Get all comments of pull request specified with the `pullrequestid`

   :param apiuser: This is filled automatically from the |authtoken|.
   :type apiuser: AuthUser
   :param repoid: Optional repository name or repository ID.
   :type repoid: str or int
   :param pullrequestid: The pull request ID.
   :type pullrequestid: int

   Example output:

   .. code-block:: bash

       id : <id_given_in_input>
       result : [
           {
             "comment_author": {
               "active": true,
               "full_name_or_username": "Tom Gore",
               "username": "admin"
             },
             "comment_created_on": "2017-01-02T18:43:45.533",
             "comment_f_path": null,
             "comment_id": 25,
             "comment_lineno": null,
             "comment_status": {
               "status": "under_review",
               "status_lbl": "Under Review"
             },
             "comment_text": "Example text",
             "comment_type": null,
             "comment_last_version: 0,
             "pull_request_version": null,
             "comment_commit_id": None,
             "comment_pull_request_id": <pull_request_id>
           }
       ],
       error :  null


get_pull_requests 
-----------------

.. py:function:: get_pull_requests(apiuser, repoid, status=<Optional:'new'>, merge_state=<Optional:False>)

   Get all pull requests from the repository specified in `repoid`.

   :param apiuser: This is filled automatically from the |authtoken|.
   :type apiuser: AuthUser
   :param repoid: Optional repository name or repository ID.
   :type repoid: str or int
   :param status: Only return pull requests with the specified status.
       Valid options are.
       * ``new`` (default)
       * ``open``
       * ``closed``
   :type status: str
   :param merge_state: Optional calculate merge state for each repository.
       This could result in longer time to fetch the data
   :type merge_state: bool

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

.. py:function:: merge_pull_request(apiuser, pullrequestid, repoid=<Optional:None>, userid=<Optional:<OptionalAttr:apiuser>>)

   Merge the pull request specified by `pullrequestid` into its target
   repository.

   :param apiuser: This is filled automatically from the |authtoken|.
   :type apiuser: AuthUser
   :param repoid: Optional, repository name or repository ID of the
       target repository to which the |pr| is to be merged.
   :type repoid: str or int
   :param pullrequestid: ID of the pull request which shall be merged.
   :type pullrequestid: int
   :param userid: Merge the pull request as this user.
   :type userid: Optional(str or int)

   Example output:

   .. code-block:: bash

       "id": <id_given_in_input>,
       "result": {
           "executed":               "<bool>",
           "failure_reason":         "<int>",
           "merge_status_message":   "<str>",
           "merge_commit_id":        "<merge_commit_id>",
           "possible":               "<bool>",
           "merge_ref":        {
                                   "commit_id": "<commit_id>",
                                   "type":      "<type>",
                                   "name":      "<name>"
                               }
       },
       "error": null


update_pull_request 
-------------------

.. py:function:: update_pull_request(apiuser, pullrequestid, repoid=<Optional:None>, title=<Optional:''>, description=<Optional:''>, description_renderer=<Optional:''>, reviewers=<Optional:None>, update_commits=<Optional:None>)

   Updates a pull request.

   :param apiuser: This is filled automatically from the |authtoken|.
   :type apiuser: AuthUser
   :param repoid: Optional repository name or repository ID.
   :type repoid: str or int
   :param pullrequestid: The pull request ID.
   :type pullrequestid: int
   :param title: Set the pull request title.
   :type title: str
   :param description: Update pull request description.
   :type description: Optional(str)
   :type description_renderer: Optional(str)
   :param description_renderer: Update pull request renderer for the description.
       It should be 'rst', 'markdown' or 'plain'
   :param reviewers: Update pull request reviewers list with new value.
   :type reviewers: Optional(list)
       Accepts username strings or objects of the format:

           [{'username': 'nick', 'reasons': ['original author'], 'mandatory': <bool>}]

   :param update_commits: Trigger update of commits for this pull request
   :type: update_commits: Optional(bool)

   Example output:

   .. code-block:: bash

       id : <id_given_in_input>
       result : {
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


