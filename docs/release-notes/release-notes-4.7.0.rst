|RCE| 4.7.0 |RNS|
-----------------

Release Date
^^^^^^^^^^^^

- 2017-04-08


New Features
^^^^^^^^^^^^

- Git: added support for Git LFS v2 protocol. RhodeCode now supports both
  Mercurial Largefiles, and Git LFS for storing large binaries.
- Largefiles: detect Git LFS or Mercurial Largefiles objects in UI.
  Those are now available for downloading together with showing their size.
- Files: Jupyter notebooks will be now rendered inside the file view. Including
  MatJax support, and relative images.
- Files: render images inside the file view.
  Instead of displaying binary message, render images icons and gifs
  inside the file view page.
- Files: relative ULR support inside rendered files. It's now possible to
  write Markup files and relative links will be handled from the RhodeCode
  instance itself. Adds basic wiki functionality.
- Files: allow to show inline pdf in browser using embedded files from source code.
- Annotation: added shortcut links to browse the annotation view with previous
  commits. Allows browsing history for each line from annotation view.
- Pull Requests: add explicit close action instead of close with status from
  status selector. This allows closing of approved or rejected
  pull requests, without performing a merge action.
- Authentication: LDAP now has an option to sync LDA groups using two
  distinct ways. Either using rfc2307 or rfc2307bis. Increases compatibility
  with different OpenLDAP and AD servers.
- Slack: updated slack integration to use the attachments for nicer formatting.
  Added number of commits inside the message, changed UI for all Slack events.
- Authentication (EE edition only): added repository scope for VCS type auth
  tokens. Each token can be now bound to particular repository for added security.
- User administration: added audit page to allow showing single user actions.
- API: implemented `get_user_audit_logs` method to fetch audit logs via API endpoint.
- User administration: It's now possible to edit user group membership from
  user view.
- User groups administration: added managing and showing the group
  synchronization in UI. It's now possible to enable manual group syncing on
  already existing user groups from external sources such as LDAP/AD.
- Repositories: added new strip view allowing removing commits from repositories
  via web interface for repository administrators.
- System Info: added info about workers and worker type.
  Added more details about CPU. Expose workers of VCSServer in system info data.
  Detect database migration errors.


General
^^^^^^^

- Core: ported many views into pure pyramid code with python3.6 compatibility.
- Core: removed deprecated Pyro4 backend from Enterprise code.
- Maintenance: implemented maintenance view for Mercurial and GIT repositories.
  For HG it will run `hg verify`, and for GIT a `git gc` command.
- Notifications: different approach with fixed/standard container. Floating
  notifications no longer hide the menu when browsed on top of the page.
  Also added option to remove single elements from stacked notifications.
- VCS server: exception-handling: better handling of remote exception and logging.
- VCS server: propagate hooks tracebacks to VCS server for easier debugging.
- Core: prevent `httplib3` logs to spam internal RhodeCode logs.
  It often confuses people looking at those entries, misleading during debug.
- Mercurial: allow editing Largefiles store location from web interface.
- Git: allow editing GIT LFS store location from web interface.
- API: add get_method API call. This allows showing the method and it's parameter
  from the CLI without reading the documentation.
  In addition use it's mechanics to propose users other methods with close names
  if the calling method is not found.
- UI: add timezone info into tooltips.
- Dependencies: bumped pyramid to 1.7.4
- Dependencies: bumped Mercurial version to 4.1.2


Security
^^^^^^^^

- Hooks: added changes to propagate commit metadata on pre-push.
  This allows easier implementation of checking hooks such as branch protection.
- Hooks: added new pretx hook to allow mercurial checks such as protected
  branches, or force push.
- Auth: give owner of user group proper admin permissions to the user group.
  This makes the behaviour consistent with repositories and repository groups.
  And allows delegation of administration of those to other users.
- Password reset: strengthen security on password reset logic.
  Generate token that has special password reset role.
  Set 10 minute expiration for the token.
  Add some logic to prevent brute forcing attacks.
  Use more implicit messages to prevent user email discovery attacks.
- Core: added checks for password change for authenticated users in pure
  Pyramid views. 2 views were still available and not forcing users to change
  their passwords.
- Auth tokens: removed builtin auth-token for users.
  Builtin token were non-removable, and always generated for new users. This
  wasn't best practice for security as some users are strictly not allowed to
  use tokens. From now on new users needs a new token generation in case they
  want to use token based authentication.
- Auth tokens: don't generate builtin token for new users.
  Also don't change them when password reset is made.
- Api: added last-activity into returned data of get_user api.


Performance
^^^^^^^^^^^

- Mercurial: enabled new `Zstandard` compression algorithm available with
  Mercurial 4.1.X. This allows faster, more CPU efficient clones when used
  with new Mercurial clients.

- Users Admin: moved user admin to pyramid, and made it load users in chunks.
  Fixed loading data to be lazy fetched, drastically improves speed of user
  administration page in case of large amount of users.


Fixes
^^^^^

- Search: goto commit search will now use a safe search option and never
  throw any exceptions even if search is misconfigured
  e.g. Elastic Search cluster is down.
- Events: fix a case for events called from API that couldn't fetch
  registered user object.
- Comments: unlock submit if we use slash commands to set status.
- UI: fixed an issue with date of last change was not displayed correctly.
- Emails: added comment types (TODO/NOTE) into emails.
- Events: fix wrongly returned author data.
- Error middleware: read the instance title from cached object.
  Reading from settings inside error handler can cause error hiding when
  error_handler was caused by database errors.
- Pull requests: show version age component should use local dates instead of UTC.
- Pull requests: lock button when updating reviewers to forbid multi-submit
  problems. Additionally fixed some small UI issues found in that view.
- Pull requests: forbid browsing versions on closed pull request.
- Pull requests: allow super-admins to delete pull requests instead of only owners.
- Diffs: support mercurial copy operation in diffs details.
- SVN: escape special chars to allow interactions with non-standard svn paths.
  Path with special characters such as '#' will no longer trigger 404 errors.
- Data grids: fix some styling and processing text display.
- API: use consistent way to extract users, repos, repo groups and user groups
  by id or name. Makes usage of Number vs String to differentiate if we pick
  object ID or it's name this will allow editing of objects by either id or
  it's name, including numeric string names.
- API: validate commit_id when using commit_comment API
- API: cleanup sessions enforce older_then must be a valid INT.


Upgrade notes
^^^^^^^^^^^^^

- Auth-tokens: a builtin token will be migrated for all users into a custom
  external token. We advise to inform users that the current builtin tokens
  will now show as external ones. Builtin tokens were removed to allow expiring
  ,or removing them. It's now possible to create users without any tokens.

  From now on new users needs a new token generation in case they want to use
  token based authentication.

- Hooks: we added via migration a pre transaction hook for Mercurial. If you're
  using a custom code inside pre-push function of rcextensions make sure it
  will not block your pushes.
