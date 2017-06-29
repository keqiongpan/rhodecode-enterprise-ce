.. _integrations-ci:

CI Server integration
=====================


RhodeCode :ref:`integrations-webhook` integration is a powerfull tool to allow
interaction with systems like Jenkin, Bamboo, TeamCity, CircleCi or any other
CI server that allows triggering a build using HTTP call.

Below are few examples on how to use :ref:`integrations-webhook` to trigger
a CI build.


General Webhook
+++++++++++++++

:ref:`integrations-webhook` allows sending a JSON payload information to specified
url with GET or POST methods. There are several variables that could be used
in the URL greatly extending the flexibility of this type of integration.

Most of the modern CI systems such as Jenkins, TeamCity, Bamboo or CircleCi
allows triggering builds via GET or POST calls.

:ref:`integrations-webhook` can be either specified per each repository or
globally, if your CI maps directly to all your projects a global
:ref:`integrations-webhook` integration can be created and will trigger builds
for each change in projects. If only some projects allow triggering builds a
global integration will also work because mostly a CI system will ignore a
call for unspecified builds.


.. note::

    A quick note on security. It's recommended to allow IP restrictions
    to only allow RhodeCode server to trigger builds. If you need to
    specify username and password this could be done by embedding it into a
    trigger URL, e.g. `http://user:password@server.com/job/${project_id}`


If users require to provide any custom parameters, they can be stored for each
project inside the :ref:`repo-xtra`. For example to migrate a current job that
has a numeric build id, storing this as `jenkins_build_id` key extra field
the url would look like that::

    http://server/job/${extra:jenkins_build_id}/


.. note::

    Please note that some variables will result in multiple calls.
    e.g. for |HG| specifying `${branch}` will trigger as many builds as how
    many branches the suer actually pushed. Same applies to `${commit_id}`
    This will trigger many builds if many commits are pushed. This allows
    triggering individual builds for each pushed commit.


Jenkins
+++++++

To use Jenkins CI with RhodeCode, a Jenkins Build with Parameters should be used.
Plugin details are available here: https://wiki.jenkins.io/display/JENKINS/Build+With+Parameters+Plugin

If the plugin is configured, RhodeCode can trigger builds automatically by
calling such example url provided in :ref:`integrations-webhook` integration::

    http://server/job/${project_id}/build-branch-${branch}/buildWithParameters?token=TOKEN&PARAMETER=value&PARAMETER2=value2


Team City
+++++++++

To use TeamCity CI it's enough to call the API and provide a buildId.
Example url after configuring :ref:`repo-xtra` would look like that::

    http://teacmtiyserver/viewType.html?buildTypeId=${extra:tc_build_id}


Each project can have many build configurations.
buildTypeId which is a unique ID for each build configuration (job).


CircleCi
++++++++

To use CircleCi, a POST call needs to be triggered. Example build url would
look like this::

    http://cicleCiServer/project/${repo_type}/${username}/${repo_id}/tree/${branch}


Circle Ci expects format of::

    POST: /project/:vcs-type/:username/:project/tree/:branch


CircleCi API documentation can be found here: https://circleci.com/docs/api/v1-reference/
