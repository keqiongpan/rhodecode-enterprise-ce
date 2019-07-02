|RCE| 4.17.0 |RNS|
------------------

Release Date
^^^^^^^^^^^^

- 2019-07-04


New Features
^^^^^^^^^^^^

- New artifacts feature.
  Ability to store binary artifacts for repository with ACL
- UI/UX refresh for most of the pages. This includes multiple fixes and improvements.
- Diffs: store wide-diff mode in user sessions to store user preference for diff display.
- Mercurial: added support for Mercurial 4.9
- API: Added search API methods
- Files: adding/editing allows previews for generated content.
- Files: allowed multi file upload using UI.
- Repository Groups: last change is now smartly calculated based on latest change
  from all it's children repositories.
- Archives: it's now currently possible to download partial directories from files view.
- SVN: allowed executing pre-commit code with rcextensions, also added example to
  validate SVN file size and paths on pre-commit level.


General
^^^^^^^
- Exception store: add filter for display and deletion.
- Files: loading history doesn't display hidden and obsolete commits anymore.
- Repositories: bring back missing watch action in summary view.
- Admin: user groups is now using pure DB filtering to speed up display
  for large number of groups.
- Mercurial: enabled full evolve+topic extensions when evolve is enabled.
- Dependencies: bumped evolve to 8.5.1
- Dependencies: bumped pyramid to 1.10.4
- Dependencies: bumped psutil to 5.5.1
- Dependencies: bumped pygments to 2.4.2
- Dependencies: bumped pyramid to 1.10.4
- Dependencies: bumped psycopg2 to 2.8.3
- Dependencies [security]: updated colander to 1.7.0


Security
^^^^^^^^

- SSH: replaced pycrypto with cryptography to generate SSH keys as pycrypto isn't
  considered safe anymore.


Performance
^^^^^^^^^^^

- Config: updated header limits on gunicorn to prevent errors on large Mercurial repositories.
- User sessions: added option to cleanup redis based sessions in user session interface.
- Authentication: reduced usage of raw auth calls inside templates to speed up rendering.
- Sessions: don't touch session for API calls. Before each API call created new session
  object which wasn't required.


Fixes
^^^^^

- hHooks: fixed more unicode problems with new pull-request link generator.
- Mercurial: fix ssh-server support for mercurial custom options.
- Pull requests: updated metadata information for failed merges with multiple heads.
- Pull requests: calculate ancestor in the same way as creation mode.
  Fixed problem with updates generating wrong diffs in case of merges.
- Pull requests: fixed a bug in removal of multiple reviewers at once.
- Summary: fix timeout issues loading summary page without styling.
- SSH: fix invocation of custom hgrc.
- SSH: call custom hooks via SSH backend
- Markup: fix styling for check-lists.
- Archives: allows downloading refs that have slashes and special refs. e.g f/feat1 branch names.
- Files: ensure we generate archives with consistent hashing (except for .tar.gz which uses temp files names in header)
- Files: fixed rendering of readme files under non-ascii paths.


Upgrade notes
^^^^^^^^^^^^^

- In this release we introduced new UI across the application.
  In case of problems with the display on your systems please send us info to support@rhodecode.com.

