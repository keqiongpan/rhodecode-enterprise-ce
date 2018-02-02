|RCE| 4.11.1 |RNS|
------------------

Release Date
^^^^^^^^^^^^

- 2018-02-02


New Features
^^^^^^^^^^^^



General
^^^^^^^



Security
^^^^^^^^



Performance
^^^^^^^^^^^



Fixes
^^^^^


- Audit logs: handle query syntax errors in whoosh query parser. Prevents 500
  errors on wrongly entered search terms in audit logs.

- Mercurial: fix new 4.4.X code change that does strict requirement checks. Fixes
  problems with Mercurial Largefiles repositories.

- VCSServer: in case of errors in the VCSServer worker restart it gracefully.
  In rare cases certain errors caused locking of workers, and
  unresponsive connections. Now we restart a worker freeing up memory and
  connection.

- Git: handle flaky and slow connection issues with git. Due to the changes in
  Pyramid, flaky connections started affecting git clones.


Upgrade notes
^^^^^^^^^^^^^

- Fixed regression on git with high latency connections.
  No upgrade problems should be expected, however please check GIT repos
  behaviour on upgrade.
