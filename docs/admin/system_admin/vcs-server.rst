.. _vcs-server:

VCS Server Management
---------------------

The VCS Server handles |RCE| backend functionality. You need to configure
a VCS Server to run with a |RCE| instance. If you do not, you will be missing
the connection between |RCE| and its |repos|. This will cause error messages
on the web interface. You can run your setup in the following configurations,
currently the best performance is one of following:

* One VCS Server per |RCE| instance.
* One VCS Server handling multiple instances.

.. important::

   If your server locale settings are not correctly configured,
   |RCE| and the VCS Server can run into issues. See this `Ask Ubuntu`_ post
   which explains the problem and gives a solution.

For more information, see the following sections:

* :ref:`install-vcs`
* :ref:`config-vcs`
* :ref:`vcs-server-options`
* :ref:`vcs-server-versions`
* :ref:`vcs-server-maintain`
* :ref:`vcs-server-config-file`
* :ref:`svn-http`

.. _install-vcs:

VCS Server Installation
^^^^^^^^^^^^^^^^^^^^^^^

To install a VCS Server, see
:ref:`Installing a VCS server <control:install-vcsserver>`.

.. _config-vcs:

Hooking |RCE| to its VCS Server
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To configure a |RCE| instance to use a VCS server, see
:ref:`Configuring the VCS Server connection <control:manually-vcsserver-ini>`.

.. _vcs-server-options:

|RCE| VCS Server Options
^^^^^^^^^^^^^^^^^^^^^^^^

The following list shows the available options on the |RCE| side of the
connection to the VCS Server. The settings are configured per
instance in the
:file:`/home/{user}/.rccontrol/{instance-id}/rhodecode.ini` file.

.. rst-class:: dl-horizontal

    \vcs.backends <available-vcs-systems>
        Set a comma-separated list of the |repo| options available from the
        web interface. The default is ``hg, git, svn``,
        which is all |repo| types available. The order of backends is also the
        order backend will try to detect requests type.

    \vcs.connection_timeout <seconds>
        Set the length of time in seconds that the VCS Server waits for
        requests to process. After the timeout expires,
        the request is closed. The default is ``3600``. Set to a higher
        number if you experience network latency, or timeout issues with very
        large push/pull requests.

    \vcs.server.enable <boolean>
        Enable or disable the VCS Server. The available options are ``true`` or
        ``false``. The default is ``true``.

    \vcs.server <host:port>
        Set the host, either hostname or IP Address, and port of the VCS server
        you wish to run with your |RCE| instance.

.. code-block:: ini

    ##################
    ### VCS CONFIG ###
    ##################
    # set this line to match your VCS Server
    vcs.server = 127.0.0.1:10004
    # Set to False to disable the VCS Server
    vcs.server.enable = True
    vcs.backends = hg, git, svn
    vcs.connection_timeout = 3600


.. _vcs-server-versions:

VCS Server Versions
^^^^^^^^^^^^^^^^^^^

An updated version of the VCS Server is released with each |RCE| version. Use
the VCS Server number that matches with the |RCE| version to pair the
appropriate ones together. For |RCE| versions pre 3.3.0,
VCS Server 1.X.Y works with |RCE| 3.X.Y, for example:

* VCS Server 1.0.0 works with |RCE| 3.0.0
* VCS Server 1.2.2 works with |RCE| 3.2.2

For |RCE| versions post 3.3.0, the VCS Server and |RCE| version numbers
match, for example:

* VCS Server |release| works with |RCE| |release|

.. _vcs-server-maintain:

VCS Server Cache Optimization
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To optimize the VCS server to manage the cache and memory usage efficiently, it's recommended to
configure the Redis backend for VCSServer caches.
Once configured, restart the VCS Server.

Make sure Redis is installed and running.
Open :file:`/home/{user}/.rccontrol/{vcsserver-id}/vcsserver.ini`
file and ensure the below settings for `repo_object` type cache are set:

