.. _authentication-ref:

Authentication Options
======================

|RCE| provides a built in authentication against its own database. This is
implemented using ``RhodeCode Internal`` plugin. This plugin is enabled by default.
Additionally, |RCE| provides a Pluggable Authentication System. This gives the
administrator greater control over how users authenticate with the system.

.. important::

  You can disable the built in |RCE| authentication plugin
  ``RhodeCode Internal`` and force all authentication to go
  through your authentication plugin of choice e.g LDAP only.
  However, if you do this, and your external authentication tools fails,
  accessing |RCE| will be blocked unless a fallback plugin is
  enabled via :file: rhodecode.ini


|RCE| comes with the following user authentication management plugins:


.. toctree::

    auth-token
    auth-ldap
    auth-ldap-groups
    auth-saml-generic
    auth-saml-onelogin
    auth-saml-duosecurity
    auth-crowd
    auth-pam
    ssh-connection
