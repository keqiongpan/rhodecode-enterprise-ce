|RCE| 4.4.2 |RNS|
-----------------

Release Date
^^^^^^^^^^^^

- 2016-10-17


New Features
^^^^^^^^^^^^



General
^^^^^^^

- Packaging: pinned against rhodecode-tools 0.10.1


Security
^^^^^^^^

- Integrations: fix 500 error on integrations page when delegated admin
  tried to access integration page after adding some integrations.
  Permission checks were to strict for delegated admins.


Performance
^^^^^^^^^^^



Fixes
^^^^^

- Vcsserver: make sure we correctly ping against bundled HG/GIT/SVN binaries.
  This should fix a problem where system binaries could be used accidentally
  by the RhodeCode.
- LDAP: fixed email extraction issues. Empty email addresses from LDAP server
  will no longer take precedence over those stored inside RhodeCode database.
