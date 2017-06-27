|RCE| 4.8.0 |RNS|
-----------------

Release Date
^^^^^^^^^^^^

- 2017-06-30


New Features
^^^^^^^^^^^^

- Code Review: added new reviewers logic. This features now is Common Criteria
  compatible and allows to define Mandatory (non-removable) reviewers.
  In addition new options were added to forbid adding new reviewers or forbid
  author of commits or the pull request itself to be a reviewer of the code.
- Audit logs: introducing new audit logs tracking most important actions in
  the system. Admins can track important events such as deletion of resources,
  permissions changes, user groups changes. Each event tracks users with his
  IP and user agent.
- Mercurial: enabled evolve extensions. Each repository can be now configured
  to support evolve, commit phases, and evolve state are also shown in
  commit and changelog views.
- VCS: expose newly pushed bookmarks or branches as quick links to open a
  pull request on client output. Allows easier pull request creation via CLI.


General
^^^^^^^

- Core: ported many views into pure pyramid code with python3.6 compatibility.
  Now almost 80% of the code is ported, and future ready. It's our ongoing
  effort to allow support for modern python version.
- Comments: show author tag in pull request comments to easily
  discover the author of changes in discussions.
- Files: allow specifying custom filename for uploaded files via web interface.
- Pull requests: changed who is allowed to close a pull request. Now it's only
  super-admin, owner or person who can merge.
  Before it was every reviewer can close. Which really doesn't make sense.
- Users: show that user is disabled when editing his properties.
- Integrations: expose user_id, and username in Webhook integration
  templates arguments.
- Integrations: exposed extra repo variables in template arguments of
  Webhook integration.
- Login: add link when using external auth to make it easier to login
  using oauth providers, such as Google or Github.
- Maintenance: added svn verify command to tasks to be able to verify the
  filesystem and repo formats from web interface. Allows much easier tracking
  of incompatible filesystem storage of subversion repositories.
- Events: expose permalink urls for pull requests, and repositories.
  Permalink url should provide a non-changeable url that can be used in
  external system.
- Svn: increase possibility to specify compatibility to pre 1.9 version.


Security
^^^^^^^^

- security(high): fixed possibility to delete other users inline comments
  for users who were repository admins.
- security(med): fixed XSS inside the tooltip for author string.
- security(med): fixed stored XSS in notifications inbox.
- security(med): use custom writer for RST rendering to prevent injection of javascript: tags.
- security(med): escape flash messaged VCS errors to prevent reflected XSS attacks.
- security(low): use 404 instead of 403 code on permission decorator to
  prevent brute force resource discovery attacks.
- security(low): fixed self XSS inside autocomplete files view.
- security(low): fixed self Xss inside repo strip view.
- security(low): fixed self Xss inside the email add functionality.
- security(none): use new safe escaped user attributes across the application.
  Will prevent all possible XSS attack vectors from user stored attributes.
  This specially can come from external authentication systems which doesn't
  validate the data.


Performance
^^^^^^^^^^^




Fixes
^^^^^

- Pull requests: make sure we process comments in the order of IDS when
  linking them. In some edge cases it could lead to comments not displaying
  correctly.
- Emails: fixed newlines in email templates that can break email sending code.
- Markdown: fixed hr and strong tags styling.
- Notifications: fixed problem with 500 errors on non-numeric entries in url.
- API: use simple schema validator to be consistent how we validate between
  API and web views for create user and create user_group calls.
- Users: fixed problem with personal repo group wasn't shown for disabled users.
- Oauth: improve Google extraction of first/last name from returned data.


Upgrade notes
^^^^^^^^^^^^^


- API: the `update_pull_request` method will no longer support a close action.
  Users should use the existing `close_pull_request` method which allows
  specifying a message and status while closing a pull request.