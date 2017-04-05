|RCE| 4.5.0 |RNS|
-----------------

Release Date
^^^^^^^^^^^^

- 2016-12-02


New Features
^^^^^^^^^^^^

- Diffs: re-implemented diff engine. Added: Syntax highlighting inside diffs,
  new side-by-side view with commenting and live chat. Enabled soft-wrapping of
  long lines and much improved rendering speed for large diffs.
- File source view: new file display engine. File view now
  soft wraps long lines. Double click inside file view show occurrences of
  clicked item. Added pygments-markdown-lexer for highlighting markdown syntax.
- Files annotation: Added new grouped annotations. Color all related commits
  by double clicking singe commit in annotation view.
- Pull request reviewers (EE only): added new default reviewers functionality.
  Allows picking users or user groups defined as reviewers for new pull request.
  Picking reviewers can be based on branch name, changed file name patterns or
  original author of changed source code. eg \*.css -> design team.
  Master branch -> repo owner, fixes #1131.
- Pull request reviewers: store and show reasons why given person is a reviewer.
  Manually adding reviewers after creating a PR will now be also indicated
  together with who added a given person to review.
- Integrations: Webhooks integration now allows to use variables inside the
  call URL. Currently supported variables are ${repo_name}, ${repo_type},
  ${repo_id}, ${repo_url}, ${branch}, ${commit_id}, ${pull_request_id},
  ${pull_request_url}. Commits are now grouped by branches as well.
  Allows much easier integration with CI systems.
- Integrations (EE only): allow wildcard * project key in Jira integration
  settings to allow referencing multiple projects per commit, fixes #4267.
- Live notifications: RhodeCode sends live notification to online
  users on certain events and pages. Currently this works on: invite to chat,
  update pull request, commit/inline comment. Part of live code review system.
  Allows users to update the reviewed code while doing the review and never
  miss any updates or comment replies as they happen. Requires channelstream
  to be enabled.
- Repository groups: added default personal repository groups. Personal groups
  are isolated playground for users allowing them to create projects or forks.
  Adds new setting to automatically create personal repo groups for newly
  created users. New groups are created from specified pattern, for example
  /u/{username}. Implements #4003.
- Security: It's now possible to disable password reset functionality.
  This is useful for cases when users only use LDAP or similar types of
  authentication. Implements #3944
- Pull requests: exposed shadow repositories to end users. Users are now given
  access to the shadow repository which represents state after merge performed.
  In this way users or especially CI servers can much easier perform code
  analysis of the final merged code.
- Pull requests: My account > pull request page now uses datagrid.
  It's faster, filterable and sortable. Fixes #4297.
- Pull requests: delete pull request action was moved from my account
  into pull request view itself. This is where everyone was looking for it.
- Pull requests: improve showing failed merges with proper status in pull
  request page.
- User groups: overhaul of edit user group page. Added new selector for
  adding new user group members.
- Licensing (EE only): exposed unlock link to deactivate users that are over
  license limit, to unlock full functionality. This might happen when migrating
  from CE into EE, and your license supports less active users then allowed.
- Global settings: add a new header/footer template to allow flash filtering.
  In case a license warning appears and admin wants to hide it for some time.
  The new template can be used to do this.
- System info: added create snapshot button to easily generate system state
  report. Comes in handy for support and reporting. System state holds
  information such as free disk/memory, CPU load and some of RhodeCode settings.
- System info: fetch and show vcs settings from vcsserver. Fixes #4276.
- System info: use real memory usage based on new psutil api available.
- System info: added info about temporary storage.
- System info: expose inode limits and usage. Fixes #4282.
- Ui: added new icon for merge commit.



General
^^^^^^^

- Notifications: move all notifications into polymer for consistency.
  Fixes #4201.
- Live chat (EE): Improved UI for live-chat. Use Codemirror editor as
  input for text box.
