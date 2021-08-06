|RCE| 4.26.0 |RNS|
------------------

Release Date
^^^^^^^^^^^^

- 2021-08-06


New Features
^^^^^^^^^^^^



General
^^^^^^^

- Caches: introduce invalidation as a safer ways to expire keys, deleting them are more problematic.
- Caches: improved locking problems with distributed lock new cache backend.
- Pull requests: optimize db transaction logic.
  This should prevent potential problems with locking of pull-requests that have a lot of reviewers.
- Pull requests: updates use retry logic in case of update is locked/fails for some concurrency issues.
- Pull requests: allow forced state change to repo admins too.
- SSH: handle subrepos better when using SSH communication.


Security
^^^^^^^^

- Drafts comments: don't allow to view history for others than owner.
- Validators: apply username validator to prevent bad values being searched in DB, and potential XSS payload sent via validators.


Performance
^^^^^^^^^^^

- SSH: use pre-compiled backends for faster matching of vcs detection.
- Routing: don't check channelstream connections for faster handling of this route.
- Routing: skip vcsdetection for ops view so they are not checked against the vcs operations.


Fixes
^^^^^

- Permissions: flush all users permissions when creating a new user group.
- Repos: recover properly from bad extraction of repo_id from URL and DB calls.
- Comments history: fixed fetching of history for comments
- Pull requests: fix potential crash on providing a wrong order-by type column.
- Caches: report damaged DB on key iterations too not only the GET call
- API: added proper full permission flush on API calls when creating repos and repo groups.

Upgrade notes
^^^^^^^^^^^^^

- Scheduled release 4.26.0.
