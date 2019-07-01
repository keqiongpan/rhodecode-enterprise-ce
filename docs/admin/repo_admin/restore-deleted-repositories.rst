.. _restore-deleted-repositories:

Restoring Deleted Repositories
==============================

By default when repository or whole repository group is deleted an archived copy
of filesystem repositories are kept. You can see them as special entries in the
repository storage such as::

    drwxrwxr-x   3 rcdev rcdev  4096 Dec  4  2017 rm__20171204_105727_400795__ce-import
    drwxrwxr-x   6 rcdev rcdev  4096 Nov 21  2017 rm__20180221_152430_675047__svn-repo
    drwxr-xr-x   7 rcdev rcdev  4096 Mar 28  2018 rm__20180328_143124_617576__test-git
    drwxr-xr-x   7 rcdev rcdev  4096 Mar 28  2018 rm__20180328_144954_317729__test-git-install-hooks


Data from those repositories can be restored by simply removing the
`rm_YYYYDDMM_HHMMSS_DDDDDD__` prefix and additionally only in case of Mercurial
repositories remove the `.hg` store prefix.::

    rm__.hg => .hg


For Git or SVN repositories this operation is not required.

After removing the prefix repository can be brought by opening
:menuselection:`Admin --> Settings --> Remap and Rescan` and running `Rescan Filesystem`

This will create a new DB entry restoring the data previously removed.
To restore OLD database entries this should be done by restoring from a Database backup.

RhodeCode also keeps the repository group structure, this is marked by entries that
in addition have GROUP in the prefix, eg::

    drwxr-xr-x   2 rcdev rcdev  4096 Jan 18 16:13 rm__20181130_120650_977082_GROUP_Test1
    drwxr-xr-x   2 rcdev rcdev  4096 Jan 18 16:13 rm__20181130_120659_922952_GROUP_Docs



.. note::

    RhodeCode Tools have a special cleanup tool for the archived repositories. Please
    see :ref:`clean-up-cmds`
