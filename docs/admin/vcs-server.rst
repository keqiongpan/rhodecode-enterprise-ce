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

VCS Server Memory Optimization
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To optimize the VCS server to manage the cache and memory usage efficiently, you need to
configure the following options in the
:file:`/home/{user}/.rccontrol/{vcsserver-id}/vcsserver.ini` file. Once
configured, restart the VCS Server. By default we use an optimal settings, but in certain
conditions tunning expiration_time and max_size can affect memory usage and performance

.. code-block:: ini

    ## cache region for storing repo_objects cache
    rc_cache.repo_object.backend = dogpile.cache.rc.memory_lru

    ## cache auto-expires after N seconds, setting this to 0 disabled cache
    rc_cache.repo_object.expiration_time = 300

    ## max size of LRU, old values will be discarded if the size of cache reaches max_size
    ## Sets the maximum number of items stored in the cache, before the cache
    ## starts to be cleared.

    ## As a general rule of thumb, running this value at 120 resulted in a
    ## 5GB cache. Running it at 240 resulted in a 9GB cache. Your results
    ## will differ based on usage patterns and |repo| sizes.

    ## Tweaking this value to run at a fairly constant memory load on your
    ## server will help performance.

    rc_cache.repo_object.max_size = 120


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

    \locale <locale_utf>
        Set the locale the VCS Server expects.

    \workers <int>
        Set the number of process workers.Recommended
        value is (2 * NUMBER_OF_CPUS + 1), eg 2CPU = 5 workers

    \max_requests <int>
        The maximum number of requests a worker will process before restarting.
        Any value greater than zero will limit the number of requests a work
        will process before automatically restarting. This is a simple method
        to help limit the damage of memory leaks.

    \max_requests_jitter <int>
        The maximum jitter to add to the max_requests setting.
        The jitter causes the restart per worker to be randomized by
        randint(0, max_requests_jitter). This is intended to stagger worker
        restarts to avoid all workers restarting at the same time.


.. note::

   After making changes, you need to restart your VCS Server to pick them up.

.. code-block:: ini

    ################################################################################
    # RhodeCode VCSServer with HTTP Backend - configuration                        #
    #                                                                              #
    ################################################################################


    [server:main]
    ## COMMON ##
    host = 127.0.0.1
    port = 10002

    ##########################
    ## GUNICORN WSGI SERVER ##
    ##########################
    ## run with gunicorn --log-config vcsserver.ini --paste vcsserver.ini
    use = egg:gunicorn#main
    ## Sets the number of process workers. Recommended
    ## value is (2 * NUMBER_OF_CPUS + 1), eg 2CPU = 5 workers
    workers = 3
    ## process name
    proc_name = rhodecode_vcsserver
    ## type of worker class, one of sync, gevent
    ## recommended for bigger setup is using of of other than sync one
    worker_class = sync
    ## The maximum number of simultaneous clients. Valid only for Gevent
    #worker_connections = 10
    ## max number of requests that worker will handle before being gracefully
    ## restarted, could prevent memory leaks
    max_requests = 1000
    max_requests_jitter = 30
    ## amount of time a worker can spend with handling a request before it
    ## gets killed and restarted. Set to 6hrs
    timeout = 21600

    [app:main]
    use = egg:rhodecode-vcsserver

    pyramid.default_locale_name = en
    pyramid.includes =

    ## default locale used by VCS systems
    locale = en_US.UTF-8

    # cache regions, please don't change
    beaker.cache.regions = repo_object
    beaker.cache.repo_object.type = memorylru
    beaker.cache.repo_object.max_items = 100
    # cache auto-expires after N seconds
    beaker.cache.repo_object.expire = 300
    beaker.cache.repo_object.enabled = true


    ################################
    ### LOGGING CONFIGURATION   ####
    ################################
    [loggers]
    keys = root, vcsserver, beaker

    [handlers]
    keys = console

    [formatters]
    keys = generic

    #############
    ## LOGGERS ##
    #############
    [logger_root]
    level = NOTSET
    handlers = console

    [logger_vcsserver]
    level = DEBUG
    handlers =
    qualname = vcsserver
    propagate = 1

    [logger_beaker]
    level = DEBUG
    handlers =
    qualname = beaker
    propagate = 1


    ##############
    ## HANDLERS ##
    ##############

    [handler_console]
    class = StreamHandler
    args = (sys.stderr,)
    level = DEBUG
    formatter = generic

    ################
    ## FORMATTERS ##
    ################

    [formatter_generic]
    format = %(asctime)s.%(msecs)03d %(levelname)-5.5s [%(name)s] %(message)s
    datefmt = %Y-%m-%d %H:%M:%S


.. _Subversion Red Book: http://svnbook.red-bean.com/en/1.7/svn-book.html#svn.ref.svn

.. _Ask Ubuntu: http://askubuntu.com/questions/162391/how-do-i-fix-my-locale-issue
