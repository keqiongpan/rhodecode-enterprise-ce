.. _user-admin-tasks:

Common Admin Tasks for Users
----------------------------


Manually Set Personal Repository Group
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Here is how to set a repository group as personal for a user using ishell.


.. code-block:: bash

    # starts the ishell interactive prompt
    $ rccontrol ishell enterprise-1

.. code-block:: python

    In [1]: repo_group = RepoGroup.get_by_group_name('some_group_name')
    In [2]: user = User.get_by_username('some_user')
    In [3]: repo_group.user = user
    In [4]: repo_group.personal = True
    In [5]: Session().add(repo_group);Session().commit()
