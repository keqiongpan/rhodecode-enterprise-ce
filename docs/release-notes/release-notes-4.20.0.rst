|RCE| 4.20.0 |RNS|
------------------

Release Date
^^^^^^^^^^^^

- 2020-07-20


New Features
^^^^^^^^^^^^

- Comments: users can now edit comments body.
  Editing is versioned and all older versions are kept for auditing.
- Pull requests: changed the order of close-branch after merge,
  so branch heads are no longer left open after the merge.
- Diffs: added diff navigation to improve UX when browsing the full context diffs.
- Emails: set the `References` header for threading in emails with different subjects.
  Only some Email clients supports this.
- Emails: added logic to allow overwriting the default email titles via rcextensions.
- Markdown: support summary/details tags to allow setting a link with expansion menu.
- Integrations: added `store_file` integration. This allows storing
  selected files from repository on disk on push.


General
^^^^^^^

- License: individual users can hide license flash messages warning about upcoming
  license expiration.
- Downloads: the default download commit is now the landing revision set in repo settings.
- Auth-tokens: expose all roles with explanation to help users understand it better.
- Pull requests: make auto generated title for pull requests show also source Ref type
  eg. branch feature1, instead of just name of the branch.
- UI: added secondary action instead of two buttons on files page, and download page.
- Emails: reduce excessive warning logs on pre-mailer.


Security
^^^^^^^^

- Branch permissions: protect from XSS on branch rules forbidden flash message.


Performance
^^^^^^^^^^^



Fixes
^^^^^

- Pull requests: detect missing commits on diffs from new PR ancestor logic. This fixes
  problem with older PRs opened before 4.19.X that had special ancestor set, which could
  lead in some cases to crash when viewing older pull requests.
- Permissions: fixed a case when a duplicate permission made repository settings active on archived repository.
- Permissions: fixed missing user info on global and repository permissions pages.
- Permissions: allow users to update settings for repository groups they still own,
  or have admin perms, when they don't change their name.
- Permissions: flush all when running remap and rescan.
- Repositories: fixed a bug for repo groups that didn't pre-fill the repo group from GET param.
- Repositories: allow updating repository settings for users without
  store-in-root permissions in case repository name didn't change.
- Comments: fixed line display icons.
- Summary: fixed summary page total commits count.


Upgrade notes
^^^^^^^^^^^^^

- Schedule feature update.
- On Mercurial repositories we changed the order of commits when the close branch on merge features is used.
  Before the commits was made after a merge leaving an open head.
  This backward incompatible change now reverses that order, which is the correct way of doing it.
