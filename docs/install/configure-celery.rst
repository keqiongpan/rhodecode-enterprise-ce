
.. _config-celery:

Configure Celery
----------------

Celery_ is an asynchronous task queue. It's a part of RhodeCode scheduler
functionality. Celery_ makes certain heavy tasks perform more efficiently.
Most important it allows sending notification emails, create repository forks,
and import repositories in async way. It is also used for bi-directional
repository sync in scheduler.

If you decide to use Celery you also need a working message queue.
There are two fully supported message brokers is rabbitmq_ and redis_ (recommended).

Since release 4.18.X we recommend using redis_ as a backend since it's generally
easier to work with, and results in simpler stack as redis is generally recommended
for caching purposes.


In order to install and configure Celery, follow these steps:

1. Install RabbitMQ or Redis for a message queue, see the documentation on the Celery website for
   `redis installation`_ or `rabbitmq installation`_


1a. If you choose RabbitMQ example configuration after installation would look like that::

   sudo rabbitmqctl add_user rcuser secret_password
   sudo rabbitmqctl add_vhost rhodevhost
   sudo rabbitmqctl set_user_tags rcuser rhodecode
   sudo rabbitmqctl set_permissions -p rhodevhost rcuser ".*" ".*" ".*"


2. Enable celery, and install `celery worker` process script using the `enable-module`::

    rccontrol enable-module celery {instance-id}

.. note::

   In case when using multiple instances in one or multiple servers it's highly
   recommended that celery is running only once, for all servers connected to
   the same database. Having multiple celery instances running without special
   reconfiguration could cause scheduler issues.


3. Configure Celery in the
   :file:`home/{user}/.rccontrol/{instance-id}/rhodecode.ini` file.
   Set the broker_url as minimal settings required to enable operation.
   If used our example data from pt 1a, here is how the broker url should look like::

        # for Redis
        celery.broker_url = redis://localhost:6379/8

        # for RabbitMQ
        celery.broker_url = amqp://rcuser:secret_password@localhost:5672/rhodevhost

   Full configuration example is below:

   .. code-block:: ini

        # Set this section of the ini file to match your Celery installation
        ####################################
        ###        CELERY CONFIG        ####
        ####################################

        use_celery = true
        celery.broker_url = redis://localhost:6379/8

        # maximum tasks to execute before worker restart
        celery.max_tasks_per_child = 100

        ## tasks will never be sent to the queue, but executed locally instead.
        celery.task_always_eager = false


.. _python: http://www.python.org/
.. _mercurial: http://mercurial.selenic.com/
.. _celery: http://celeryproject.org/
.. _redis: http://redis.io
.. _redis installation: https://redis.io/topics/quickstart
.. _rabbitmq: http://www.rabbitmq.com/
.. _rabbitmq installation: http://docs.celeryproject.org/en/latest/getting-started/brokers/rabbitmq.html
.. _rabbitmq website installation: http://www.rabbitmq.com/download.html
.. _Celery installation: http://docs.celeryproject.org/en/latest/getting-started/introduction.html#bundles
