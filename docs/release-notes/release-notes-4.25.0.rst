|RCE| 4.25.0 |RNS|
------------------

Release Date
^^^^^^^^^^^^

- 2021-04-02


New Features
^^^^^^^^^^^^

- SSH: allow clone by ID via SSH operations.
- Artifacts: added an admin panel to manage artifacts.
- Redmine: added option to add note to a ticket without changing its status in Redmine integration.


General
^^^^^^^

- Git: change lookups logic. Prioritize reference names over numerical ids.
  Numerical ids are supported as a fallback if ref matching is unsuccessful.
- Permissions: changed fork permission help text to reflect the actual state on how it works.
- Permissions: flush permissions on owner changes for repo and repo groups. This
  would fix problems when owner of repository changes then the new owner lacked permissions
  until cache expired.
- Artifacts: added API function to remove artifacts.
- Archives: use a special name for non-hashed archives to fix caching issues.
- Packaging: fixed few packages requirements for a proper builds.
- Packaging: fix rhodecode-tools for docker builds.
- Packaging: fixed some problem after latest setuptools-scm release.
- Packaging: added setuptools-scm to packages for build.
- Packaging: fix jira package for reproducible builds.
- Packaging: fix zipp package patches.


Security
^^^^^^^^

- Comments: forbid removal of comments by anyone except the owners.
  Previously admins of a repository could remove them if they would construct a special url with data.
- Pull requests: fixed some xss problems when a deleted file with special characters were commented on.


Performance
^^^^^^^^^^^

- License: skip channelstream connect on license checks logic to reduce calls handling times.
- Core: optimize some calls to skip license/scm detection on them. Each license check is expensive
  and we don't need them on each call.


Fixes
^^^^^

- Branch-permissions: fixed ce view. Fixes #5656
- Feed: fix errors on feed access of empty repositories.
- Archives: if implicit ref name was used (e.g master) to obtain archive, we now
  redirect to explicit commit sha so we can have the proper caching for references names.
- rcextensions: fixed pre-files extractor return code support.
- Svn: fix subprocess problems on some of the calls for file checking.
- Pull requests: fixed multiple repetitions of referenced tickets in pull requests summary sidebar.
- Maintenance: fixed bad routes def
- clone-uri: fixed the problems with key mismatch that caused errors on summary page.
- Largefiles: added fix for downloading largefiles which had no extension in file name.
- Compare: fix referenced commits bug.
- Git: fix for unicode branches


Upgrade notes
^^^^^^^^^^^^^

- Scheduled release 4.25.0.



