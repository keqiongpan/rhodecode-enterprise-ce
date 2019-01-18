.. _indexing-ref:

Full-text Search
----------------

By default RhodeCode is configured to use `Whoosh`_ to index |repos| and
provide full-text search.

|RCE| also provides support for `Elasticsearch 6`_ as a backend more for advanced
and scalable search. See :ref:`enable-elasticsearch` for details.

Indexing
^^^^^^^^

To run the indexer you need to have an |authtoken| with admin rights to all |repos|.

To index new content added, you have the option to set the indexer up in a
number of ways, for example:

* Call the indexer via a cron job. We recommend running this once at night.
  In case you need everything indexed immediately it's possible to index few
  times during the day.
* Set the indexer to infinitely loop and reindex as soon as it has run its previous cycle.
* Hook the indexer up with your CI server to reindex after each push.

The indexer works by indexing new commits added since the last run. If you
wish to build a brand new index from scratch each time,
use the ``force`` option in the configuration file.

.. important::

   You need to have |RCT| installed, see :ref:`install-tools`. Since |RCE|
   3.5.0 they are installed by default and available with community/enterprise installations.

To set up indexing, use the following steps:

1. :ref:`config-rhoderc`, if running tools remotely.
2. :ref:`run-index`
3. :ref:`set-index`
4. :ref:`advanced-indexing`

.. _config-rhoderc:

