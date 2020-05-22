.. _known-issues:

Known Issues
============

Windows Upload
--------------

There can be an issue with uploading files from web interface on Windows,
and afterwards users cannot properly clone or synchronize with the repository.

Early testing shows that often uploading files via HTML forms on Windows
includes the full path of the file being uploaded and not the name of the file.

Old Format of Git Repositories
------------------------------

There is an issue when trying to import old |git| format |repos| into recent
versions of |RCE|. This issue can occur when importing from external |git|
repositories or from older versions of |RCE| (<=2.2.7).

To convert the old version into a current version, clone the old
|repo| into a local machine using a recent |git| client, then push it to a new
|repo| inside |RCE|.


VCS Server Memory Consumption
-----------------------------

The VCS Server cache grows without limits if not configured correctly. This
applies to |RCE| versions prior to the 3.3.2 releases, as 3.3.2
shipped with the optimal configuration as default. See the
:ref:`vcs-server-maintain` section for details.

To fix this issue, upgrade to |RCE| 3.3.2 or greater, and if you discover
memory consumption issues check the VCS Server settings.

Newer Operating system locales
------------------------------

|RCC| has a know problem with locales, due to changes in glibc 2.27+ which affects
the local-archive format, which is now incompatible with our used glibc 2.26.

Mostly affected are:
- Fedora 23+
- Ubuntu 18.04
- CentOS / RHEL 8

To work around this problem, you need set path to ``$LOCAL_ARCHIVE`` to the
locale package in older pre glibc 2.27 format, or set `LC_ALL=C` in your enviroment.

To use the pre 2.27 locale-archive fix follow these steps:

1. Download the pre 2.27 locale-archive package

.. code-block:: bash

    wget https://dls.rhodecode.com/assets/locale-archive


2. Point ``$LOCAL_ARCHIVE`` to the locale package.

.. code-block:: bash

    $ export LOCALE_ARCHIVE=/home/USER/locale-archive  # change to your path

This should be added *both* in `enviroment` variable of `~/.rccontrol/supervisor/supervisord.ini`
e.g

```
[supervisord]
environment = HOME=/home/user/rhodecode,LOCALE_ARCHIVE=/YOUR-PATH/locale-archive`
```

and in user .bashrc/.zshrc etc, or via a startup script that
runs `rccontrol self-init`

If you happen to be running |RCC| from systemd, use the following
example to pass the correct locale information on boot.

.. code-block:: ini

    [Unit]
    Description=Rhodecode
    After=network.target

    [Service]
    Type=forking
    User=scm
    Environment="LOCALE_ARCHIVE=/YOUR-PATH/locale-archive"
    ExecStart=/YOUR-PATH/.rccontrol-profile/bin/rccontrol-self-init

    [Install]
    WantedBy=multi-user.target

