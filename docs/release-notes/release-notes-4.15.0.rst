|RCE| 4.15.0 |RNS|
------------------

Release Date
^^^^^^^^^^^^

- 2018-12-10


New Features
^^^^^^^^^^^^

- Authentication: Added SAML 2.0 Authentication, with support of OneLogin and DUO Security.
- Core: add debug mode that switches logging to debug.
  It's no longer required to reconfigure all logging. A `debug=true` set in .ini file
  does it automatically.


General
^^^^^^^

- Authentication: rename oauth to external identity as it would now be serving both
  oAuth and SAML.
- Authentication: allow setting extern type with registration.
  This will allow external identity plugins to define proper externs instead of always
  using "rhodecode" one.
- Authentication: show if plugin is activated and enabled in the list.
- Authentication: add better logging for ldap related attributes to help track
  LDAP connection problems more easily.
- Visual: add change logo header template
- UI: updated error pages style to be consistent with other pages.
- Utils: updated request generation so ishell can run some automation scripts.
- Docs: updated documentation for SVN 1.10 Wandisco repositories.
- System info: expose base_url set in .ini file.
- Style: update pygments template styling.
- Style: updated li style and markdown style.
- Dependencies: added python-saml library.
- Dependencies: bumped hgsubversion to 1.9.3 release.
- Dependencies: bumped gevent to 1.3.7 release.
- Dependencies: bumped lxml to 4.2.5 release.
- Dependencies: bumped gevent to 1.3.7 release.
- Dependencies: bumped alembic to 1.0.5 release.
- Dependencies: bumped peppercorn to 0.6 release.
- Dependencies: bumped pyotp to 2.2.7 release.
- Dependencies: bumped deform to 2.0.7 release
- Dependencies: bumped py-gfm to 0.1.4 release.
- Dependencies: bumped colander to 1.5.1 release
- Dependencies: bumped appenlight-client to 0.6.26 release.
- Dependencies: bumped bleach to 3.0.2 release.
- Dependencies: bumped pygments to 2.3.0


Security
^^^^^^^^

- Mercurial: support evolve sub-commands when checking for permissions.
  Those defaulted to write, while only read is required for evolve.
- auth/security: enforce that external users cannot reset their password.
  External users don't use RhodeCode passwords, so resetting them shouldn't be allowed.


Performance
^^^^^^^^^^^

- Markdown: use lazy loaded markdown initialization to speed up app startup.
- Gevent: changed DNS resolver to ares for better stability on long running processes.


Fixes
^^^^^

- Default Reviewers: use target repo owner as default reviewer in case of CE edition.
- LDAP: ensure the proper cert files and dirs are set.
  It's also now possible to specify custom paths for those.
- Markdown: fixed auto checkbox generation from markdown code


Upgrade notes
^^^^^^^^^^^^^

- In this release we introduced new options for cert directory and file for LDAP plugins.
  In case of problems with LDAPS please verify the settings in the LDAP plugin configuration.
