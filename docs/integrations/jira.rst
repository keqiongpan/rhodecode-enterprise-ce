.. _integrations-jira:

JIRA integration
================

.. important::

    JIRA integration is only available in |RCEE|.


.. important::

    In order to make issue numbers clickable in commit messages, see the
    :ref:`rhodecode-issue-trackers-ref` section. The JIRA integration
    only deals with altering JIRA issues.


The JIRA integration allows you to reference and change issue statuses in
JIRA directly from commit messages using commit message patterns such as
``fixes #JIRA-235`` in order to change the status of issue JIRA-235 to
eg. "Resolved".

In order to apply a status to a JIRA issue, it is necessary to find the
transition status id in the *Workflow* section of JIRA.

Once you have the transition status id, you can create a JIRA integration
as outlined in :ref:`creating-integrations`.
