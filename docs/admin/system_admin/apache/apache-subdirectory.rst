.. _apache-sub-ref:

Apache URL Prefix Configuration
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Use the following example to configure Apache to use a URL prefix.

.. code-block:: apache

    # Change someprefix into your chosen prefix
    <Location /someprefix >
      ProxyPreserveHost On
      ProxyPass "http://127.0.0.1:5000/"
      ProxyPassReverse "http://127.0.0.1:5000/"
      Header set X-Url-Scheme https env=HTTPS
    </Location>

In addition to the regular Apache setup you will need to add the following
lines into the ``rhodecode.ini`` file.

* Above ``[app:main]`` section of the ``rhodecode.ini`` file add the
  following section if it doesn't exist yet.

.. code-block:: ini

    [filter:proxy-prefix]
    use = egg:PasteDeploy#prefix
    prefix = /<someprefix> # Change <someprefix> into your chosen prefix

* In the the ``[app:main]`` section of your ``rhodecode.ini`` file add the
  following line.

.. code-block:: ini

    filter-with = proxy-prefix
