.. _sec-sophos-umc:

Securing Your Server via Sophos UTM 9
-------------------------------------



Below is an example configuration for Sophos UTM 9 Webserver Protection::

    Sophos UTM 9 Webserver Protection
    Web Application Firewall based on apache2 modesecurity2
    --------------------------------------------------
    1. Firewall Profiles -> Firewall Profile
    --------------------------------------------------
    Name: RhodeCode (can be anything)
    Mode: Reject
    Hardening & Signing:
        [ ] Static URL hardeninig
        [ ] Form hardening
        [x] Cookie Signing
    Filtering:
        [x] Block clients with bad reputation
        [x] Common Threats Filter
        [ ] Rigid Filtering
            Skip Filter Rules:
                960015
                950120
                981173
                970901
                960010
                960032
                960035
                958291
                970903
                970003
    Common Threat Filter Categories:
        [x] Protocol violations
        [x] Protocol anomalies
        [x] Request limit
        [x] HTTP policy
        [x] Bad robots
        [x] Generic attacks
        [x] SQL injection attacks
        [x] XSS attacks
        [x] Tight security
        [x] Trojans
        [x] Outbound
    Scanning:
        [ ] Enable antivirus scanning
        [ ] Block uploads by MIME type
    --------------------------------------------------
    2. Web Application Firewall -> Real Webservers
    --------------------------------------------------
    Name: RhodeCode (can be anything)
    Host: Your RhodeCode-Server (UTM object)
    Type: Encrypted (HTTPS)
    Port: 443
    --------------------------------------------------
    3. Web Application Firewall -> Virual Webservers
    --------------------------------------------------
    Name: RhodeCode (can be anything)
    Interface: WAN (your WAN interface)
    Type: Encrypted (HTTPS) & redirect
    Certificate: Wildcard or matching domain certificate
        Domains (in case of Wildcard certificate):
            rhodecode.yourcompany.com (match your DNS configuration)
            gist.yourcompany.com (match your DNS & RhodeCode configuration)
    Real Webservers for path '/':
        [x] RhodeCode (created in step 2)
    Firewall: RhodeCode (created in step 1)
    --------------------------------------------------
    4. Firewall Profiles -> Exceptions
    --------------------------------------------------
    Name: RhodeCode exceptions (can be anything)
    Skip these checks:
        [ ] Cookie signing
        [ ] Static URL Hardening
        [ ] Form hardening
        [x] Antivirus scanning
        [x] True file type control
        [ ] Block clients with bad reputation
    Skip these categories:
        [ ] Protocol violations
        [x] Protocol anomalies
        [x] Request limits
        [ ] HTTP policy
        [ ] Bad robots
        [ ] Generic attacks
        [ ] SQL injection attacks
        [ ] XSS attacks
        [ ] Tight security
        [ ] Trojans
        [x] Outbound
    Virtual Webservers:
        [x] RhodeCode (created in step 3)
    For All Requests:
        Web requests matching this pattern:
            /_channelstream/ws
            /Repository1/*
            /Repository2/*
            /Repository3/*