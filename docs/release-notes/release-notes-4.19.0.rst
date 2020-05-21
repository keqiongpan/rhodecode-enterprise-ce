|RCE| 4.19.0 |RNS|
------------------

Release Date
^^^^^^^^^^^^

- 2020-05-22


New Features
^^^^^^^^^^^^

- Pull requests: add information about changes in source repositories in pull-request show page.
  Fixes #5611, Fixes #5561
  Added new preview for size (commits/files) of PRs before opening, this is now based
  on the special logic that calculates common ancestor and has access to preview diff
  Store common ancestor in DB so updates of pull-requests are consistent
- Pull requests: fixed case for GIT repositories when a merge check failed due to
  merge conflicts the pull request wrongly reported missing commits.
  we're now searching for dangling commits in a repo that has them and cannot see them
  because of failed merge checks.
- Pull requests: allow filter displayed results by author
- Pull requests: added filters to my account pull requests page.
- Quick search: added ability to search for pull-requests using `pr:` prefix.
  Permissions are checked against the access to target repositories, and users
  can now search for pull request number, description or title.
- UI: replaced js prompts with sweet-alert prompts.
- SVN: bumped shipped SVN to 1.13.0 release.
- Integration Hooks: added new hooks for comments on pull requests and commits.
  Allows writing custom actions on top of commenting.
  E.g `@CI-BOT re-test` could trigger CI job to re-test a pull requests or commit.
  Added new rcextension hooks, Fixes #5583, and added examples on how to trigger CI build on certain comments.
- Exception tracker: added possibility to send notification email when server encountered an unhandled exception.
  new .ini file flag: `exception_tracker.send_email = false` and `exception_tracker.send_email_recipients =`
  can be set to enable this function.
- Mercurial: enable enhanced diffs for Mercurial that show context of changed functions inside the diff.
  This makes diff actually more consistent with how GIT backend shows them. Fixes #5614


General
^^^^^^^

- Pull requests: fixed small UI glitches in pull request view.
- System Info: Python packages now expose the package location info.
- Exceptions: don't report lookup errors as exceptions stored in the exception store.
  Those are regular not found problems that don't indicate any exceptional case
  also make the errors report nicer, not as KeyError, or generic Exception
- Exception tracker: store request info if available to track which URL caused an error.
- Integrations: handle new commenting events and optimize calls for Jira/Redmine
  Speed up issue fetching by optimizing how Jira/Redmine client behaves
  For redmine we don't iterate issues anymore which is *much* faster, and makes pushes with tickets faster.
- SVN: allow to specify any svn compatible version string not only hardcoded values.
  The new SVN code allows to specify this by numeric values now. e.g 1.13 etc.
  Fixes #5605.
- Emails: added `premailer` parsing for inline style formatting to make emails render
  nicer on all email clients.
- Repositories: switched repo type selector to radio buttons and preserve order of
  enabled backends inside .ini files.
- Repositories: show recommendation for updating hooks if they are outdated.
- Files: add pre-commit checks on file edit/delete/add operations. This prevents
  loosing content while editing when repositories changes during those operations.
  Fixes #5607.
- Files: changed the copy path label to indicate we're actually copying only the path.
  Added copy permalink helper to copy the url quickly. Fixes #5602
- LDAP: updated ldap plugin to help with debug and support by extending logging and
  improving error messages.
- LDAP: fixed example LDAPs port.
- Dependencies: bump redmine client.
- Dependencies: bumped bleach==3.1.3
- Dependencies: bumped webtest==2.0.34
- Dependencies: bumped packaging==20.3
- Dependencies: bumped pyparsing==2.4.7
- Dependencies: bumped sqlalchemy==1.3.15
- Dependencies: bumped hupper==1.10.2
- Dependencies: bumped alembic==1.4.2
- Dependencies: bumped wcwidth==0.1.9
- Dependencies: bumped python-ldap==3.2.0
- Dependencies: bumped importlib-metadata==1.5.0
- Dependencies: bumped redis==3.4.1
- Dependencies: bumped importlib-metadata==1.6.0
- Dependencies: bumped pytz==2019.3
- Dependencies: bumped paste==3.4.0
- Dependencies: bumped weberror==0.13.1
- Dependencies: bumped pyparsing==2.4.6
- Dependencies: bumped ipdb==0.13.2
- Dependencies: bumped pastedeploy==2.1.0
- Dependencies: bumped docutils==0.16.0
- Dependencies: bumped pyramid-debugtoolbar==4.6.1
- Dependencies: bumped gevent==1.5.0
- Dependencies: bumped psutil==5.7.0


Security
^^^^^^^^

- Logging: expose usernames in the logs for each request made to RhodeCode.
  This enables auditing capabilities for all actions against the web interface.
- Users: increased security on the way we're displaying authentication tokens.
  We don't expose all on single page. Request needs a validation before viewing of each token.
- Logging: added some nicer logging for file path ACL checks.
- Audit Log: extend the commit api data with references to commit_id or pull_request_id.
  This allows tracking those in the audit-logs.


Performance
^^^^^^^^^^^

- Exception Tracker: optimized the check for smtp_server before doing heavy lifting
  of exception email sending.
- Auth: enabled cache flags for fetching ACL ids.
  Those are now safe to cache since we have a proper cache invalidation logic for
  permissions of users, for lots of repo this makes our goto switcher much much faster.
- Application: use simpler way to extract default_user_id, this will be now registered
  at server boot, reducing number of times we fetch this from database.
- Pull requests: changed reviewers metadata function for optimizing the diff calculations.
  We're now doing a single request to calculate reviewers and diff preview instead of twice like before.


Fixes
^^^^^

- GIT: fixed readme searcher for Git repositories using libgit2 and non-ascii directories.
- Full text search: fixed error while highlighting special search terms e.g 'enabled \= '
- Full text search: fixed problems with non-ascii files indexing.
- Diffs: improve text on unresolved comments attached to files that no longer exist in the review.
  Fixes #5615.
- Auth: fixed generation of authomatic secrets for new plugins.
- Auth: failsafe github auth if it doesn't provide full name for users.
- Permissions: fixed problem with permissions changes from permission page due to missing cache flush.
  This caused certain permission changed be visible after some time of the edit.
  We now ensure *all* caches used for permissions are properly flushed right after the change.
- SVN: explicitly specify tunnel-user to properly map rhodecode username on svn commit
  via SSH backend. Fixes #5608.
- SVN: fixed case of wrong extracted repository name for SSH backend. In cases
  where we commit to a nested subdirs SVN reported the access path with the subdir paths in it.
  We couldn't then match that extended name into proper rhodecode repository for ACL checks.
  Current implementation gives an slight overhead as we have to lookup all repositories.
  Fixes #5606
- SVN: fixed problem with special characters inside subdirectories.
- SVN: fixed SVN refs switcher on files that used old format of diff url. Fixes #5599, #5610
- Search: remove excessive quoting on search pagination. Fixes #5604
- File browser: fixed the repo switcher `?at=` flag being lost when walking on the file tree.
- File browser: fixed unicode problems on image preview, and make images center, no-stretch.
- DB migrations: fixed db migrate for latest sqlite version.
- Feed generator: fixed missing utc definition that could cause server 500 error.


Upgrade notes
^^^^^^^^^^^^^

- RhodeCode has been tested on CentOS/RHEL 8 and we added those as officially supported platforms.
- This release introduces lots of optimizations and changes how the pull requests reviewers,
  and diff preview is made. We cut the pull request creation time by 50%.
  Please look closer to this new logic na report any potential problems with this change.
- SVN was bumped to 1.13 version.