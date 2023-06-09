# -*- coding: utf-8 -*-

# Copyright (C) 2010-2020 RhodeCode GmbH
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License, version 3
# (only), as published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# This program is dual-licensed. If you wish to learn more about the
# RhodeCode Enterprise Edition, including its added features, Support services,
# and proprietary license terms, please see https://rhodecode.com/licenses/

import textwrap

import mock
import pytest

from rhodecode.lib.codeblocks import DiffSet
from rhodecode.lib.diffs import (
    DiffProcessor,
    NEW_FILENODE, DEL_FILENODE, MOD_FILENODE, RENAMED_FILENODE,
    CHMOD_FILENODE, BIN_FILENODE, COPIED_FILENODE)
from rhodecode.lib.utils2 import AttributeDict
from rhodecode.lib.vcs.backends.git import GitCommit
from rhodecode.tests.fixture import Fixture, no_newline_id_generator
from rhodecode.lib.vcs.backends.git.repository import GitDiff
from rhodecode.lib.vcs.backends.hg.repository import MercurialDiff
from rhodecode.lib.vcs.backends.svn.repository import SubversionDiff

fixture = Fixture()


def test_diffprocessor_as_html_with_comments():
    raw_diff = textwrap.dedent('''
        diff --git a/setup.py b/setup.py
        index 5b36422..cfd698e 100755
        --- a/setup.py
        +++ b/setup.py
        @@ -2,7 +2,7 @@
         #!/usr/bin/python
         # Setup file for X
         # Copyright (C) No one
        -
        +x
         try:
             from setuptools import setup, Extension
         except ImportError:
    ''')
    diff = GitDiff(raw_diff)
    processor = DiffProcessor(diff)
    processor.prepare()

    # Note that the cell with the context in line 5 (in the html) has the
    # no-comment class, which will prevent the add comment icon to be displayed.
    expected_html = textwrap.dedent('''
        <table class="code-difftable">
        <tr class="line context">
            <td class="add-comment-line"><span class="add-comment-content"></span></td><td class="comment-toggle tooltip" title="Toggle Comment Thread"><i class="icon-comment"></i></td>
            <td  class="lineno old">...</td>
            <td  class="lineno new">...</td>
            <td class="code no-comment">
                <pre>@@ -2,7 +2,7 @@
        </pre>
            </td>
        </tr>
        <tr class="line unmod">
            <td class="add-comment-line"><span class="add-comment-content"><a href="#"><span class="icon-comment-add"></span></a></span></td><td class="comment-toggle tooltip" title="Toggle Comment Thread"><i class="icon-comment"></i></td>
            <td id="setuppy_o2" class="lineno old"><a href="#setuppy_o2" class="tooltip"
                        title="Click to select line">2</a></td>
            <td id="setuppy_n2" class="lineno new"><a href="#setuppy_n2" class="tooltip"
                        title="Click to select line">2</a></td>
            <td class="code">
                <pre>#!/usr/bin/python
        </pre>
            </td>
        </tr>
        <tr class="line unmod">
            <td class="add-comment-line"><span class="add-comment-content"><a href="#"><span class="icon-comment-add"></span></a></span></td><td class="comment-toggle tooltip" title="Toggle Comment Thread"><i class="icon-comment"></i></td>
            <td id="setuppy_o3" class="lineno old"><a href="#setuppy_o3" class="tooltip"
                        title="Click to select line">3</a></td>
            <td id="setuppy_n3" class="lineno new"><a href="#setuppy_n3" class="tooltip"
                        title="Click to select line">3</a></td>
            <td class="code">
                <pre># Setup file for X
        </pre>
            </td>
        </tr>
        <tr class="line unmod">
            <td class="add-comment-line"><span class="add-comment-content"><a href="#"><span class="icon-comment-add"></span></a></span></td><td class="comment-toggle tooltip" title="Toggle Comment Thread"><i class="icon-comment"></i></td>
            <td id="setuppy_o4" class="lineno old"><a href="#setuppy_o4" class="tooltip"
                        title="Click to select line">4</a></td>
            <td id="setuppy_n4" class="lineno new"><a href="#setuppy_n4" class="tooltip"
                        title="Click to select line">4</a></td>
            <td class="code">
                <pre># Copyright (C) No one
        </pre>
            </td>
        </tr>
        <tr class="line del">
            <td class="add-comment-line"><span class="add-comment-content"><a href="#"><span class="icon-comment-add"></span></a></span></td><td class="comment-toggle tooltip" title="Toggle Comment Thread"><i class="icon-comment"></i></td>
            <td id="setuppy_o5" class="lineno old"><a href="#setuppy_o5" class="tooltip"
                        title="Click to select line">5</a></td>
            <td  class="lineno new"><a href="#setuppy_n" class="tooltip"
                        title="Click to select line"></a></td>
            <td class="code">
                <pre>
        </pre>
            </td>
        </tr>
        <tr class="line add">
            <td class="add-comment-line"><span class="add-comment-content"><a href="#"><span class="icon-comment-add"></span></a></span></td><td class="comment-toggle tooltip" title="Toggle Comment Thread"><i class="icon-comment"></i></td>
            <td  class="lineno old"><a href="#setuppy_o" class="tooltip"
                        title="Click to select line"></a></td>
            <td id="setuppy_n5" class="lineno new"><a href="#setuppy_n5" class="tooltip"
                        title="Click to select line">5</a></td>
            <td class="code">
                <pre><ins>x</ins>
        </pre>
            </td>
        </tr>
        <tr class="line unmod">
            <td class="add-comment-line"><span class="add-comment-content"><a href="#"><span class="icon-comment-add"></span></a></span></td><td class="comment-toggle tooltip" title="Toggle Comment Thread"><i class="icon-comment"></i></td>
            <td id="setuppy_o6" class="lineno old"><a href="#setuppy_o6" class="tooltip"
                        title="Click to select line">6</a></td>
            <td id="setuppy_n6" class="lineno new"><a href="#setuppy_n6" class="tooltip"
                        title="Click to select line">6</a></td>
            <td class="code">
                <pre>try:
        </pre>
            </td>
        </tr>
        <tr class="line unmod">
            <td class="add-comment-line"><span class="add-comment-content"><a href="#"><span class="icon-comment-add"></span></a></span></td><td class="comment-toggle tooltip" title="Toggle Comment Thread"><i class="icon-comment"></i></td>
            <td id="setuppy_o7" class="lineno old"><a href="#setuppy_o7" class="tooltip"
                        title="Click to select line">7</a></td>
            <td id="setuppy_n7" class="lineno new"><a href="#setuppy_n7" class="tooltip"
                        title="Click to select line">7</a></td>
            <td class="code">
                <pre>    from setuptools import setup, Extension
        </pre>
            </td>
        </tr>
        <tr class="line unmod">
            <td class="add-comment-line"><span class="add-comment-content"><a href="#"><span class="icon-comment-add"></span></a></span></td><td class="comment-toggle tooltip" title="Toggle Comment Thread"><i class="icon-comment"></i></td>
            <td id="setuppy_o8" class="lineno old"><a href="#setuppy_o8" class="tooltip"
                        title="Click to select line">8</a></td>
            <td id="setuppy_n8" class="lineno new"><a href="#setuppy_n8" class="tooltip"
                        title="Click to select line">8</a></td>
            <td class="code">
                <pre>except ImportError:
        </pre>
            </td>
        </tr>
        </table>
    ''').strip()
    html = processor.as_html(enable_comments=True).replace('\t', '    ')

    assert html == expected_html


