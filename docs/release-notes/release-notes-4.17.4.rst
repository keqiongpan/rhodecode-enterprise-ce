|RCE| 4.17.4 |RNS|
------------------

Release Date
^^^^^^^^^^^^

- 2019-10-28


New Features
^^^^^^^^^^^^



General
^^^^^^^

- Permissions: properly flush user cache permissions in more cases of permission changes.
  Some API methods and user-group additions didn't invalidate permission caches resulting in
  users not seeing the permission changes immediately.
- Pull requests: properly handle exceptions in state change logic, and improve logging on this.


Security
^^^^^^^^
- Security: fixed XSS in file editing.


Performance
^^^^^^^^^^^



Fixes
^^^^^

- Diffs: handle paths with quotes in diffs.
- Diffs: fixed outdated files in pull-requests re-using the filediff raw_id for anchor generation.
  This could make rendering diff crash in cases of only having outdated files in a diff.
- Diffs: handle very odd case of binary, corrupted diffs which crashed the diff parser.
- Svn: handle non-ascii message editing.


Upgrade notes
^^^^^^^^^^^^^

- Scheduled release addressing problems in 4.17.X releases.
