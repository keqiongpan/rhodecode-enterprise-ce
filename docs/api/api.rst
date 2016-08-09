.. _api:

API Documentation
=================

The |RCE| API uses a single scheme for calling all API methods. The API is
implemented with JSON protocol in both directions. To send API requests to
your instance of |RCE|, use the following URL format
``<your_server>/_admin``

.. note::

   To use the API, you should configure the :file:`~/.rhoderc` file with
   access details per instance. For more information, see
   :ref:`config-rhoderc`.


API ACCESS FOR WEB VIEWS
------------------------

API access can also be turned on for each web view in |RCE| that is
decorated with a `@LoginRequired` decorator. To enable API access, change
the standard login decorator to `@LoginRequired(api_access=True)`.

From |RCM| version 1.7.0 you can configure a white list
of views that have API access enabled by default. To enable these,
edit the |RCM| configuration ``.ini`` file. The default location is:

* |RCM| Pre-2.2.7 :file:`root/rhodecode/data/production.ini`
* |RCM| 3.0 :file:`/home/{user}/.rccontrol/{instance-id}/rhodecode.ini`

To configure the white list, edit this section of the file. In this
configuration example, API access is granted to the patch/diff raw file and
archive.

.. code-block:: ini

    ## List of controllers (using glob syntax) that AUTH TOKENS could be used for access.
    ## Adding ?auth_token = <token> to the url authenticates this request as if it
    ## came from the the logged in user who own this authentication token.
    ##
    ## Syntax is <ControllerClass>:<function_pattern>.
    ## The list should be "," separated and on a single line.
    ##
    api_access_controllers_whitelist = ChangesetController:changeset_patch,ChangesetController:changeset_raw,ilesController:raw,FilesController:archivefile,

After this change, a |RCE| view can be accessed without login by adding a
GET parameter ``?auth_token=<auth_token>`` to a url. For example to
access the raw diff.

.. code-block:: html

   http://<server>/<repo>/changeset-diff/<sha>?auth_token=<auth_token>

By default this is only enabled on RSS/ATOM feed views. Exposing raw diffs is a
good way to integrate with 3rd party services like code review, or build farms
that could download archives.

API ACCESS
----------

All clients are required to send JSON-RPC spec JSON data.

.. code-block:: bash

    {
        "id:"<id>",
        "auth_token":"<auth_token>",
        "method":"<method_name>",
        "args":{"<arg_key>":"<arg_val>"}
    }

Example call for auto pulling from remote repositories using curl:

.. code-block:: bash

    curl https://server.com/_admin/api -X POST -H 'content-type:text/plain' --data-binary '{"id":1,
    "auth_token":"xe7cdb2v278e4evbdf5vs04v832v0efvcbcve4a3","method":"pull", "args":{"repo":"CPython"}}'

Provide those parameters:
 - **id** A value of any type, which is used to match the response with the
   request that it is replying to.
 - **auth_token** for access and permission validation.
 - **method** is name of method to call
 - **args** is an ``key:value`` list of arguments to pass to method

.. note::

    To get your |authtoken|, from the |RCE| interface,
    go to:
    :menuselection:`username --> My account --> Auth tokens`

    For security reasons you should always create a dedicated |authtoken| for
    API use only.


The |RCE| API will always return a JSON-RPC response:

.. code-block:: bash

    {
        "id": <id>, # matching id sent by request
        "result": "<result>"|null, # JSON formatted result, null if any errors
        "error": "null"|<error_message> # JSON formatted error (if any)
    }

All responses from API will be with `HTTP/1.0 200 OK` status code.
If there is an error when calling the API, the *error* key will contain a
failure description and the *result* will be `null`.

API CLIENT
----------

To install the |RCE| API, see :ref:`install-tools`. To configure the API per
instance, see the :ref:`rc-tools` section as you need to configure a
:file:`~/.rhoderc` file with your |authtokens|.

Once you have set up your instance API access, use the following examples to
get started.

.. code-block:: bash

    # Getting the 'rhodecode' repository
    # from a RhodeCode Enterprise instance
    rhodecode-api --instance-name=enterprise-1 get_repo repoid:rhodecode

    Calling method get_repo => http://127.0.0.1:5000
    Server response
    {
        <json data>
    }

    # Creating a new mercurial repository called 'brand-new'
    # with a description 'Repo-description'
    rhodecode-api --instance-name=enterprise-1 create_repo repo_name:brand-new repo_type:hg description:Repo-description
    {
      "error": null,
      "id": 1110,
      "result": {
        "msg": "Created new repository `brand-new`",
        "success": true,
        "task": null
      }
    }

A broken example, what not to do.

.. code-block:: bash

    # A call missing the required arguments
    # and not specifying the instance
    rhodecode-api get_repo

    Calling method get_repo => http://127.0.0.1:5000
    Server response
    "Missing non optional `repoid` arg in JSON DATA"

You can specify pure JSON using the ``--format`` parameter.

.. code-block:: bash

    rhodecode-api --format=json get_repo repoid:rhodecode

In such case only output that this function shows is pure JSON, we can use that
and pipe output to some json formatter.

If output is in pure JSON format, you can pipe output to a JSON formatter.

.. code-block:: bash

    rhodecode-api --instance-name=enterprise-1 --format=json get_repo repoid:rhodecode | python -m json.tool

API METHODS
-----------

Each method by default required following arguments.

.. code-block:: bash

    id :      "<id_for_response>"
    auth_token : "<auth_token>"
    method :  "<method name>"
    args :    {}

Use each **param** from docs and put it in args, Optional parameters
are not required in args.

.. code-block:: bash

    args: {"repoid": "rhodecode"}

.. Note: From this point on things are generated by the script in
   `scripts/fabfile.py`. To change things below, update the docstrings in the
   ApiController.

.. --- API DEFS MARKER ---
.. toctree::

   methods/license-methods
   methods/deprecated-methods
   methods/gist-methods
   methods/pull-request-methods
   methods/repo-methods
   methods/repo-group-methods
   methods/server-methods
   methods/user-methods
   methods/user-group-methods
