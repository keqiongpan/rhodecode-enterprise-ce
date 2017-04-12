|RCE| 4.7.1 |RNS|
-----------------

Release Date
^^^^^^^^^^^^

- 2017-04-13


New Features
^^^^^^^^^^^^



General
^^^^^^^


Security
^^^^^^^^

- Auth plugins: don't expose sensitive information inside DEBUG log for auth
  plugins (such as ldap access passwords).
  Each plugin now defines a black-list of arguments to hide from logging.


Performance
^^^^^^^^^^^



Fixes
^^^^^

- Largefiles: fix errors on fetching largefiles from web interface when viewing
  from specific branch.
- User Admin: fix problem with sorting for Mysql database.


Upgrade notes
^^^^^^^^^^^^^


