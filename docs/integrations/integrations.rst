.. _integrations:

Integrations
------------

Rhodecode supports integrations with external services for various events,
such as commit pushes and pull requests. Multiple integrations of the same type
can be added at the same time; this is useful for posting different events to
different Slack channels, for example.

Supported integrations
^^^^^^^^^^^^^^^^^^^^^^

============================    ============    =====================================
Type/Name                       |RC| Edition    Description
============================    ============    =====================================
:ref:`integrations-slack`       |RCCEshort|     https://slack.com/
:ref:`integrations-hipchat`     |RCCEshort|     https://www.hipchat.com/
:ref:`integrations-webhook`     |RCCEshort|     POST events as `json` to a custom url
:ref:`integrations-ci`          |RCCEshort|     Trigger Builds for Common CI Systems
:ref:`integrations-email`       |RCCEshort|     Send repo push commits by email
:ref:`integrations-redmine`     |RCEEshort|     Close/Resolve/Reference redmine issues
:ref:`integrations-jira`        |RCEEshort|     Close/Resolve/Reference JIRA issues
============================    ============    =====================================

.. _creating-integrations:

Creating an Integration
^^^^^^^^^^^^^^^^^^^^^^^

Integrations can be added globally via the admin UI:

:menuselection:`Admin --> Integrations`

or per repository in each repository's settings:

:menuselection:`Admin --> Repositories --> Edit --> Integrations`

To create an integration, select the type from the list in the *Create New
Integration* section.

The *Current Integrations* section shows existing integrations that have been
created along with their type (eg. Slack) and enabled status.

See pages specific to each type of integration for more instructions:

.. toctree::

   slack
   hipchat
   redmine
   jira
   webhook
   email
