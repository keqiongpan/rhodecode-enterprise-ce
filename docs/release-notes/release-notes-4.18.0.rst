|RCE| 4.18.0 |RNS|
------------------

Release Date
^^^^^^^^^^^^

- 2020-01-05


New Features
^^^^^^^^^^^^

- Artifacts: are no longer in BETA. New info page is available for uploaded artifacts
  which exposes some useful information like sha256, various access urls etc, and also
  allows deletion of artifacts, and updating their description.
- Artifacts: support new download url based on access to artifacts using new auth-token types.
- Artifacts: added ability to store artifacts using API, and internal cli upload.
  This allows uploading of artifacts that can have 100s of GBs in size efficiently.
- Artifacts: added metadata logic to store various extra custom data for artifacts.
- Comments: added support for adding comment attachments using the artifacts logic.
  Logged in users can now pick or drag and drop attachments into comment forms.
- Comments: enable linkification of certain patterns on comments in repo/pull request scopes.
  This will render now active links to commits, pull-requests mentioned in comments body.
- Jira: new update integration plugin.
  Plugin now fetches possible transitions from tickets and show them to users in the interface.
  Allow sending extra attributes during a transition like `resolution` message.
- Navigation: Added new consistent and contextual way of creating new objects
  likes gists, repositories, and repository groups using dedicated action (with a `+` sign)
  available in the top navigation.
- Hovercards: added new tooltips and hovercards to expose certain information for objects shown in UI.
  RhodeCode usernames, issues, pull-requests will have active hovercard logic that will
  load extra information about them and exposing them to users.
- Files: all readme files found in repository file browser will be now rendered, allowing having readme per directory.
- Search: expose line counts in search files information.
- Audit-logs: expose download user audit logs as JSON file.
- Users: added description field for users.
  Allows users to write a short BIO, or description of their role in the organization.
- Users: allow super-admins to change bound authentication type for users.
  E.g internal rhodecode accounts can be changed to ldap easily from user settings page.
- Pull requests: simplified the UI for display view, hide less important information and expose the most important ones.
- Pull requests: add merge check that detects WIP marker in title.
  Usually WIP in title means unfinished task that needs still some work, such marker will prevent accidental merges.
- Pull requests: TODO comments have now a dedicated box below reviewers to keep track
  of important TODOs that still need attention before review process is finalized.
- Pull requests: participants of pull request will receive an email about update of a
  pull requests with a small summary of changes made.
- Pull requests: change the naming from #NUM into !NUM.
  !NUM format is now parsed and linkified in comments and commit messages.
- Pull requests: pull requests which state is changing can now be viewed with a limited view.
- Pull requests: re-organize merge/close buttons and merge checks according to the new UI.
- Pull requests: update commits button allows a force-refresh update now using dropdown option.
- Pull requests: added quick filter to grid view to filter/search pull requests in a repository.
- Pull requests: closing a pull-request without a merge requires additional confirmation now.
- Pull requests: merge checks will now show which files caused conflicts and are blocking the merge.
- Emails: updated all generated emails design and cleanup the data fields they expose.
  a) More consistent UI for all types of emails. b) Improved formatting of plaintext emails
  c) Added reply link to comment type emails for quicker response action.


General
^^^^^^^

- Artifacts: don't show hidden artifacts, allow showing them via a GET ?hidden=1 flag.
  Hidden artifacts are for example comment attachments.
- UI: new commits page, according to the new design, which started on 4.17.X release lines
- UI: use explicit named actions like "create user" instead of generic "save" which is bad UX.
- UI: fixed problems with generating last change in repository groups.
  There's now a new logic that checks all objects inside group for latest update time.
- API: add artifact `get_info`, and `store_metadata` methods.
- API: allowed to specify extra recipients for pr/commit comments api methods.
- Vcsserver: set file based cache as default for vcsserver which can be shared
  across multiple workers saving memory usage.
