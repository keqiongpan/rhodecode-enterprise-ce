|RCE| 4.9.0 |RNS|
-----------------

Release Date
^^^^^^^^^^^^

- 2017-08-12


New Features
^^^^^^^^^^^^



General
^^^^^^^

- Off cycle Minor release to fix SCM vulnerabilities.


Security
^^^^^^^^

- security(critical): Bumped GIT to 2.9.5 fixes CVE-2017-1000117
  https://www.mail-archive.com/linux-kernel@vger.kernel.org/msg1466490.html
- security(critical): Bumped SVN to 1.9.7 fixes CVE-2017-9800
  https://subversion.apache.org/security/CVE-2017-9800-advisory.txt
- security(critical): Bumped Mercurial to 4.2.3 fixes  CVE-2017-1000116
  https://www.mercurial-scm.org/wiki/WhatsNew#Mercurial_4.3_.282017-08-10.29


Performance
^^^^^^^^^^^

- Fixed Mercurial Stream support for very large repositories. Due to discovered
  bug in WebOb library we manage to fix Mercurial stream support.
  Now cloning very large repos e.g 100GB, ~1mln commits should be much
  faster, and use less memory.


Fixes
^^^^^

- Fixed problem with default-reviewers in EE package that was missing panel
  title and in some occasions generate 500 errors.
- Fixed problem with potential URL generation inside our integration.
  This was introduced during pyramid porting. We know ensure that proper
  routing generation is done on all events.


Upgrade notes
^^^^^^^^^^^^^


- The 4.9.0 release is an off-cycle release. Due to the fact that we needed to
  bump Mercurial from 4.1.X to 4.2.X, and Subversion from 1.9.4 to 1.9.7, we
  released this version not as 4.8.1 security bug fix but 4.9.0.
  We know historically that SVN and Mercurial can have internal api changes.
  We tested basic functionality for all 3 vcs-es but due to very short release
  time we were unable to test everything. Please report any found problems to us
  and we'll for sure address them.

  Note to SVN users: Please make sure to upgrade mod_dav to 1.9.7 version.
  At this time we know Wandisco provides 1.9.7 packages for most major distros.


