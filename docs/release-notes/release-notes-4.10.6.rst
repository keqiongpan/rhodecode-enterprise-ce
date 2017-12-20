|RCE| 4.10.6 |RNS|
------------------

Release Date
^^^^^^^^^^^^

- 2017-12-20


New Features
^^^^^^^^^^^^



General
^^^^^^^

- dependencies: bump webob to 1.7.4 that fixes 1.7.3 regression for streaming.
- svn: extend detection of SVN PROPFIND/PROPATCH methods. This increases the
  compatibility with svn methods such as svn mkdir or svn delete with
  tortoise SVN.


Security
^^^^^^^^



Performance
^^^^^^^^^^^

- hooks: decrease pool interval to 10ms. For SVN operations and lots of requests
  this can lead to almost 4x speed improvement.


Fixes
^^^^^

- celery: fix potential 404 problems with celery and sync creation
  of repositories.
- fixed git streaming support for instance that are not behind a buffering
  proxies. Webob library removed default chunked encoding support, and now
  requires an explicit flag to make it work again.


Upgrade notes
^^^^^^^^^^^^^

- Fixed regression with streaming, and increased svn support.
  No upgrade problems should be expected, however please check GIT repos
  behaviour on upgrade.

