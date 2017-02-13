|RCE| 4.6.1 |RNS|
-----------------

Release Date
^^^^^^^^^^^^

- 2017-02-13


New Features
^^^^^^^^^^^^



General
^^^^^^^

- HTTP Protocol: large incoming requests will now properly stream data
  into VCSServer. In some cases a large push in GIT can send streaming data.
  previously RhodeCode unbundled that data before sending back to VCSServer.
  This sometimes caused errors because of wrong headers sent (chunked-encoding)
  RhodeCode will now simply stream data back to VCSServer. This should fix the
  push problems, and also be much faster for large pushes.

- Docs: updated contribution and dev setup docs.


Security
^^^^^^^^



Performance
^^^^^^^^^^^



Fixes
^^^^^

- Api: cleanup sessions enforces older_then must be a valid INT.
- Api: validate sent commit_id when using commit_comment API.
- Events: fix a case events were called from API and we
  couldn't fetch registered user.

- Search: goto repository commit search functionality will now use a safe
  search option and try not to throw meaningless errors to users from this view.
- Annotations: fixed UI problems in annotation view for newer browsers.

Upgrade notes
^^^^^^^^^^^^^

- Streaming support was changed for push operations. We tested this in several
  cases, but please send any feedback if you encounter any problems with it.

