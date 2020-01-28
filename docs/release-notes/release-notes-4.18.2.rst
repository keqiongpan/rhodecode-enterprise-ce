|RCE| 4.18.2 |RNS|
------------------

Release Date
^^^^^^^^^^^^

- 2020-01-28


New Features
^^^^^^^^^^^^



General
^^^^^^^

- Permissions: add better help text about default permissions, and correlation with anonymous access enabled.
- Mentions: markdown renderer now wraps username in hovercard logic allowing checking the mentioned user.
- Documentation: added note about hard restart due to celery update.
- Maintenance: run rebuildfncache for Mercurial in maintenance command.


Security
^^^^^^^^



Performance
^^^^^^^^^^^

- Authentication: cache plugins for auth and their settings in the auth_registry for single request.
  This heavily influences SVN performance on multiple-file commits.


Fixes
^^^^^

- Descriptions: fixed rendering problem with certain meta-tags in repo description.
- Emails: fixed fonts rendering problems in Outlook.
- Emails: fixed bug in test email sending.
- Summary: fixed styling of readme indicator.
- Flash: fixed display problem with flash messages on error pages.


Upgrade notes
^^^^^^^^^^^^^

- Scheduled release addressing problems in 4.18.X releases.