class TestMixedFilenameEncodings(object):

    @pytest.fixture(scope="class")
    def raw_diff(self):
        return fixture.load_resource(
            'hg_diff_mixed_filename_encodings.diff')

    @pytest.fixture()
    def processor(self, raw_diff):
        diff = MercurialDiff(raw_diff)
        processor = DiffProcessor(diff)
        return processor

    def test_filenames_are_decoded_to_unicode(self, processor):
        diff_data = processor.prepare()
        filenames = [item['filename'] for item in diff_data]
        assert filenames == [
            u'späcial-utf8.txt', u'sp�cial-cp1252.txt', u'sp�cial-latin1.txt']

    def test_raw_diff_is_decoded_to_unicode(self, processor):
        diff_data = processor.prepare()
        raw_diffs = [item['raw_diff'] for item in diff_data]
        new_file_message = u'\nnew file mode 100644\n'
        expected_raw_diffs = [
            u' a/späcial-utf8.txt b/späcial-utf8.txt' + new_file_message,
            u' a/sp�cial-cp1252.txt b/sp�cial-cp1252.txt' + new_file_message,
            u' a/sp�cial-latin1.txt b/sp�cial-latin1.txt' + new_file_message]
        assert raw_diffs == expected_raw_diffs

    def test_as_raw_preserves_the_encoding(self, processor, raw_diff):
        assert processor.as_raw() == raw_diff


