|RCE| 4.9.1 |RNS|
-----------------

Release Date
^^^^^^^^^^^^

- 2017-10-26


New Features
^^^^^^^^^^^^



General
^^^^^^^



Security
^^^^^^^^

- security(critical): repo-forks: fix issue when forging fork_repo_id parameter
  could allow reading other people forks.
- security(high): auth: don't expose full set of permissions into channelstream
  payload. Forged requests could return list of private repositories in the system.
- security(medium): general-security: limit the maximum password input length
  to 72 characters.
- security(medium): select2: always escape .text attributes to prevent XSS
  via branches or tags names.



Performance
^^^^^^^^^^^

- git: improve performance and reduce memory usage on large clones.



Fixes
^^^^^


- user-groups: fix potential problem with ldap group sync in external auth plugins.



Upgrade notes
^^^^^^^^^^^^^

- This release changes the maximum allowed input password to 72 characters. This
  prevent resource consumption attack. If you need longer password than 72
  characters please contact our team.
