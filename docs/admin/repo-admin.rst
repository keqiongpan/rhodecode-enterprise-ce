.. _repo-admin-set:
.. _permissions-info-add-group-ref:

Repository Administration
=========================

Repository permissions in |RCE| can be managed in a number of different ways.
This overview should give you an insight into how you could adopt particular
settings for your needs:

* Global |repo| permissions: This allows you to set the default permissions
  for each new |repo| created within |RCE|, see :ref:`repo-default-ref`. All
  |repos| created will inherit these permissions unless explicitly configured.
* Individual |repo| permissions: To set individual |repo| permissions,
  see :ref:`set-repo-perms`.
* Repository Group permissions: This allows you to define the permissions for
  a group, and all |repos| created within that group will inherit the same
  permissions.

.. toctree::

    repo_admin/repo-perm-steps
    repo_admin/repo-extra-fields
    repo_admin/repo-hooks
    repo_admin/repo-issue-tracker
    repo_admin/repo-vcs
    repo_admin/restore-deleted-repositories
    repo_admin/repo-admin-tasks