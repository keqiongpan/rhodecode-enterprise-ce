
.. _config-celery:

Configure Celery
----------------

To improve |RCM| performance you should configure and enabled Celery_ as it makes
asynchronous tasks work efficiently. Most important it allows sending notification
emails, create repository forks, and import repositories in async way.

If you decide to use Celery you also need a working message queue.
The recommended message broker is rabbitmq_.


In order to have install and configure Celery, follow these steps:

1. Install RabbitMQ, see the documentation on the Celery website for
   `rabbitmq installation`_.

2. Configure Celery in the
   :file:`home/{user}/.rccontrol/{instance-id}/rhodecode.ini` file.
   Set the following minimal settings, that are set during rabbitmq_ installation::

        broker.host =
        broker.vhost =
        broker.user =
        broker.password =

   Full configuration example is below:

   .. code-block:: ini

        # Set this section of the ini file to match your Celery installation
        ####################################
        ###        CELERY CONFIG        ####
        ####################################
        ## Set to true
        use_celery = true
        broker.host = localhost
        broker.vhost = rabbitmqvhost
        broker.port = 5672
        broker.user = rabbitmq
        broker.password = secret

        celery.imports = rhodecode.lib.celerylib.tasks

        celery.result.backend = amqp
        celery.result.dburi = amqp://
        celery.result.serialier = json

        #celery.send.task.error.emails = true
        #celery.amqp.task.result.expires = 18000

        celeryd.concurrency = 2
        #celeryd.log.file = celeryd.log
        celeryd.log.level = debug
        celeryd.max.tasks.per.child = 1

        ## tasks will never be sent to the queue, but executed locally instead.
        celery.always.eager = false


3. Enable celery, and install `celeryd` process script using the `enable-module`::

    rccontrol enable-module celery {instance-id}


.. _python: http://www.python.org/
.. _mercurial: http://mercurial.selenic.com/
.. _celery: http://celeryproject.org/
.. _rabbitmq: http://www.rabbitmq.com/
.. _rabbitmq installation: http://docs.celeryproject.org/en/latest/getting-started/brokers/rabbitmq.html
.. _Celery installation: http://docs.celeryproject.org/en/latest/getting-started/introduction.html#bundles
