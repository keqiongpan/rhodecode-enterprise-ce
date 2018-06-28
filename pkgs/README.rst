
==============================
 Generate the Nix expressions
==============================

Details can be found in the repository of `RhodeCode Enterprise CE`_ inside of
the file `docs/contributing/dependencies.rst`.

Start the environment as follows:

.. code:: shell

   nix-shell pkgs/shell-generate.nix



Python dependencies
===================

.. code:: shell

   pip2nix generate --licenses
   # or
   nix-shell pkgs/shell-generate.nix --command "pip2nix generate --licenses"


NodeJS dependencies
===================

.. code:: shell

   # switch to pkgs dir
   pushd pkgs
   node2nix --input ../package.json \
            -o node-packages.nix \
            -e node-env.nix \
            -c node-default.nix \
            -d --flatten --nodejs-6
   popd



Bower dependencies
==================

.. code:: shell

   bower2nix bower.json pkgs/bower-packages.nix
   # or
   nix-shell pkgs/shell-generate.nix --command "bower2nix bower.json pkgs/bower-packages.nix"


.. Links

.. _RhodeCode Enterprise CE: https://code.rhodecode.com/rhodecode-enterprise-ce
