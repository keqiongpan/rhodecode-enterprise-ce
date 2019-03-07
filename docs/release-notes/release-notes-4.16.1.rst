|RCE| 4.16.1 |RNS|
------------------

Release Date
^^^^^^^^^^^^

- 2019-03-07


New Features
^^^^^^^^^^^^



General
^^^^^^^

- Docs: added missing reference for the user bookmarks feature.


Security
^^^^^^^^

- Comments: prevent from allowing to resolve TODO comments across projects. In certain
  conditions users could resolve TODOs not belonging to the same project.


Performance
^^^^^^^^^^^



Fixes
^^^^^

- Downloads: fixed archive links from file tree view.
- Markdown: fixed sanitization of checkbox extensions that removed "checked" attribute.
- Upgrade: fixed upgrades from older versions of RhodeCode.
- Pull Requests: handle non-ascii branches from short branch selector via URL.
- Hooks: fixed again unicode problems with new pull request link generator.



Upgrade notes
^^^^^^^^^^^^^

- Scheduled release addressing problems in 4.16.X releases.
