.. _scale-horizontal:

Scale Horizontally
------------------

|RCE| is built in a way it support horizontal scaling across multiple machines.
There are two main pre-requisites for that:

- Shared storage that each machine can access.
- Shared DB connection across machines.


Horizontal scaling means adding more machines or workers into your pool of
resources. Horizontally scaling |RCE| gives a huge performance increase,
especially under large traffic scenarios with a high number of requests. This
is very beneficial when |RCE| is serving many users simultaneously,
or if continuous integration servers are automatically pulling and pushing code.


If you scale across different machines, each |RCM| instance
needs to store its data on a shared disk, preferably together with your
|repos|. This data directory contains template caches, a full text search index,
and is used for task locking to ensure safety across multiple instances.
To do this, set the following properties in the :file:`rhodecode.ini` file to
set the shared location across all |RCM| instances.

.. code-block:: ini

    cache_dir = /shared/path/caches                 # set to shared location
    search.location = /shared/path/search_index     # set to shared location

    ####################################
    ###         BEAKER CACHE        ####
    ####################################
    beaker.cache.data_dir = /shared/path/data       # set to shared location
    beaker.cache.lock_dir = /shared/path/lock       # set to shared location


.. note::

    If you use custom caches such as `beaker.cache.auth_plugins.` it's recommended
    to set it to the memcached/redis or database backend so it can be shared
    across machines.


It is recommended to create another dedicated |RCE| instance to handle
traffic from build farms or continuous integration servers.

.. note::

   You should configure your load balancing accordingly. We recommend writing
   load balancing rules that will separate regular user traffic from
   automated process traffic like continuous servers or build bots.

.. note::

     If Celery is used on each instance then you should run separate Celery
     instances, but the message broker should be the same for all of them.
