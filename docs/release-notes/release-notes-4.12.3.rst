|RCE| 4.12.3 |RNS|
------------------

Release Date
^^^^^^^^^^^^

- 2018-06-18


New Features
^^^^^^^^^^^^



General
^^^^^^^

- Git: set GIT_DISCOVERY_ACROSS_FILESYSTEM flag for better compatibility,
  and error tracking on mounted drives.


Security
^^^^^^^^

- Git: Upgraded GIT version to 2.16.4 to address security problems
  in earlier versions.


Performance
^^^^^^^^^^^



Fixes
^^^^^

- Caches: fix beaker sqlalchemy options propagation. This should fix some of the
  MySQL problems ("MySQL has gone away") reported with db cache backend.
- Shadow repos: use safer way to delete shadow repositories. Use the same
  mechanism as deleting repositories for shadow repos too. This tries to
  address problems on failed removal of shadow repositories that cause
  later problems.
- Pull requests: solve an issue with long database transaction row locking for
  large pull requests. Mysql backend row locking caused access problem to the
  server during time a large PR was beeing created. This is now solved by
  smarter DB transaction management.
- SVN: Fixed misleading errors when SSL was force enabled byt users used
  plain HTTP. Now we report proper errors instead of missing header error
  caused by a bug.


Upgrade notes
^^^^^^^^^^^^^

- Scheduled release addressing reported GIT client security problem,
  and some reported bugs.

