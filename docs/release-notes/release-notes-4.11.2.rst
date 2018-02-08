|RCE| 4.11.2 |RNS|
------------------

Release Date
^^^^^^^^^^^^

- 2018-02-08


New Features
^^^^^^^^^^^^



General
^^^^^^^

- git: stabilize long running git processes to prevent potential worker freezes.


Security
^^^^^^^^

- Repo Checks(low): prevent from html injection on repo-check page. It could
  be prepared to fake the displayed text fooling users into unwanted actions.


Performance
^^^^^^^^^^^



Fixes
^^^^^

- Diffs: in case of text lexers don't do any HL because of pygments problems.
  Fixed newline rendering for certain very unique diffs using Pygments.
- Webhook: fixed extra variable replacement in webhook url.
- Subprocessio: use safe b.read() and prevent potential valueErrors
- Subprocess: use subprocessio helper to run various subprocess commands.
- Git: use subprocessio for hooks execution to use non-blocking subprocess.


Upgrade notes
^^^^^^^^^^^^^

- Scheduled bugfix release fixing certain requested problems with diffs and, Git.
