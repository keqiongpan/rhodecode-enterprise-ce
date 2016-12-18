|RCE| 4.5.2 |RNS|
-----------------

Release Date
^^^^^^^^^^^^

- 2016-12-19


New Features
^^^^^^^^^^^^



General
^^^^^^^

- Github authentication: no longer require repository permissions when
  connecting RhodeCode account with Github login.
- Api: added new function get_repo_refs. This was accidentally exposed in our
  documentation as valid function, but wasn't implemented. This function is now
  backported from next major release due the documentation issues.


Security
^^^^^^^^



Performance
^^^^^^^^^^^



Fixes
^^^^^

- Api: Fixed a regression in API validation on create_* functions.
  Before this fix it always converted given data to lowercase.
- System info: fixed reporting of free inodes as taken.


Upgrade notes
^^^^^^^^^^^^^


