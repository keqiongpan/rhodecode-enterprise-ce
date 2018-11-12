|RCE| 4.14.1 |RNS|
------------------

Release Date
^^^^^^^^^^^^

- 2018-11-12


New Features
^^^^^^^^^^^^



General
^^^^^^^

- ui: increase label width after font changes.
- ui: make branding consistent in all pages.


Security
^^^^^^^^



Performance
^^^^^^^^^^^



Fixes
^^^^^

- hooks: fixed SVN hook problem on commit with new rcextensions.
- hooks: use safer way to validate kwargs. If rcextensions are disable we shouldn't
  validate any parameters.
- mailer: use default port for mails. Without ports mailer would fail with an odd
  unrelated error message.


Upgrade notes
^^^^^^^^^^^^^

- Un-scheduled release addressing reported problems.

