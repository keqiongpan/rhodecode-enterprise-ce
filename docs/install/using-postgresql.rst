.. _install-postgresql-database:

PostgreSQL
----------

To use a PostgreSQL database, you should install and configure the database
before installing |RCE|. This is because during |RCE| installation you will
setup the connection to your PostgreSQL database. To work with PostgreSQL,
use the following steps:

1. Depending on your |os|, install a PostgreSQL database following the
   appropriate instructions from the `PostgreSQL website`_.
2. Configure the database with a username and password, which you will use
   with |RCE|.
3. Install |RCE|, and during installation select PostgreSQL as your database.
4. Enter the following information during the database setup:

   * Your network IP Address
   * The port number for PostgreSQL access; the default port is ``5434``
   * Your database username
   * Your database password
   * A new database name

.. _PostgreSQL website: http://www.postgresql.org/