.. code-block:: ini

    ; ensure the default file based cache is *commented out*
    ##rc_cache.repo_object.backend = dogpile.cache.rc.file_namespace
    ##rc_cache.repo_object.expiration_time = 2592000

    ; `repo_object` cache settings for vcs methods for repositories
    rc_cache.repo_object.backend = dogpile.cache.rc.redis_msgpack

    ; cache auto-expires after N seconds
    ; Examples: 86400 (1Day), 604800 (7Days), 1209600 (14Days), 2592000 (30days), 7776000 (90Days)
    rc_cache.repo_object.expiration_time = 2592000

    ; redis_expiration_time needs to be greater then expiration_time
    rc_cache.repo_object.arguments.redis_expiration_time = 3592000

    rc_cache.repo_object.arguments.host = localhost
    rc_cache.repo_object.arguments.port = 6379
    rc_cache.repo_object.arguments.db = 5
    rc_cache.repo_object.arguments.socket_timeout = 30
    ; more Redis options: https://dogpilecache.sqlalchemy.org/en/latest/api.html#redis-backends
    rc_cache.repo_object.arguments.distributed_lock = true


To clear the cache completely, you can restart the VCS Server.

.. important::

   While the VCS Server handles a restart gracefully on the web interface,
   it will drop connections during push/pull requests. So it is recommended
   you only perform this when there is very little traffic on the instance.

Use the following example to restart your VCS Server,
for full details see the :ref:`RhodeCode Control CLI <control:rcc-cli>`.

.. code-block:: bash

    $ rccontrol status

.. code-block:: vim

    - NAME: vcsserver-1
    - STATUS: RUNNING
      logs:/home/ubuntu/.rccontrol/vcsserver-1/vcsserver.log
    - VERSION: 4.7.2 VCSServer
    - URL: http://127.0.0.1:10008
    - CONFIG: /home/ubuntu/.rccontrol/vcsserver-1/vcsserver.ini

    $ rccontrol restart vcsserver-1
    Instance "vcsserver-1" successfully stopped.
    Instance "vcsserver-1" successfully started.

.. _vcs-server-config-file:

VCS Server Configuration
^^^^^^^^^^^^^^^^^^^^^^^^

You can configure settings for multiple VCS Servers on your
system using their individual configuration files. Use the following
properties inside the configuration file to set up your system. The default
location is :file:`home/{user}/.rccontrol/{vcsserver-id}/vcsserver.ini`.
For a more detailed explanation of the logger levers, see :ref:`debug-mode`.

.. rst-class:: dl-horizontal

    \host <ip-address>
        Set the host on which the VCS Server will run. VCSServer is not
        protected by any authentication, so we *highly* recommend running it
        under localhost ip that is `127.0.0.1`

    \port <int>
        Set the port number on which the VCS Server will be available.


.. note::

   After making changes, you need to restart your VCS Server to pick them up.

