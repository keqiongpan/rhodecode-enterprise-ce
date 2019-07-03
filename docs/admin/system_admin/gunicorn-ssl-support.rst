.. _gunicorn-ssl-support:


Gunicorn SSL support
--------------------


:term:`Gunicorn` wsgi server allows users to use HTTPS connection directly
without a need to use HTTP server like Nginx or Apache. To Configure
SSL support directly with :term:`Gunicorn` you need to simply add the key
and certificate paths to your configuration file.

1. Open the :file:`home/{user}/.rccontrol/{instance-id}/rhodecode.ini` file.
2. In the ``[server:main]`` section, add two new variables
   called `certfile` and `keyfile`.

.. code-block:: ini

    [server:main]
    host = 127.0.0.1
    port = 10002
    use = egg:gunicorn#main
    workers = 1
    threads = 1
    proc_name = RhodeCodeEnterprise
    worker_class = sync
    max_requests = 1000
    timeout = 3600
    # adding ssl support
    certfile = /home/ssl/my_server_com.pem
    keyfile = /home/ssl/my_server_com.key

4. Save your changes.
5. Restart your |RCE| instance, using the following command:

.. code-block:: bash

    $ rccontrol restart enterprise-1

After this is enabled you can *only* access your instances via https://
protocol. Check out more docs here `Gunicorn SSL Docs`_

.. note::

   This change only can be applied to |RCE|. VCSServer doesn't support SSL
   and should be only used with http protocol. Because only |RCE| is available
   externally all communication will still be over SSL even without VCSServer
   SSL enabled.

.. _Gunicorn SSL Docs: http://docs.gunicorn.org/en/stable/settings.html#ssl