# TODO: mikhail: format the following data structure properly
DIFF_FIXTURES = [
    ('hg',
     'hg_diff_add_single_binary_file.diff',
     [('US Warszawa.jpg', 'A',
       {'added': 0,
        'deleted': 0,
        'binary': True,
        'ops': {NEW_FILENODE: 'new file 100755',
                BIN_FILENODE: 'binary diff hidden'}}),
      ]),
    ('hg',
     'hg_diff_mod_single_binary_file.diff',
     [('US Warszawa.jpg', 'M',
       {'added': 0,
        'deleted': 0,
        'binary': True,
        'ops': {MOD_FILENODE: 'modified file',
                BIN_FILENODE: 'binary diff hidden'}}),
      ]),
    ('hg',
     'hg_diff_mod_single_file_and_rename_and_chmod.diff',
     [('README', 'M',
       {'added': 3,
        'deleted': 0,
        'binary': False,
        'ops': {MOD_FILENODE: 'modified file',
                RENAMED_FILENODE: 'file renamed from README.rst to README',
                CHMOD_FILENODE: 'modified file chmod 100755 => 100644'}}),
      ]),
    ('hg',
     'hg_diff_no_newline.diff',
     [('server.properties', 'M',
       {'added': 2,
        'deleted': 1,
        'binary': False,
        'ops': {MOD_FILENODE: 'modified file'}}),
      ]),
    ('hg',
     'hg_diff_mod_file_and_rename.diff',
     [('README.rst', 'M',
       {'added': 3,
        'deleted': 0,
        'binary': False,
        'ops': {MOD_FILENODE: 'modified file',
                RENAMED_FILENODE: 'file renamed from README to README.rst'}}),
      ]),
    ('hg',
     'hg_diff_del_single_binary_file.diff',
     [('US Warszawa.jpg', 'D',
       {'added': 0,
        'deleted': 0,
        'binary': True,
        'ops': {DEL_FILENODE: 'deleted file',
                BIN_FILENODE: 'binary diff hidden'}}),
      ]),
    ('hg',
     'hg_diff_chmod_and_mod_single_binary_file.diff',
     [('gravatar.png', 'M',
       {'added': 0,
        'deleted': 0,
        'binary': True,
        'ops': {CHMOD_FILENODE: 'modified file chmod 100644 => 100755',
                BIN_FILENODE: 'binary diff hidden'}}),
      ]),
    ('hg',
     'hg_diff_chmod.diff',
     [('file', 'M',
       {'added': 0,
        'deleted': 0,
        'binary': True,
        'ops': {CHMOD_FILENODE: 'modified file chmod 100755 => 100644'}}),
      ]),
    ('hg',
     'hg_diff_rename_file.diff',
     [('file_renamed', 'M',
       {'added': 0,
        'deleted': 0,
        'binary': True,
        'ops': {RENAMED_FILENODE: 'file renamed from file to file_renamed'}}),
      ]),
    ('hg',
     'hg_diff_rename_and_chmod_file.diff',
     [('README', 'M',
       {'added': 0,
        'deleted': 0,
        'binary': True,
        'ops': {CHMOD_FILENODE: 'modified file chmod 100644 => 100755',
                RENAMED_FILENODE: 'file renamed from README.rst to README'}}),
      ]),
    ('hg',
     'hg_diff_binary_and_normal.diff',
     [('img/baseline-10px.png', 'A',
       {'added': 0,
        'deleted': 0,
        'binary': True,
        'ops': {NEW_FILENODE: 'new file 100644',
                BIN_FILENODE: 'binary diff hidden'}}),
      ('js/jquery/hashgrid.js', 'A',
       {'added': 340,
        'deleted': 0,
        'binary': False,
        'ops': {NEW_FILENODE: 'new file 100755'}}),
      ('index.html', 'M',
       {'added': 3,
        'deleted': 2,
        'binary': False,
        'ops': {MOD_FILENODE: 'modified file'}}),
      ('less/docs.less', 'M',
       {'added': 34,
        'deleted': 0,
        'binary': False,
        'ops': {MOD_FILENODE: 'modified file'}}),
      ('less/scaffolding.less', 'M',
       {'added': 1,
        'deleted': 3,
        'binary': False,
        'ops': {MOD_FILENODE: 'modified file'}}),
      ('readme.markdown', 'M',
       {'added': 1,
        'deleted': 10,
        'binary': False,
        'ops': {MOD_FILENODE: 'modified file'}}),
      ('img/baseline-20px.png', 'D',
       {'added': 0,
        'deleted': 0,
        'binary': True,
        'ops': {DEL_FILENODE: 'deleted file',
                BIN_FILENODE: 'binary diff hidden'}}),
      ('js/global.js', 'D',
       {'added': 0,
        'deleted': 75,
        'binary': False,
        'ops': {DEL_FILENODE: 'deleted file'}})
      ]),
    ('git',
     'git_diff_chmod.diff',
     [('work-horus.xls', 'M',
       {'added': 0,
        'deleted': 0,
        'binary': True,
        'ops': {CHMOD_FILENODE: 'modified file chmod 100644 => 100755'}})
      ]),
    ('git',
     'git_diff_js_chars.diff',
     [('\\"><img src=x onerror=prompt(0)>/\\"><img src=x onerror=prompt(1)>.txt', 'M',
       {'added': 1,
        'deleted': 0,
        'binary': False,
        'ops': {MOD_FILENODE: 'modified file'}})
      ]),
    ('git',
     'git_diff_rename_file.diff',
     [('file.xls', 'M',
       {'added': 0,
        'deleted': 0,
        'binary': True,
        'ops': {
            RENAMED_FILENODE: 'file renamed from work-horus.xls to file.xls'}})
      ]),
    ('git',
     'git_diff_mod_single_binary_file.diff',
     [('US Warszawa.jpg', 'M',
       {'added': 0,
        'deleted': 0,
        'binary': True,
        'ops': {MOD_FILENODE: 'modified file',
                BIN_FILENODE: 'binary diff hidden'}})
      ]),
    ('git',
     'git_diff_binary_and_normal.diff',
     [('img/baseline-10px.png', 'A',
       {'added': 0,
        'deleted': 0,
        'binary': True,
        'ops': {NEW_FILENODE: 'new file 100644',
                BIN_FILENODE: 'binary diff hidden'}}),
      ('js/jquery/hashgrid.js', 'A',
       {'added': 340,
        'deleted': 0,
        'binary': False,
        'ops': {NEW_FILENODE: 'new file 100755'}}),
      ('index.html', 'M',
       {'added': 3,
        'deleted': 2,
        'binary': False,
        'ops': {MOD_FILENODE: 'modified file'}}),
      ('less/docs.less', 'M',
       {'added': 34,
        'deleted': 0,
        'binary': False,
        'ops': {MOD_FILENODE: 'modified file'}}),
      ('less/scaffolding.less', 'M',
       {'added': 1,
        'deleted': 3,
        'binary': False,
        'ops': {MOD_FILENODE: 'modified file'}}),
      ('readme.markdown', 'M',
       {'added': 1,
        'deleted': 10,
        'binary': False,
        'ops': {MOD_FILENODE: 'modified file'}}),
      ('img/baseline-20px.png', 'D',
       {'added': 0,
        'deleted': 0,
        'binary': True,
        'ops': {DEL_FILENODE: 'deleted file',
                BIN_FILENODE: 'binary diff hidden'}}),
      ('js/global.js', 'D',
       {'added': 0,
        'deleted': 75,
        'binary': False,
        'ops': {DEL_FILENODE: 'deleted file'}}),
      ]),
    ('hg',
     'diff_with_diff_data.diff',
     [('vcs/backends/base.py', 'M',
       {'added': 18,
        'deleted': 2,
        'binary': False,
        'ops': {MOD_FILENODE: 'modified file'}}),
      ('vcs/backends/git/repository.py', 'M',
       {'added': 46,
        'deleted': 15,
        'binary': False,
        'ops': {MOD_FILENODE: 'modified file'}}),
      ('vcs/backends/hg.py', 'M',
       {'added': 22,
        'deleted': 3,
        'binary': False,
        'ops': {MOD_FILENODE: 'modified file'}}),
      ('vcs/tests/test_git.py', 'M',
       {'added': 5,
        'deleted': 5,
        'binary': False,
        'ops': {MOD_FILENODE: 'modified file'}}),
      ('vcs/tests/test_repository.py', 'M',
       {'added': 174,
        'deleted': 2,
        'binary': False,
        'ops': {MOD_FILENODE: 'modified file'}}),
      ]),
    ('hg',
     'hg_diff_copy_file.diff',
     [('file2', 'M',
       {'added': 0,
        'deleted': 0,
        'binary': True,
        'ops': {COPIED_FILENODE: 'file copied from file1 to file2'}}),
      ]),
    ('hg',
     'hg_diff_copy_and_modify_file.diff',
     [('file3', 'M',
       {'added': 1,
        'deleted': 0,
        'binary': False,
        'ops': {COPIED_FILENODE: 'file copied from file2 to file3',
                MOD_FILENODE: 'modified file'}}),
      ]),
    ('hg',
     'hg_diff_copy_and_chmod_file.diff',
     [('file4', 'M',
       {'added': 0,
        'deleted': 0,
        'binary': True,
        'ops': {COPIED_FILENODE: 'file copied from file3 to file4',
                CHMOD_FILENODE: 'modified file chmod 100644 => 100755'}}),
      ]),
    ('hg',
     'hg_diff_copy_chmod_and_edit_file.diff',
     [('file5', 'M',
       {'added': 2,
        'deleted': 1,
        'binary': False,
        'ops': {COPIED_FILENODE: 'file copied from file4 to file5',
                CHMOD_FILENODE: 'modified file chmod 100755 => 100644',
                MOD_FILENODE: 'modified file'}})]),

    # Diffs to validate rename and copy file with space in its name
    ('git',
     'git_diff_rename_file_with_spaces.diff',
     [('file_with_  two spaces.txt', 'M',
         {'added': 0,
          'deleted': 0,
          'binary': True,
          'ops': {
              RENAMED_FILENODE: (
                  'file renamed from file_with_ spaces.txt to file_with_ '
                  ' two spaces.txt')}
          }), ]),
    ('hg',
     'hg_diff_rename_file_with_spaces.diff',
     [('file_changed _.txt', 'M',
         {'added': 0,
          'deleted': 0,
          'binary': True,
          'ops': {
              RENAMED_FILENODE: (
                  'file renamed from file_ with update.txt to file_changed'
                  ' _.txt')}
          }), ]),
    ('hg',
     'hg_diff_copy_file_with_spaces.diff',
     [('file_copied_ with  spaces.txt', 'M',
         {'added': 0,
          'deleted': 0,
          'binary': True,
          'ops': {
              COPIED_FILENODE: (
                  'file copied from file_changed_without_spaces.txt to'
                  ' file_copied_ with  spaces.txt')}
          }),
      ]),

    # special signs from git
    ('git',
     'git_diff_binary_special_files.diff',
     [('css/_Icon\\r', 'A',
         {'added': 0,
          'deleted': 0,
          'binary': True,
          'ops': {NEW_FILENODE: 'new file 100644',
                  BIN_FILENODE: 'binary diff hidden'}
          }),
      ]),
    ('git',
     'git_diff_binary_special_files_2.diff',
     [('css/Icon\\r', 'A',
         {'added': 0,
          'deleted': 0,
          'binary': True,
          'ops': {NEW_FILENODE: 'new file 100644', }
          }),
      ]),

    ('svn',
     'svn_diff_binary_add_file.diff',
     [('intl.dll', 'A',
       {'added': 0,
        'deleted': 0,
        'binary': False,
        'ops': {NEW_FILENODE: 'new file 10644',
                #TODO(Marcink): depends on binary detection on svn patches
                # BIN_FILENODE: 'binary diff hidden'
                }
        }),
      ]),

    ('svn',
     'svn_diff_multiple_changes.diff',
     [('trunk/doc/images/SettingsOverlay.png', 'M',
       {'added': 0,
        'deleted': 0,
        'binary': False,
        'ops': {MOD_FILENODE: 'modified file',
                #TODO(Marcink): depends on binary detection on svn patches
                # BIN_FILENODE: 'binary diff hidden'
                }
        }),
      ('trunk/doc/source/de/tsvn_ch04.xml', 'M',
       {'added': 89,
        'deleted': 34,
        'binary': False,
        'ops': {MOD_FILENODE: 'modified file'}
        }),
      ('trunk/doc/source/en/tsvn_ch04.xml', 'M',
       {'added': 66,
        'deleted': 21,
        'binary': False,
        'ops': {MOD_FILENODE: 'modified file'}
        }),
      ('trunk/src/Changelog.txt', 'M',
       {'added': 2,
        'deleted': 0,
        'binary': False,
        'ops': {MOD_FILENODE: 'modified file'}
        }),
      ('trunk/src/Resources/TortoiseProcENG.rc', 'M',
       {'added': 19,
        'deleted': 13,
        'binary': False,
        'ops': {MOD_FILENODE: 'modified file'}
        }),
      ('trunk/src/TortoiseProc/SetOverlayPage.cpp', 'M',
       {'added': 16,
        'deleted': 1,
        'binary': False,
        'ops': {MOD_FILENODE: 'modified file'}
        }),
      ('trunk/src/TortoiseProc/SetOverlayPage.h', 'M',
       {'added': 3,
        'deleted': 0,
        'binary': False,
        'ops': {MOD_FILENODE: 'modified file'}
        }),
      ('trunk/src/TortoiseProc/resource.h', 'M',
       {'added': 2,
        'deleted': 0,
        'binary': False,
        'ops': {MOD_FILENODE: 'modified file'}
        }),
      ('trunk/src/TortoiseShell/ShellCache.h', 'M',
       {'added': 50,
        'deleted': 1,
        'binary': False,
        'ops': {MOD_FILENODE: 'modified file'}
        }),
      ]),

]