Configure the ``.rhoderc`` File
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. note::

    Optionally it's possible to use indexer without the ``.rhoderc``. Simply instead of
    executing with `--instance-name=enterprise-1` execute providing the host and token
    directly: `--api-host=http://127.0.0.1:10000 --api-key=<auth token goes here>


|RCT| uses the :file:`/home/{user}/.rhoderc` file for connection details
to |RCE| instances. If this file is not automatically created,
you can configure it using the following example. You need to configure the
details for each instance you want to index.

.. code-block:: bash

    # Check the instance details
    # of the instance you want to index
    $ rccontrol status

    - NAME: enterprise-1
    - STATUS: RUNNING
    - TYPE: Enterprise
    - VERSION: 4.1.0
    - URL: http://127.0.0.1:10003

To get your API Token, on the |RCE| interface go to
:menuselection:`username --> My Account --> Auth tokens`

.. code-block:: ini

    # Configure .rhoderc with matching details
    # This allows the indexer to connect to the instance
    [instance:enterprise-1]
    api_host = http://127.0.0.1:10000
    api_key = <auth token goes here>


.. _run-index:

Run the Indexer
^^^^^^^^^^^^^^^

Run the indexer using the following command, and specify the instance you want to index:

.. code-block:: bash

   # Using default installation
   $ /home/user/.rccontrol/enterprise-1/profile/bin/rhodecode-index \
       --instance-name=enterprise-1

   # Using a custom mapping file
   $ /home/user/.rccontrol/enterprise-1/profile/bin/rhodecode-index \
       --instance-name=enterprise-1 \
       --mapping=/home/user/.rccontrol/enterprise-1/search_mapping.ini

   # Using a custom mapping file and invocation without ``.rhoderc``
   $ /home/user/.rccontrol/enterprise-1/profile/bin/rhodecode-index \
       --api-host=http://rhodecodecode.myserver.com --api-key=xxxxx \
       --mapping=/home/user/.rccontrol/enterprise-1/search_mapping.ini

   # From inside a virtualev on your local machine or CI server.
   (venv)$ rhodecode-index --instance-name=enterprise-1


.. note::

   In case of often indexing the index may become fragmented. Most often a result of that
   is error about `too many open files`. To fix this indexer needs to be executed with
   --optimize flag. E.g `rhodecode-index --instance-name=enterprise-1 --optimize`
   This should be executed regularly, once a week is recommended.


.. _set-index:

Schedule the Indexer
^^^^^^^^^^^^^^^^^^^^

To schedule the indexer, configure the crontab file to run the indexer inside
your |RCT| virtualenv using the following steps.

1. Open the crontab file, using ``crontab -e``.
2. Add the indexer to the crontab, and schedule it to run as regularly as you
   wish.
3. Save the file.

.. code-block:: bash

    $ crontab -e

    # The virtualenv can be called using its full path, so for example you can
    # put this example into the crontab

    # Run the indexer daily at 4am using the default mapping settings
    * 4 * * * /home/ubuntu/.virtualenv/rhodecode-venv/bin/rhodecode-index \
    --instance-name=enterprise-1

    # Run the indexer every Sunday at 3am using default mapping
    * 3 * * 0 /home/ubuntu/.virtualenv/rhodecode-venv/bin/rhodecode-index \
    --instance-name=enterprise-1

    # Run the indexer every 15 minutes
    # using a specially configured mapping file
    */15 * * * * ~/.rccontrol/enterprise-4/profile/bin/rhodecode-index \
       --instance-name=enterprise-4 \
       --mapping=/home/user/.rccontrol/enterprise-4/search_mapping.ini

.. _advanced-indexing:

Advanced Indexing
^^^^^^^^^^^^^^^^^


Force Re-Indexing single repository
+++++++++++++++++++++++++++++++++++

Often it's required to re-index whole repository because of some repository changes,
or to remove some indexed secrets, or files. There's a special `--repo-name=` flag
for the indexer that limits execution to a single repository. For example to force-reindex
single repository such call can be made::

    rhodecode-index --instance-name=enterprise-1 --force --repo-name=rhodecode-vcsserver


Removing repositories from index
++++++++++++++++++++++++++++++++

The indexer automatically removes renamed repositories and builds index for new names.
In case that you wish to remove indexed repository manually such call would allow that::

    rhodecode-index --instance-name=enterprise-1 --remove-only --repo-name=rhodecode-vcsserver


Using search_mapping.ini file for advanced index rules
++++++++++++++++++++++++++++++++++++++++++++++++++++++

By default rhodecode-index runs for all repositories, all files with parsing limits
defined by the CLI default arguments. You can change those limits by calling with
different flags such as `--max-filesize 2048kb` or `--repo-limit 10`

For more advanced execution logic it's possible to use a configuration file that
would define detailed rules which repositories and how should be indexed.

|RCT| provides an example index configuration file called :file:`search_mapping.ini`.
This file is created by default during installation and is located at:

* :file:`/home/{user}/.rccontrol/{instance-id}/search_mapping.ini`, using default |RCT|.
* :file:`~/venv/lib/python2.7/site-packages/rhodecode_tools/templates/mapping.ini`,
  when using ``virtualenv``.

.. note::

    If you need to create the :file:`search_mapping.ini` file manually, use the |RCT|
    ``rhodecode-index --create-mapping path/to/search_mapping.ini`` API call.
    For details, see the :ref:`tools-cli` section.

To Run the indexer with mapping file provide it using `--mapping` flag::

    rhodecode-index --instance-name=enterprise-1 --mapping=/my/path/search_mapping.ini


Here's a detailed example of using :file:`search_mapping.ini` file.

.. code-block:: ini

    [__DEFAULT__]
    ; Create index on commits data, and files data in this order. Available options
    ; are `commits`, `files`
    index_types = commits,files

    ; Commit fetch limit. In what amount of chunks commits should be fetched
    ; via api and parsed. This allows server to transfer smaller chunks and be less loaded
    commit_fetch_limit = 1000

    ; Commit process limit. Limit the number of commits indexer should fetch, and
    ; store inside the full text search index. eg. if repo has 2000 commits, and
    ; limit is 1000, on the first run it will process commits 0-1000 and on the
    ; second 1000-2000 commits. Help reduce memory usage, default is 50000
    ; (set -1 for unlimited)
    commit_process_limit = 50000

    ; Limit of how many repositories each run can process, default is -1 (unlimited)
    ; in case of 1000s of repositories it's better to execute in chunks to not overload
    ; the server.
    repo_limit = -1

    ; Default patterns for indexing files and content of files. Binary files
    ; are skipped by default.

    ; Add to index those comma separated files; globs syntax
    ; e.g index_files = *.py, *.c, *.h, *.js
    index_files = *,

    ; Do not add to index those comma separated files, this excludes
    ; both search by name and content; globs syntax
    ; e.g index_files = *.key, *.sql, *.xml
    skip_files = ,

    ; Add to index content of those comma separated files; globs syntax
    ; e.g index_files = *.h, *.obj
    index_files_content = *,

    ; Do not add to index content of those comma separated files; globs syntax
    ; e.g index_files = *.exe, *.bin, *.log, *.dump
    skip_files_content = ,

    ; Force rebuilding an index from scratch. Each repository will be rebuild from
    ; scratch with a global flag. Use --repo-name=NAME --force to rebuild single repo
    force = false

    ; maximum file size that indexer will use, files above that limit are not going
    ; to have they content indexed.
    ; Possible options are KB (kilobytes), MB (megabytes), eg 1MB or 1024KB
    max_filesize = 2MB


    [__INDEX_RULES__]
    ; Ordered match rules for repositories. A list of all repositories will be fetched
    ; using API and this list will be filtered using those rules.
    ; Syntax for entry: `glob_pattern_OR_full_repo_name = 0 OR 1` where 0=exclude, 1=include
    ; When this ordered list is traversed first match will return the include/exclude marker
    ; For example:
    ;    upstream/binary_repo = 0
    ;    upstream/subrepo/xml_files = 0
    ;    upstream/* = 1
    ;    special-repo = 1
    ;    * = 0
    ; This will index all repositories under upstream/*, but skip upstream/binary_repo
    ; and upstream/sub_repo/xml_files, last * = 0 means skip all other matches

    ; Another example:
    ;    *-fork = 0
    ;    * = 1
    ; This will index all repositories, except those that have -fork as suffix.

    rhodecode-vcsserver = 1
    rhodecode-enterprise-ce = 1
    upstream/mozilla/firefox-repo = 0
    upstream/git-binaries = 0
    upstream/* = 1
    * = 0

    ; == EXPLICIT REPOSITORY INDEXING ==
    ; If defined this will skip using __INDEX_RULES__, and will not use API to fetch
    ; list of repositories, it will explicitly take names defined with [NAME] format and
    ; try to build the index, to build index just for repo_name_1 and special-repo use:
    ;    [repo_name_1]
    ;    [special-repo]

    ; == PER REPOSITORY CONFIGURATION ==
    ; This allows overriding the global configuration per repository.
    ; example to set specific file limit, and skip certain files for repository special-repo
    ;    [conf:special-repo]
    ;    max_filesize = 5mb
    ;    skip_files = *.xml, *.sql
    ;    index_types = files,

    [conf:rhodecode-vcsserver]
    index_types = files,
    max_filesize = 5mb
    skip_files = *.xml, *.sql
    index_files = *.py, *.c, *.h, *.js


In case of 1000s of repositories it can be tricky to write the include/exclude rules at first.
There's a special flag to test the mapping file rules and list repositories that would
be indexed. Run the indexer with `--show-matched-repos` to list only the match rules::

    rhodecode-index --instance-name=enterprise-1 --show-matched-repos --mapping=/my/path/search_mapping.ini


.. _enable-elasticsearch:

Enabling Elasticsearch
^^^^^^^^^^^^^^^^^^^^^^

Elasticsearch is available in EE edition only. It provides much scalable and more advanced
search capabilities. While Whoosh is fine for upto 1-2GB of data beyond that amount of
data it starts slowing down, and can cause other problems. Elasticsearch 6 also provides
much more advanced query language allowing advanced filtering by file paths, extensions
OR statements, ranges etc. Please check query language examples in the search field for
some advanced query language usage.


1. Open the :file:`rhodecode.ini` file for the instance you wish to edit. The
   default location is
   :file:`home/{user}/.rccontrol/{instance-id}/rhodecode.ini`
2. Find the search configuration section:

.. code-block:: ini

    ###################################
    ## SEARCH INDEXING CONFIGURATION ##
    ###################################

    search.module = rhodecode.lib.index.whoosh
    search.location = %(here)s/data/index

and change it to:

.. code-block:: ini

    search.module = rc_elasticsearch
    search.location = http://localhost:9200
    ## specify Elastic Search version, 6 for latest or 2 for legacy
    search.es_version = 6

where ``search.location`` points to the elasticsearch server
by default running on port 9200.

Index invocation also needs change. Please provide --es-version= and
--engine-location= parameters to define elasticsearch server location and it's version.
For example::

    rhodecode-index --instace-name=enterprise-1 --es-version=6 --engine-location=http://localhost:9200


.. _Whoosh: https://pypi.python.org/pypi/Whoosh/
.. _Elasticsearch 6: https://www.elastic.co/