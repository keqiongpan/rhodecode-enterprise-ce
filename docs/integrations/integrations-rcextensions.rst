.. _integrations-rcextensions:


rcextensions integrations
=========================


Since RhodeCode 4.14 release rcextensions aren't part of rhodecode-tools, and instead
they are shipped with the new or upgraded installations.

The rcextensions template `rcextensions.tmpl` is created in the `etc/` directory
of enterprise or community installation. It's always re-created and updated on upgrades.


Activating rcextensions
+++++++++++++++++++++++

To activate rcextensions simply copy or rename the created template rcextensions
into the path where the rhodecode.ini file is located::

    pushd ~/.rccontrol/enterprise-1/
    or
    pushd ~/.rccontrol/community-1/

    mv profile/etc/rcextensions.tmpl rcextensions


rcextensions are loaded when |RCE| starts. So a restart is required after activation or
change of code in rcextensions.

Simply restart only the enterprise/community instance::

    rccontrol restart enterprise-1
    or
    rccontrol restart community-1


Example usage
+++++++++++++


To see examples of usage please check the examples directory under:

https://code.rhodecode.com/rhodecode-enterprise-ce/files/stable/rhodecode/config/rcextensions/examples
