.. _svn-http:

|svn| With Write Over HTTP
^^^^^^^^^^^^^^^^^^^^^^^^^^

To use |svn| with read/write support over the |svn| HTTP protocol, you have to
configure the HTTP |svn| backend.

Prerequisites
=============

- Enable HTTP support inside the admin VCS settings on your |RCE| instance
- You need to install the following tools on the machine that is running an
  instance of |RCE|:
  ``Apache HTTP Server`` and ``mod_dav_svn``.


.. tip::

   We recommend using Wandisco repositories which provide latest SVN versions
   for most platforms.
   Here is an example how to add the Wandisco repositories for Ubuntu.

    .. code-block:: bash

        $ sudo sh -c 'echo "deb http://opensource.wandisco.com/ubuntu `lsb_release -cs` svn110" >> /etc/apt/sources.list.d/subversion110.list'
        $ sudo wget -q http://opensource.wandisco.com/wandisco-debian-new.gpg -O- | sudo apt-key add -
        $ sudo apt-get update

    Here is an example how to add the Wandisco repositories for Centos/Redhat. Using
    a yum config

    .. code-block:: bash

        [wandisco-Git]
        name=CentOS-6 - Wandisco Git
        baseurl=http://opensource.wandisco.com/centos/6/git/$basearch/
        enabled=1
        gpgcheck=1
        gpgkey=http://opensource.wandisco.com/RPM-GPG-KEY-WANdisco



Example installation of required components for Ubuntu platform:

.. code-block:: bash

    $ sudo apt-get install apache2
    $ sudo apt-get install libapache2-svn

Once installed you need to enable ``dav_svn`` on Ubuntu:

.. code-block:: bash

    $ sudo a2enmod dav_svn
    $ sudo a2enmod headers
    $ sudo a2enmod authn_anon


Example installation of required components for RedHat/CentOS platform:

.. code-block:: bash

    $ sudo yum install httpd
    $ sudo yum install subversion mod_dav_svn


Once installed you need to enable ``dav_svn`` on RedHat/CentOS:

.. code-block:: bash

    sudo vi /etc/httpd/conf.modules.d/10-subversion.conf
    ## The file should read:

    LoadModule dav_svn_module     modules/mod_dav_svn.so
    LoadModule headers_module     modules/mod_headers.so
    LoadModule authn_anon_module  modules/mod_authn_anon.so


Configuring Apache Setup
========================

.. tip::

   It is recommended to run Apache on a port other than 80, due to possible
   conflicts with other HTTP servers like nginx. To do this, set the
   ``Listen`` parameter in the ``/etc/apache2/ports.conf`` file, for example
   ``Listen 8090``.


.. warning::

   Make sure your Apache instance which runs the mod_dav_svn module is
   only accessible by |RCE|. Otherwise everyone is able to browse
   the repositories or run subversion operations (checkout/commit/etc.).

It is also recommended to run apache as the same user as |RCE|, otherwise
permission issues could occur. To do this edit the ``/etc/apache2/envvars``

   .. code-block:: apache

      export APACHE_RUN_USER=rhodecode
      export APACHE_RUN_GROUP=rhodecode

1. To configure Apache, create and edit a virtual hosts file, for example
   :file:`/etc/apache2/sites-enabled/default.conf`. Below is an example
   how to use one with auto-generated config ```mod_dav_svn.conf```
   from configured |RCE| instance.

.. code-block:: apache

    <VirtualHost *:8090>
        ServerAdmin rhodecode-admin@localhost
        DocumentRoot /var/www/html
        ErrorLog ${'${APACHE_LOG_DIR}'}/error.log
        CustomLog ${'${APACHE_LOG_DIR}'}/access.log combined
        LogLevel info
        # allows custom host names, prevents 400 errors on checkout
        HttpProtocolOptions Unsafe
        Include /home/user/.rccontrol/enterprise-1/mod_dav_svn.conf
    </VirtualHost>


2. Go to the :menuselection:`Admin --> Settings --> VCS` page, and
   enable :guilabel:`Proxy Subversion HTTP requests`, and specify the
   :guilabel:`Subversion HTTP Server URL`.

3. Open the |RCE| configuration file,
   :file:`/home/{user}/.rccontrol/{instance-id}/rhodecode.ini`

4. Add the following configuration option in the ``[app:main]``
   section if you don't have it yet.

   This enables mapping of the created |RCE| repo groups into special
   |svn| paths. Each time a new repository group is created, the system will
   update the template file and create new mapping. Apache web server needs to
   be reloaded to pick up the changes on this file.
   To do this, simply configure `svn.proxy.reload_cmd` inside the .ini file.
   Example configuration:


.. code-block:: ini

    ############################################################
    ### Subversion proxy support (mod_dav_svn)               ###
    ### Maps RhodeCode repo groups into SVN paths for Apache ###
    ############################################################
    ## Enable or disable the config file generation.
    svn.proxy.generate_config = true
    ## Generate config file with `SVNListParentPath` set to `On`.
    svn.proxy.list_parent_path = true
    ## Set location and file name of generated config file.
    svn.proxy.config_file_path = %(here)s/mod_dav_svn.conf
    ## Used as a prefix to the <Location> block in the generated config file.
    ## In most cases it should be set to `/`.
    svn.proxy.location_root = /
    ## Command to reload the mod dav svn configuration on change.
    ## Example: `/etc/init.d/apache2 reload`
    svn.proxy.reload_cmd = /etc/init.d/apache2 reload
    ## If the timeout expires before the reload command finishes, the command will
    ## be killed. Setting it to zero means no timeout. Defaults to 10 seconds.
    #svn.proxy.reload_timeout = 10


This would create a special template file called ```mod_dav_svn.conf```. We
used that file path in the apache config above inside the Include statement.
It's also possible to manually generate the config from the
:menuselection:`Admin --> Settings --> VCS` page by clicking a
`Generate Apache Config` button.

5. Now only things left is to enable svn support, and generate the initial
   configuration.

   - Select `Proxy subversion HTTP requests` checkbox
   - Enter http://localhost:8090 into `Subversion HTTP Server URL`
   - Click the `Generate Apache Config` button.

This config will be automatically re-generated once an user-groups is added
to properly map the additional paths generated.



Using |svn|
===========

Once |svn| has been enabled on your instance, you can use it with the
following examples. For more |svn| information, see the `Subversion Red Book`_

.. code-block:: bash

    # To clone a repository
    svn checkout http://my-svn-server.example.com/my-svn-repo

    # svn commit
    svn commit


.. _Subversion Red Book: http://svnbook.red-bean.com/en/1.7/svn-book.html#svn.ref.svn

.. _Ask Ubuntu: http://askubuntu.com/questions/162391/how-do-i-fix-my-locale-issue