DIFF_FIXTURES_WITH_CONTENT = [
    (
        'hg', 'hg_diff_single_file_change_newline.diff',
        [
            (
                'file_b',  # filename
                'A',  # change
                {  # stats
                   'added': 1,
                   'deleted': 0,
                   'binary': False,
                   'ops': {NEW_FILENODE: 'new file 100644', }
                },
                '@@ -0,0 +1 @@\n+test_content b\n'  # diff
            ),
        ],
    ),
    (
        'hg', 'hg_diff_double_file_change_newline.diff',
        [
            (
                'file_b',  # filename
                'A',  # change
                {  # stats
                   'added': 1,
                   'deleted': 0,
                   'binary': False,
                   'ops': {NEW_FILENODE: 'new file 100644', }
                },
                '@@ -0,0 +1 @@\n+test_content b\n'  # diff
            ),
            (
                'file_c',  # filename
                'A',  # change
                {  # stats
                   'added': 1,
                   'deleted': 0,
                   'binary': False,
                   'ops': {NEW_FILENODE: 'new file 100644', }
                },
                '@@ -0,0 +1 @@\n+test_content c\n'  # diff
            ),
        ],
    ),
    (
        'hg', 'hg_diff_double_file_change_double_newline.diff',
        [
            (
                'file_b',  # filename
                'A',  # change
                {  # stats
                   'added': 1,
                   'deleted': 0,
                   'binary': False,
                   'ops': {NEW_FILENODE: 'new file 100644', }
                },
                '@@ -0,0 +1 @@\n+test_content b\n\n'  # diff
            ),
            (
                'file_c',  # filename
                'A',  # change
                {  # stats
                   'added': 1,
                   'deleted': 0,
                   'binary': False,
                   'ops': {NEW_FILENODE: 'new file 100644', }
                },
                '@@ -0,0 +1 @@\n+test_content c\n'  # diff
            ),
        ],
    ),
    (
        'hg', 'hg_diff_four_file_change_newline.diff',
        [
            (
                'file',  # filename
                'A',  # change
                {  # stats
                   'added': 1,
                   'deleted': 0,
                   'binary': False,
                   'ops': {NEW_FILENODE: 'new file 100644', }
                },
                '@@ -0,0 +1,1 @@\n+file\n'  # diff
            ),
            (
                'file2',  # filename
                'A',  # change
                {  # stats
                   'added': 1,
                   'deleted': 0,
                   'binary': False,
                   'ops': {NEW_FILENODE: 'new file 100644', }
                },
                '@@ -0,0 +1,1 @@\n+another line\n'  # diff
            ),
            (
                'file3',  # filename
                'A',  # change
                {  # stats
                   'added': 1,
                   'deleted': 0,
                   'binary': False,
                   'ops': {NEW_FILENODE: 'new file 100644', }
                },
                '@@ -0,0 +1,1 @@\n+newline\n'  # diff
            ),
            (
                'file4',  # filename
                'A',  # change
                {  # stats
                   'added': 1,
                   'deleted': 0,
                   'binary': False,
                   'ops': {NEW_FILENODE: 'new file 100644', }
                },
                '@@ -0,0 +1,1 @@\n+fil4\n\\ No newline at end of file'  # diff
            ),
        ],
    ),

]


