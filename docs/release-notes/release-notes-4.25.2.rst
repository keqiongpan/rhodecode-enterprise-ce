|RCE| 4.25.2 |RNS|
------------------

Release Date
^^^^^^^^^^^^

- 2021-04-14


New Features
^^^^^^^^^^^^



General
^^^^^^^

- Comments: refresh on draft sidebar on draft submit.
- Vcsserver: log exceptions into the logs
- Archiving: make it explicit archiving a repo is irreversible.
- My-account: updated bookmarks UX
- Pull requests: added awaiting my review filter for users pull-requests.
  Additionally the awaiting my review now properly filters pull requests that have no review votes on them.


Security
^^^^^^^^



Performance
^^^^^^^^^^^



Fixes
^^^^^

- Draft comments: fixed logic in toggle all draft for submit.
- Draft comments: when submitting edited drafts also clear the history to prevent DB problems.
- Mercurial: fixed a case of lookup branches that had 40 characters in length.
- Gists: block id input for public gists.
- Pull requests: fixed problems with unicode characters in branches.
- Pull requests: small ui fix for grid.
- Summary: fixed ui on summary page for non-admins.
  The setup instructions were broken if user had no write permissions.
- Users: make user data loading more resilient to errors.


Upgrade notes
^^^^^^^^^^^^^

- Scheduled release addressing problems in 4.25.X releases.
