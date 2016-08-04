.. _integrations-hipchat:

Hipchat integration
===================

In order to set a hipchat integration up it is necessary to obtain the Hipchat
service url by:

1. Login to Hipchat (https://www.hipchat.com/)
2. Goto `Integrations` -> `Build your own`
3. Select a room to post notifications to and save it

Once the integration is setup on hipchat you should have a url of the
form: `
which can be used in :ref:`creating-integrations`

Once you have set up a Hipchat webhook integrations url of the form:
``https://yourapp.hipchat.com/v2/room/123456/notification?auth_token=...``,
create a ``hipchat`` integration in :ref:`creating-integrations`.