- Vcsserver: added redis as possible cache backend for even greater performance.
- Dependencies: bumped GIT version to 2.23.0
- Dependencies: bumped SVN version to 1.12.2
- Dependencies: bumped Mercurial version to 5.1.1 and hg-evolve to 9.1.0
- Search: added logic for sorting ElasticSearch6 backend search results.
- User bookmarks: make it easier to re-organize existing entries.
- Data grids: hide pagination for single pages in grids.
- Gists: UX, removed private/public gist buttons and replaced them with radio group.
- Gunicorn: moved all configuration of gunicorn workers to .ini files.
- Gunicorn: added worker memory management allowing setting maximum per-worker memory usage.
- Automation: moved update groups task into celery task
- Cache commits: add option to refresh caches manually from advanced pages.
- Pull requests: add indication of state change in list of pull-requests and actually show them in the list.
- Cache keys: register and self cleanup cache keys used for invalidation to prevent leaking lot of them into DB on worker recycle
- Repo groups: removed locking inheritance flag from repo-groups. We'll deprecate this soon and this only brings in confusion
- System snapshot: improved formatting for better readability
- System info: expose data about vcsserver.
- Packages: updated celery to 4.3.0 and switch default backend to redis instead of RabbitMQ.
  Redis is stable enough and easier to install. Having Redis simplifies the stack as it's used in other parts of RhodeCode.
- Dependencies: bumped alembic to 1.2.1
- Dependencies: bumped amqp==2.5.2 and kombu==4.6.6
- Dependencies: bumped atomicwrites==1.3.0
- Dependencies: bumped cffi==1.12.3
- Dependencies: bumped configparser==4.0.2
- Dependencies: bumped deform==2.0.8
- Dependencies: bumped dogpile.cache==0.9.0
- Dependencies: bumped hupper==1.8.1
- Dependencies: bumped mako to 1.1.0
- Dependencies: bumped markupsafe to 1.1.1
- Dependencies: bumped packaging==19.2
- Dependencies: bumped paste==3.2.1
- Dependencies: bumped pastescript==3.2.0
- Dependencies: bumped pathlib2 to 2.3.4
- Dependencies: bumped pluggy==0.13.0
- Dependencies: bumped psutil to 5.6.3
- Dependencies: bumped psutil==5.6.5
- Dependencies: bumped psycopg2==2.8.4
- Dependencies: bumped pycurl to 7.43.0.3
- Dependencies: bumped pyotp==2.3.0
- Dependencies: bumped pyparsing to 2.4.2
- Dependencies: bumped pyramid-debugtoolbar==4.5.1
- Dependencies: bumped pyramid-mako to 1.1.0
- Dependencies: bumped redis to 3.3.8
- Dependencies: bumped sqlalchemy to 1.3.8
- Dependencies: bumped sqlalchemy==1.3.11
- Dependencies: bumped test libraries.
- Dependencies: freeze alembic==1.3.1
- Dependencies: freeze python-dateutil
- Dependencies: freeze redis==3.3.11
- Dependencies: freeze supervisor==4.1.0


Security
^^^^^^^^

- Security: fixed issues with exposing wrong http status (403) indicating repository with
  given name exists and we don't have permissions to it. This was exposed in the redirection
  logic of the global pull-request page. In case of redirection we also exposed
  repository name in the URL.


Performance
^^^^^^^^^^^

- Core: many various small improvements and optimizations to make rhodecode faster then before.
- VCSServer: new cache implementation for remote functions.
  Single worker shared caches that can use redis/file-cache.
  This greatly improves performance on larger instances, and doesn't trigger cache
  re-calculation on worker restarts.
- GIT: switched internal git operations from Dulwich to libgit2 in order to obtain better performance and scalability.
- SSH: skip loading unneeded application parts for SSH to make execution of ssh commands faster.
- Main page: main page will now load repositories and repositories groups using partial DB calls instead of big JSON files.
  In case of many repositories in root this could lead to very slow page rendering.
- Admin pages: made all grids use same DB based partial loading logic. We'll no longer fetch
  all objects into JSON for display purposes. This significantly improves speed of those pages in case
  of many objects shown in them.
- Summary page: use non-memory cache for readme, and cleanup cache for repo stats.
  This change won't re-cache after worker restarts and can be shared across all workers
- Files: only check for git_lfs/hg_largefiles if they are enabled.
  This speeds up fetching of files if they are not LF and very big.
