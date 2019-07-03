.. _repo-admin-tasks:

Common Admin Tasks for Repositories
-----------------------------------


Manually Force Delete Repository
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

In case of attached forks or pull-requests repositories should be archived.
Here is how to force delete a repository and remove all dependent objects


.. code-block:: bash

    # starts the ishell interactive prompt
    $ rccontrol ishell enterprise-1

.. code-block:: python

    In [4]: from rhodecode.model.repo import RepoModel
    In [3]: repo = Repository.get_by_repo_name('test_repos/repo_with_prs')
    In [5]: RepoModel().delete(repo, forks='detach', pull_requests='delete')
    In [6]: Session().commit()
