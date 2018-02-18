|RCE| 4.11.4 |RNS|
------------------

Release Date
^^^^^^^^^^^^

- 2018-02-18


New Features
^^^^^^^^^^^^



General
^^^^^^^



Security
^^^^^^^^



Performance
^^^^^^^^^^^



Fixes
^^^^^

- Ssh: fixed problems with svn ssh clones in certain configurations.
- Caches: use individual namespaces per user to prevent beaker caching problems in database backends.
  In some cases of large LDAP data we could generate mysql table errors
  with too big data. Now each user will use individual row in db cache
- Reviewers: fixed logic with wildcard (*) match for source/target branches.
  Reverting a regression when * didn't work as expected in branch matching.


Upgrade notes
^^^^^^^^^^^^^

- Unscheduled bugfix release fixing several reported issues.
