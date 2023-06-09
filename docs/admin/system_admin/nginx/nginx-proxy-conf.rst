.. _nginx-proxy-conf:

Nginx Proxy Config
------------------


Set the following properties in your ``/etc/nginx/proxy.conf`` so it does not
timeout during large pushes.

.. code-block:: nginx

    proxy_redirect              off;
    proxy_set_header            Host $http_host;

    ## If you use HTTPS make sure you disable gzip compression
    ## to be safe against BREACH attack.
    gzip                        off;

    # Don't buffer requests in NGINX stream them using chunked-encoding
    proxy_buffering             off;

    ## This is also required for later GIT to use streaming.
    ## Works only for Nginx 1.7.11 and newer
    proxy_request_buffering off;
    proxy_http_version 1.1;

    ## Set this to a larger number if you experience timeouts
    ## or 413 Request Entity Too Large, 10GB is enough for most cases
    client_max_body_size        10240m;

    ## needed for container auth
    # proxy_set_header          REMOTE_USER $remote_user;
    # proxy_set_header          X-Forwarded-User $remote_user;

    proxy_set_header            X-Url-Scheme $scheme;
    proxy_set_header            X-Host $http_host;
    proxy_set_header            X-Real-IP $remote_addr;
    proxy_set_header            X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header            X-Forwarded-Proto $proto;
    proxy_set_header            X-Url-Scheme $scheme;
    proxy_set_header            Proxy-host $proxy_host;

    proxy_connect_timeout       7200;
    proxy_send_timeout          7200;
    proxy_read_timeout          7200;
    proxy_buffers               8 32k;

    add_header X-Frame-Options SAMEORIGIN;
    add_header Strict-Transport-Security "max-age=31536000; includeSubdomains;";
