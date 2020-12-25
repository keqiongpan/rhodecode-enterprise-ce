|RCE| 4.23.2 |RNS|
------------------

Release Date
^^^^^^^^^^^^

- 2020-12-06


New Features
^^^^^^^^^^^^



General
^^^^^^^

- Repo extra keys: fixed some texts to improve UI.


Security
^^^^^^^^



Performance
^^^^^^^^^^^

- Core: speed up cache loading on application startup.


Fixes
^^^^^

- Diffs: added scroll down/scroll up helper. Fixes #5643
- Diffs: fixed diff rendering when a common ancestor was a different commit than the source of changes.
- Commits / changelog: small fixes from found problems.
- Comments: side-bar comments hover also shows an ID of comment now.
- Comments: make dismiss less prominent, and text only to not mix icons/text together.
- Comments: UX improvements for comment buttons.
- Reviewers: small ui fixes for display of review rules, and added new reviewer entries.
- Pull-requests: fixed source/target in PR creation, affecting how we load default reviewers based on branches.


Upgrade notes
^^^^^^^^^^^^^

- Un-scheduled release addressing problems in 4.23.X releases.
