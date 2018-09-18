.. _scale-horizontal-cluster:


Scale Horizontally / RhodeCode Cluster
--------------------------------------

|RCE| is built in a way it support horizontal scaling across multiple machines.
There are three main pre-requisites for that:

- Shared storage that each machine can access. Using NFS or other shared storage system.
- Shared DB connection across machines. Using `MySQL`/`PostgreSQL` that each node can access.
- |RCE| user sessions and caches need to use a shared storage (e.g `Redis`_/`Memcached`)


Horizontal scaling means adding more machines or workers into your pool of
resources. Horizontally scaling |RCE| gives a huge performance increase,
especially under large traffic scenarios with a high number of requests.
This is very beneficial when |RCE| is serving many users simultaneously,
or if continuous integration servers are automatically pulling and pushing code.
It also adds High-Availability to your running system.


Cluster Overview
^^^^^^^^^^^^^^^^

Below we'll present a configuration example that will use two separate nodes to serve
|RCE| in a load-balanced environment. The 3rd node will act as a shared storage/cache
and handle load-balancing. In addition 3rd node will be used as shared database instance.

This setup can be used both in Docker based configuration or with individual
physical/virtual machines. Using the 3rd node for Storage/Redis/PostgreSQL/Nginx is
optional. All those components can be installed on one of the two nodes used for |RCE|.
We'll use following naming for our nodes:

 - `rc-node-1` (NFS, DB, Cache node)
 - `rc-node-2` (Worker node1)
 - `rc-node-3` (Worker node2)

Our shares NFS storage in the example is located on `/home/rcdev/storage` and
it's RW accessible on **each** node.

In this example we used certain recommended components, however many
of those can be replaced by other, in case your organization already uses them, for example:

- `MySQL`/`PostgreSQL`: Aren't replaceable and are the two only supported databases.
- `Nginx`_ on `rc-node-1` can be replaced by: `Hardware Load Balancer (F5)`, `Apache`_, `HA-Proxy` etc.
- `Nginx`_ on rc-node-2/3 acts as a reverse proxy and can be replaced by other HTTP server
  acting as reverse proxy such as `Apache`_.
- `Redis`_ on `rc-node-1` can be replaced by: `Memcached`


Here's an overview what components should be installed/setup on each server in our example:

- **rc-node-1**:

 - main storage acting as NFS host.
 - `nginx` acting as a load-balancer.
 - `postgresql-server` used for database and sessions.
 - `redis-server` used for storing shared caches.
 - optionally `rabbitmq-server` for `Celery` if used.
 - optionally if `Celery` is used Enterprise/Community instance + VCSServer.
 - optionally mailserver that can be shared by other instances.
 - optionally channelstream server to handle live communication for all instances.


- **rc-node-2/3**:

 - `nginx` acting as a reverse proxy to handle requests to |RCE|.
 - 1x RhodeCode Enterprise/Community instance.
 - 1x VCSServer instance.
 - optionally for testing connection: postgresql-client, redis-client (redis-tools).


Before we start here are few assumptions that should be fulfilled:

- make sure each node can access each other.
- make sure `Redis`_/`MySQL`/`PostgreSQL`/`RabbitMQ`_ are running on `rc-node-1`
- make sure both `rc-node-2`/`3` can access NFS storage with RW access
- make sure rc-node-2/3 can access `Redis`_/`PostgreSQL`, `MySQL` database on `rc-node-1`.
- make sure `Redis`_/Database/`RabbitMQ`_ are password protected and accessible only from rc-node-2/3.



Setup rc-node-2/3
^^^^^^^^^^^^^^^^^

Initially before `rc-node-1` we'll configure both nodes 2 and 3 to operate as standalone
nodes with their own hostnames. Use a default installation settings, and use
the default local addresses (127.0.0.1) to configure VCSServer and Community/Enterprise instances.
All external connectivity will be handled by the reverse proxy (`Nginx`_ in our example).

This way we can ensure each individual host works,
accepts connections, or do some operations explicitly on chosen node.

In addition this would allow use to explicitly direct certain traffic to a node, e.g
CI server will only call directly `rc-node-3`. This should be done similar to normal
installation so check out `Nginx`_/`Apache`_ configuration example to configure each host.
Each one should already connect to shared database during installation.


1) Assuming our final url will be http://rc-node-1, Configure `instances_id`, `app.base_url`

a) On **rc-node-2** find the following settings and edit :file:`/home/{user}/.rccontrol/{instance-id}/rhodecode.ini`

.. code-block:: ini

    ## required format is: *NAME-
    instance_id = *rc-node-2-
    app.base_url = http://rc-node-1


b) On **rc-node-3** find the following settings and edit :file:`/home/{user}/.rccontrol/{instance-id}/rhodecode.ini`

.. code-block:: ini

    ## required format is: *NAME-
    instance_id = *rc-node-3-
    app.base_url = http://rc-node-1



