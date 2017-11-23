|RCE| 4.10.5 |RNS|
------------------

Release Date
^^^^^^^^^^^^

- 2017-11-23


New Features
^^^^^^^^^^^^



General
^^^^^^^

- dependencies: pin against rhodecode-tools 0.13.1. Fixes a cleanup-repos bug.


Security
^^^^^^^^

- Pull requests: security(low), check for permissions on exposure of repo-refs.
  Prevents exposure of branches/tags on private repositories.
- Metatags: limit the scope of url => metatag to http, https and / links.
  Prevents possible JS injection in those types of links which is unsafe.


Performance
^^^^^^^^^^^



Fixes
^^^^^


- Emails: fixed validation of emails with whitespace in them.
- Repo groups: fix bad route redirect on check if user tried to revoke
  permissions on himself.
- Comments: place the left over comments (outdated/misplaced) to the left or
  right pane in side-by-side diff.
- Comments: allow to properly initialize outdated comments that are still attached.
  Fixes a problem when outdated TODO notes couldn't be properly resolved.
- Diffs: fixed problem with rendering no newline at the end of file markers.
  In case of unified diff that would show incorrect diffs in rare cases.
- Settings: fix potential 500 problem on bad data passed in.


Upgrade notes
^^^^^^^^^^^^^

- Fixes regression in nested repository groups update. No upgrade problems should
  be expected