diff_class = {
    'git': GitDiff,
    'hg': MercurialDiff,
    'svn': SubversionDiff,
}


@pytest.fixture(params=DIFF_FIXTURES)
def diff_fixture(request):
    vcs, diff_fixture, expected = request.param
    diff_txt = fixture.load_resource(diff_fixture)
    diff = diff_class[vcs](diff_txt)
    return diff, expected


def test_diff_lib(diff_fixture):
    diff, expected_data = diff_fixture
    diff_proc = DiffProcessor(diff)
    diff_proc_d = diff_proc.prepare()
    data = [(x['filename'], x['operation'], x['stats']) for x in diff_proc_d]
    assert expected_data == data


@pytest.fixture(params=DIFF_FIXTURES_WITH_CONTENT)
def diff_fixture_w_content(request):
    vcs, diff_fixture, expected = request.param
    diff_txt = fixture.load_resource(diff_fixture)
    diff = diff_class[vcs](diff_txt)
    return diff, expected


def test_diff_over_limit(request):

    diff_limit = 1024
    file_limit = 1024

    raw_diff = fixture.load_resource('large_diff.diff')
    vcs_diff = GitDiff(raw_diff)
    diff_processor = DiffProcessor(
        vcs_diff, format='newdiff', diff_limit=diff_limit, file_limit=file_limit,
        show_full_diff=False)

    _parsed = diff_processor.prepare()

    commit1 = GitCommit(repository=mock.Mock(), raw_id='abcdef12', idx=1)
    commit2 = GitCommit(repository=mock.Mock(), raw_id='abcdef34', idx=2)

    diffset = DiffSet(
        repo_name='repo_name',
        source_node_getter=lambda *a, **kw: AttributeDict({'commit': commit1}),
        target_node_getter=lambda *a, **kw: AttributeDict({'commit': commit2})
    )

    diffset = diffset.render_patchset(_parsed, commit1, commit2)

    assert len(diffset.files) == 2
    assert diffset.limited_diff is True
    assert diffset.files[0].patch['filename'] == 'example.go'
    assert diffset.files[0].limited_diff is True

    assert diffset.files[1].patch['filename'] == 'README.md'
    assert diffset.files[1].limited_diff is False


def test_diff_lib_newlines(diff_fixture_w_content):
    diff, expected_data = diff_fixture_w_content
    diff_proc = DiffProcessor(diff)
    diff_proc_d = diff_proc.prepare()
    data = [(x['filename'], x['operation'], x['stats'], x['raw_diff'])
            for x in diff_proc_d]
    assert expected_data == data


@pytest.mark.parametrize('input_str', [
    '',
    '\n',
    '\n\n',
    'First\n+second',
    'First\n+second\n',

    '\n\n\n Multi \n\n\n',
    '\n\n\n Multi beginning',
    'Multi end \n\n\n',
    'Multi end',
    '@@ -0,0 +1 @@\n+test_content \n\n b\n'
], ids=no_newline_id_generator)
def test_splitlines(input_str):
    result = DiffProcessor.diff_splitter(input_str)
    assert list(result) == input_str.splitlines(True)
