|RCE| 4.12.0 |RNS|
------------------

Release Date
^^^^^^^^^^^^

- 2018-04-24


New Features
^^^^^^^^^^^^

- Svn: added support for RhodeCode integration framework. All integrations like
  slack, email, Jenkins now also fully work for SVN.
- Integrations: added new dedicated Jenkins integration with the support of
  CSRF authentication. Available in EE edition only.
- Automation: added new bi-directional remote sync. RhodeCode instances can now
  automatically push or pull from/to remote locations. This feature is powered
  by the Scheduler of 4.11 release, and it is required to be enabled for this feature to work.
  Available in EE edition only.
- Mercurial: path-based permissions. RhodeCode can now use Mercurials narrowhg
  to implement path-based permissions. All permissions are read from .hg/hgacl.
  Thanks to the great contribution from Sandu Turcan.
- VCS: added new diff caches. Available as an option under vcs settings.
  Diff caches work on pull-request, or individual commits for greater
  performance and reduced memory usage. This feature increases speed of large
  pull requests significantly. In addition for pull requests it will allow
  showing old closed pull requests even if commits from source were removed,
  further enhancing auditing capabilities.
- Audit: added few new audit log entries especially around changing permissions.
- LDAP: added connection pinning and timeout option to ldap plugin. This should
  prevent problems when connection to LDAP is not stable causing RhodeCode
  instances to freeze waiting on LDAP connections.
- User groups: expose public user group profiles. Allows to see members of a user
  groups by other team members, if they have proper permissions.
- UI: show pull request page in quick nav menu on my account for quicker access.
- UI: hidden/outdated comments now have visible markers next to line numbers.
  This allows access to them without showing all hidden comments.


General
^^^^^^^

- Ssh: show conflicting fingerprint when adding an already existing key.
  Helps to track why adding a key failed.
- System info: added ulimit to system info. This is causing lots of problems
  when we hit any of those limits, that is why it's important to show this.
- Repository settings: add hidden view to force re-install hooks.
  Available under /{repo_name}/settings/advanced/hooks
- Integrations: Webhook now handles response errors and show response for
  easier debugging.
- Cli: speed up CLI execution start by skipping auth plugin search/registry.
- SVN: added an example in the docs on how to enable path-based permissions.
- LDAP: enable connection recycling on LDAP plugin.
- Auth plugins: use a nicer visual display of auth plugins that would
  highlight that order of enabled plugins does matter.
- Events: expose shadow repo build url.
- Events: expose pull request title and uid in event data.
- API: enable setting sync flag for user groups on create/edit.
- API: update pull method with a possible specification of the url
- Logging: improved consistency of auth plugins logs.
- Logging: improved log for ssl required
- Dependencies: bumped mercurial to 4.4 series
- Dependencies: bumped zope.cachedescriptors==4.3.1
- Dependencies: bumped zope.deprecation==4.3.0
- Dependencies: bumped zope.event==4.3.0
- Dependencies: bumped zope.interface==4.4.3
- Dependencies: bumped graphviz 0.8.2
- Dependencies: bumped to ipaddress 0.1.19
- Dependencies: bumped pyexpect to 4.3.1
- Dependencies: bumped ws4py to 0.4.3
- Dependencies: bumped bleach to 2.1.2
- Dependencies: bumped html5lib 1.0.1
- Dependencies: bumped greenlet to 0.4.13
- Dependencies: bumped markdown to 2.6.11
- Dependencies: bumped psutil to 5.4.3
- Dependencies: bumped beaker to 1.9.1
- Dependencies: bumped alembic to 0.6.8 release.
- Dependencies: bumped supervisor to 3.3.4
- Dependencies: bumped pyexpect to 4.4.0 and scandir to 1.7
- Dependencies: bumped appenlight client to 0.6.25
- Dependencies: don't require full mysql lib for the db driver.
  Reduces installation package size by around 100MB.


Security
^^^^^^^^

- My account: changing email in my account now requires providing user
  access password. This is a case for only RhodeCode built-in accounts.
  Prevents adding recovery email by unauthorized users who gain
  access to logged in session of user.
- Logging: fix leaking of tokens to logging.
- General: serialize the repo name in repo checks to prevent potential
  html injections by providing a malformed url.


Performance
^^^^^^^^^^^

- Diffs: don't use recurred diffset attachment in diffs. This makes
this structure much harder to garbage collect. Reduces memory usage.
- Diff cache: added caching for better performance of large pull requests.


Fixes
^^^^^

- Age helper: fix issues with proper timezone detection for certain timezones.
  Fixes wrong age display in few cases.
- API: added audit logs for user group related calls that were
  accidentally missing.
- Diffs: fix and improve line selections and anchor links.
- Pull requests: fixed cases with default expected refs are closed or unavailable.
  For Mercurial with closed default branch a compare across forks could fail.
- Core: properly report 502 errors for gevent and gunicorn.
  Gevent wtih Gunicorn doesn't raise normal pycurl errors.
- Auth plugins: fixed problem with cache of settings in multi-worker mode.
  The previous implementation had a bug that cached the settings in each class,
  caused not refreshing the update of settings in multi-worker mode.
  Only restart of RhodeCode loaded new settings.
- Audit logs: properly handle query syntax in the search field.
- Repositories: better handling of missing requirements errors for repositories.
- API: fixed problems with repository fork/create using celery backend.
- VCS settings: added missing flash message on validation errors to prevent
  missing out some field input validation problems.


Upgrade notes
^^^^^^^^^^^^^

- This release adds support for SVN hook. This required lots of changes on how we
handle SVN protocol. We did thoughtful tests for SVN compatibility.
Please be advised to check the behaviour of SVN repositories during this update.

A check and migrate of SVN hooks is required. In order to do so, please execute
`Rescan filesystem` from admin > settings > Remap and Rescan. This will migrate
all SVN hook to latest available version. To migrate single repository only,
please go to the following url: `your-rhodecode-server.com/REPO_NAME/settings/advanced/hooks`

- Diff caches are turned off by default for backward compatibility. We however recommend
turning them on either individually for bigger repositories or globally for every repository.
This setting can be found in admin > settings > vcs, or repository > settings > vcs
