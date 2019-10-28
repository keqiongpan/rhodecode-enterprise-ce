|RCE| 4.17.3 |RNS|
------------------

Release Date
^^^^^^^^^^^^

- 2019-07-25


New Features
^^^^^^^^^^^^



General
^^^^^^^

- RSS: use permalinks without slashes for feeds. Fixes #5557. RSS feed will now use
  links that won't change when a repository is renamed, and in addition they now have
  better compatibility with Outlook.
- Pull Requests: make merge state calculation default to disabled.
  This causes a lot of performance problems and should default to faster way
- Pull Requests: add indication of state change in list of pull-requests and actually
  show them in the list. Before PRs that were in states like "merging" were hidden from
  the PR list. Now we show them with grey-out display indicating PR is changing states.
- API: extended upload api to be able to upload files with ACL checks enabled


Security
^^^^^^^^



Performance
^^^^^^^^^^^

- Pull Requests: don't calculate merge state several times for repo on each pr display object state.
- Logging: http logging should limit the data to some sane amount.
  In some cases we could log 100MBs into logs that weren't useful at all.


Fixes
^^^^^

- config: fixed special character in gunicorn config that caused problems during installation.
- path-filter: enable checking for files access for quick search menu in files view.
- rcextensions: improved messaging on rcextensions load fail
- Repository permissions: enable shortcut to set private mode in permission page.
- UI: fixed style for ancestor commit. Fixes #5558
- Events: ensure stable execution of integrations (in order: global, per-group, per-repo)
- Settings: custom header/footer code message correction
- Artifacts: don't crash when metadata isn't complete. This can be a case for edited upload attachements


Upgrade notes
^^^^^^^^^^^^^

- Scheduled release addressing problems in 4.17.X releases.
