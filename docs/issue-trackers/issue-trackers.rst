.. _rhodecode-issue-trackers-ref:

Issue Tracker Integration
=========================

You can set an issue tracker connection in two ways with |RCE|.

* At the instance level, you can set a default issue tracker.
* At the |repo| level, you can configure an integration with a different issue
  tracker.

To integrate |RCE| with an issue tracker, you need to define a regular
expression that will fetch the issue ID stored in commit messages, and replace
it with a URL. This enables |RCE| to generate a link matching each issue to the
target |repo|.

Default Issue Tracker Configuration
-----------------------------------

To integrate your issue tracker, use the following steps:

1. Open :menuselection:`Admin --> Settings --> Issue Tracker`.
2. In the new entry field, enter the following information:

    * :guilabel:`Description`: A name for this set of rules.
    * :guilabel:`Pattern`: The regular expression that will match issues
      tagged in commit messages, or more see :ref:`issue-tr-eg-ref`.
    * :guilabel:`URL`: The URL to your issue tracker.
    * :guilabel:`Prefix`: The prefix with which you want to mark issues.

3. Select **Add** so save the rule to your issue tracker configuration.

Repository Issue Tracker Configuration
--------------------------------------

You can configure specific |repos| to use a different issue tracker than the
default one. See the instructions in :ref:`repo-it`

.. _issue-tr-eg-ref:


Jira Integration
----------------

Please check examples in the view for configuration the issue trackers.


Confluence (Wiki)
-----------------

Please check examples in the view for configuration the issue trackers.


Redmine Integration
-------------------

Please check examples in the view for configuration the issue trackers.


Redmine wiki Integration
------------------------

Please check examples in the view for configuration the issue trackers.


Pivotal Tracker
---------------

Please check examples in the view for configuration the issue trackers.


Trello
------

Please check examples in the view for configuration the issue trackers.

