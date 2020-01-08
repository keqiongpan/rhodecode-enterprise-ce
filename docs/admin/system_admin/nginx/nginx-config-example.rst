Nginx Configuration Example
---------------------------

Use the following example to configure Nginx as a your web server.


.. code-block:: nginx

    ## Rate limiter for certain pages to prevent brute force attacks
    limit_req_zone  $binary_remote_addr  zone=req_limit:10m   rate=1r/s;

    ## cache zone
    proxy_cache_path /etc/nginx/nginx_cache levels=1:2 use_temp_path=off keys_zone=cache_zone:10m inactive=720h max_size=10g;

    ## Custom log format
    log_format log_custom '$remote_addr - $remote_user [$time_local] '
                          '"$request" $status $body_bytes_sent '
                          '"$http_referer" "$http_user_agent" '
                          '$request_time $upstream_response_time $pipe';

    ## Define one or more upstreams (local RhodeCode instance) to connect to
    upstream rc {
        # Url to running RhodeCode instance.
        # This is shown as `- URL: <host>` in output from rccontrol status.
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

        ## Strict http prevents from https -> http downgrade
        add_header Strict-Transport-Security "max-age=31536000; includeSubdomains;";

        ## Diffie-Hellman parameter for DHE ciphersuites, recommended 2048 bits
        #ssl_dhparam /etc/nginx/ssl/dhparam.pem;

        rewrite ^/(.+)$ https://rhodecode.myserver.com/_admin/gists/$1;
        rewrite (.*)    https://rhodecode.myserver.com/_admin/gists;
    }


    ## MAIN SSL enabled server
    server {
        listen       443 ssl http2;
        server_name  rhodecode.myserver.com;

        access_log   /var/log/nginx/rhodecode.access.log log_custom;
        error_log    /var/log/nginx/rhodecode.error.log;

        ssl_certificate     rhodecode.myserver.com.crt;
        ssl_certificate_key rhodecode.myserver.com.key;

        # enable session resumption to improve https performance
        # http://vincent.bernat.im/en/blog/2011-ssl-session-reuse-rfc5077.html
        ssl_session_cache shared:SSL:50m;
        ssl_session_timeout 5m;

        ## Diffie-Hellman parameter for DHE ciphersuites, recommended 2048 bits
        #ssl_dhparam /etc/nginx/ssl/dhparam.pem;

        # enables server-side protection from BEAST attacks
        # http://blog.ivanristic.com/2013/09/is-beast-still-a-threat.html
        ssl_prefer_server_ciphers on;

        # disable SSLv3(enabled by default since nginx 0.8.19) since it's less secure then TLS http://en.wikipedia.org/wiki/Secure_Sockets_Layer#SSL_3.0
        ssl_protocols TLSv1 TLSv1.1 TLSv1.2;

        # ciphers chosen for forward secrecy and compatibility
        # http://blog.ivanristic.com/2013/08/configuring-apache-nginx-and-openssl-for-forward-secrecy.html
        ssl_ciphers "ECDHE-RSA-AES256-GCM-SHA384:ECDHE-RSA-AES128-GCM-SHA256:DHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-SHA384:ECDHE-RSA-AES128-SHA256:ECDHE-RSA-AES256-SHA:ECDHE-RSA-AES128-SHA:DHE-RSA-AES256-SHA256:DHE-RSA-AES128-SHA256:DHE-RSA-AES256-SHA:DHE-RSA-AES128-SHA:ECDHE-RSA-DES-CBC3-SHA:EDH-RSA-DES-CBC3-SHA:AES256-GCM-SHA384:AES128-GCM-SHA256:AES256-SHA256:AES128-SHA256:AES256-SHA:AES128-SHA:DES-CBC3-SHA:HIGH:!aNULL:!eNULL:!EXPORT:!DES:!MD5:!PSK:!RC4";

        client_body_buffer_size     128k;
        # maximum number and size of buffers for large headers to read from client request
        large_client_header_buffers 16 256k;

        ## uncomment to serve static files by Nginx, recommended for performance
        # location /_static/rhodecode {
        #    gzip on;
        #    gzip_min_length  500;
        #    gzip_proxied     any;
        #    gzip_comp_level 4;
        #    gzip_types  text/css text/javascript text/xml text/plain text/x-component application/javascript application/json application/xml application/rss+xml font/truetype font/opentype application/vnd.ms-fontobject image/svg+xml;
        #    gzip_vary on;
        #    gzip_disable     "msie6";
        #    expires 60d;
        #    alias /path/to/.rccontrol/community-1/static;
        #    alias /path/to/.rccontrol/enterprise-1/static;
        # }

        ## channelstream location handler, if channelstream live chat and notifications
        ## are enable this will proxy the requests to channelstream websocket server
        location /_channelstream {
            rewrite /_channelstream/(.*) /$1 break;
            gzip                         off;
            tcp_nodelay                  off;

            proxy_connect_timeout        10;
            proxy_send_timeout           10m;
            proxy_read_timeout           10m;

            proxy_set_header             Host $host;
            proxy_set_header             X-Real-IP $remote_addr;
            proxy_set_header             X-Url-Scheme $scheme;
            proxy_set_header             X-Forwarded-Proto $scheme;
            proxy_set_header             X-Forwarded-For $proxy_add_x_forwarded_for;

            proxy_http_version           1.1;
            proxy_set_header Upgrade     $http_upgrade;
            proxy_set_header Connection  "upgrade";

            proxy_pass                  http://127.0.0.1:9800;
        }

        ## rate limit this endpoint to prevent login page brute-force attacks
        location /_admin/login {
            limit_req  zone=req_limit  burst=10  nodelay;
            try_files $uri @rhodecode_http;
        }

        ## Special Cache for file store, make sure you enable this intentionally as
        ## it could bypass upload files permissions
        # location /_file_store/download {
        #
        #    proxy_cache cache_zone;
        #    # ignore Set-Cookie
        #    proxy_ignore_headers Set-Cookie;
        #    proxy_ignore_headers Cookie;
        #
        #    proxy_cache_key $host$uri$is_args$args;
        #    proxy_cache_methods GET;
        #
        #    proxy_cache_bypass  $http_cache_control;
        #    proxy_cache_valid 200 302 720h;
        #
        #    proxy_cache_use_stale error timeout http_500 http_502 http_503 http_504;
        #
        #    # returns cache status in headers
        #    add_header X-Proxy-Cache $upstream_cache_status;
        #    add_header Cache-Control "public";
        #
        #    proxy_cache_lock on;
        #    proxy_cache_lock_age 5m;
        #
        #    proxy_pass  http://rc;
        #
        # }

        location / {
            try_files $uri @rhodecode_http;
        }

        location @rhodecode_http {
            # example of proxy.conf can be found in our docs.
            include     /etc/nginx/proxy.conf;
            proxy_pass  http://rc;
        }

        ## Custom 502 error page.
        ## Will be displayed while RhodeCode server is turned off
        error_page 502 /502.html;
        location = /502.html {
           #root  /path/to/.rccontrol/community-1/static;
           root  /path/to/.rccontrol/enterprise-1/static;
        }
    }