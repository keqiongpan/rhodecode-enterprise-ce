.. _user-admin-set:

User Administration
===================

|RCE| enables you to define permissions for the following entities within the
system; **users**, **user groups**, **repositories**, **repository groups**.

Within each one of these entities you can set default settings,
and then all users or |repos| inherit those default permission settings
unless individually defined. Each of these entities can have the following
permissions applied to it; |perm|.

.. toctree::

    user_admin/public-access
    user_admin/default-user-perms
    user_admin/adding-anonymous-user
    user_admin/adding-new-user
    user_admin/setting-default-permissions
    user_admin/setting-usergroup-permissions
    user_admin/user-admin-tasks

.. |perm| replace:: **None**, **Read**, **Write**, or **Admin**
