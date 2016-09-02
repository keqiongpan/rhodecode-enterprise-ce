
=======================
 Dependency management
=======================


Overview
========

We use the Nix package manager to handle our dependencies. In general we use the
packages out of the package collection `nixpkgs`. For frequently changing
dependencies for Python and JavaScript we use the tools which are described in
this section to generate the needed Nix derivations.


Python dependencies
===================

We use the tool `pip2nix` to generate the Nix derivations for our Python
dependencies.

Generating the dependencies should be done with the following command:

.. code:: shell

   pip2nix generate --license


.. note::

   License extraction support is still experimental, use the version from the
   following pull request: https://github.com/ktosiek/pip2nix/pull/30



Node dependencies
=================

After adding new dependencies via ``npm install --save``, use `node2nix` to
update the corresponding Nix derivations:

.. code:: shell

   cd pkgs
   node2nix --input ../package.json \
            -o node-packages.nix \
            -e node-env.nix \
            -c node-default.nix \
            -d --flatten


Bower dependencies
==================

Frontend dependencies are managed based on `bower`, with `bower2nix` a tool
exists which can generate the needed Nix derivations:

.. code:: shell

   bower2nix bower.json pkgs/bower-packages.nix
