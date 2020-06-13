.. _integrations-redmine:

Redmine integration
===================

.. important::

    Redmine integration is only available in |RCEE|.


.. important::

    In order to make issue numbers clickable in commit messages, see the section
    :ref:`rhodecode-issue-trackers-ref`. Redmine integration is specifically for
    altering Redmine issues.


Redmine integration allows you to reference and change issue statuses in
Redmine directly from commit messages, using commit message patterns such as
``fixes #235`` in order to change the status of issue 235 to eg. "Resolved".

To set a Redmine integration up, it is first necessary to obtain a Redmine API
key. This can be found under *My Account* in the Redmine application.
You may have to enable API Access in Redmine settings if it is not already
available.

Once you have the API key, create a Redmine integration as outlined in
:ref:`creating-integrations`.


.. note::

    There's an option to configure integration templates. Please see :ref:`integrations-rcextensions` section.
    rcextensions examples are here: https://code.rhodecode.com/rhodecode-enterprise-ce/files/default/rhodecode/config/rcextensions/examples/custom_integration_templates.py