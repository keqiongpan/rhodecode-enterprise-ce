|RCE| 4.3.0 |RNS|
-----------------

Release Date
^^^^^^^^^^^^

- 2016-08-12


General
^^^^^^^

- Subversion: detect requests also based on magic path.
  This adds subversion 1.9 support for SVN backend.
- Summary/changelog: unified how data is displayed for those pages.
    * use consistent order of columns
    * fix the link to commit status
    * fix order of displaying comments
- Live-chat: refactor live chat system for code review based on
  latest channelstream changes.
- SVN: Add template to generate the apache mod_dav_svn config for all
  repository groups. Repository groups can now be automatically mapped to be
  supported by SVN backend. Set `svn.proxy.generate_config = true` and similar
  options found inside .ini config.
- Readme/markup: improved order of generating readme files. Fixes #4050
    * we now use order based on default system renderer
    * having multiple readme files will pick correct one as set renderer
- Api: add a max_file_bytes parameter to get_nodes so that large files
  can be skipped.
- Auth-ldap: added flag to set debug mode for LDAP connections.
- Labs: moved rebase-merge option from labs settings into VCS settings.
- System: send platform type and version to upgrade endpoint when checking
  for new versions.
- Packaging: update rhodecode-tools from 0.8.3 to 0.10.0
- Packaging: update codemirror from 5.4.0 to 5.11.0
- Packaging: updated pygments to 2.1.3
- Packaging: bumped supervisor to 3.3.0
- Packaging: bumped psycopg2 to 2.6.1
- Packaging: bumped mercurial to 3.8.4


New Features
^^^^^^^^^^^^

- Integrations: created new event based integration framework.
  Allows to configure global, or per repo: Slack, Hipchat, Webhooks, Email
  integrations. This also deprecated usage of rcextensions for those.
- Integrations (EE only): added smart commits for Jira and Redmine with
  ability to map keywords into issue tracker actions.
  `Fixes #123 -> resolves issues`, `Closes #123 -> closes issue` etc.
- Markdown: added improved support for Github flavored markdown.
- Labs: enable labs setting by default. Labs are new experimental features in
  RhodeCode that can be used to test new upcomming features.
- Api: Add api methods to get/set repository settings, implements #4021.
- Gravatars: commit emails are now displayed based on the actual email
  used inside commit rather then the main one of associated account
  inside RhodeCode, #4037.
- Emails: All emails got new styling. They look now consistent
  to UI of application. We also added bunch of usefull information into
  email body, #4087.
- Pull requests: add show/hide comment functionality inside diffs, #4106.
- Notifications: added real-time notifications with via channelstream
  about new comments when reviewing the code. Never miss someone replies
  onto comments you submitted while doing a code-review.


Security
^^^^^^^^

- Api: make `comment_commits` api call have consistent permissions
  with web interface.
- Files: fixes display of "Add File" button missing or present despite
  permissions, because of cached version of the page was rendered, fixes #4083.
- Login/Registration: fixed flash message problem on login/registration
  pages, fixes #4043.
- Auth-token: allow other authentication types to use auth-token.
  Accounts associated with other types like LDAP, or PAM can
  now use auth-tokens to authenticate via RhodeCode.


Performance
^^^^^^^^^^^

- Core: made all RhodeCode components gevent compatible. RhodeCode can now make
  use of async workers. You can handle dozens of concurrent operations using a
  single worker. This works only with new HTTP backend.
- Core: added new very efficient HTTP backend can be used to replace pyro4.
- Core: Set 'gzip_responses' to false by default. We no longer require any
  gzip computations on backed, thus speeding up large file transfers.
- UI: optimized events system for JavaScript to boost performance on
  large html pages.
- VCS: moved VCSMiddleware up to pyramid layer as wrapper around pylons app.
  Skips few calls, and allows slightly faster clones/pulls and pushes.


Fixes
^^^^^

- VCS: add vcsserver cache invalidation to mercurial backend.
  Fixes multi-process problems after Mercurial 3.8.X release with server
  side merges.
- VCS: clear caches on remap-and-rescan option.
- VCS: improved logic of updating commit caches in cases of rebases.
- Caches: Add an argument to make the cache context thread scoped. Brings
  support to gevent compatible handling.
- Diff2way: fixed unicode problem on non-ascii files.
- Full text search: whoosh schema uses now bigger ints, fixes #4035
- File-browser: optimized cached tree calculation, reduced load times by
  50% on complex file trees.
- Styling: #4086 fixing bug where long commit messages did not wrap in file view.
- SVN: Ignore the content length header from response, fixes #4112.
  Fixes the "svn: E120106: ra_serf: The server sent a truncated HTTP response body."
- Auth: Fix password_changed function, fixes #4043.
- UI/tables: better message when tables are empty #685 #1832.
- UX: put gravatar and username together in user list #3203.
- Gists: use colander schema to validate input data.
    * brings consistent validation acros API and web
    * use nicer and stricter schemas to validate data
    * fixes #4118
- Appenlight: error reporting can now also report VCSMiddleware errors.
- Users: hash email key for User.get_by_email() fixes #4132