- Api: WARNING DEPRECATION, refactor repository group schemas. Fixes #4133.
  When using create_repo, create_repo_group, update_repo, update_repo_group
  the \*_name parameter now takes full path including sub repository groups.
  This is the only way to add resource under another repository group.
  Furthermore giving non-existing path will no longer create the missing
  structure. This change makes the api more consistent, it better validates
  the errors in the data sent to given api call.
- Pull requests: disable subrepo handling on pull requests. It means users can
  now use more types of repositories with subrepos to create pull requests.
  Since handling is disabled, repositories behind authentication, or outside
  of network can be used.
- VCSServer: fetch backend info from vcsserver including git/hg/svn versions
  and connection information.
- Svn support: it's no longer required to put in repo root path to
  generate mod-dav-svn config. Fixes #4203.
- Svn support: Add reload command option (svn.proxy.reload_cmd) to ini files.
  Apache can now be automatically reloaded when the mod_dav_svn config changes.
- Svn support: Add a view to trigger the (re)generation of Apache mod_dav_svn
  configuration file. Users are able to generate such file manually by clicking
  that button.
- Dependency: updated subversion library to 1.9.
- Dependency: updated ipython to 5.1.0.
- Dependency: updated psutil to 4.3.1.


Security
^^^^^^^^

- Hipchat: escape user entered data to avoid xss/formatting problems.
- VCSServer: obfuscate credentials added into remote url during remote
  repository creation. Prevents leaking of those credentials inside
  RhodeCode logs.


Performance
^^^^^^^^^^^

- Diffs: new diff engine is much smarter when it comes to showing huge diffs.
  The rendering speed should be much improved in such cases, however showing
  full diff is still supported.
- VCS backends: when using a repo object from database, re-use this information
  instead of trying to detect a backend. Reduces the traffic to vcsserver.
- Pull requests: Add a column to hold the last merge revision. This will skip
  heavy recalculation of merge state if nothing changed inside a pull request.
- File source view: don't load the file if it is over the size limit since it
  won't be displayed anyway. This increases speed of loading the page when a
  file is above cut-off limit defined.


Fixes
^^^^^

- Users admin: fixed search filter in user admin page.
- Autocomplete: improve the lookup of users with non-ascii characters. In case
  of unicode email the previous method could generate wrong data, and
  make search not show up such users.
- Svn: added request header downgrade for COPY command to work on
  https setup. Fixes #4307.
- Svn: add handling of renamed files inside our generated changes metadata.
  Fixes #4258.
- Pull requests: fixed problem with creating pull requests on empty repositories.
- Events: use branch from previous commit for repo push event commits data so
  that per-branch grouping works. Fixes #4233.
- Login: make sure recaptcha data is always validated. Fixes #4279.
- Vcs: Use commit date as modification time when creating archives.
  Fixes problem with unstable hashes for archives. Fixes #4247.
- Issue trackers: fixed bug where saving empty issue tracker via form was
  causing exception. Fixes #4278.
- Styling: fixed gravatar size for pull request reviewers.
- Ldap: fixed email extraction typo. An empty email from LDAP server will now
  not overwrite the stored one.
- Integrations: use consistent formatting of users data in Slack integration.
- Meta-tags: meta tags are not taken into account when truncating descriptions
  that are too long. Fixes #4305.


Upgrade notes
^^^^^^^^^^^^^

- Api: please adjust your scripts that uses any of create_repo,
  create_repo_group, update_repo, update_repo_group. There's an important change
  in how the repo_name/group_name parameters work. Please check the API docs
  for latest information.

- Installation: starting from 4.5.0 installer now changes the default mode to http.
  If you were using the `self_managed_supervisor=True` flag inside
  `.rccontrol.ini` to manually switch to that mode. This is no longer required
  and we recommend removing that flag. Migration should already change that
  however in case of any troubles with VCSServer after upgrade
  please make sure `vcs.protocol=` is set to `http` and not `pyro4` inside
  rhodecode.ini

- New setting about password recovery was introduced. Please make sure to
  adjust what ever default you want to have inside your instance. The default
  is that password recovery is enabled.
