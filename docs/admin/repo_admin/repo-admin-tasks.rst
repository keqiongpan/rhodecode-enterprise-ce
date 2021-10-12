.. _repo-admin-tasks:

Common Admin Tasks for Repositories
-----------------------------------


Manually Force Delete Repository
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

In case of attached forks or pull-requests repositories should be archived.
Here is how to force delete a repository and remove all dependent objects


.. code-block:: bash
   :dedent: 1

    # starts the ishell interactive prompt
    $ rccontrol ishell enterprise-1

.. code-block:: python
   :dedent: 1

    In [4]: from rhodecode.model.repo import RepoModel
    In [3]: repo = Repository.get_by_repo_name('test_repos/repo_with_prs')
    In [5]: RepoModel().delete(repo, forks='detach', pull_requests='delete')
    In [6]: Session().commit()


Below is a fully automated example to force delete repositories reading from a
file where each line is a repository name. This can be executed via simple CLI command
without entering the interactive shell.

Save the below content as a file named `repo_delete_task.py`


.. code-block:: python
   :dedent: 1

    from rhodecode.model.db import *
    from rhodecode.model.repo import RepoModel
    with open('delete_repos.txt', 'rb') as f:
        # read all lines from file
        repos = f.readlines()
        for repo_name in repos:
            repo_name = repo_name.strip()  # cleanup the name just in case
            repo = Repository.get_by_repo_name(repo_name)
            if not repo:
                raise Exception('Repo with name {} not found'.format(repo_name))
            RepoModel().delete(repo, forks='detach', pull_requests='delete')
            Session().commit()
            print('Removed repository {}'.format(repo_name))


The code above will read the names of repositories from a file called `delete_repos.txt`
Each lines should represent a single name e.g `repo_name_1` or `repo_group/repo_name_2`

Run this line from CLI to execute the code from the `repo_delete_task.py` file and
exit the ishell after the execution::

    echo "%run repo_delete_task.py" | rccontrol ishell enterprise-1




Bulk edit permissions for all repositories or groups
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

In case when a permissions should be applied in bulk here are two ways to apply
the permissions onto *all* repositories and/or repository groups.

1) Start by running the interactive ishell interface

.. code-block:: bash
   :dedent: 1

    # starts the ishell interactive prompt
    $ rccontrol ishell enterprise-1


2a) Add user called 'admin' into all repositories with write permission.
    Permissions can be also `repository.read`, `repository.admin`, `repository.none`

.. code-block:: python
   :dedent: 1

   In [1]: from rhodecode.model.repo import RepoModel
   In [2]: user = User.get_by_username('admin')
   In [3]: permission_name = 'repository.write'
   In [4]: for repo in Repository.get_all():
      ...:     RepoModel().grant_user_permission(repo, user, permission_name)
      ...:     Session().commit()

2b) Add user called 'admin' into all repository groups with write permission.
    Permissions can be also can be `group.read`, `group.admin`, `group.none`

.. code-block:: python
   :dedent: 1

   In [1]: from rhodecode.model.repo import RepoModel
   In [2]: user = User.get_by_username('admin')
   In [3]: permission_name = 'group.write'
   In [4]: for repo_group in RepoGroup.get_all():
       ...:     RepoGroupModel().grant_user_permission(repo_group, user, permission_name)
       ...:     Session().commit()


Delete a problematic pull request
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python
   :dedent: 1

   In [1]: from rhodecode.model.pull_request import PullRequestModel
   In [2]: pullrequest_id = 123
   In [3]: pr = PullRequest.get(pullrequest_id)
   In [4]: super_admin = User.get_first_super_admin()
   In [5]: PullRequestModel().delete(pr, super_admin)
   In [6]: Session().commit()
