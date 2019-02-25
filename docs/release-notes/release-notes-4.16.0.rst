|RCE| 4.16.0 |RNS|
------------------

Release Date
^^^^^^^^^^^^

- 2019-02-15


New Features
^^^^^^^^^^^^


- Full-text search: added support for ElasticSearch 6.X (ES6)
- Full-text search: Expose a quick way to search within repository groups using ES6.
- Full-text search: Add quick links to broaden/narrow search scope to repositories or
  repository groups from global search.
- Full-text search: ES6 backend adds new highlighter, and search markers for better UX when searching.
- Full-text search: ES6 backend has enabled advanced `query string syntax`
  adding more search and filtering capabilities.
- Full-text search: ES6 engine will now show added information where available such as line numbers file size.
- Files: added option to use highlight marker to show keywords inside file source. This
  is used now for ES6 backend extended highlighting capabilities
- Artifacts (beta): EE edition exposes new feature called storage_api this allows storing
  binary files outside of Version Control System, but in the scope of a repository or group.
  This will soon become an Artifacts functionality available in EE edition.
- User bookmarks: added customizable Bookmark links for logged in users. RhodeCode users can now optionally
  set upto 10 favorites links to repositories, repository groups, CI linkes, or any other generic links.
- Authentication: introduced `User restriction` and `Scope restriction` for RhodeCode authentication plugins.
  Admins can limit usage of RhodeCode plugins to super-admins user types, and usage in Web, or VCS protocol only.
  This is mostly to help to migrate users to SAML, keeping the super-admins to manage instances via local-logins,
  and secondly to force usage of AuthenticationTokens instead of re-using same credentials for
  WEB and VCS authentication.
- API: added basic upload API for the storage_api. It's possible to store files using internal
  API. This is a start for attachments upload in RhodeCode.
- API: added store_exception_api for remote exception storage. This is used by a new
  indexer that will report any problems back into the RhodeCode instance in case of indexing problems.
- API: added function to fetch comments for a repository.
- Quick search: improve the styling of search input and results.
- Pull requests: allowed to select all forks and parent forks of target repository in creation UI.
  This is a common workflow supported by GitHub etc.


General
^^^^^^^

- Users/Repositories/Repository groups: expose IDs of those objects in advanced views.
  Useful for API calls or usage in ishell.
- UI: moved repo group select next to the name as it's very relevant to each other.
- Pull requests: increase the stability of concurrent pull requests created.
- Pull requests: introduced operation state for pull requests to prevent from
  locks during merge/update operations in concurrent busy environments.
- Pull requests: ensure that merge response provide more details about failed operations.
- UI / Files: expose downloads options onto files view similar as in summary page.
- Repositories: show hooks version and update link in the advanced section of repository page.
- Events: trigger 'review_status_change' in all cases when reviewers are changed
  influencing review status.
- Files: display submodules in a sorted way, equal to how Directories are sorted.
- API: fetching all pull-requests now sorts the results and exposed a flag to show/hide
  the merge result state for faster result fetching.
- API: merge_pull_request expose detailed merge message in the merge operation
  next to numeric merge response code.
- API: added possibility to specify owner to create_pull_request API.
- SSH: Added ability to disable server-side SSH key generation to enforce users
  generated SSH keys only outside of the server.
- Integrations: allow PUT method for WebHook integration.
- Dependencies: bumped git to 2.19.2 release.
- Dependencies: dropped pygments-markdown-lexer as it's natively supported by pygments now.
- Dependencies: bumped pyramid to 1.10.1
- Dependencies: bumped pastedeploy to 2.0.1
- Dependencies: bumped pastescript to 3.0.0
- Dependencies: bumped pathlib2 to 2.3.3
- Dependencies: bumped webob to 1.8.4
- Dependencies: bumped iso8601 to 0.1.12
- Dependencies: bumped more-itertools to 5.0.0
- Dependencies: bumped psutil to 5.4.8
- Dependencies: bumped pyasn1 to 0.4.5
- Dependencies: bumped pygments to 2.3.1
- Dependencies: bumped pyramid-debugtoolbar to 4.5.0
- Dependencies: bumped subprocess32 to 3.5.3
- Dependencies: bumped supervisor to 3.3.5
- Dependencies: bumped dogpile.cache to 0.7.1
- Dependencies: bumped simplejson to 3.16.0
- Dependencies: bumped gevent to 1.4.0
- Dependencies: bumped configparser to 3.5.1


Security
^^^^^^^^

- Fork page: don't expose fork origin link if we don't have permission to access this repository.
  Additionally don't pre-select such repository in pull request ref selector.
- Security: fix possible XSS in the issue tracker URL.
- Security: sanitize plaintext renderer with bleach, preventing XSS in rendered html.
- Audit logs: added audit logs for API permission calls.


Performance
^^^^^^^^^^^

- Summary page: don't load repo size when showing expanded information about repository.
  Size calculation needs to be triggered manually.
- Git: use rev-list for fetching last commit data in case of single commit history.
  In some cases, it is much faster than previously used git log command.


Fixes
^^^^^

- Installer: fixed 32bit package builds broken in previous releases.
- Git: use iterative fetch to prevent errors about too many arguments on
  synchronizing very large repositories.
- Git: pass in the SSL dir that is exposed from wire for remote GIT commands.
- LDAP+Groups: improve logging, and fix the case when extracting group name from LDAP
  returned nothing. We should warn about that, but not FAIL on login.
- Default reviewers: fixed submodule support in picking reviewers from annotation for files.
- Hooks: handle non-ascii characters in hooks new pull-requests open template.
- Diffs: fixed missing limited diff container display on over-size limit diffs.
- Diffs: fixed 500 error in case of some very uncommon diffs containing only Unicode characters.
- Repositories: handle VCS backend unavailable correctly in advanced settings for the repository.
- Remap & rescan: prevent empty/damaged repositories to break the remap operation.
- Visual: fixed show revision/commit length settings.
- Mercurial submodules: only show submodule in the path that it belongs too.
  Before even submodules from root node were shown in subdirectories.
- UI/Files: fixed icons in file tree search.
- WebHook integration: quote URL variables to prevent URL errors with special chars
  like # in the title.
- API: pull-requests, fixed invocation of merge as another user.
- VCS: limit fd leaks on subprocessio calls.
- VCS: expose SSL certificate path over the wire to the vcsserver, this solves some
  remote SSL import problems reported.


Upgrade notes
^^^^^^^^^^^^^

This release brings the new Full-text search capabilities using ElasticSearch 6.
If you use Elastic Search backend a backward compatibility mode is enabled and
ElasticSearch backend defaults to previously used ElasticSearch 2.

To use new features a full index rebuild is required, in addition ```--es-version=6``` flag
needs to be used with indexer and ```search.es_version = 6``` should be set in rhodecode.ini

Additionally new mapping format is available for the indexer that has additional capabilities
for include/exclude rules. Old format should work as well, but we encourage to
generate a new mapping.ini file using rhodecode-index command, and migrate your repositories
to the new format.

Please refer to the :ref:`indexing-ref` documentation for more details.

