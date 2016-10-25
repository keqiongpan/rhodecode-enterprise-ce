.. _backup-ref:

Backup and Restore
==================

*“The condition of any backup is unknown until a restore is attempted.”*
`Schrödinger's Backup`_

To snapshot an instance of |RCE|, and save its settings, you need to backup the
following parts of the system at the same time.

* The |repos| managed by the instance together with the stored Gists.
* The |RCE| database.
* Any configuration files or extensions that you've configured. In most
  cases it's only the :file:`rhodecode.ini` file.
* Installer files such as those in `/opt/rhodecode` can be backed-up, however
  it's not required since in case of a recovery installer simply
  re-creates those.


.. important::

   Ideally you should script all of these functions so that it creates a
   backup snapshot of your system at a particular timestamp and then run that
   script regularly.

Backup Details
--------------

To backup the relevant parts of |RCE| required to restore your system, use
the information in this section to identify what is important to you.

Repository Backup
^^^^^^^^^^^^^^^^^

To back up your |repos|, use the API to get a list of all |repos| managed,
and then clone them to your backup location. This is the most safe backup option.
Backing up the storage directory could potentially result in a backup of
partially committed files or commits. (Backup taking place during a big push)
As an alternative you could use a rsync or simple `cp` commands if you can
ensure your instance is only in read-only mode or stopped at the moment.


Use the ``get_repos`` method to list all your managed |repos|,
and use the ``clone_uri`` information that is returned. See the :ref:`api`
for more information. Be sure to keep the structure or repositories with their
repository groups.

.. important::

   This will not work for |svn| |repos|. Currently the only way to back up
   your |svn| |repos| is to make a copy of them.

   It is also important to note, that you can only restore the |svn| |repos|
   using the same version as they were saved with.

Database Backup
^^^^^^^^^^^^^^^

The instance database contains all the |RCE| permissions settings,
and user management information. To backup your database,
export it using the following appropriate example, and then move it to your
backup location:

.. code-block:: bash

   # For MySQL DBs
   $ mysqldump -u <uname> -p <pass> rhodecode_db_name > mysql-db-backup
   # MySQL restore command
   $ mysql -u <uname> -p <pass> rhodecode_db_name < mysql-db-backup

   # For PostgreSQL DBs
   $ PGPASSWORD=<pass> pg_dump rhodecode_db_name > postgresql-db-backup
   # PosgreSQL restore
   $ PGPASSWORD=<pass> psql -U <uname> -h localhost -d rhodecode_db_name -1 -f postgresql-db-backup

   # For SQLite
   $ sqlite3 rhodecode.db ‘.dump’ > sqlite-db-backup
   # SQLite restore
   $ copy sqlite-db-backup rhodecode.db


The default |RCE| SQLite database location is
:file:`/home/{user}/.rccontrol/{instance-id}/rhodecode.db`

If running MySQL or PostgreSQL databases, you will have configured these
separately, for more information see :ref:`rhodecode-database-ref`

Configuration File Backup
^^^^^^^^^^^^^^^^^^^^^^^^^

Depending on your setup, you could have a number of configuration files that
should be backed up. You may have some, or all of the configuration files
listed in the :ref:`config-rce-files` section. Ideally you should back these
up at the same time as the database and |repos|. It really depends on if you need
the configuration file like logs, custom modules. We always recommend backing
those up.

Gist Backup
^^^^^^^^^^^

To backup the gists on your |RCE| instance you usually have to backup the
gist storage path. If this haven't been changed it's located inside
:file:`.rc_gist_store` and the metadata in :file:`.rc_gist_metadata`.
You can use the ``get_users`` and ``get_gists`` API methods to fetch the
gists for each user on the instance.

Extension Backups
^^^^^^^^^^^^^^^^^

You should also backup any extensions added in the
:file:`home/{user}/.rccontrol/{instance-id}/rcextensions` directory.

Full-text Search Backup
^^^^^^^^^^^^^^^^^^^^^^^

You may also have full text search set up, but the index can be rebuild from
re-imported |repos| if necessary. You will most likely want to backup your
:file:`mapping.ini` file if you've configured that. For more information, see
the :ref:`indexing-ref` section.

Restoration Steps
-----------------

To restore an instance of |RCE| from its backed up components, to a fresh
system use the following steps.

1. Install a new instance of |RCE| using sqlite option as database.
2. Restore your database.
2. Once installed, replace you backed up the :file:`rhodecode.ini` with your
   backup version. Ensure this file points to the restored
   database, see the :ref:`config-database` section.
3. Restart |RCE| and remap and rescan your |repos| to verify filesystem access,
   see the :ref:`remap-rescan` section.


Post Restoration Steps
^^^^^^^^^^^^^^^^^^^^^^

Once you have restored your |RCE| instance to basic functionality, you can
then work on restoring any specific setup changes you had made.

* To recreate the |RCE| index, use the backed up :file:`mapping.ini` file if
  you had made changes and rerun the indexer. See the
  :ref:`indexing-ref` section for details.
* To reconfigure any extensions, copy the backed up extensions into the
  :file:`/home/{user}/.rccontrol/{instance-id}/rcextensions` and also specify
  any custom hooks if necessary. See the :ref:`extensions-hooks-ref` section for
  details.

.. _Schrödinger's Backup: http://novabackup.novastor.com/blog/schrodingers-backup-good-bad-backup/
