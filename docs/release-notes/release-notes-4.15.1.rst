|RCE| 4.15.1 |RNS|
------------------

Release Date
^^^^^^^^^^^^

- 2019-01-01


New Features
^^^^^^^^^^^^



General
^^^^^^^

- Downloads: properly encode " in the filenames, and add RFC 5987 header for non-ascii files.
- Documentation: updated configuration for Nginx and reverse proxy.
- VCS: streaming will use now 100kb chunks for faster network throughput.


Security
^^^^^^^^

- Diffs: fixed xss in context diff menu.
- Downloads: properly encode " in the filenames, prevents from hiding executable
  files disguised in another type of file using crafted file names.

Performance
^^^^^^^^^^^



Fixes
^^^^^

- VCS: handle excessive slashes in from of the repo name path, fixes #5522.
  This prevents 500 errors when excessive slashes are used
- SVN: support proxy-prefix properly, fixes #5521.
- Pull requests: validate ref types on API calls for pull request so users cannot
  provide wrongs ones.
- Scheduler: fix url generation with proxy prefix.
- Celery: add DB connection ping to validate DB connection is working at worker startup.


Upgrade notes
^^^^^^^^^^^^^

- Scheduled release addressing reported problems in 4.15.X releases.
