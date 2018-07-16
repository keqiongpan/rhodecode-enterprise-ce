|RCE| 4.12.4 |RNS|
------------------

Release Date
^^^^^^^^^^^^

- 2018-07-13


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

- Repository: fixed problems with mercurial/git url validators.
- User Groups: fixed audit log data on user group permissions view.
  This caused an 500 error when editing user groups.
- Authentication: fixed problem with displaying social auth providers in the login page.
- Google Authentication: updated google user info api to latest version. The previous
  endpoint was deprecated and it caused problems with Google authentication.
- API: fixed problem with setting recursive permissions changes to repo group.
- API: fixed problem with creation of pull request with custom reviewers rules.
- API: fixed problem with proper diff calculation with using pull-request API.


Upgrade notes
^^^^^^^^^^^^^

- Scheduled release addressing reported problems, and improving stability.
