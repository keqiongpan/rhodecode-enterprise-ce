.. _user-session-ref:

Increase User Session Performance
---------------------------------

The default file-based sessions are only suitable for smaller setups, or
instances that doesn't have a lot of users or traffic.
They are set as default option because it's setup-free solution.

The most common issue of file based sessions are file limit errors which occur
if there are lots of session files.

Therefore, in a large scale deployment, to give better performance,
scalability, and maintainability we recommend switching from file-based
sessions to database-based user sessions or memcached sessions.

To switch to database-based user sessions uncomment the following section in
your :file:`/home/{user}/.rccontrol/{instance-id}/rhodecode.ini` file.


.. code-block:: ini

      ## db based session, fast, and allows easy management over logged in users
      beaker.session.type = ext:database
      beaker.session.table_name = db_session

      # use just one of the following accoring to the type of database
      beaker.session.sa.url = postgresql://postgres:secret@localhost/rhodecode
      beaker.session.sa.url = mysql://root:secret@127.0.0.1/rhodecode

      beaker.session.sa.pool_recycle = 3600
      beaker.session.sa.echo = false


and make sure you comment out the file based sessions.

.. code-block:: ini

      ## types are file, ext:memcached, ext:database, and memory (default).
      #beaker.session.type = file
      #beaker.session.data_dir = %(here)s/data/sessions/data


To switch to memcached-based user sessions uncomment the following section in
your :file:`/home/{user}/.rccontrol/{instance-id}/rhodecode.ini` file.

.. code-block:: ini

      ## memcached sessions
      beaker.session.type = ext:memcached
      beaker.session.url = localhost:11211


and make sure you comment out the file based sessions.

.. code-block:: ini

      ## types are file, ext:memcached, ext:database, and memory (default).
      #beaker.session.type = file
      #beaker.session.data_dir = %(here)s/data/sessions/data