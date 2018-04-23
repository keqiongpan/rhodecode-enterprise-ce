.. _svn-path-permissions:

|svn| Enabling Path Permissions
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Because |RCEE| uses standard svn apache mod_svn we can take advantage of the
authz configuration to protect paths and branches.


Configuring RhodeCode
=====================


1. To configure path based permissions first we need to use a customized
   mod_dav_svn.conf.

   Open :file:`home/{user}/.rccontrol/{instance-id}/rhodecode.ini` file.
   And find `svn.proxy.config_template` setting. Now set a new path to read
   the template from. For example:

    .. code-block:: ini

        svn.proxy.config_template = /home/ubuntu/rhodecode/custom_mod_dav_svn.conf.mako


2. Create the file as in example: `/home/ubuntu/rhodecode/custom_mod_dav_svn.conf.mako`
   You can download one from:

    `<https://code.rhodecode.com/rhodecode-enterprise-ce/files/default/rhodecode/apps/svn_support/templates/mod-dav-svn.conf.mako/>`_

3. Add (if not yet exists) a section `AuthzSVNReposRelativeAccessFile`  in order
   to read the path auth file.

   Example modified config section enabling reading the authz file relative
   to repository path. Means located in `/storage_dir/repo_name/conf/authz`

    .. code-block:: text


        # snip ...

        # use specific SVN conf/authz file for each repository
        AuthzSVNReposRelativeAccessFile authz

        Allow from all
        # snip ...

    .. note::

       The `AuthzSVNReposRelativeAccessFile` should go above the `Allow from all`
       directive.


4. Restart RhodeCode, Go to
   the :menuselection:`Admin --> Settings --> VCS` page, and
   click :guilabel:`Generate Apache Config`.
   This will now generate a new configuration with enabled changes to read
   the authz file. You can verify if changes were made by checking the generated
   mod_dav_svn.conf file which is included in your apache configuration.

5. Specify new rules in the repository authz configuration.
   edit a file in :file:`repo_name/conf/authz`. For example, we specify that
   only admin is allowed to push to develop branch

    .. code-block:: ini

        [/branches/develop]
        * = r
        admin = rw


   For more example see:
   `<https://svn.apache.org/repos/asf/subversion/trunk/subversion/mod_authz_svn/INSTALL/>`_

  Those rules also work for paths, so not only branches but all different
  paths inside the repository can be specified.

6. Reload Apache. If all is configured correctly it should not be allowed to
   commit according to specified rules.

