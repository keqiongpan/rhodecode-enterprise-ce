.. _integrations-slack:

Slack integration
=================

To set a Slack integration up, it is first necessary to set up a Slack webhook
API endpoint for your Slack channel. This can be done at:

https://my.slack.com/services/new/incoming-webhook/

Select the channel you would like to use, and Slack will provide you with the
webhook URL for configuration.

You can now create a Slack integration as outlined in
:ref:`creating-integrations`.

.. note::
    Some settings in the RhodeCode admin are identical to the options within the
    Slack integration. For example, if notifications are to be sent in a private
    chat, leave the "Channel" field blank. Likewise, the Emoji option within
    RhodeCode can override the one set in the Slack admin.