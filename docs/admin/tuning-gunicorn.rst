.. _increase-gunicorn:

Configure Gunicorn Workers
--------------------------


|RCE| comes with `Gunicorn`_ which is a Python WSGI HTTP Server for UNIX.

To improve |RCE| performance you can increase the number of `Gunicorn`_  workers.
This allows to handle more connections concurrently, and provide better
responsiveness and performance.

By default during installation |RCC|  tries to detect how many CPUs are
available in the system, and set the number workers based on that information.
However sometimes it's better to manually set the number of workers.

To do this, use the following steps:

1. Open the :file:`home/{user}/.rccontrol/{instance-id}/rhodecode.ini` file.
2. In the ``[server:main]`` section, change the number of Gunicorn
   ``workers`` using the following default formula :math:`(2 * Cores) + 1`.
   We however not recommend using more than 8-12 workers per server. It's better
   to start using the :ref:`scale-horizontal-cluster` in case that performance
   with 8-12 workers is not enough.

.. code-block:: ini

    use = egg:gunicorn#main
    ## Sets the number of process workers. You must set `instance_id = *`
    ## when this option is set to more than one worker, recommended
    ## value is (2 * NUMBER_OF_CPUS + 1), eg 2CPU = 5 workers
    ## The `instance_id = *` must be set in the [app:main] section below
    workers = 4
    ## process name
    proc_name = rhodecode
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

3. In the ``[app:main]`` section, set the ``instance_id`` property to ``*``.

.. code-block:: ini

    # In the [app:main] section
    [app:main]
    # You must set `instance_id = *`
    instance_id = *

4. Change the VCSServer workers too. Open the
   :file:`home/{user}/.rccontrol/{instance-id}/vcsserver.ini` file.

5. In the ``[server:main]`` section, increase the number of Gunicorn
   ``workers`` using the following formula :math:`(2 * Cores) + 1`.

.. code-block:: ini

    ## run with gunicorn --log-config vcsserver.ini --paste vcsserver.ini
    use = egg:gunicorn#main
    ## Sets the number of process workers. Recommended
    ## value is (2 * NUMBER_OF_CPUS + 1), eg 2CPU = 5 workers
    workers = 4
    ## process name
    proc_name = rhodecode_vcsserver
    ## type of worker class, currently `sync` is the only option allowed.
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

6. Save your changes.
7. Restart your |RCE| instances, using the following command:

.. code-block:: bash

    $ rccontrol restart '*'


Gunicorn Gevent Backend
-----------------------

Gevent is an asynchronous worker type for Gunicorn. It allows accepting multiple
connections on a single `Gunicorn`_  worker. This means you can handle 100s
of concurrent clones, or API calls using just few workers. A setting called
`worker_connections` defines on how many connections each worker can
handle using `Gevent`.


To enable `Gevent` on |RCE| do the following:


1. Open the :file:`home/{user}/.rccontrol/{instance-id}/rhodecode.ini` file.
2. In the ``[server:main]`` section, change `worker_class` for Gunicorn.


.. code-block:: ini

    ## type of worker class, one of sync, gevent
    ## recommended for bigger setup is using of of other than sync one
    worker_class = gevent
    ## The maximum number of simultaneous clients. Valid only for Gevent
    worker_connections = 30


.. note::

    `Gevent` is currently only supported for Enterprise/Community instances.
    VCSServer doesn't yet support gevent.



.. _Gunicorn: http://gunicorn.org/
