.. _git-lfs-files:

|git| LFS Extension
===================


Git Large File Storage (or LFS) is a new, open-source extension to Git that
aims to improve handling of large files. It does this by replacing large files
in your repository—such as graphics and videos—with simple text pointers.
|RC| Server includes an embedded LFS object store server, allowing storage of
large files without the need for an external object store.
Git LFS is disabled by default, globally, and for each individual repository.

.. note::

    |RC| implements V2 API of Git LFS. Please make sure your git client is
    using the latest version (2.0.X recommended) to leverage full feature set
    of the V2 API.



Enabling Git LFS
++++++++++++++++

Git LFS is disabled by default within |RC| Server.

To enable Git LFS Globally:

    - Go to :menuselection:`Admin --> Settings --> VCS`

    - Scroll down into `Git settings`

    - Tick `Enable lfs extension`

    - Save your settings.

Those settings apply globally to each repository that inherits from the defaults
You can leave `lfs extension` disabled globally, and only enable it per
repository that would use the lfs.


.. note::

    You might want to adjust the global storage location at that point, however
    we recommend leaving the default one created.


Installing and using the Git LFS command line client
++++++++++++++++++++++++++++++++++++++++++++++++++++

Git LFS aims to integrate with the standard Git workflow as seamlessly
as possible. To push your first Git LFS files to an existing repository
Download and install the git-lfs command line client
Install the Git LFS filters::

    git lfs install

This adds the following lines to the .gitconfig file located in your home directory::

    [filter "lfs"]
        clean = git-lfs clean %f
        smudge = git-lfs smudge %f
        required = true

The above change applies globally, so it is not necessary to run this for
each repository you work with. Choose the file types you would like LFS to
handle by executing the git lfs track command. The git lfs track command
creates or updates the .gitattributes file in your repository.
Change to your cloned repository, then execute git add to ensure updates
to the .gitattributes are later committed::

    git lfs track "*.jpg"
    git add .gitattributes

Add, commit, and push your changes as you normally would::

    git add image.jpg
    git commit -m "Added an image"
    git push

When pushed, the Git tree updates to include a pointer to the file actual
file content. This pointer will include the SHA256 hash of the object and its
size in bytes. For example::

    oid sha256:4fa32d6f9b1461c4a53618a47324ee43e36ce7ceaea2ad440cc811a7e6881be1
    size 2580390


The object itself will be uploaded to a separate location via the Git LFS Batch API.
The transfer is validated and authorized by |RC| server itself.

If give repository has Git LFS disabled, a proper message will be sent back to
the client and upload of LFS objects will be forbidden.
