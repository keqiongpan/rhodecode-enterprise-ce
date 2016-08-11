.. _integrations:

Integrations
------------

Rhodecode supports integrations with external services for various events
such as commit pushes and pull requests. Multiple integrations of the same type
(eg. slack) can be added at the same time which is useful for example to post
different events to different slack channels.

Supported integrations
^^^^^^^^^^^^^^^^^^^^^^

============================    ============    =====================================
Type/Name                       |RC| Edition    Description
============================    ============    =====================================
:ref:`integrations-slack`       |RCCEshort|     https://slack.com/
:ref:`integrations-hipchat`     |RCCEshort|     https://www.hipchat.com/
:ref:`integrations-webhook`     |RCCEshort|     POST events as `json` to a custom url
:ref:`integrations-email`       |RCEEshort|     Send repo push commits by email
:ref:`integrations-redmine`     |RCEEshort|     Close/Resolve/Reference redmine issues
:ref:`integrations-jira`        |RCEEshort|     Close/Resolve/Reference JIRA issues
============================    ============    =====================================

.. _creating-integrations:

Creating an integration
^^^^^^^^^^^^^^^^^^^^^^^

Integrations can be added globally via the admin UI:

:menuselection:`Admin --> Integrations`

or per repository in the repository settings:

:menuselection:`Admin --> Repositories --> Edit --> Integrations`

To create an integration, select the type from the list of types in the
`Create an integration` section.

The `Current integrations` section shows existing integrations that have been
created along with their type (eg. slack) and enabled status.

.. toctree::

   slack
   hipchat
   redmine
   jira
   webhook
