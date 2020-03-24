|RCE| 4.18.1 |RNS|
------------------

Release Date
^^^^^^^^^^^^

- 2020-01-20


New Features
^^^^^^^^^^^^



General
^^^^^^^

- API: invalidate license cache on set_license_key call.
- API: add send_email flag for comments api to allow commenting without email notification.
- API: added pull requests versions into returned API data.
- Dashboard: fixed jumping of text in grid loading by new loading indicator.
- Installation: add few extra defaults that makes RhodeCode nicer out of the box.
- Pull Requests: small code cleanup to define other type of merge username.
  RC_MERGE_USER_NAME_ATTR env variable defines what should be used from user as merge username.
- Gists: cleanup UI and make the gist access id use monospace according to the new UI.


Security
^^^^^^^^

- Repository permission: properly flush permission caches on set private mode of repository.
  Otherwise we get cached values still in place until it expires.
- Repository permission: add set/un-set of private repository from permissions page.
- Permissions: flush all user permissions in case of default user permission changes.


Performance
^^^^^^^^^^^

- Caches: used more efficient way of fetching all users for permissions invalidation.
- Issue trackers: optimized performance of fetching issue tracker patterns.


Fixes
^^^^^

- SSH: fixed SSH problems with EE edition.
- Branch permissions: remove emtpy tooltips on branch permission entries.
- Core: fixed cython compat inspect that caused some API calls to not work correctly in EE release.
- Audit logger: use copy of params we later modify to prevent from modification by the store
  function of parameters that we only use for reading.
- Users: fixed wrong mention of readme in user description help block.
- Issue trackers: fixed wrong examples in patterns.
- Issue trackers: fixed missing option to get back to inherited settings.


Upgrade notes
^^^^^^^^^^^^^

- Scheduled release addressing problems in 4.18.X releases.
