|RCE| 4.13.1 |RNS|
------------------

Release Date
^^^^^^^^^^^^

- 2018-08-06


New Features
^^^^^^^^^^^^



General
^^^^^^^

- core: added option to prefix cache keys for usage in cluster.
- exception-tracker: store event sending exception for easier event fail debugging.
- maintenance: add repack and fsck for git maintenance execution list.


Security
^^^^^^^^



Performance
^^^^^^^^^^^



Fixes
^^^^^

- caches: use single default cache dir for all backends.
- caches: don't use lower in cache settings to support uppercase PATHS


Upgrade notes
^^^^^^^^^^^^^

- Unscheduled release addressing reported problems, and improving stability.
