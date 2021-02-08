|RCE| 4.24.0 |RNS|
------------------

Release Date
^^^^^^^^^^^^

- 2021-01-10


New Features
^^^^^^^^^^^^

- Artifacts: expose additional headers, and content-disposition for downloads from artifacts exposing the real name of the file.
- Token access: allow token in headers not only in GET/URL.
- File-store: added a stream upload endpoint, it allows to upload GBs of data into artifact store efficiently.
  Can be used for backups etc.
- Pull requests: expose commit versions in the pull-request commit list.


General
^^^^^^^

- Deps: bumped redis to 3.5.3
- Rcextensions: improve examples for some usage.
- Setup: added optional parameters to apply a default license, or skip re-creation of database at install.
- Docs: update headers for NGINX
- Beaker cache: remove no longer used beaker cache init
- Installation: the installer no longer requires gzip and bzip packages, and works on python 2 and 3


Security
^^^^^^^^



Performance
^^^^^^^^^^^

- Core: speed up cache loading on application startup.
- Core: allow loading all auth plugins in once place for CE/EE code.
- Application: not use config.scan(), and replace all @add_view decorator into a explicit add_view call for faster app start.


Fixes
^^^^^

- Svn: don't print exceptions in case of safe calls
- Vcsserver: use safer maxfd reporting, some linux systems get a problem with this
- Hooks-daemon: fixed problem with lost hooks value from .ini file.
- Exceptions: fixed truncated exception text


Upgrade notes
^^^^^^^^^^^^^

- Scheduled release 4.24.0
