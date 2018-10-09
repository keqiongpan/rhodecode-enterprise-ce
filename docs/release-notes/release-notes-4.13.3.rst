|RCE| 4.13.3 |RNS|
------------------

Release Date
^^^^^^^^^^^^

- 2018-10-09


New Features
^^^^^^^^^^^^



General
^^^^^^^

- VCS: use a real two user First Last name for merge operation.
  This allows certain user naming checks to pass and be validated correctly.


Security
^^^^^^^^

- GIT: bumped release to 2.17.2 which addresses cve-2018-17456.


Performance
^^^^^^^^^^^



Fixes
^^^^^

- Repository import: skip validating root storage path in detection of VCS types.
  This check doesn't need to be visible in logs and by that it will reduce the
  number of errors in logs significantly.
- VCS: Properly handle VCS traffic from web app routes and API.
  Before accessing those via any VCS produced a 500 error.
- Users: when deleting users ensure we also properly clear personal flag so we
  don't have multiple personal groups which is produces 500 errors.
- Users: in case of multiple personal groups, return the first instead of an error.
- Webhook: handle ${commit_id} variable independent from ${branch}.
- Hooks: handle errors before trying to fetch the output. This allows easier debugging
  of hook related problems
- Dependencies: Backported a patch from Dulwich to handle GIT references that are
  directories. Such references should be skipped, but before made repository show
  500 errors.


Upgrade notes
^^^^^^^^^^^^^

- Scheduled release addressing reported problems, and GIT security vulnerability.

