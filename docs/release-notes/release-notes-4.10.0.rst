|RCE| 4.10.0 |RNS|
------------------

Release Date
^^^^^^^^^^^^

- 2017-11-02


New Features
^^^^^^^^^^^^

- SSH (Beta): added support for authentication via SSH keys. It's possible
  to use SSH key based authentication instead of HTTP. Users are allowed to
  store multiple keys and use them to push/pull code via SSH.
- Pull requests: store and show a merge strategy. Pull request strategy will
  be also now shown in the UI.
  Close/delete branch are shown if that option is selected.
- Pull requests: Add option to close a branch before merging for Mercurial.
- Processes page. RhodeCode will show a list of all current workers with
  CPU and Memory usage.
  It's also possible to restart each worker from the web interface.
- Auth tokens: allow specifying a custom expiration date from UI.
- Integrations: webhook, allow to set a custom header.
- Integrations: webhook, add possibility to specify username and password.
- UI: added copy-to-clipboard for commits, file paths, gist/clone urls.
- UI: improve support for meta-tags in repository description:
  Tags are extracted to the beginning of the description during rendering.
  Show helpers in proper places in groups/repos/forks with all available tags.
  Add a new deprecated tag.
- UI: commits page, hide evolve commits.
  Now optionally it's possible to show them via a new link on changelog page.
- Audit logs: allow showing individual entries for audit log.
- Audit logs: expose repo related audit logs in repository view.
- User sessions: get ability to count memcached sessions.
- Core: added support for REDIS based user sessions and cache backend.
- Core: added support for Golang go-import functionality.
- SVN: allow specifying alternative template file for mod_dav config.
- Markup: make relative links pin to raw files for images/files as links.
  Allows building relative MD/RST links that go to rendered content
- Auth: allow binding the whitelist views to specific auth tokens. This allows
  to access only specific pages via given auth token. E.g possible to expose
  raw diff/raw file content only for specific single token.
  The new format is `viewName@TOKEN`
- Channelstream: push events with comments on single commits. Users will get
  live notification for events on single commits too.


General
^^^^^^^

- License: add helper to show alternative application method for license via
  ishell.
- http: set REMOTE_USER and REMOTE_HOST http variables in order for more
  Mercurial extensions compatibility.
- User/User groups: show if users or user groups are a part of review rules.
- Permissions: new improved visual permissions summary. Show exactly how
  permissions were inherited, and which rule overwrote the other.
- Permissions: added new JSON endpoint to extract permissions as JSON data
  for 3rd party processing. This allows access for reporting tools without
  giving any ADMIN API access to fetch permissions.
- Pyramid: ported all controllers to Pyramid, with python3 compatible code.
- Gunicorn: allow custom logger to be set for a consistent formatting of
  Gunicorn logs with RhodeCode logs.
- Search: per-repo search shouldn't require admin permissions. Read is enough
  because we access the repo data only.
- Git: updated to 2.13.5 release
- Mercurial: updated to 4.2.3 release.
- Mercurial Evolve: updated to 6.6.0 release.
- Dependencies: bumped pysqlite to Mako to 1.0.7
- Dependencies: bumped pysqlite to 2.8.3
- Dependencies: bumped psycopg2 to 2.7.1
- Dependencies: bumped docutils to 0.13.1
- Dependencies: bumped simplejson to 3.11.1
- Dependencies: bumped alembic to 0.9.2
- Dependencies: bumped Beaker to 1.9.0
- Dependencies: bumped Markdown to 2.6.8
- Dependencies: bumped dogpile.cache to 0.6.4
- Dependencies: bumped colander to 1.3.3
- Dependencies: bumped appenlight_client to 0.6.21
- Dependencies: bumped cprofileV to 1.0.7
- Dependencies: bumped ipdb to 0.10.3
- Dependencies: bumped supervisor to 3.3.2
- Dependencies: bumped subprocess32 to 3.2.7
- Dependencies: bumped pathlib2 to 2.3.0.
- Dependencies: bumped gunicorn==19.7.1
- Dependencies: bumped gevent to 1.2.2 together with greenlet to 0.4.12
- Dependencies: bumped venusian to 1.1.0
- Dependencies: bumped ptyprocess to 0.5.2
- Dependencies: bumped testpath to 0.3.1
- Dependencies: bumped Pyramid to 1.9.1
- Dependencies: bumped supervisor to 3.3.3
- Dependencies: bumped sqlalchemy to version 1.1.11


