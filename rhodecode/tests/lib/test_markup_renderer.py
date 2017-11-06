# -*- coding: utf-8 -*-

# Copyright (C) 2010-2017 RhodeCode GmbH
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

import pytest

from rhodecode.lib.markup_renderer import (
    MarkupRenderer, RstTemplateRenderer, relative_path, relative_links)


@pytest.mark.parametrize(
    "filename, expected_renderer",
    [
        ('readme.md', 'markdown'),
        ('readme.Md', 'markdown'),
        ('readme.MdoWn', 'markdown'),
        ('readme.rst', 'rst'),
        ('readme.Rst', 'rst'),
        ('readme.rest', 'rst'),
        ('readme.rest', 'rst'),

        ('markdown.xml', 'plain'),
        ('rest.xml', 'plain'),
        ('readme.xml', 'plain'),

        ('readme', 'plain'),
        ('README', 'plain'),
        ('readme.mdx', 'plain'),
        ('readme.rstx', 'plain'),
        ('readmex', 'plain'),
    ])
def test_detect_renderer(filename, expected_renderer):
    detected_renderer = MarkupRenderer()._detect_renderer(
        '', filename=filename).__name__
    assert expected_renderer == detected_renderer


def test_markdown_xss_link():
    xss_md = "[link](javascript:alert('XSS: pwned!'))"
    rendered_html = MarkupRenderer.markdown(xss_md)
    assert 'href="javascript:alert(\'XSS: pwned!\')"' not in rendered_html


def test_markdown_xss_inline_html():
    xss_md = '\n'.join([
        '> <a name="n"',
        '> href="javascript:alert(\'XSS: pwned!\')">link</a>'])
    rendered_html = MarkupRenderer.markdown(xss_md)
    assert 'href="javascript:alert(\'XSS: pwned!\')">' not in rendered_html


def test_markdown_inline_html():
    xss_md = '\n'.join(['> <a name="n"',
                        '> href="https://rhodecode.com">link</a>'])
    rendered_html = MarkupRenderer.markdown(xss_md)
    assert '[HTML_REMOVED]link[HTML_REMOVED]' in rendered_html


def test_rst_xss_link():
    xss_rst = "`Link<javascript:alert('XSS: pwned!')>`_"
    rendered_html = MarkupRenderer.rst(xss_rst)
    assert "href=javascript:alert('XSS: pwned!')" not in rendered_html


@pytest.mark.xfail(reason='Bug in docutils. Waiting answer from the author')
def test_rst_xss_inline_html():
    xss_rst = '<a href="javascript:alert(\'XSS: pwned!\')">link</a>'
    rendered_html = MarkupRenderer.rst(xss_rst)
    assert 'href="javascript:alert(' not in rendered_html


def test_rst_xss_raw_directive():
    xss_rst = '\n'.join([
        '.. raw:: html',
        '',
        '  <a href="javascript:alert(\'XSS: pwned!\')">link</a>'])
    rendered_html = MarkupRenderer.rst(xss_rst)
    assert 'href="javascript:alert(' not in rendered_html


def test_render_rst_template_without_files():
    expected = u'''\
Pull request updated. Auto status change to |under_review|

.. role:: added
.. role:: removed
.. parsed-literal::

  Changed commits:
    * :added:`2 added`
    * :removed:`3 removed`

  No file changes found

.. |under_review| replace:: *"NEW STATUS"*'''

    params = {
        'under_review_label': 'NEW STATUS',
        'added_commits': ['a', 'b'],
        'removed_commits': ['a', 'b', 'c'],
        'changed_files': [],
        'added_files': [],
        'modified_files': [],
        'removed_files': [],
    }
    renderer = RstTemplateRenderer()
    rendered = renderer.render('pull_request_update.mako', **params)
    assert expected == rendered


