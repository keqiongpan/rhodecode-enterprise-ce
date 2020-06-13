|RCE| 4.19.2 |RNS|
------------------

Release Date
^^^^^^^^^^^^

- 2020-06-10


New Features
^^^^^^^^^^^^

- Files: landing refs will be the default for files view, resulting in names of branches instead of hashes.
  This fixes some problems reported with navigation, and also SVN.
- Diffs: expose per-file comment counts.


General
^^^^^^^

- Navigation: explicitly link to summary page for summary link.
- Main Page: simplify footer, and expose docs link.
- Docs: added mention how to change default integration templates.
- Files: use ref names in the url, and make usage of default landing refs.
- Files: report the name of missing commit.
- Sweet alerts: reduced font size.


Security
^^^^^^^^

- Branch permissions: fix XSS on branch permissions adding screen.


Performance
^^^^^^^^^^^



Fixes
^^^^^

- Emails: improved styling, and fixed problems with some email clients rendering.
- Files: fixed label for copy-path action.
- Files: use a common function to handle url-by-refs, and fix landing refs for SVN.


Upgrade notes
^^^^^^^^^^^^^

- Un-scheduled release addressing problems in 4.19.X releases.
  It brings some added features that weren't ready for 4.19.0.
