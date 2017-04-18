|RCE| 4.7.2 |RNS|
-----------------

Release Date
^^^^^^^^^^^^

- 2017-04-18


New Features
^^^^^^^^^^^^



General
^^^^^^^

- git-lfs: always validate uploaded files size. In case an upload is damaged, or
  interrupted RhodeCode will send the upload as failed making git-lfs client
  re-try the upload of large files.
- dependencies: bumped rhodecode-tools to version 0.12.0


Security
^^^^^^^^



Performance
^^^^^^^^^^^



Fixes
^^^^^


- make usage of gunicorn wrappers to write data to disk.
- git-lfs: report chunked encoding support properly to the client.
- git-lfs: report returned data as 'application/vnd.git-lfs+json'
  instead of plain json
- http-app: simplify detection of chunked encoding, when doing git-lfs uploads.
- rcextensions: fixed default template of rcextensions to propery
  handle pre-push callback.


Upgrade notes
^^^^^^^^^^^^^

- This release fixes some found problems with git-lfs stream uploads. Please
  try to run `git lfs push --all origin` to re-validate uploaded large-objects.