def test_render_rst_template_with_files():
    expected = u'''\
Pull request updated. Auto status change to |under_review|

.. role:: added
.. role:: removed
.. parsed-literal::

  Changed commits:
    * :added:`1 added`
    * :removed:`3 removed`

  Changed files:
    * `A /path/a.py <#a_c--68ed34923b68>`_
    * `A /path/b.js <#a_c--64f90608b607>`_
    * `M /path/d.js <#a_c--85842bf30c6e>`_
    * `M /path/ę.py <#a_c--d713adf009cd>`_
    * R /path/ź.py

.. |under_review| replace:: *"NEW STATUS"*'''

    added = ['/path/a.py', '/path/b.js']
    modified = ['/path/d.js', u'/path/ę.py']
    removed = [u'/path/ź.py']

    params = {
        'under_review_label': 'NEW STATUS',
        'added_commits': ['a'],
        'removed_commits': ['a', 'b', 'c'],
        'changed_files': added + modified + removed,
        'added_files': added,
        'modified_files': modified,
        'removed_files': removed,
    }
    renderer = RstTemplateRenderer()
    rendered = renderer.render('pull_request_update.mako', **params)

    assert expected == rendered


def test_render_rst_auto_status_template():
    expected = u'''\
Auto status change to |new_status|

.. |new_status| replace:: *"NEW STATUS"*'''

    params = {
        'new_status_label': 'NEW STATUS',
        'pull_request': None,
        'commit_id': None,
    }
    renderer = RstTemplateRenderer()
    rendered = renderer.render('auto_status_change.mako', **params)
    assert expected == rendered


@pytest.mark.parametrize(
    "src_path, server_path, is_path, expected",
    [
        ('source.png', '/repo/files/path', lambda p: False,
         '/repo/files/path/source.png'),

        ('source.png', 'mk/git/blob/master/README.md', lambda p: True,
         '/mk/git/blob/master/source.png'),

        ('./source.png', 'mk/git/blob/master/README.md', lambda p: True,
         '/mk/git/blob/master/source.png'),

        ('/source.png', 'mk/git/blob/master/README.md', lambda p: True,
         '/mk/git/blob/master/source.png'),

        ('./source.png', 'repo/files/path/source.md', lambda p: True,
         '/repo/files/path/source.png'),

        ('./source.png', '/repo/files/path/file.md', lambda p: True,
         '/repo/files/path/source.png'),

        ('../source.png', '/repo/files/path/file.md', lambda p: True,
         '/repo/files/source.png'),

        ('./../source.png', '/repo/files/path/file.md', lambda p: True,
         '/repo/files/source.png'),

        ('./source.png', '/repo/files/path/file.md', lambda p: True,
         '/repo/files/path/source.png'),

        ('../../../source.png', 'path/file.md', lambda p: True,
         '/source.png'),

        ('../../../../../source.png', '/path/file.md', None,
         '/source.png'),

        ('../../../../../source.png', 'files/path/file.md', None,
         '/source.png'),

        ('../../../../../https://google.com/image.png', 'files/path/file.md', None,
         '/https://google.com/image.png'),

        ('https://google.com/image.png', 'files/path/file.md', None,
         'https://google.com/image.png'),

        ('://foo', '/files/path/file.md', None,
         '://foo'),

        (u'한글.png', '/files/path/file.md', None,
         u'/files/path/한글.png'),

        ('my custom image.png', '/files/path/file.md', None,
         '/files/path/my custom image.png'),
    ])
def test_relative_path(src_path, server_path, is_path, expected):
    path = relative_path(src_path, server_path, is_path)
    assert path == expected


@pytest.mark.parametrize(
    "src_html, expected_html",
    [
        ('<div></div>', '<div></div>'),
        ('<img src="/file.png"></img>', '<img src="/path/raw/file.png">'),
        ('<img src="data:abcd"/>', '<img src="data:abcd">'),
        ('<a href="/file.png?raw=1"></a>', '<a href="/path/raw/file.png?raw=1"></a>'),
        ('<a href="/file.png"></a>', '<a href="/path/file.png"></a>'),
        ('<a href="#anchor"></a>', '<a href="#anchor"></a>'),
        ('<a href="./README.md?raw=1"></a>', '<a href="/path/raw/README.md?raw=1"></a>'),
        ('<a href="./README.md"></a>', '<a href="/path/README.md"></a>'),
        ('<a href="../README.md"></a>', '<a href="/README.md"></a>'),

    ])
def test_relative_links(src_html, expected_html):
    server_paths = {'raw': '/path/raw/file.md', 'standard': '/path/file.md'}
    assert relative_links(src_html, server_paths=server_paths) == expected_html
