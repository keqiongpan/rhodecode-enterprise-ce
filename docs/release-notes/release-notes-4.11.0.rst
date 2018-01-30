|RCE| 4.11.0 |RNS|
------------------

Release Date
^^^^^^^^^^^^

- 2018-02-01


New Features
^^^^^^^^^^^^

- Default reviewers(EE only): introduced new voting rule logic that allows
  defining how many members of user group need to vote for approvals. E.g
  adding 4 people group with security people, it can be specified that at least
  1 (or all) need to vote for approval from that group.
- Default reviewers(EE only): added source/target branch flow distinction and
  option to add names to rules.
- RhodeCode-Scheduler (Beta, EE only): after celery 4.X upgrade we introduced a
  new scheduler option. RhodeCode scheduler now allows specifying via super-admin
  interface periodic tasks that should be run crontab style.
  Currently available tasks are:
  - repo maintenance: (repo quality/git gc)
  - repo remote code pull: pull changed on periodic bases from given url
  - repo remote code push: push all changes on periodic bases to given url
  - check for updates
- Ui: a ssh clone uri was added to summary view for clone. This allows to
  customize how the ssh clone url would look like, and also exposes SSH clone
  url to summary page.
- Integrations: parse pushed tags, and lightweight tags for git.
    - now aggregated as 'tags' key
    - handles the case for email/webhook integrations
- Files browser: allow making a range selection of code lines with
  shift-click from line numbers.
- Pull requests: allow opening PR from changelog based on selected refs for
  git as well as hg.
- Process management: auto refresh option was added to the processes
  page to live track usage.
- Api: pull-requests added option to fetch comments from a pull requests.
- Api: added new data called `permissions_summary` for user and
  user_groups that expose the summary of permissions for each of those.


General
^^^^^^^

- Core: removed all pylons dependencies and backward compatibility code.
  RhodeCode is now 100% pyramid app.
- Audit logs: added user.register audit log entry.
- Celery: update celery support 4.X series.
- Logging: log traceback for errors that are known to help debugging.
- Pull requests: don't select first commit in case we don't have a default
  branch for repository. Loading compare from commit 0 to something selected
  is very heavy to compute. Now it's left to users to decide what
  compare base to pick.
- Dependencies: bumped Mercurial version to 4.4.2
- Dependencies: bumped hgevolve to 7.0.1
- Dependencies: bumped libs not explicitly set by requirements
    - ws4py to 0.4.2
    - scandir to 1.6
    - plaster to 1.0
    - mistune to 0.8
    - jupyter-core to 4.4.0
- Dependencies: pin to rhodecode-tools 0.14.0
- Dependencies: bumped click to 6.6.0
- Dependencies: bumped transifex-clients to 0.12.5
- Dependencies: bumped six to 1.11.0
- Dependencies: bumped waitress to 1.1.0
- Dependencies: bumped setproctitle 1.1.10
- Dependencies: bumped iso8601 to 0.1.12
- Dependencies: bumped repoze.lru to 0.7.0
- Dependencies: bumped python-ldap to 2.4.45
- Dependencies: bumped gnureadline 6.3.8
- Dependencies: bumped bottle to 0.12.13
- Dependencies: bumped psycopg2 2.7.3.2
- Dependencies: bumped alembic to 0.9.6
- Dependencies: bumped sqlalchemy to 1.1.15
- Dependencies: bumped markupsafe to 1.0.0
- Dependencies: bumped markdown to 2.6.9
- Dependencies: bumped objgraph to 3.1.1
- Dependencies: bumped psutil to 5.4.0
- Dependencies: bumped docutils to 0.14.0
- Dependencies: bumped decorator to 4.1.2
- Dependencies: bumped pyramid-jinja to 2.7.0
- Dependencies: bumped jinja to 2.9.6
- Dependencies: bumped colander to 1.4.0
- Dependencies: bumped mistune to 0.8.1
- Dependencies: bumped webob to 1.7.4
- Dependencies: dropped nose dependency.


Security
^^^^^^^^

- Security(low): fix self xss on repo downloads picker for svn case.


Performance
^^^^^^^^^^^

- Pyramid: removed pylons layer, this should result in general speed
  improvement over previous version.
- Authentication: use cache_ttl for anonymous access taken from the
  rhodecode main auth plugin. For operations like svn this boosts performance
  significantly with anonymous access enabled.
- Issue trackers: cache the fetched issue tracker patterns in changelog
  page before loop iteration to speed up fetching and parsing the tracker
  patterns.


Fixes
^^^^^

- Slack: expose the FULL message instead of title.
  Slack uses it's own trim, we should avoid sending trimmed data and
  let users via Slack trim logic control the data.
- Comments: place the left over comments (outdated/misplaced) to the left or
  right side-by-side pane. This way the original context where they were
  placed is kept.
- Comments: allow to properly initialize outdated comments that are attached
  to the end of diffs. This allows resolving TODOs that are outdated.
- Git: handle cases of git push without branch specified in the eventing system.
- Git: merge simulation fixes. Fetch other branch data if it's different
  from target. This prevents potentially missing commits error when doing a test merge.
  Also fix edge cases using .gitattributes file modification that could
  lead to the same problem.
- Age component: use local flag to fix the problem of wrongly reported last
  update times on repository groups.


Upgrade notes
^^^^^^^^^^^^^

Please note that this release is first in series that drops completely pylons
dependency. This means that certain `paster` commands are no longer available.

Commands changed after dropping pylons compatibility layer:
  - paster upgrade-db /path/ini_file  => rc-upgrade-db /path/ini_file
  - paster setup-app /path/ini_file   => rc-setup-app /path/ini_file
  - paster ishell /path/ini_file      => rc-ishell /path/ini_file
  - paster celeryd /path/ini_file     => celery worker --app rhodecode.lib.celerylib.loader /path/ini_file

Commands no longer available:
 - paster make-config (replaced by rhodecode-config from rhodecode-tools package)
 - paster update-repoinfo (replaced by API calls)
 - paster cache-keys, no equivalent available, this command was removed.


RhodeCode 4.11 uses latest Celery 4.X series. This means that there's a new way to
run the celery workers. To upgrade to latest simply run
`rccontrol enable-module celery` to convert the currently running celery setup
into a new version that also powers the RhodeCode scheduler.
