|RCE| 4.3.1 |RNS|
-----------------

Release Date
^^^^^^^^^^^^

- 2016-08-23


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

- Core: fixed database session cleanups. This will make sure RhodeCode can
  function correctly after database server problems. Fixes #4173, refs #4166
- Diffs: limit the file context to ~1mln lines. Fixes #4184, also make sure
  this doesn't trigger Integer overflow for msgpack.