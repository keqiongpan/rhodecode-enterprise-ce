|RCE| 4.13.2 |RNS|
------------------

Release Date
^^^^^^^^^^^^

- 2018-09-18


New Features
^^^^^^^^^^^^

- audit-logs: add audit logs for branch permissions.


General
^^^^^^^

- svn: properly handle credentials from URL during remote repository import.
- svn: use more detailed logs/errors so `exception_tracker` can show it with details.
- svn: use streaming uploads/downloads of files.
- svn: use shared configurable storage for svn_txn_id interception logic.
- celery: use `exception_tracker` to store tasks exceptions for easier debugging.


Security
^^^^^^^^



Performance
^^^^^^^^^^^



Fixes
^^^^^

- exception_tracker: use a default value of exception store that is working across
  all instances e.g vcsserver and enterprise. This fixed problem with usage in
  cluster type setup.
- Comments: fixed problem with audit-logs receiving a empty value in certain
  conditions resulting in 500 error on commenting.
- Branch Permissions: during creation of rule add special check for existing entries to
  prevent duplicates if two users edit branch permissions at the same time.


Upgrade notes
^^^^^^^^^^^^^

- Scheduled release addressing reported problems, and improving stability.
