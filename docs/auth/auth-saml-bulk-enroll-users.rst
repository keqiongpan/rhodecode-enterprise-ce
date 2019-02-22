.. _auth-saml-bulk-enroll-users-ref:


Bulk enroll multiple existing users
-----------------------------------


RhodeCode Supports standard SAML 2.0 SSO for the web-application part.
Below is an example how to enroll list of all or some users to use SAML authentication.
This method simply enables SAML authentication for many users at once.


From the server RhodeCode Enterprise is running run ishell on the instance which we
want to apply the SAML migration::

    rccontrol ishell enterprise-1

Follow these steps to enable SAML authentication for multiple users.


1) Create a user_id => attribute mapping


`saml2user` is a mapping of external ID from SAML provider such as OneLogin, DuoSecurity, Google.
This mapping consists of local rhodecode user_id mapped to set of required attributes needed to bind SAML
account to internal rhodecode user.
For example, 123 is local rhodecode user_id, and '48253211' is OneLogin ID.
For other providers you'd have to figure out what would be the user-id, sometimes it's the email, i.e for Google
The most important this id needs to be unique for each user.

.. code-block:: python

    In [1]: saml2user = {
       ...: # OneLogin, uses externalID available to read from in the UI
       ...: 123: {'id: '48253211'},
       ...: # for Google/DuoSecurity email is also an option for unique ID
       ...: 124: {'id: 'email@domain.com'},
       ...: }


2) Import the plugin you want to run migration for.

From available options pick only one and run the `import` statement

.. code-block:: python

    # for Duo Security
    In [2]: from rc_auth_plugins.auth_duo_security import RhodeCodeAuthPlugin
    # for OneLogin
    In [2]: from rc_auth_plugins.auth_onelogin import RhodeCodeAuthPlugin
    # generic SAML plugin
    In [2]: from rc_auth_plugins.auth_saml import RhodeCodeAuthPlugin

3) Run the migration based on saml2user mapping.

Enter in the ishell prompt

.. code-block:: python

    In [3]: for user in User.get_all():
       ...:     existing_identity = ExternalIdentity().query().filter(ExternalIdentity.local_user_id == user.user_id).scalar()
       ...:     attrs = saml2user.get(user.user_id)
       ...:     provider = RhodeCodeAuthPlugin.uid
       ...:     if existing_identity:
       ...:         print('Identity for user `{}` already exists, skipping'.format(user.username))
       ...:         continue
       ...:     if attrs:
       ...:         external_id = attrs['id']
       ...:         new_external_identity = ExternalIdentity()
       ...:         new_external_identity.external_id = external_id
       ...:         new_external_identity.external_username = '{}-saml-{}'.format(user.username, user.user_id)
       ...:         new_external_identity.provider_name = provider
       ...:         new_external_identity.local_user_id = user_id
       ...:         new_external_identity.access_token = ''
       ...:         new_external_identity.token_secret = ''
       ...:         new_external_identity.alt_token = ''
       ...:         Session().add(ex_identity)
       ...:         Session().commit()
       ...:         print('Set user `{}` external identity bound to ExternalID:{}'.format(user.username, external_id))

.. note::

    saml2user can be really big and hard to maintain in ishell. It's also possible
    to load it as a JSON file prepared before and stored on disk. To do so run::

        import json
        saml2user = json.loads(open('/path/to/saml2user.json','rb').read())