.. code-block:: ini

    ; #################################
    ; RHODECODE VCSSERVER CONFIGURATION
    ; #################################

    [server:main]
    ; COMMON HOST/IP CONFIG
    host = 127.0.0.1
    port = 10002

    ; ###########################
    ; GUNICORN APPLICATION SERVER
    ; ###########################

    ; run with gunicorn --log-config rhodecode.ini --paste rhodecode.ini

    ; Module to use, this setting shouldn't be changed
    use = egg:gunicorn#main

    ; Sets the number of process workers. More workers means more concurrent connections
    ; RhodeCode can handle at the same time. Each additional worker also it increases
    ; memory usage as each has it's own set of caches.
    ; Recommended value is (2 * NUMBER_OF_CPUS + 1), eg 2CPU = 5 workers, but no more
    ; than 8-10 unless for really big deployments .e.g 700-1000 users.
    ; `instance_id = *` must be set in the [app:main] section below (which is the default)
    ; when using more than 1 worker.
    workers = 6

    ; Gunicorn access log level
    loglevel = info

    ; Process name visible in process list
    proc_name = rhodecode_vcsserver

    ; Type of worker class, one of sync, gevent
    ; currently `sync` is the only option allowed.
    worker_class = sync

    ; The maximum number of simultaneous clients. Valid only for gevent
    worker_connections = 10

    ; Max number of requests that worker will handle before being gracefully restarted.
    ; Prevents memory leaks, jitter adds variability so not all workers are restarted at once.
    max_requests = 1000
    max_requests_jitter = 30

    ; Amount of time a worker can spend with handling a request before it
    ; gets killed and restarted. By default set to 21600 (6hrs)
    ; Examples: 1800 (30min), 3600 (1hr), 7200 (2hr), 43200 (12h)
    timeout = 21600

    ; The maximum size of HTTP request line in bytes.
    ; 0 for unlimited
    limit_request_line = 0

    ; Limit the number of HTTP headers fields in a request.
    ; By default this value is 100 and can't be larger than 32768.
    limit_request_fields = 32768

    ; Limit the allowed size of an HTTP request header field.
    ; Value is a positive number or 0.
    ; Setting it to 0 will allow unlimited header field sizes.
    limit_request_field_size = 0

    ; Timeout for graceful workers restart.
    ; After receiving a restart signal, workers have this much time to finish
    ; serving requests. Workers still alive after the timeout (starting from the
    ; receipt of the restart signal) are force killed.
    ; Examples: 1800 (30min), 3600 (1hr), 7200 (2hr), 43200 (12h)
    graceful_timeout = 3600

    # The number of seconds to wait for requests on a Keep-Alive connection.
    # Generally set in the 1-5 seconds range.
    keepalive = 2

    ; Maximum memory usage that each worker can use before it will receive a
    ; graceful restart signal 0 = memory monitoring is disabled
    ; Examples: 268435456 (256MB), 536870912 (512MB)
    ; 1073741824 (1GB), 2147483648 (2GB), 4294967296 (4GB)
    memory_max_usage = 1073741824

    ; How often in seconds to check for memory usage for each gunicorn worker
    memory_usage_check_interval = 60

    ; Threshold value for which we don't recycle worker if GarbageCollection
    ; frees up enough resources. Before each restart we try to run GC on worker
    ; in case we get enough free memory after that, restart will not happen.
    memory_usage_recovery_threshold = 0.8


    [app:main]
    use = egg:rhodecode-vcsserver

    pyramid.default_locale_name = en
    pyramid.includes =

    ; default locale used by VCS systems
    locale = en_US.UTF-8

    ; #############
    ; DOGPILE CACHE
    ; #############

    ; Default cache dir for caches. Putting this into a ramdisk can boost performance.
    ; eg. /tmpfs/data_ramdisk, however this directory might require large amount of space
    cache_dir = %(here)s/data

    ; **********************************************************
    ; `repo_object` cache with redis backend
    ; recommended for larger instance, or for better performance
    ; **********************************************************

    ; `repo_object` cache settings for vcs methods for repositories
    rc_cache.repo_object.backend = dogpile.cache.rc.redis_msgpack

    ; cache auto-expires after N seconds
    ; Examples: 86400 (1Day), 604800 (7Days), 1209600 (14Days), 2592000 (30days), 7776000 (90Days)
    rc_cache.repo_object.expiration_time = 2592000

    ; redis_expiration_time needs to be greater then expiration_time
    rc_cache.repo_object.arguments.redis_expiration_time = 3592000

    rc_cache.repo_object.arguments.host = localhost
    rc_cache.repo_object.arguments.port = 6379
    rc_cache.repo_object.arguments.db = 5
    rc_cache.repo_object.arguments.socket_timeout = 30
    ; more Redis options: https://dogpilecache.sqlalchemy.org/en/latest/api.html#redis-backends
    rc_cache.repo_object.arguments.distributed_lock = true

    ; #####################
    ; LOGGING CONFIGURATION
    ; #####################
    [loggers]
    keys = root, vcsserver

    [handlers]
    keys = console

    [formatters]
    keys = generic

    ; #######
    ; LOGGERS
    ; #######
    [logger_root]
    level = NOTSET
    handlers = console

    [logger_vcsserver]
    level = DEBUG
    handlers =
    qualname = vcsserver
    propagate = 1


    ; ########
    ; HANDLERS
    ; ########

    [handler_console]
    class = StreamHandler
    args = (sys.stderr, )
    level = INFO
    formatter = generic

    ; ##########
    ; FORMATTERS
    ; ##########

    [formatter_generic]
    format = %(asctime)s.%(msecs)03d [%(process)d] %(levelname)-5.5s [%(name)s] %(message)s
    datefmt = %Y-%m-%d %H:%M:%S


.. _Subversion Red Book: http://svnbook.red-bean.com/en/1.7/svn-book.html#svn.ref.svn

.. _Ask Ubuntu: http://askubuntu.com/questions/162391/how-do-i-fix-my-locale-issue
