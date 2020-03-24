|RCE| 4.18.3 |RNS|
------------------

Release Date
^^^^^^^^^^^^

- 2020-03-24


New Features
^^^^^^^^^^^^

- LDAP: added nested user groups sync which was planned in 4.18.X but didn't
  make it to the release. New option for sync is available in the LDAP configuration.


General
^^^^^^^

- API: added branch permissions functions.
- Pull requests: added creating indicator to let users know they should wait until PR is creating.
- Pull requests: allow super-admins to force change state of locked PRs.
- Users/User groups: in edit mode we now show the actual name of what we're editing.
- SSH: allow generation of legacy SSH keys for older systems and Windows users.
- File store: don't response with cookie data on file-store download response.
- File store: use our own logic for setting content-type. This solves a problem
  when previously used resolver set different content-type+content-encoding which
  is an incorrect behaviour.
- My Account: show info about password usage for external accounts e.g github/google etc
  We now recommend using auth-tokens instead of actual passwords.
- Repositories: in description field we now show mention of metatags only if they
  are enabled.


Security
^^^^^^^^

- Remote sync: don't expose credentials in displayed URLs.
  Remote links url had visible credentials displayed in the link.
  This was used for web-view and not needed anymore.


Performance
^^^^^^^^^^^

- Full text search: significantly improved GIT commit indexing performance by reducing
  number of calls to the vcsserver.


Fixes
^^^^^

- Mercurial: fixed cases of lookup of branches that are exactly 20 character long.
- SVN: allow legacy (pre SVN 1.7) extraction of post commit data.
- GIT: use non-unicode author extraction as it's returned as bytes from backend, and
  we can get an unicode errors while there's some non-ascii characters.
- GIT: use safe configparser for git submodules to prevent from errors on submodules with % sign.
- System info: fixed UI problem with new version update info screen.


Upgrade notes
^^^^^^^^^^^^^

- Scheduled release addressing problems in 4.18.X releases.
