|RCE| 4.10.3 |RNS|
------------------

Release Date
^^^^^^^^^^^^

- 2017-11-11


New Features
^^^^^^^^^^^^



General
^^^^^^^

- ldap: increase timeouts and timelimits for operations


Security
^^^^^^^^

- security(low): fix self xss on repo downloads picker for svn case.


Performance
^^^^^^^^^^^



Fixes
^^^^^


- Pull requests: loosen permissions on creation of PR, fixing regression.
- LDAP: fix regression in ldap search filter implementation after upgrade to
  newer version of python-ldap library.


Upgrade notes
^^^^^^^^^^^^^

- Changes helpers to support regression in PR creation and increase
  LDAP server timeouts, no potential problems with upgrade.
