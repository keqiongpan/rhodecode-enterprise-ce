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

    ; Sets the number of process workers. More workers means more concurrent connections
    ; RhodeCode can handle at the same time. Each additional worker also it increases
    ; memory usage as each has it's own set of caches.
    ; Recommended value is (2 * NUMBER_OF_CPUS + 1), eg 2CPU = 5 workers, but no more
    ; than 8-10 unless for really big deployments .e.g 700-1000 users.
    ; `instance_id = *` must be set in the [app:main] section below (which is the default)
    ; when using more than 1 worker.
    workers = 6

    ; Type of worker class, one of `sync`, `gevent`
    ; Use `gevent` for rhodecode
    worker_class = gevent

    ; The maximum number of simultaneous clients per worker. Valid only for gevent
    worker_connections = 10


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

    ; Sets the number of process workers. More workers means more concurrent connections
    ; RhodeCode can handle at the same time. Each additional worker also it increases
    ; memory usage as each has it's own set of caches.
    ; Recommended value is (2 * NUMBER_OF_CPUS + 1), eg 2CPU = 5 workers, but no more
    ; than 8-10 unless for really big deployments .e.g 700-1000 users.
    ; `instance_id = *` must be set in the [app:main] section below (which is the default)
    ; when using more than 1 worker.
    workers = 8

    ; Type of worker class, one of `sync`, `gevent`
    ; Use `sync` for vcsserver
    worker_class = sync


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

    ; Type of worker class, one of `sync`, `gevent`
    ; Use `gevent` for rhodecode
    worker_class = gevent

    ; The maximum number of simultaneous clients per worker. Valid only for gevent
    worker_connections = 30


.. note::

    `Gevent` is currently only supported for Enterprise/Community instances.
    VCSServer doesn't support gevent.



.. _Gunicorn: http://gunicorn.org/