Security
^^^^^^^^

- Security: use no-referrer for outside link to stop leaking potential
  parameters such as auth token stored inside GET flags.
- Auth tokens: always check permissions to scope tokens to prevent resource
  discovery of private repos.
- Strip: fix XSS in repo strip view.
- Files: prevent XSS in fake errors message on filenodes.
- Files: remove right-to-left override character for display in files.
  This allows faking the name a bit, we in this particular place want to
  skip the override for enhanced security.
- Repo forks: security, check for access to fork_id parameter to prevent
  resource discovery.
- Pull requests: security double check permissions on injected forms of
  source and target repositories. Fixes resource discovery.
- Pull requests: security, prevent from injecting comments to other pull
  requests for users don't have access to.


Performance
^^^^^^^^^^^

- Goto-switcher: use special commit: prefix to explicitly search for commits.
  previous solution could make the go-to switcher slow in case of larger search
  index present.
- Goto-switcher: optimized performance and query capabilities.
- Diffs: use whole chunk diff to calculate if it's oversized or not.
  This fixes an issue if a file is added that has very large number of small
  lines. In this case the time to detect if the diff should be limited was
  very long and CPU intensive.
- Markup: use cached version of http pattern for urlify_text. This
  increases performance because we don't have to compile the pattern each time
  we execute this commonly used function.
- Changelog: fix and optimize loading of chunks for file history.
- Vcs: reduce sql queries used during pull/push operations.
- Auth: use cache_ttl from a plugin to also cache calculated permissions.
  This gives a 30% speed increase in operations like svn commit.


Fixes
^^^^^

- Initial-gravatars: fix case of dot being present before @domain.
- Vcs: report 404 for shadow repos that are not existing anymore.
- RSS/Atom Feeds: generate entries with proper unique ids.
- DB: use LONGTEXT for mysql in user_logs. Fixes problem with mysql rejecting
  insert because of too long json data.
- Pull request: add missing audit data for pull_request.close action.
- User groups: properly set add/delete members for usage in audit data.
- Repo, auth-tokens: UX, set VCS scope if repo scopped token is selected.
- Changelog: fix and optimize loading of chunks for file history.
- Error reporting: improve handling of exception that are non-standard.
  Inject traceback information into unhandled exceptions.
- Users: add additional information why user with pending reviews
  shouldn't be deleted.
- Auth ldap: improve messages when users failed to authenticate via LDAP.
- Sqlalchemy: enabled connection ping.
  should fix potential issues with Mysql server has gone away issues.
- License page: fix usage of url() that could prevent from using convert license.
- Permissions: use same way of sorting of user_group permissions like user ones.


Upgrade notes
^^^^^^^^^^^^^

- Searching for commits in goto-switcher must be now prefixed with
  commit:<hash>
- Because of pyramid porting view names have changed, and we made a backward
  compatibility mapping for most common ones only.
  We recommend reviewing your whitelist view access list.
  There's a new dedicated page with ALL views listed under admin > permissions
  Please take a look in there to port any non-standard views for whitelist access.

- SSH support is implemented via combination of internal, and installed hooks.
  A file called `hgrc_rhodecode` is added to each repository that was used with
  SSH access. This file is then imported inside main hgrc file, it contains
  some Mercurial hooks for ACL checks.
  This breaks full backward compatibility with releases prior to 4.10.0.
  If you install 4.10+, enable SSH module and use SSH with a Mercurial repo, then
  rollback used version to 4.9.1. In such case one additional actions is required.
  Remove following line from `hgrc` file stored inside the repository:
  `%include hgrc_rhodecode`
