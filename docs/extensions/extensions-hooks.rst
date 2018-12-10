.. _extensions-hooks-ref:

Extensions & Hooks
==================

The extensions & hooks section references three concepts regularly,
so to clarify what is meant each time, read the following definitions:

* **Plugin**: A Plugin is software that adds a specific feature to
  an existing software application.
* **Extension**: An extension extends the capabilities of,
  or the data available to, an existing software application.
* **Hook**: A hook intercepts function calls, messages, or events passed
  between software components and can be used to trigger plugins, or their
  extensions.


Hooks
-----

Within |RCE| there are two types of supported hooks.

* **Internal built-in hooks**: The internal |hg|, |git| or |svn| hooks are
  triggered by different VCS operations, like push, pull,
  or clone and are non-configurable, but you can add your own VCS hooks,
  see :ref:`custom-hooks`.
* **Custom rcextensions hooks**: User defined hooks centre around the lifecycle of
  certain actions such are |repo| creation, user creation etc. The actions
  these hooks trigger can be rejected based on the API permissions of the
  user calling them.

On instructions how to use the custom `rcextensions`
see :ref:`integrations-rcextensions` section.



