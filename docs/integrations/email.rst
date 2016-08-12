.. _integrations-email:

Email integration
=================

The email integration allows you to send the summary of repo pushes to a
list of email recipients in the format:

An example::

    User: johndoe
    Branches: default
    Repository: http://rhodecode.company.com/repo
    Commit: 8eab60a44a612e331edfcd59b8d96b2f6a935cd9
    URL: http://rhodecode.company.com/repo/changeset/8eab60a44a612e331edfcd59b8d96b2f6a935cd9
    Author: John Doe
    Date: 2016-03-01 11:20:44
    Commit Message:

    fixed bug with thing


To create one, create a ``email`` integration in `creating-integrations`.
