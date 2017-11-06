.. _ssh-connection:

SSH Connection
--------------

If you wish to connect to your |repos| using SSH protocol, use the
following instructions.

1. Include |RCE| generated `authorized_keys` file into your sshd_config.

   By default a file `authorized_keys_rhodecode` is created containing
   configuration and all allowed user connection keys are stored inside.
   On each change of stored keys inside |RCE| this file is updated with
   proper data.

   .. code-block:: bash

       # Edit sshd_config file most likely at /etc/ssh/sshd_config
       # add or edit the AuthorizedKeysFile, and set to use custom files

       AuthorizedKeysFile %h/.ssh/authorized_keys %h/.ssh/authorized_keys_rhodecode

   This way we use a separate file for SSH access and separate one for
   SSH access to |RCE| repositories.


2. Enable the SSH module on instance.

   On the server where |RCE| is running executing:

   .. code-block:: bash

       rccontrol enable-module ssh {instance-id}

   This will add the following configuration into :file:`rhodecode.ini`.
   This also can be done manually:

   .. code-block:: ini

        ############################################################
        ### SSH Support Settings                                 ###
        ############################################################

        ## Defines if a custom authorized_keys file should be created and written on
        ## any change user ssh keys. Setting this to false also disables posibility
        ## of adding SSH keys by users from web interface. Super admins can still
        ## manage SSH Keys.
        ssh.generate_authorized_keyfile = true

        ## Options for ssh, default is `no-pty,no-port-forwarding,no-X11-forwarding,no-agent-forwarding`
        # ssh.authorized_keys_ssh_opts =

        ## Path to the authrozied_keys file where the generate entries are placed.
        ## It is possible to have multiple key files specified in `sshd_config` e.g.
        ## AuthorizedKeysFile %h/.ssh/authorized_keys %h/.ssh/authorized_keys_rhodecode
        ssh.authorized_keys_file_path = ~/.ssh/authorized_keys_rhodecode

        ## Command to execute the SSH wrapper. The binary is available in the
        ## rhodecode installation directory.
        ## e.g ~/.rccontrol/community-1/profile/bin/rc-ssh-wrapper
        ssh.wrapper_cmd = ~/.rccontrol/community-1/rc-ssh-wrapper

        ## Allow shell when executing the ssh-wrapper command
        ssh.wrapper_cmd_allow_shell = false

        ## Enables logging, and detailed output send back to the client during SSH
        ## operations. Usefull for debugging, shouldn't be used in production.
        ssh.enable_debug_logging = false

        ## Paths to binary executable, by default they are the names, but we can
        ## override them if we want to use a custom one
        ssh.executable.hg = ~/.rccontrol/vcsserver-1/profile/bin/hg
        ssh.executable.git = ~/.rccontrol/vcsserver-1/profile/bin/git
        ssh.executable.svn = ~/.rccontrol/vcsserver-1/profile/bin/svnserve


3. Set base_url for instance to enable proper event handling (Optional):

   If you wish to have integrations working correctly via SSH please configure
   The Application base_url.

   Use the ``rccontrol status`` command to view instance details.
   Hostname is required for the integration to properly set the instance URL.

   When your hostname is known (e.g https://code.rhodecode.com) please set it
   inside :file:`/home/{user}/.rccontrol/{instance-id}/rhodecode.ini`

   add into `[app:main]` section the following configuration:

   .. code-block:: ini

       app.base_url = https://code.rhodecode.com


4. Add the public key to your user account for testing.
   First generate a new key, or use your existing one and have your public key
   at hand.

   Go to
   :menuselection:`My Account --> SSH Keys` and add the public key with proper description.

   This will generate a new entry inside our configured `authorized_keys_rhodecode` file.

   Test the connection from your local machine using the following example:

   .. note::

       In case of connection problems please set
       `ssh.enable_debug_logging = true` inside the SSH configuration of
       :file:`/home/{user}/.rccontrol/{instance-id}/rhodecode.ini`
       Then add, remove your SSH key and try connecting again.
       Debug logging will be printed to help find the problems on the server side.

   Test connection using the ssh command from the local machine


   For SVN:

   .. code-block:: bash

       SVN_SSH="ssh -i ~/.ssh/id_rsa_test_ssh" svn checkout svn+ssh://rhodecode@rc-server/repo_name

   For GIT:

   .. code-block:: bash

       GIT_SSH_COMMAND='ssh -i ~/.ssh/id_rsa_test_ssh' git clone ssh://rhodecode@rc-server/repo_name

   For Mercurial:

   .. code-block:: bash

       Add to hgrc:

       [ui]
       ssh = ssh -C -i ~/.ssh/id_rsa_test_ssh

       hg clone ssh://rhodecode@rc-server/repo_name
