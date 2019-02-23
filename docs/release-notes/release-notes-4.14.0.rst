|RCE| 4.14.0 |RNS|
------------------

Release Date
^^^^^^^^^^^^

- 2018-11-02


New Features
^^^^^^^^^^^^

- Diffs: expose range diff inside the PR view. It's now possible to show
  commit-per-commit view of changes in pull request.
- Diffs: new sticky context bar.
  When browsing diffs we show file path of the current diff so users are aware all the time
  what file they are reviewing.
- Diffs: added quick file selector in diffs views. Now it's possible to select a file
  in large diffs from the sticky header for quicker access to certain interesting files
  in diffs.
- Diffs: introducing diff menu for whitespace toggle and context changes.
  It's now possible to show/hide whitespace changes and toggle the file context in
  all diff places including pull requests.
- Comments: allow commenting on empty files without content.
- Repositories: added option to archive repositories instead of deleting them.
  Archived repositories are useful for future auditing, but they are read-only.
- rcextensions: new rcextensions. We're introducing new `rcextensions` that will be base
  for future low-level integrations. It's now possible to expose nice messages back
  to the users when using `rcextensions`.
- Summary page: slightly re-organize summary page for better user experience.


General
^^^^^^^

- Mailing: switched from custom library to pyramid_mailer with python3 compatibility.
- Frontend: Switched to Polymer 3.0.
- Frontend: fixed problems with IE11 and brought back support for that browser.
- Git: use a fetch_sync based creation of remote repositories.
  This fixes problems with importing from Bitbucket.
- Comments: update comments email templates.
- Packaging: only wrap external dependency scripts. This makes execution of scripts
  roughly 5x faster due to much smaller PATH tree.
- HTTP: use application wide detection of invalid bytes sent via URL/GET/POST data.
- Fonts/UI: use consistent fonts across the whole application.
  Few places had non-standard custom fonts.
- Google: updated google auth plugin with latest API changes.
- Core: handle edge case requesting matched routes but with hg/svn/git or api context.
- Dependencies: bumped rhodecode-tools to 1.0.0 release using Apache2 license.
- Dependencies: atomicwrites==1.2.1
- Dependencies: attrs==18.2.0
- Dependencies: dogpile.cache==0.6.7
- Dependencies: psutil==5.4.7
- Dependencies: pathlib2==2.3.2
- Dependencies: subprocess32==3.5.2
- Dependencies: gevent==1.3.6
- Dependencies: greenlet==0.4.15
- Dependencies: pytest==3.8.2
- Dependencies: py==1.6.0
- Dependencies: pytest-cov==2.6.0
- Dependencies: pytest-timeout==1.3.2
- Dependencies: coverage==4.5.1
- Dependencies: psycopg2==2.7.5


Security
^^^^^^^^

- RST: improve Javascript RST sandbox.
- Jupyter: sanitize markdown cells similar as we do for our own markdown cleanup.


Performance
^^^^^^^^^^^

- SSH: improved SSH wrapper execution speed by using optimized binary script wrapping.
- Core: reduced font and JavaScript load times.


Fixes
^^^^^

- Comments: ensure we always display unmatched comments.
- Branch Permissions: fixed changing rule order for branch permissions.
- Users: ensure get_first_superadmin actually gets the 1st created super-admin.
- Users: when deleting users ensure we also clear personal flag.
  This fixes some problems with multiple personal groups.
- Diffs: disable the error border on highlight errors.
- Integrations: implement retry to HTTP[S] calls for integrations.
  Web parts will do a 3x retry call in case service is not reachable or
  responds with 5XX codes.
- Git: fixed pull-request updates in case branch names are the same as the file names.
- Supervisor: add patch for older kernel support.
- Compare: fixed file after/before links in compare view for cross repo compare.
- Emails: improve fonts and rendering of email HTML.
- Permissions: flush members of user groups permissions to clear caches.
- Repository: add check preventing of removal of repo with attached pull requests. Users
  should use the new archive repo function instead.


Upgrade notes
^^^^^^^^^^^^^

- In this release, we're shipping a new `rcextensions`. The changes made are
  backward incompatible. An update of `rcextensions` is required
  prior to using them again. Please check the new `rcextensions.tmpl` directory
  located in `profile/etc/rcextensions.tmpl` in your instance installation path.
  Old code should be 100% portable by just copy&paste to the right function.

- Mailing: We introduced a new mailing library. The older options should be compatible and
  generally, old configuration doesn't need any changes in order to send emails.
  We, however, encourage users to re-check mailing setup in case of some more
  sophisticated email setups.
  There's a possibility to send a test email from admin > settings > email section.
