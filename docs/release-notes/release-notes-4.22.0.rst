|RCE| 4.22.0 |RNS|
------------------

Release Date
^^^^^^^^^^^^

- 2020-10-12


New Features
^^^^^^^^^^^^

- Reviewers: added observers as another role for reviewers.
  Observers is a role that doesn't require voting, but still gets notified about
  PR and should participate in review process.
- Issue trackers: implemented more sophisticated ticket data extraction based on
  advanced regex module. This allows using ticket references without false positives
  like catching ticket data in an URL.
- Channelstream: Notification about updates and comments now works via API, and both
  Pull-requests and individual commits.


General
^^^^^^^

- Data tables: unified tables look for main pages of rhodecode repo pages.
- Users: autocomplete now sorts by matched username to show best matches first.
- Pull requests: only allow actual reviewers to leave status/votes in order to not
  confuse others users about voting from people who aren't actual reviewers.

Security
^^^^^^^^



Performance
^^^^^^^^^^^

- Default reviewers: optimize diff data, and creation of PR with advanced default reviewers
- default-reviewers: diff data should load more things lazy for better performance.
- Pull requests: limit the amount of data saved in default reviewers data for better memory usage
- DB: don't use lazy loaders on PR related objects, to optimize memory usage on large
  Pull requests with lots of comments, and commits.

Fixes
^^^^^

- Quick search bar: fixes #5634, crash when search on non-ascii characters.
- Sidebar: few fixes for panel rendering of reviewers/observers for both commits and PRS.

Upgrade notes
^^^^^^^^^^^^^

- Scheduled feature release.

