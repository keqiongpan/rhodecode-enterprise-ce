|RCE| 4.15.2 |RNS|
------------------

Release Date
^^^^^^^^^^^^

- 2019-01-22


New Features
^^^^^^^^^^^^



General
^^^^^^^

- Rcextensions: updated examples and fixed some small inconsistencies.
- Api/pull-requests: trigger events for comments/review status changes.
- Events: trigger 'review_status_change' when reviewers are updated.
- Diffs: fixed missing limited diff container display on large diffs
- Pull-requests: increase stability of concurrent pull requests creation by flushing
  prematurely the statuses of commits.


Security
^^^^^^^^



Performance
^^^^^^^^^^^



Fixes
^^^^^

- Cache: use global flock to prevent recursion when using gevent workers.
- Permissions: clear cache for permissions correctly for forks/repos when celery is used.
- Permissions: clear cache for default user permissions on global app permission changes.
- Permissions: handle more cases for invalidating permission caches
- Files-editor: preserve filemode on web edits. Editing files with +x flag removed it.


Upgrade notes
^^^^^^^^^^^^^

- Scheduled release addressing reported problems in 4.15.X releases.
