.. _integrations-redmine:

Redmine integration
===================

.. important::

    In order to make issue numbers clickable in commit messages see the
    :ref:`rhodecode-issue-trackers-ref` section. The Redmine integration
    only deals with altering Redmine issues.

.. important::

    Redmine integration is only available in |RCEE|.

The Redmine integration allows you to reference and change issue statuses in
Redmine directly from commit messages using commit message patterns such as
``fixes #235`` in order to change the status of issue 235 to eg. ``Resolved``

To set a Redmine integration up it is first necessary to obtain a Redmine api
key. This can be found in ``My Account`` in the Redmine application.
If it is not there, you may have to enable API Access in Redmine settings.

Once you have the api key, create a ``redmine`` integration in
:ref:`creating-integrations`.
