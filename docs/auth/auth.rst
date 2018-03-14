.. _authentication-ref:

Authentication Options
======================

|RCE| provides a built in authentication against its own database. This is
implemented using ``rhodecode.lib.auth_rhodecode`` plugin. This plugin is
enabled by default.
Additionally, |RCE| provides a Pluggable Authentication System. This gives the
administrator greater control over how users authenticate with the system.

.. important::

  You can disable the built in |RCM| authentication plugin
  ``rhodecode.lib.auth_rhodecode`` and force all authentication to go
  through your authentication plugin of choice e.g LDAP only.
  However, if you do this, and your external authentication tools fails,
  you will be unable to access |RCM|.

|RCM| comes with the following user authentication management plugins:


.. toctree::

    auth-ldap
    auth-ldap-groups
    auth-crowd
    auth-pam
    auth-token
    ssh-connection