2) Configure `User Session` to use a shared database. Example config that should be
   changed on both **rc-node-2** and **rc-node-3** .
   Edit :file:`/home/{user}/.rccontrol/{instance-id}/rhodecode.ini`

.. code-block:: ini

    ####################################
    ###       BEAKER SESSION        ####
    ####################################

    ## Disable the default `file` sessions
    #beaker.session.type = file
    #beaker.session.data_dir = %(here)s/data/sessions

    ## use shared db based session, fast, and allows easy management over logged in users
    beaker.session.type = ext:database
    beaker.session.table_name = db_session
    # use our rc-node-1 here
    beaker.session.sa.url = postgresql://postgres:qweqwe@rc-node-1/rhodecode
    beaker.session.sa.pool_recycle = 3600
    beaker.session.sa.echo = false

In addition make sure both instances use the same `session.secret` so users have
persistent sessions across nodes. Please generate other one then in this example.

.. code-block:: ini

    # use an unique generated long string
    beaker.session.secret = 70e116cae2274656ba7265fd860aebbd

3) Configure stored cached/archive cache to our shared NFS `rc-node-1`

.. code-block:: ini

    # note the `_` prefix that allows using a directory without
    # remap and rescan checking for vcs inside it.
    cache_dir = /home/rcdev/storage/_cache_dir/data
    # note archive cache dir is disabled by default, however if you enable
    # it also needs to be shared
    #archive_cache_dir = /home/rcdev/storage/_tarball_cache_dir


4) Use shared exception store. Example config that should be
   changed on both **rc-node-2** and **rc-node-3**, and also for VCSServer.
   Edit :file:`/home/{user}/.rccontrol/{instance-id}/rhodecode.ini` and
   :file:`/home/{user}/.rccontrol/{vcsserver-instance-id}/vcsserver.ini`
   and add/change following setting.

.. code-block:: ini

    exception_tracker.store_path = /home/rcdev/storage/_exception_store_data


5) Change cache backends to use `Redis`_ based caches. Below full example config
   that replaces default file-based cache to shared `Redis`_ with Distributed Lock.


.. code-block:: ini

    #####################################
    ###         DOGPILE CACHE        ####
    #####################################

    ## `cache_perms` cache settings for permission tree, auth TTL.
    #rc_cache.cache_perms.backend = dogpile.cache.rc.file_namespace
    #rc_cache.cache_perms.expiration_time = 300

    ## alternative `cache_perms` redis backend with distributed lock
    rc_cache.cache_perms.backend = dogpile.cache.rc.redis
    rc_cache.cache_perms.expiration_time = 300
    ## redis_expiration_time needs to be greater then expiration_time
    rc_cache.cache_perms.arguments.redis_expiration_time = 7200
    rc_cache.cache_perms.arguments.socket_timeout = 30
    rc_cache.cache_perms.arguments.host = rc-node-1
    rc_cache.cache_perms.arguments.password = qweqwe
    rc_cache.cache_perms.arguments.port = 6379
    rc_cache.cache_perms.arguments.db = 0
    rc_cache.cache_perms.arguments.distributed_lock = true

    ## `cache_repo` cache settings for FileTree, Readme, RSS FEEDS
    #rc_cache.cache_repo.backend = dogpile.cache.rc.file_namespace
    #rc_cache.cache_repo.expiration_time = 2592000

    ## alternative `cache_repo` redis backend with distributed lock
    rc_cache.cache_repo.backend = dogpile.cache.rc.redis
    rc_cache.cache_repo.expiration_time = 2592000
    ## redis_expiration_time needs to be greater then expiration_time
    rc_cache.cache_repo.arguments.redis_expiration_time = 2678400
    rc_cache.cache_repo.arguments.socket_timeout = 30
    rc_cache.cache_repo.arguments.host = rc-node-1
    rc_cache.cache_repo.arguments.password = qweqwe
    rc_cache.cache_repo.arguments.port = 6379
    rc_cache.cache_repo.arguments.db = 1
    rc_cache.cache_repo.arguments.distributed_lock = true

    ## cache settings for SQL queries, this needs to use memory type backend
    rc_cache.sql_cache_short.backend = dogpile.cache.rc.memory_lru
    rc_cache.sql_cache_short.expiration_time = 30

    ## `cache_repo_longterm` cache for repo object instances, this needs to use memory
    ## type backend as the objects kept are not pickle serializable
    rc_cache.cache_repo_longterm.backend = dogpile.cache.rc.memory_lru
    ## by default we use 96H, this is using invalidation on push anyway
    rc_cache.cache_repo_longterm.expiration_time = 345600
    ## max items in LRU cache, reduce this number to save memory, and expire last used
    ## cached objects
    rc_cache.cache_repo_longterm.max_size = 10000


6) Configure `Nginx`_ as reverse proxy on `rc-node-2/3`:
   Minimal `Nginx`_ config used:


