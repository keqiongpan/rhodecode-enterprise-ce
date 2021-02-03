|RCE| 4.24.1 |RNS|
------------------

Release Date
^^^^^^^^^^^^

- 2021-02-04


New Features
^^^^^^^^^^^^



General
^^^^^^^

- Core: added statsd client for statistics usage.
- Clone urls: allow custom clone by id template so users can set clone-by-id as default.
- Automation: enable check for new version for EE edition as automation task that will send notifications when new RhodeCode version is available

Security
^^^^^^^^



Performance
^^^^^^^^^^^

- Core: bumped git to 2.30.0


Fixes
^^^^^

- Comments: add ability to resolve todos from the side-bar. This should prevent situations
  when a TODO was left over in outdated/removed code pieces, and users needs to search to resolve them.
- Pull requests: fixed a case when template marker was used in description field causing 500 errors on commenting.
- Merges: fixed excessive data saved in merge metadata that could not fit inside the DB table.
- Exceptions: fixed problem with exceptions formatting resulting in limited exception data reporting.


Upgrade notes
^^^^^^^^^^^^^

- Un-scheduled release addressing problems in 4.24.X releases.
