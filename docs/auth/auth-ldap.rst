.. _config-ldap-ref:

LDAP/AD
-------

|RCE| supports LDAP (Lightweight Directory Access Protocol) or
AD (active Directory) authentication.
All LDAP versions are currently supported.

RhodeCode reads all data defined from plugin and creates corresponding
accounts on local database after receiving data from LDAP. This is done on
every user log-in including operations like pushing/pulling/checkout.


.. important::

   The email used with your |RCE| super-admin account needs to match the email
   address attached to your admin profile in LDAP. This is because
   within |RCE| the user email needs to be unique, and multiple users
   cannot share an email account.

   Likewise, if as an admin you also have a user account, the email address
   attached to the user account needs to be different.


LDAP Configuration Steps
^^^^^^^^^^^^^^^^^^^^^^^^

To configure |LDAP|, use the following steps:

1. From the |RCE| interface, select
   :menuselection:`Admin --> Authentication`
2. Activate the `LDAP` plugin and select :guilabel:`Save`
3. Go to newly available menu option called `LDAP` on the left side.
4. Check the `enabled` check box in the plugin configuration section,
   and fill in the required LDAP information and :guilabel:`Save`, for more details,
   see :ref:`config-ldap-examples`

For a more detailed description of LDAP objects, see :ref:`ldap-gloss-ref`:

.. _config-ldap-examples:

Example LDAP configuration
^^^^^^^^^^^^^^^^^^^^^^^^^^

Below is example setup that can be used with Active Directory/LDAP server::

    *option*: `enabled` => `True`
    # Enable or disable this authentication plugin.

    *option*: `cache_ttl` => `360`
    # Amount of seconds to cache the authentication and permissions check response call for this plugin.
    # Useful for expensive calls like LDAP to improve the performance of the system (0 means disabled).

    *option*: `host` => `192.168.245.143,192.168.1.240`
    # Host[s] of the LDAP Server
    # (e.g., 192.168.2.154, or ldap-server.domain.com.
    #  Multiple servers can be specified using commas

    *option*: `port` => `389`
    # Custom port that the LDAP server is listening on. Default value is: 389, use 689 for LDAPS(SSL)

    *option*: `timeout` => `300`
    # Timeout for LDAP connection

    *option*: `dn_user` => `Administrator@rhodecode.com`
    # Optional user DN/account to connect to LDAP if authentication is required.
    # e.g., cn=admin,dc=mydomain,dc=com, or uid=root,cn=users,dc=mydomain,dc=com, or admin@mydomain.com

    *option*: `dn_pass` => `SomeSecret`
    # Password to authenticate for given user DN.

    *option*: `tls_kind` => `PLAIN`
    # TLS Type

    *option*: `tls_reqcert` => `NEVER`
    # Require Cert over TLS?. Self-signed and custom certificates can be used when
    #  `RhodeCode Certificate` found in admin > settings > system info page is extended.

    *option*: `tls_cert_file` => ``
    # This specifies the PEM-format file path containing certificates for use in TLS connection.
    # If not specified `TLS Cert dir` will be used

    *option*: `tls_cert_dir` => `/etc/openldap/cacerts`
    # This specifies the path of a directory that contains individual CA certificates in separate files.

    *option*: `base_dn` => `cn=Rufus Magillacuddy,ou=users,dc=rhodecode,dc=com`
    # Base DN to search. Dynamic bind is supported. Add `$login` marker in it to be replaced with current user credentials
    # (e.g., dc=mydomain,dc=com, or ou=Users,dc=mydomain,dc=com)

    *option*: `filter` => `(objectClass=person)`
    # Filter to narrow results
    # (e.g., (&(objectCategory=Person)(objectClass=user)), or
    # (memberof=cn=rc-login,ou=groups,ou=company,dc=mydomain,dc=com)))

    *option*: `search_scope` => `SUBTREE`
    # How deep to search LDAP. If unsure set to SUBTREE

    *option*: `attr_login` => `sAMAccountName`
    # LDAP Attribute to map to user name (e.g., uid, or sAMAccountName)

    *option*: `attr_email` => `mail`
    # LDAP Attribute to map to email address (e.g., mail).
    # Emails are a crucial part of RhodeCode.
    # If possible add a valid email attribute to ldap users.

    *option*: `attr_firstname` => `givenName`
    # LDAP Attribute to map to first name (e.g., givenName)

    *option*: `attr_lastname` => `sn`
    # LDAP Attribute to map to last name (e.g., sn)


.. toctree::

   ldap-active-directory
   ldap-authentication
