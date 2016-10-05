.. _integrations-webhook:

Webhook integration
===================

The Webhook integration allows you to POST events such as repository pushes
or pull requests to a custom http endpoint as a json dict with details of the
event.

Starting from 4.5.0 release, webhook integration allows to use variables
inside the URL. For example in URL `https://server-example.com/${repo_name}`
${repo_name} will be replaced with the name of repository which events is
triggered from. Some of the variables like
`${branch}` will result in webhook be called multiple times when multiple
branches are pushed.

Some of the variables like `${pull_request_id}` will be replaced only in
the pull request related events.

To create a webhook integration, select "webhook" in the integration settings
and use the URL and key from your any previous custom webhook created. See
:ref:`creating-integrations` for additional instructions.
