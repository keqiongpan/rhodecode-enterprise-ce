.. _dev-setup:

===================
 Development setup
===================


RhodeCode Enterprise runs inside a Nix managed environment. This ensures build
environment dependencies are correctly declared and installed during setup.
It also enables atomic upgrades, rollbacks, and multiple instances of RhodeCode
Enterprise running with isolation.

To set up RhodeCode Enterprise inside the Nix environment, use the following steps:



Setup Nix Package Manager
-------------------------

To install the Nix Package Manager, please run::

   $ curl https://releases.nixos.org/nix/nix-2.3.4/install | sh

or go to https://nixos.org/nix/ and follow the installation instructions.
Once this is correctly set up on your system, you should be able to use the
following commands:

* `nix-env`

* `nix-shell`


.. tip::

   Update your channels frequently by running ``nix-channel --update``.

.. note::

   To uninstall nix run the following:

    remove the . "$HOME/.nix-profile/etc/profile.d/nix.sh" line in your ~/.profile or ~/.bash_profile
    rm -rf $HOME/{.nix-channels,.nix-defexpr,.nix-profile,.config/nixpkgs}
    sudo rm -rf /nix

Switch nix to the latest STABLE channel
---------------------------------------

run::

   nix-channel --add https://nixos.org/channels/nixos-20.03 nixpkgs

Followed by::

   nix-channel --update
   nix-env -i nix-2.3.4


Install required binaries
-------------------------

We need some handy tools first.

run::

    nix-env -i nix-prefetch-hg
    nix-env -i nix-prefetch-git


Speed up JS build by installing PhantomJS
-----------------------------------------

PhantomJS will be downloaded each time nix-shell is invoked. To speed this by
setting already downloaded version do this::

    nix-env -i phantomjs-2.1.1

    # and set nix bin path
    export PATH=$PATH:~/.nix-profile/bin


Clone the required repositories
-------------------------------

After Nix is set up, clone the RhodeCode Enterprise Community Edition and
RhodeCode VCSServer repositories into the same directory.
RhodeCode currently is using Mercurial Version Control System, please make sure
you have it installed before continuing.

To obtain the required sources, use the following commands::

    mkdir rhodecode-develop && cd rhodecode-develop
    hg clone -u default https://code.rhodecode.com/rhodecode-enterprise-ce
    hg clone -u default https://code.rhodecode.com/rhodecode-vcsserver

.. note::

   If you cannot clone the repository, please contact us via support@rhodecode.com


Install some required libraries
-------------------------------

There are some required drivers and dev libraries that we need to install to
test RhodeCode under different types of databases. For example in Ubuntu we
need to install the following.

required libraries::

    # svn related
    sudo apt-get install libapr1-dev libaprutil1-dev
    sudo apt-get install libsvn-dev
    # libcurl required too
    sudo apt-get install libcurl4-openssl-dev
    # mysql/pg server for development, optional
    sudo apt-get install mysql-server libmysqlclient-dev
    sudo apt-get install postgresql postgresql-contrib libpq-dev



Enter the Development Shell
---------------------------

The final step is to start the development shells. To do this, run the
following command from inside the cloned repository::

   # first, the vcsserver
   cd ~/rhodecode-vcsserver
   nix-shell

   # then enterprise sources
   cd ~/rhodecode-enterprise-ce
   nix-shell

.. note::

   On the first run, this will take a while to download and optionally compile
   a few things. The following runs will be faster. The development shell works
   fine on both MacOS and Linux platforms.


Create config.nix for development
---------------------------------

In order to run proper tests and setup linking across projects, a config.nix
file needs to be setup::

    # create config
    mkdir -p ~/.nixpkgs
    touch ~/.nixpkgs/config.nix

    # put the below content into the ~/.nixpkgs/config.nix file
    # adjusts, the path to where you cloned your repositories.

    {
      rc = {
       sources = {
        rhodecode-vcsserver = "/home/dev/rhodecode-vcsserver";
        rhodecode-enterprise-ce = "/home/dev/rhodecode-enterprise-ce";
        rhodecode-enterprise-ee = "/home/dev/rhodecode-enterprise-ee";
       };
      };
    }



Creating a Development Configuration
------------------------------------

To create a development environment for RhodeCode Enterprise,
use the following steps:

1. Create a copy of vcsserver config:
    `cp ~/rhodecode-vcsserver/configs/development.ini ~/rhodecode-vcsserver/configs/dev.ini`
2. Create a copy of rhodocode config:
    `cp ~/rhodecode-enterprise-ce/configs/development.ini ~/rhodecode-enterprise-ce/configs/dev.ini`
3. Adjust the configuration settings to your needs if needed.

.. note::

  It is recommended to use the name `dev.ini` since it's included in .hgignore file.


Setup the Development Database
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To create a development database, use the following example. This is a one
time operation executed from the nix-shell of rhodecode-enterprise-ce sources ::

    rc-setup-app dev.ini \
        --user=admin --password=secret \
        --email=admin@example.com \
        --repos=~/my_dev_repos


Compile CSS and JavaScript
^^^^^^^^^^^^^^^^^^^^^^^^^^

To use the application's frontend and prepare it for production deployment,
you will need to compile the CSS and JavaScript with Grunt.
This is easily done from within the nix-shell using the following command::

    make web-build

When developing new features you will need to recompile following any
changes made to the CSS or JavaScript files when developing the code::

    grunt watch

This prepares the development (with comments/whitespace) versions of files.

Start the Development Servers
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

From the rhodecode-vcsserver directory, start the development server in another
nix-shell, using the following command::

      pserve configs/dev.ini

In the adjacent nix-shell which you created for your development server, you may
now start CE with the following command::


      pserve --reload configs/dev.ini

.. note::

  `--reload` flag will automatically reload the server when source file changes.


Run the Environment Tests
^^^^^^^^^^^^^^^^^^^^^^^^^

Please make sure that the tests are passing to verify that your environment is
set up correctly. RhodeCode uses py.test to run tests.
While your instance is running, start a new nix-shell and simply run
``make test`` to run the basic test suite.


Need Help?
^^^^^^^^^^

Join us on Slack via https://rhodecode.com/join or post questions in our
Community Portal at https://community.rhodecode.com
