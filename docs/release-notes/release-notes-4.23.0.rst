|RCE| 4.23.0 |RNS|
------------------

Release Date
^^^^^^^^^^^^

- 2020-11-20


New Features
^^^^^^^^^^^^

- Comments: introduced new draft comments.

  * drafts are private to author
  * not triggering any notifications
  * sidebar doesn't display draft comments
  * They are just placeholders for longer review.

- Comments: when channelstream is enabled, comments are pushed live, so there's no
  need to refresh page to see other participant comments.
  New comments are marker in the sidebar.

- Comments: multiple changes on comments navigation/display logic.

  * toggle icon is smarter, open/hide windows according to actions. E.g commenting opens threads
  * toggle are mor explicit
  * possible to hide/show only single threads using the toggle icon.
  * new UI for showing thread comments

- Reviewers: new logic for author/commit-author rules.
  It's not possible to define if author or commit author should be excluded, or always included in a review.
- Reviewers: no reviewers would now allow a PR to be merged, unless review rules require some.
  Use case is that pr can be created without review needed, maybe just for sharing, or CI checks
- Pull requests: save permanently the state if sorting columns for pull-request grids.
- Commit ranges: enable combined diff compare directly from range selector.


General
^^^^^^^

- Authentication: enable custom names for auth plugins. It's possible to name the authentication
  buttons now for SAML plugins.
- Login: optimized UI for login/register/password reset windows.
- Repo mapper: make it more resilient to errors, it's better it executes and skip certain
  repositories, rather then crash whole mapper.
- Markdown: improved styling, and fixed nl2br extensions to only do br on new elements not inline.
- Pull requests: show pr version in the my-account and repo pr listing grids.
- Archives: allowing to obtain archives without the commit short id in the name for
  better automation of obtained artifacts.
  New url flag called `?=with_hash=1` controls this
- Error document: update info about stored exception retrieval.
- Range diff: enable hovercards for commits in range-diff.


Security
^^^^^^^^



Performance
^^^^^^^^^^^

- Improved logic of repo archive, now it's much faster to run archiver as VCSServer
  communication was removed, and job is delegated to VCSServer itself.
- Improved VCSServer startup times.
- Notifications: skip double rendering just to generate email title/desc.
  We'll re-use those now for better performance of creating notifications.
- App: improve logging, and remove DB calls on app startup.


Fixes
^^^^^

- Login/register: fixed header width problem on mobile devices
- Exception tracker: don't fail on empty request in context of celery app for example.
- Exceptions: improved reporting of unhandled vcsserver exceptions.
- Sidebar: fixed refresh of TODOs url.
- Remap-rescan: fixes #5636 initial rescan problem.
- API: fixed SVN raw diff export. The API method was inconsistent, and used different logic.
  Now it shares the same code as raw-diff from web-ui.


Upgrade notes
^^^^^^^^^^^^^

- Scheduled feature release.
  Please note that now the reviewers logic changed a bit, it's possible to create a pull request
  Without any reviewers initially, and such pull request doesn't need to have an approval for merging.
