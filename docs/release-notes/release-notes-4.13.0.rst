|RCE| 4.13.0 |RNS|
------------------

Release Date
^^^^^^^^^^^^

- 2018-09-05


New Features
^^^^^^^^^^^^

- Branch permissions: new set of permissions were added to control branch modification.
  There are 4 basic permissions that can be set for branch names/branch patterns:
  * no-access (any modification for given branch is forbidden)
  * web-merge (modify branch by web based PR merge)
  * push (only non-forced modification on branch are allowed)
  * forced push (all modification to branch are allowed)
  Available in EE edition only.
- Unified search and repo-switcher: a new persistent search box is now present allowing
  to search for repositories, repository groups, commits (using full text search),
  users, user-groups. Replaces redundant quick-filters/repo switcher.
- Default Reviewers: added possibility to match against regex based pattern as
  alternative syntax to glob which didn't handle all the cases.
- Built-in Error tracker: added new exception tracking capability. All errors are now
  tracked and stored. This allows instance admins to see potential problems without
  access to the machine and logs.
- User Groups: each user group which users have access to expose public profile link.
  It's possible to view the members of a group before attaching it to any resource.
- New caching framework: existing Beaker cache was completely replaced by dogpile.cache
  library. This new cache framework in addition to solving multiple
  performance/reliability problems of Beaker is used to cache permissions tree.
  This gives huge performance boosts for very large and complex permission trees.
- Pull Requests: description field is now allowed to use a RST/Markdown syntax.
- SVN: added support for SVN 1.10 release line.


General
^^^^^^^

- Google: updated google auth plugin with latest API changes.
- Frontend: Switched to Polymer 2.0.
- Events: added a default timeout for operation calling the endpoint url, so
  they won't block forever.
- SQLAlchemy: allow DB connection ping/refresh using dedicated flag from .ini file.
  `sqlalchemy.db1.ping_connection = true`
- Pull Requests: added option to force-refresh merge workspace in case of problems.
  Adding GET param `?force_refresh=1` into PR page triggers the refresh.
- Pull Requests: show more info about version of comment vs latest version.
- Diffs: skip line numbers during copy from a diff view.
- License: use simple cache to read license info.
  Due to the complex and expensive encryption, this reduces requests time by ~10ms.
- Debug: add new custom logging to track unique requests across systems.
  Allows tracking single requests in very busy system by unique ID added into logging system.
- Configuration: .ini files now can replace a special placeholders e.g "{ENV_NAME}"
  into a value from the ENVIRONMENT. Allows easier setup in Docker and similar.
- Backend: don't support vcsserver.scm_app anymore, now it uses http even if scm_app
  is specified.
- Repositories: re-order creation/fork forms for better UX and consistency.
- UI: Add the number of inactive users in _admin/users and _admin/user_groups
- UX: updated registration form to better indicate what is the process of binding a
  RhodeCode account with external one like Google.
- API: pull-requests allow automatic title generation via API
- VCSServer: errors: use a better interface to track exceptions and tracebacks.
- VCSServer: caches: replaced beaker with dogpile cache.
- GIT: use GIT_DISCOVERY_ACROSS_FILESYSTEM for better compatibility on NFS servers.
- Dependencies: bumped mercurial to 4.6.2
- Dependencies: bumped evolve to 8.0.1
- Dependencies: bumped hgsubversion to 1.9.2
- Dependencies: bumped git version to 2.16.4
- Dependencies: bumped SVN to 1.10.2
- Dependencies: added alternative pymysql drivers for mysql
- NIX: updated to 18.03 nix packages, now shipped with python 2.7.15
  release and multiple other new libraries.


Security
^^^^^^^^

- Mercurial: general protocol security updates.
  * Fixes Mercurial's CVE for lack of permissions checking on mercurial batch commands.
  * Introduced more strict checks for permissions, now they default to push instead of pull.
  * Decypher batch commands and pick top-most permission to be required.
  * This follows changes in Mercurial CORE after 4.6.1 release.
- Fixed bug in bleach sanitizer allowing certain custom payload to bypass it. Now
  we always fails if sanitizing fails. This could lead to stored XSS
- Fixed stored XSS in binary file rendering.
- Fixed stored XSS in repo forks datagrid.


Performance
^^^^^^^^^^^

- Permissions: Permission trees for users and now cached, after calculation.
  This reduces response time for some pages dramatically.
  In case of any permission changes caches are invalidated.
- Core: new dogpile.cache based cache framework was introduced, which is faster than
  previously used Beaker.


Fixes
^^^^^

- Audit Logs: store properly IP for certain events.
- External Auth: pass along came_from into the url so we get properly
  redirected back after logging using external auth provider.
- Pull Requests: lock submit on pull request to prevent double submission on a fast click.
- Pull Requests: fixed a case of unresolved comments attached to removed file in pull request.
  That prevented from closing it.
- Pull Requests: use numeric repo id for creation of shadow repos. Fixes a problem
  when repository is renamed during PR lifetime.
- API: fixed creation of a pull request with default reviewer rules.
- Default Reviewers: fixed voting rule calculation on user group.
- Pull Requests: in GIT use force fetch and update for target ref.
  This solves a case when in PR a target repository is force updated (by push force)
  and is out of sync.
- VCSServer: detect early potential locale problem, and fallback to LC_ALL=C,
  instead of crashing vcsserver.
- Pull Requests: use a safer way of destroying shadow repositories.
  Fixes some problems in NFS storage and big repositories


Upgrade notes
^^^^^^^^^^^^^

- The direct backend `vcsserver.scm_app` is not supported anymore. This backed was
  already deprecated some time ago. Now it will use `http` mode even if scm_app is
  specified. Please contact us in case you still use it, and not sure how to upgrade.
- New dogpile cache settings are not ported to converted .ini. If users want to do
  adjustments please copy the settings over dogpile cache section from a newly
  generated rhodecode.template.ini file. This file is stored next to rhodecode.ini
- SVN 1.10.2 was introduced in this release. Please make sure to update your
  mod_dav to the same version for best compatibility.
