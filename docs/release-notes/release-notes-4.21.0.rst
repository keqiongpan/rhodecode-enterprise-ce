|RCE| 4.21.0 |RNS|
------------------

Release Date
^^^^^^^^^^^^

- 2020-09-28


New Features
^^^^^^^^^^^^

- Pull requests: overhaul of the UX/UI by adding new sidebar
- Pull requests: new live reviewer present indicator (requires channelstream enabled)
- Pull requests: new live new comments indicator (requires channelstream enabled)
- Pull requests: new sidebar with comments/todos/referenced tickets navigation
- Commits page: Introduced sidebar for single commits pages


General
^^^^^^^

- API: allow repo admins to get/set settings.
  Previously it was only super-admins that could do that.
- Sessions: patch baker to take expire time for redis for auto session cleanup feature.
- Git: bumped git version to 2.27.0
- Packages: bumped to channelstream==0.6.14


Security
^^^^^^^^

- Issue trackers: fix XSS with description field.


Performance
^^^^^^^^^^^

- Artifacts: speed-up of artifacts download request processing.


Fixes
^^^^^

- Pull requests: properly save merge failure metadata.
  In rare cases merge check reported conflicts which there were none.
- Sessions: fixed cleanup with corrupted session data issue.


Upgrade notes
^^^^^^^^^^^^^

- Scheduled feature release.
- Git version was bumped to 2.27.0
