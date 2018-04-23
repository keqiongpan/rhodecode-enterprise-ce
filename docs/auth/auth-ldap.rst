.. _config-ldap-ref:

LDAP/AD
-------

|RCM| supports LDAP (Lightweight Directory Access Protocol) or
AD (active Directory) authentication.
All LDAP versions are supported, with the following |RCM| plugins managing each:

* For LDAP or Active Directory use ``LDAP (egg:rhodecode-enterprise-ce#ldap)``

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

1. From the |RCM| interface, select
   :menuselection:`Admin --> Authentication`
2. Enable the ldap plugin and select :guilabel:`Save`
3. Select the :guilabel:`Enabled` check box in the plugin configuration section
4. Add the required LDAP information and :guilabel:`Save`, for more details,
   see :ref:`config-ldap-examples`

For a more detailed description of LDAP objects, see :ref:`ldap-gloss-ref`:

.. _config-ldap-examples:

Example LDAP configuration
^^^^^^^^^^^^^^^^^^^^^^^^^^
.. code-block:: bash

        # Auth Cache TTL, Defines the caching for authentication to offload LDAP server.
        # This means that cache result will be saved for 3600 before contacting LDAP server to verify the user access
        3600
        # Host, comma seperated format is optionally possible to specify more than 1 server
        https://ldap1.server.com/ldap-admin/,https://ldap2.server.com/ldap-admin/
        # Default LDAP Port, use 689 for LDAPS
        389
        # Account, used for SimpleBind if LDAP server requires an authentication
        e.g admin@server.com
        # Password used for simple bind
        ldap-user-password
        # LDAP connection security
        LDAPS
        # Certificate checks level
        DEMAND
        # Base DN
        cn=Rufus Magillacuddy,ou=users,dc=rhodecode,dc=com
        # LDAP search filter to narrow the results
        (objectClass=person)
        # LDAP search scope
        SUBTREE
        # Login attribute
        sAMAccountName
        # First Name Attribute to read
        givenName
        # Last Name Attribute to read
        sn
        # Email Attribute to read email address from
        mail


Below is example setup that can be used with Active Directory/LDAP server.

.. image:: ../images/ldap-example.png
   :alt: LDAP/AD setup example
   :scale: 50 %


.. toctree::

   ldap-active-directory
   ldap-authentication