.. code-block:: nginx

    ## rate limiter for certain pages to prevent brute force attacks
    limit_req_zone  $binary_remote_addr  zone=req_limit:10m   rate=1r/s;

    ## custom log format
    log_format log_custom '$remote_addr - $remote_user [$time_local] '
                          '"$request" $status $body_bytes_sent '
                          '"$http_referer" "$http_user_agent" '
                          '$request_time $upstream_response_time $pipe';

    server {
        listen          80;
        server_name     rc-node-2;
        #server_name     rc-node-3;

        access_log   /var/log/nginx/rhodecode.access.log log_custom;
        error_log    /var/log/nginx/rhodecode.error.log;

        # example of proxy.conf can be found in our docs.
        include     /etc/nginx/proxy.conf;

        ## serve static files by Nginx, recommended for performance
        location /_static/rhodecode {
            gzip on;
            gzip_min_length  500;
            gzip_proxied     any;
            gzip_comp_level 4;
            gzip_types  text/css text/javascript text/xml text/plain text/x-component application/javascript application/json application/xml application/rss+xml font/truetype font/opentype application/vnd.ms-fontobject image/svg+xml;
            gzip_vary on;
            gzip_disable     "msie6";
            #alias /home/rcdev/.rccontrol/community-1/static;
            alias /home/rcdev/.rccontrol/enterprise-1/static;
        }


        location /_admin/login {
            limit_req  zone=req_limit  burst=10  nodelay;
            try_files $uri @rhode;
        }

        location / {
            try_files $uri @rhode;
        }

        location @rhode {
            # Url to running RhodeCode instance.
            # This is shown as `- URL: <host>` in output from rccontrol status.
            proxy_pass      http://127.0.0.1:10020;
        }

        ## custom 502 error page. Will be displayed while RhodeCode server
        ## is turned off
        error_page 502 /502.html;
        location = /502.html {
           #root  /home/rcdev/.rccontrol/community-1/static;
           root  /home/rcdev/.rccontrol/enterprise-1/static;
        }
    }


7) Optional: Full text search, in case you use `Whoosh` full text search we also need a
   shared storage for the index. In our example our NFS is mounted at `/home/rcdev/storage`
   which represents out storage so we can use the following:

.. code-block:: ini

    # note the `_` prefix that allows using a directory without
    # remap and rescan checking for vcs inside it.
    search.location = /home/rcdev/storage/_index_data/index


.. note::

    If you use ElasticSearch it's by default shared, and simply running ES node is
    by default cluster compatible.


8) Optional: If you intend to use mailing all instances need to use either a shared
   mailing node, or each will use individual local mail agent. Simply put node-1/2/3
   needs to use same mailing configuration.



Setup rc-node-1
^^^^^^^^^^^^^^^


Configure `Nginx`_ as Load Balancer to rc-node-2/3.
Minimal `Nginx`_ example below:

.. code-block:: nginx

    ## define rc-cluster which contains a pool of our instances to connect to
    upstream rc-cluster {
        # rc-node-2/3 are stored in /etc/hosts with correct IP addresses
        server rc-node-2:80;
        server rc-node-3:80;
    }

    server {
        listen          80;
        server_name     rc-node-1;

        location / {
            proxy_pass http://rc-cluster;
        }
    }


.. note::

   You should configure your load balancing accordingly. We recommend writing
   load balancing rules that will separate regular user traffic from
   automated process traffic like continuous servers or build bots. Sticky sessions
   are not required.


Show which instance handles a request
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

You can easily check if load-balancing is working as expected. Visit our main node
`rc-node-1` URL which at that point should already handle incoming requests and balance
it across node-2/3.

Add a special GET param `?showrcid=1` to show current instance handling your request.

For example: visiting url `http://rc-node-1/?showrcid=1` will show, in the bottom
of the screen` cluster instance info.
e.g: `RhodeCode instance id: rc-node-3-rc-node-3-3246`
which is generated from::

    <NODE_HOSTNAME>-<INSTANCE_ID>-<WORKER_PID>


Using Celery with cluster
^^^^^^^^^^^^^^^^^^^^^^^^^


If `Celery` is used we recommend setting also an instance of Enterprise/Community+VCSserver
on the node that is running `RabbitMQ`_. Those instances will be used to executed async
tasks on the `rc-node-1`. This is the most efficient setup. `Celery` usually
handles tasks such as sending emails, forking repositories, importing
repositories from external location etc. Using workers on instance that has
the direct access to disks used by NFS as well as email server gives noticeable
performance boost. Running local workers to the NFS storage results in faster
execution of forking large repositories or sending lots of emails.

Those instances need to be configured in the same way as for other nodes.
The instance in rc-node-1 can be added to the cluser, but we don't recommend doing it.
For best results let it be isolated to only executing `Celery` tasks in the cluster setup.


.. _Gunicorn: http://gunicorn.org/
.. _Whoosh: https://pypi.python.org/pypi/Whoosh/
.. _Elasticsearch: https://www.elastic.co/..
.. _RabbitMQ: http://www.rabbitmq.com/
.. _Nginx: http://nginx.io
.. _Apache: http://nginx.io
.. _Redis: http://redis.io

