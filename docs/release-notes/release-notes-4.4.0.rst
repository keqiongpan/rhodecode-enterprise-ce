|RCE| 4.4.0 |RNS|
-----------------

Release Date
^^^^^^^^^^^^

- 2016-09-16


General
^^^^^^^

- UI: introduced Polymer webcomponents into core application. RhodeCode will
  be now shipped together with Polymer framework webcomponents. Most of
  dynamic UI components that require large amounts of interaction
  will be done now with Polymer.
- live-notifications: use rhodecode-toast for live notifications instead of
  toastr jquery plugin.
- Svn: moved svn http support out of labs settings. It's tested and stable now.


New Features
^^^^^^^^^^^^

- Integrations: integrations can now be configure on whole repo group to apply
  same integrations on multiple projects/groups at once.
- Integrations: added scopes on integrations, scopes are: Global,
  Repository Group (with/without children), Repositories, Root Repositories Only.
  It will allow to configure exactly which projects use which integrations.
- Integrations: show branches/commits separately when posting push events
  to hipchat/slack, fixes #4192.
- Pull-requests: summary page now shows update dates for pull request to
  easier see which one were receantly updated.
- UI: hidden inline comments will be shown in side view when browsing the diffs
- Diffs: added inline comments toggle into pull requests diff view. #2884
- Live-chat: added summon reviewers functionality. You can now request
  presence from online users into a chat for collaborative code-review.
  This requires channelstream to be enabled.
- UX: added a static 502 page for gateway error. Once configured via
  Nginx or Apache it will present a custom RhodeCode page while
  backend servers are offline. Fixes #4202.


Security
^^^^^^^^

- Passwords: forced password change will not allow users to put in the
  old password as new one.


Performance
^^^^^^^^^^^

- Vcs: refactor vcs-middleware to handle order of .ini file backends in
  detection of vcs protocol. Detection ends now on first match and speeds
  overall transaction speed.
- Summary: Improve the algorithm and performance of detection README files
  inside summary page. In some cases we reduced cold-cache time from 50s to 1s.
- Safari: improved speed of large diffs on Safari browser.
- UX: remove position relative on diff td as it causes very slow
  rendering in browsers.

Fixes
^^^^^

- UX: change confirm password widget to have spacing between the fields to
  match rest of ui, fixes: #4200.
- UX: show multiple tags/branches in changelog/summary instead of
  truncating them.
- My-account: fix test notifications for IE10+
- Vcs: change way refs are retrieved for git so same name branch/tags and
  remotes can be supported, fixes #298.
- Lexers: added small extensions table to extend syntax highlighting for file
  sources. Fixes #4227.
- Search: fix bug where file path link was wrong when the repository name was
  in the file path, fixes #4228
- Fixed INT overflow bug
- Events: send pushed commits always in the correct in order.