- Vcsserver: added support for streaming data from the remote methods. This allows
  to stream very large files without taking up memory, mostly for usage in SVN when
  downloading large binaries from vcs system.
- Files: added streaming remote attributes for vcsserver.
  This change enables streaming raw content or raw downloads of large files without
  transferring them over to enterprise for pack & repack using msgpack.
  Msgpack has a limit of 2gb and generally pack+repack for ~2gb is very slow.
- Files: ensure over size limit files never do any content fetching when viewing such files.
- VCSServer: skip host verification to speed up pycurl calls.
- User-bookmarks: cache fetching of bookmarks since this is quite expensive query to
  make with joinedload on repos/repo groups.
- Goto-switcher: reduce query data to only required attributes for speedups.
- My account: owner/watched repos are now loaded only using DB queries.


Fixes
^^^^^

- Mercurial: move imports from top-level to prevent from loading mercurial code on hook execution for svn/git.
- GIT: limit sync-fetch logic to only retrieve tags/ and heads/ with default execution arguments.
- GIT: fixed issue with git submodules detection.
- SVN: fix checkout url for ssh+svn backend not having special prefix resulting in incorrect command shown.
- SVN: fixed problem with showing empty directories.
- OAuth: use a vendored version of `authomatic` library, and switch Bitbucket authentication to use oauth2.
- Diffs: handle paths with quotes in diffs.
- Diffs: fixed outdated files in pull-requests re-using the filediff raw_id for anchor generation. Fixes #5567
- Diffs: toggle race condition on sticky vs wide-diff-mode that caused some display problems on larger diffs.
- Pull requests: handle exceptions in state change and improve logging.
- Pull requests: fixed title/description generation for single commits which are numbers.
- Pull requests: changed the source of changes to be using shadow repos if it exists.
  In case of `git push -f` and rebase we lost commits in the repo resulting in
  problems of displaying versions of pull-requests.
- Pull requests: handle case when removing existing files from a repository in compare versions diff.
- Files: don't expose copy content helper in case of binary files.
- Registration: properly expose first_name/last_name into email on user registration.
- Markup renderers: fixed broken code highlight for rst files.
- Ui: make super admin be named consistently across ui.
- Audit logs: fixed search cases with special chars such as `-`.


Upgrade notes
^^^^^^^^^^^^^

- New Automation task. We've changed the logic for updating latest change inside repository group.
  New logic includes scanning for changes in all nested objects. Since this is a heavy task
  a new dedicated scheduler task has been created to update it automatically on a scheduled base.
  Please review in `admin > settings > automation` to enable this task.

- New safer encryption algorithm. Some setting values are encrypted before storing it inside the database.
  To keep full backward compatibility old AES algorithm is used.
  If you wish to enable a safer option set fernet encryption instead inside rhodecode.ini
  `rhodecode.encrypted_values.algorithm = fernet`

- Pull requests UI changes. We've simplified the UI on pull requests page.
  Please review the new UI to prevent surprises. All actions from old UI should be still possible with the new one.

- Redis is now a default recommended backend for Celery and replaces previous rabbitmq.
  Redis is generally easier to manage and install, and it's also very stable for usage
  in the scheduler/celery async tasks. Since we also recommend Redis for caches the application
  stack can be simplified by removing rabbitmq and replacing it with single Redis instance.

- Recommendation for using Redis as the new cache backend on vcsserver.
  Since Version 4.18.0 VCSServer has a new cache implementation for VCS data.
  By default, for simplicity the cache type is file based. We strongly recommend using
  Redis instead for better Performance and scalability
  Please review vcsserver.ini settings under:
  `rc_cache.repo_object.backend = dogpile.cache.rc.redis_msgpack`

- New memory monitoring for Gunicorn workers. Starting from 4.18 release a option was added
  to limit the maximum amount of memory used by a worker.
  Please review new settings in `[server:main]` section for memory management in both
  rhodecode.ini and vcsserver.ini::

    ; Maximum memory usage that each worker can use before it will receive a
    ; graceful restart signal 0 = memory monitoring is disabled
    ; Examples: 268435456 (256MB), 536870912 (512MB)
    ; 1073741824 (1GB), 2147483648 (2GB), 4294967296 (4GB)
    memory_max_usage = 0
