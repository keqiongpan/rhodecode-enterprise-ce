.. _apache-conf-eg:

Apache Configuration Example
----------------------------

Use the following example to configure Apache as a your web server.
Below config if for an Apache Reverse Proxy configuration.

.. note::

   Apache requires the following modules to be enabled. Below is an example
   how to enable them on Ubuntu Server


.. code-block:: bash

    $ sudo a2enmod proxy
    $ sudo a2enmod proxy_http
    $ sudo a2enmod proxy_balancer
    $ sudo a2enmod headers
    $ sudo a2enmod ssl
    $ sudo a2enmod rewrite

    # requires Apache 2.4+, required to handle websockets/channelstream
    $ sudo a2enmod proxy_wstunnel


.. code-block:: apache

    ## HTTP to HTTPS rewrite
    <VirtualHost *:80>
       ServerName rhodecode.myserver.com
       DocumentRoot /var/www/html
       Redirect permanent / https://rhodecode.myserver.com/
    </VirtualHost>

    ## MAIN SSL enabled server
    <VirtualHost *:443>

        ServerName rhodecode.myserver.com
        ServerAlias rhodecode.myserver.com

        ## serve static files by Apache, recommended for performance
        #Alias /_static /home/ubuntu/.rccontrol/community-1/static

        RequestHeader set X-Forwarded-Proto "https"

        ## channelstream websocket handling
        ProxyPass /_channelstream ws://localhost:9800
        ProxyPassReverse /_channelstream ws://localhost:9800

        <Proxy *>
          Order allow,deny
          Allow from all
        </Proxy>

        # Directive to properly generate url (clone url) for RhodeCode
        ProxyPreserveHost On

        # Url to running RhodeCode instance. This is shown as `- URL:` when
        # running rccontrol status.
        ProxyPass / http://127.0.0.1:10002/
        ProxyPassReverse / http://127.0.0.1:10002/

        # strict http prevents from https -> http downgrade
        Header always set Strict-Transport-Security "max-age=63072000; includeSubdomains; preload"

        # Set x-frame options
        Header always append X-Frame-Options SAMEORIGIN

        # To enable https use line below
        # SetEnvIf X-Url-Scheme https HTTPS=1

        # SSL setup
        SSLEngine On
        SSLCertificateFile /etc/apache2/ssl/rhodecode.myserver.pem
        SSLCertificateKeyFile /etc/apache2/ssl/rhodecode.myserver.key

        SSLProtocol             all -SSLv2 -SSLv3
        SSLCipherSuite          ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-AES256-GCM-SHA384:DHE-RSA-AES128-GCM-SHA256:DHE-DSS-AES128-GCM-SHA256:kEDH+AESGCM:ECDHE-RSA-AES128-SHA256:ECDHE-ECDSA-AES128-SHA256:ECDHE-RSA-AES128-SHA:ECDHE-ECDSA-AES128-SHA:ECDHE-RSA-AES256-SHA384:ECDHE-ECDSA-AES256-SHA384:ECDHE-RSA-AES256-SHA:ECDHE-ECDSA-AES256-SHA:DHE-RSA-AES128-SHA256:DHE-RSA-AES128-SHA:DHE-DSS-AES128-SHA256:DHE-RSA-AES256-SHA256:DHE-DSS-AES256-SHA:DHE-RSA-AES256-SHA:AES128-GCM-SHA256:AES256-GCM-SHA384:AES128-SHA256:AES256-SHA256:AES128-SHA:AES256-SHA:AES:CAMELLIA:DES-CBC3-SHA:!aNULL:!eNULL:!EXPORT:!DES:!RC4:!MD5:!PSK:!aECDH:!EDH-DSS-DES-CBC3-SHA:!EDH-RSA-DES-CBC3-SHA:!KRB5-DES-CBC3-SHA
        SSLHonorCipherOrder     on

        # Diffie-Hellman parameter for DHE ciphersuites, recommended 2048 bits
        #SSLOpenSSLConfCmd DHParameters "/etc/apache2/dhparam.pem"

    </VirtualHost>

