|RCE| 4.6.0 |RNS|
-----------------

Release Date
^^^^^^^^^^^^

- 2017-02-03


New Features
^^^^^^^^^^^^

- Pull requests: introduced versioning for pull requests.
  Each update of pull requests creates and exposes a new version of it.
  Users can navigate each version to show the previous state of pull request, or
  generate diffs between versions to show what changed since the last update.
  Also on each update attached comments are pinned to versions, so users can
  tell at which state particular comment was made.
  Various UI/UX fixes on PR page.

- Pull requests: introduced new merge-checks.
  Merge checks show nicer UI for the status of merge approval.
  Merge checks now also forbid a merge if TODO notes are present.
  Submitting a status will auto-refresh merge checks, it means that it's no
  longer required to re-load diff to merge a PR.
  Same logic is now used for API, pre-conditions on show, and checks on
  actual merge API call.

- Code review: approval state is now bound to pull request versioning. Users
  can track their last approval and only show changes of pull requests between
  their last approval and latest state.
- Code review: inline and main comments have now two types. a `note` and `todo`.
  unresolved TODO comments show up in pull requests or commit view.
  Unresolved TODO also prevents a PR from being merged.
- Code review: added navigation on outdated comments.

- Diffs: compare mode overhaul.
  Made compare and commit range pages more consistent with other commit
  diff pages. Old diff2way is replaced by new diffs with side-by-side
  mode, and it also removes mergerly. Cleanup button behaviour on the compare
  page. Switched file-diffs to use the  compare page with file filter.
  Added collapse/expand commits buttons in compare views. Generally improved UX.
- Diffs: added a wide-mode button to expand large diffs.

- Comments: an overhaul of comments forms. Adjust them for new comment types and
  resolution comments.
- Comments: replaced a ctrl+space commands with slash commands. This becomes
  more standardized and easier to use.

- Changelog: added load more anchors into changelog view.
  Users in changelog can now load comments via ajax and extend the data
  set to show more than 100 commits. This also re-renders the graph. So it's
  possible to show 1000s of commits in an efficient way with the DAG graph.

- User sessions: added interface to show, and cleanup user auth sessions.
  It's possible to show, and clean obsolete sessions. Also a cleanup of all
  sessions option were added to completely log-out all users from the system.

- Integrations: webhook integration have now additional setting to choose if
  the call should be made with POST or GET.

- API: get_repos call now allows to filter returned data by specifying a start
  root location. Additionally, a traverse flag was added to define if returned
  data should be only from top-level or recursive.
- API: comment_type (`note` or `todo`) for comment API.
- API: added comment_resolved_id into comments API to resolve TODO notes.


General
^^^^^^^

- Api: comment_pull_request, added commit_id parameter to validate status
  changed on particular commit. In case users set status on the commit
  which is not current valid head this API call won't change the status anymore.
- Channelstream: added testing panel for live notifications.
- Authentication: disable password change form for accounts that are not
  managed by RhodeCode, in the case of external accounts such as LDAP/oAuth,
  password reset doesn't make sense.
- Core: let pyramid handle tracebacks for all exceptions.
  Otherwise, we'll miss exception caused in pure pyramid views.
- Vcs server: expose remote tracebacks from HTTP backend using
  the Pyro4AwareFormatter. This will now in most cases propagate VCSServer
  exception into Enterprise logs for easier tracking of errors
- Ishell: updated code with latest iShell changes.
- Svn: generate HTTP downgrade via the auto-generated config. This allows
  a HTTPs/HTTP configuration with SVN.
- Dependencies: bumped various pytest related libraries to latest versions.
- Dependencies: bumped gevent to 1.1.2 and greenlet to 0.4.10 versions.
- Dependencies: bumped msgpack to version 0.4.8.
- Dependencies: bumped supervisor to 3.3.1 version.
- Dependencies: bumped Whoosh to version 2.7.4.
- Dependencies: bumped Markdown library to 2.6.7
- Dependencies: bumped mako templates to 1.0.6
- Dependencies: bumped waitress version to 1.0.1
- Dependencies: bumped pygments to 2.2.0
- dependencies: bumped Mercurial version to 4.0.2
- dependencies: bumped git version to 2.9.3


Security
^^^^^^^^

- Login: Don't display partial password helper hash inside the logs.
  The information is not-required and will prevent people worrying about this
  shown in logs.
- Auth: use pyramid HTTP exception when detecting CSRF errors. It helps
  catching this error by our error handler and displaying it nicely to users.
- SVN: hide password entries in logs using specially generated configuration
  for Apache Mod-Dav
- Permissions: fixed call to correctly check permissions for admin, before admin
  users were ban deleting of pull requests in certain conditions.


Performance
^^^^^^^^^^^

- Markup renderer: use global Markdown object to speed up markdown rendering.
  We'll skip heavy initialization on each render thanks to this.
- Diffs: optimize how lexer is fetched for rich highlight mode.
  Speeds up initial diff creation significantly since lexer cache is re used
  and we don't need to fetch lexer many times.
- VCS: do an early detection of vcs-type request.
  In case we're handling a VCS request, we can skip some of the pylons
  stack initialization, speeding the request processing.


Fixes
^^^^^

- Code review: render outdated comments that don't fit current context.
  Comments attached to files that were removed from pull-request now will also
  properly show up.
- Markup renderer: don't render plaintext files as RST. This prevents plain
  Readme files have been wrongly rendered.
- VCS: raise a better exception if file node history cannot be extracted.
  Helps to trace corrupted repositories.
- Exception handling: nicer error catching on repository creation.
- Fixed excessive number of session object creation. There should be now a
  significant reduction in new file or DB entries created for sessions.
- Core: remove global timezone hook from tests. This was leaking into main
  application causing TZ problems (such as UTC log dates).
- Pull requests: wait for all dynamic checks before enabling opening a PR.
  This ensures that all code analysis were run before users are allowed to open
  a pull request.
- i18n: use a consistent way of setting user language.
- API: added merge checks into API because it was not validated before and could
  return an error if the merge wasn't possible for some reason.
- VCSServer: fetch proper locale before defaulting to default. Prevents
  errors on some machines that don't have locales set.
- VCSServer: fixed 500 error if the wrong URL on HTTP mode vcsserver was accessed.


Upgrade notes
^^^^^^^^^^^^^

- Integrations: since new POST/GET option was added to integrations, users
  are advised to optionally check Webhooks integrations and pick one.
  (default is still POST)