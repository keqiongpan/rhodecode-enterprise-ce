Nginx Configuration Example
---------------------------

Use the following example to configure Nginx as a your web server.


.. code-block:: nginx
    ## rate limiter for certain pages to prevent brute force attacks
    limit_req_zone  $binary_remote_addr  zone=dl_limit:10m   rate=1r/s;

    ## custom log format
    log_format log_custom '$remote_addr - $remote_user [$time_local] '
                          '"$request" $status $body_bytes_sent '
                          '"$http_referer" "$http_user_agent" '
                          '$request_time $upstream_response_time $pipe';

    ## define upstream (local RhodeCode instance) to connect to
    upstream rc {
        # Url to running RhodeCode instance.
        # This is shown as `- URL:` in output from rccontrol status.
        server 127.0.0.1:10002;

        # add more instances for load balancing
        # server 127.0.0.1:10003;
        # server 127.0.0.1:10004;
    }

    ## HTTP to HTTPS rewrite
    server {
        listen          80;
        server_name     rhodecode.myserver.com;

        if ($http_host = rhodecode.myserver.com) {
            rewrite  (.*)  https://rhodecode.myserver.com$1 permanent;
        }
    }

    ## Optional gist alias server, for serving nicer GIST urls.
    server {
        listen          443;
        server_name     gist.myserver.com;
        access_log      /var/log/nginx/gist.access.log log_custom;
        error_log       /var/log/nginx/gist.error.log;

        ssl on;
        ssl_certificate     gist.rhodecode.myserver.com.crt;
        ssl_certificate_key gist.rhodecode.myserver.com.key;

        ssl_session_timeout 5m;

        ssl_protocols TLSv1 TLSv1.1 TLSv1.2;
        ssl_prefer_server_ciphers on;
        ssl_ciphers 'ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-AES256-GCM-SHA384:DHE-RSA-AES128-GCM-SHA256:DHE-DSS-AES128-GCM-SHA256:kEDH+AESGCM:ECDHE-RSA-AES128-SHA256:ECDHE-ECDSA-AES128-SHA256:ECDHE-RSA-AES128-SHA:ECDHE-ECDSA-AES128-SHA:ECDHE-RSA-AES256-SHA384:ECDHE-ECDSA-AES256-SHA384:ECDHE-RSA-AES256-SHA:ECDHE-ECDSA-AES256-SHA:DHE-RSA-AES128-SHA256:DHE-RSA-AES128-SHA:DHE-DSS-AES128-SHA256:DHE-RSA-AES256-SHA256:DHE-DSS-AES256-SHA:DHE-RSA-AES256-SHA:AES128-GCM-SHA256:AES256-GCM-SHA384:AES128-SHA256:AES256-SHA256:AES128-SHA:AES256-SHA:AES:CAMELLIA:DES-CBC3-SHA:!aNULL:!eNULL:!EXPORT:!DES:!RC4:!MD5:!PSK:!aECDH:!EDH-DSS-DES-CBC3-SHA:!EDH-RSA-DES-CBC3-SHA:!KRB5-DES-CBC3-SHA';

        # strict http prevents from https -> http downgrade
        add_header Strict-Transport-Security "max-age=31536000; includeSubdomains;";

        # Diffie-Hellman parameter for DHE ciphersuites, recommended 2048 bits
        #ssl_dhparam /etc/nginx/ssl/dhparam.pem;

        rewrite ^/(.+)$ https://rhodecode.myserver.com/_admin/gists/$1;
        rewrite (.*)    https://rhodecode.myserver.com/_admin/gists;
    }


    ## MAIN SSL enabled server
    server {
        listen       443 ssl;
        server_name  rhodecode.myserver.com;

        access_log   /var/log/nginx/rhodecode.access.log log_custom;
        error_log    /var/log/nginx/rhodecode.error.log;

        ssl on;
        ssl_certificate     rhodecode.myserver.com.crt;
        ssl_certificate_key rhodecode.myserver.com.key;

        ssl_session_timeout 5m;

        ssl_protocols TLSv1 TLSv1.1 TLSv1.2;
        ssl_prefer_server_ciphers on;
        ssl_ciphers 'ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-AES256-GCM-SHA384:DHE-RSA-AES128-GCM-SHA256:DHE-DSS-AES128-GCM-SHA256:kEDH+AESGCM:ECDHE-RSA-AES128-SHA256:ECDHE-ECDSA-AES128-SHA256:ECDHE-RSA-AES128-SHA:ECDHE-ECDSA-AES128-SHA:ECDHE-RSA-AES256-SHA384:ECDHE-ECDSA-AES256-SHA384:ECDHE-RSA-AES256-SHA:ECDHE-ECDSA-AES256-SHA:DHE-RSA-AES128-SHA256:DHE-RSA-AES128-SHA:DHE-DSS-AES128-SHA256:DHE-RSA-AES256-SHA256:DHE-DSS-AES256-SHA:DHE-RSA-AES256-SHA:AES128-GCM-SHA256:AES256-GCM-SHA384:AES128-SHA256:AES256-SHA256:AES128-SHA:AES256-SHA:AES:CAMELLIA:DES-CBC3-SHA:!aNULL:!eNULL:!EXPORT:!DES:!RC4:!MD5:!PSK:!aECDH:!EDH-DSS-DES-CBC3-SHA:!EDH-RSA-DES-CBC3-SHA:!KRB5-DES-CBC3-SHA';

        # Diffie-Hellman parameter for DHE ciphersuites, recommended 2048 bits
        #ssl_dhparam /etc/nginx/ssl/dhparam.pem;

        include     /etc/nginx/proxy.conf;

        ## serve static files by Nginx, recommended for performance
        # location /_static/rhodecode {
        #    alias /path/to/.rccontrol/enterprise-1/static;
        # }

        ## channelstream websocket handling
        location /_channelstream {
            rewrite /_channelstream/(.*) /$1 break;

            proxy_pass                  http://127.0.0.1:9800;

            proxy_connect_timeout        10;
            proxy_send_timeout           10m;
            proxy_read_timeout           10m;
            tcp_nodelay                  off;
            proxy_set_header             Host $host;
            proxy_set_header             X-Real-IP $remote_addr;
            proxy_set_header             X-Url-Scheme $scheme;
            proxy_set_header             X-Forwarded-Proto $scheme;
            proxy_set_header             X-Forwarded-For $proxy_add_x_forwarded_for;
            gzip                         off;
            proxy_http_version           1.1;
            proxy_set_header Upgrade     $http_upgrade;
            proxy_set_header Connection  "upgrade";
        }

        location /_admin/login {
            ## rate limit this endpoint
            limit_req  zone=dl_limit  burst=10  nodelay;
            try_files $uri @rhode;
        }

        location / {
            try_files $uri @rhode;
        }

        location @rhode {
            proxy_pass      http://rc;
        }

        ## custom 502 error page
        error_page 502 /502.html;
        location = /502.html {
           root  /path/to/.rccontrol/enterprise-1/static;
        }
    }