|RCE| 4.12.1 |RNS|
------------------

Release Date
^^^^^^^^^^^^

- 2018-05-15


New Features
^^^^^^^^^^^^



General
^^^^^^^

- SVN: execute web-based hooks for SVN so integration framework work also via
  web based editor.
- ReCaptcha: adjust for v2 that is the only left one supported since 1st of May.
- JIRA integration: add support for proxy server connection to JIRA server.


Security
^^^^^^^^



Performance
^^^^^^^^^^^



Fixes
^^^^^

- SVN: make hooks safer and fully backward compatible. In certain old setups
  new integration for SVN could make problems. We use a safer hooks now that
  shouldn't break usage of older SVN and still provide required functionality
  for integration framework
- LDAP: use connection ping only in case of single server.
- Repository feed: fix path-based permissions condition on caching element.


Upgrade notes
^^^^^^^^^^^^^

- Scheduled release addressing found problems reported by users.
