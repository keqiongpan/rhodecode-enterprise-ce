# -*- coding: utf-8 -*-

# Copyright (C) 2010-2019 RhodeCode GmbH
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
                        '> onload="javascript:alert()" href="https://rhodecode.com">link</a>'])
    rendered_html = MarkupRenderer.markdown(xss_md)
    assert '<a href="https://rhodecode.com" name="n">link</a>' in rendered_html


def test_markdown_bleach_renders_correct():
    test_md = """
This is intended as a quick reference and showcase. For more complete info, see [John Gruber's original spec](http://daringfireball.net/projects/markdown/) and the [Github-flavored Markdown info page](http://github.github.com/github-flavored-markdown/).

Note that there is also a [Cheatsheet specific to Markdown Here](./Markdown-Here-Cheatsheet) if that's what you're looking for. You can also check out [more Markdown tools](./Other-Markdown-Tools).

##### Table of Contents  
[Headers](#headers)  
[Emphasis](#emphasis)  
[Lists](#lists)  
[Links](#links)  
[Images](#images)  
[Code and Syntax Highlighting](#code)  
[Tables](#tables)  
[Blockquotes](#blockquotes)  
[Inline HTML](#html)  
[Horizontal Rule](#hr)  
[Line Breaks](#lines)  
[Youtube videos](#videos)  


## Headers

```no-highlight
# H1
## H2
### H3
#### H4
##### H5
###### H6

Alternatively, for H1 and H2, an underline-ish style:

Alt-H1
======

Alt-H2
------
```

# H1
## H2
### H3
#### H4
##### H5
###### H6

Alternatively, for H1 and H2, an underline-ish style:

Alt-H1
======

Alt-H2
------

## Emphasis

```no-highlight
Emphasis, aka italics, with *asterisks* or _underscores_.

Strong emphasis, aka bold, with **asterisks** or __underscores__.

Combined emphasis with **asterisks and _underscores_**.

Strikethrough uses two tildes. ~~Scratch this.~~
```

Emphasis, aka italics, with *asterisks* or _underscores_.

Strong emphasis, aka bold, with **asterisks** or __underscores__.

Combined emphasis with **asterisks and _underscores_**.

Strikethrough uses two tildes. ~~Scratch this.~~


## Lists

(In this example, leading and trailing spaces are shown with with dots: ⋅)

```no-highlight
1. First ordered list item
2. Another item
⋅⋅* Unordered sub-list. 
1. Actual numbers don't matter, just that it's a number
⋅⋅1. Ordered sub-list
4. And another item.

⋅⋅⋅You can have properly indented paragraphs within list items. Notice the blank line above, and the leading spaces (at least one, but we'll use three here to also align the raw Markdown).

⋅⋅⋅To have a line break without a paragraph, you will need to use two trailing spaces.⋅⋅
⋅⋅⋅Note that this line is separate, but within the same paragraph.⋅⋅
⋅⋅⋅(This is contrary to the typical GFM line break behaviour, where trailing spaces are not required.)

* Unordered list can use asterisks
- Or minuses
+ Or pluses
```

1. First ordered list item
2. Another item
  * Unordered sub-list. 
1. Actual numbers don't matter, just that it's a number
  1. Ordered sub-list
4. And another item.

   You can have properly indented paragraphs within list items. Notice the blank line above, and the leading spaces (at least one, but we'll use three here to also align the raw Markdown).

   To have a line break without a paragraph, you will need to use two trailing spaces.  
   Note that this line is separate, but within the same paragraph.  
   (This is contrary to the typical GFM line break behaviour, where trailing spaces are not required.)

* Unordered list can use asterisks
- Or minuses
+ Or pluses


## Links

There are two ways to create links.

```no-highlight
[I'm an inline-style link](https://www.google.com)

[I'm an inline-style link with title](https://www.google.com "Google's Homepage")

[I'm a reference-style link][Arbitrary case-insensitive reference text]

[I'm a relative reference to a repository file (LICENSE)](./LICENSE)

[I'm a relative reference to a repository file (IMAGE)](./img/logo.png)

[I'm a relative reference to a repository file (IMAGE2)](img/logo.png)

[You can use numbers for reference-style link definitions][1]

Or leave it empty and use the [link text itself].

URLs and URLs in angle brackets will automatically get turned into links. 
http://www.example.com or <http://www.example.com> and sometimes 
example.com (but not on Github, for example).

Some text to show that the reference links can follow later.

[arbitrary case-insensitive reference text]: https://www.mozilla.org
[1]: http://slashdot.org
[link text itself]: http://www.reddit.com
```

[I'm an inline-style link](https://www.google.com)

[I'm an inline-style link with title](https://www.google.com "Google's Homepage")

[I'm a reference-style link][Arbitrary case-insensitive reference text]

[I'm a relative reference to a repository file (LICENSE)](./LICENSE)

[I'm a relative reference to a repository file (IMAGE)](./img/logo.png)

[I'm a relative reference to a repository file (IMAGE2)](img/logo.png)

[You can use numbers for reference-style link definitions][1]

Or leave it empty and use the [link text itself].

URLs and URLs in angle brackets will automatically get turned into links. 
http://www.example.com or <http://www.example.com> and sometimes 
example.com (but not on Github, for example).

Some text to show that the reference links can follow later.

[arbitrary case-insensitive reference text]: https://www.mozilla.org
[1]: http://slashdot.org
[link text itself]: http://www.reddit.com


## Images

```no-highlight
Here's our logo (hover to see the title text):

Inline-style: 
![alt text](https://github.com/adam-p/markdown-here/raw/master/src/common/images/icon48.png "Logo Title Text 1")

relative-src-style: 
![alt text](img/logo.png)

Reference-style: 
![alt text][logo]

[logo]: https://github.com/adam-p/markdown-here/raw/master/src/common/images/icon48.png "Logo Title Text 2"
```

Here's our logo (hover to see the title text):

Inline-style: 
![alt text](https://github.com/adam-p/markdown-here/raw/master/src/common/images/icon48.png "Logo Title Text 1")

relative-src-style: 
![alt text](img/logo.png)

relative-src-style: 
![alt text](./img/logo.png)

Reference-style: 
![alt text][logo]

[logo]: https://github.com/adam-p/markdown-here/raw/master/src/common/images/icon48.png "Logo Title Text 2"


## Code and Syntax Highlighting

Code blocks are part of the Markdown spec, but syntax highlighting isn't. However, many renderers -- like Github's and *Markdown Here* -- support syntax highlighting. Which languages are supported and how those language names should be written will vary from renderer to renderer. *Markdown Here* supports highlighting for dozens of languages (and not-really-languages, like diffs and HTTP headers); to see the complete list, and how to write the language names, see the [highlight.js demo page](http://softwaremaniacs.org/media/soft/highlight/test.html).

```no-highlight
Inline `code` has `back-ticks around` it.
```

Inline `code` has `back-ticks around` it.

Blocks of code are either fenced by lines with three back-ticks <code>```</code>, or are indented with four spaces. I recommend only using the fenced code blocks -- they're easier and only they support syntax highlighting.

```javascript
var s = "JavaScript syntax highlighting";
console.log(s);
```
 
```python
s = "Python syntax highlighting"
print s
```
 
```
No language indicated, so no syntax highlighting. 
But let's throw in a &lt;b&gt;tag&lt;/b&gt;.
```


```javascript
var s = "JavaScript syntax highlighting";
alert(s);
```

```python
s = "Python syntax highlighting"
print s
```

```
No language indicated, so no syntax highlighting in Markdown Here (varies on Github). 
But let's throw in a <b>tag</b>.
```


## Tables

Tables aren't part of the core Markdown spec, but they are part of GFM and *Markdown Here* supports them. They are an easy way of adding tables to your email -- a task that would otherwise require copy-pasting from another application.

```no-highlight
Colons can be used to align columns.

| Tables        | Are           | Cool  |
| ------------- |:-------------:| -----:|
| col 3 is      | right-aligned | $1600 |
| col 2 is      | centered      |   $12 |
| zebra stripes | are neat      |    $1 |

There must be at least 3 dashes separating each header cell.
The outer pipes (|) are optional, and you don't need to make the 
raw Markdown line up prettily. You can also use inline Markdown.

Markdown | Less | Pretty
--- | --- | ---
*Still* | `renders` | **nicely**
1 | 2 | 3
```

Colons can be used to align columns.

| Tables        | Are           | Cool |
| ------------- |:-------------:| -----:|
| col 3 is      | right-aligned | $1600 |
| col 2 is      | centered      |   $12 |
| zebra stripes | are neat      |    $1 |

There must be at least 3 dashes separating each header cell. The outer pipes (|) are optional, and you don't need to make the raw Markdown line up prettily. You can also use inline Markdown.

Markdown | Less | Pretty
--- | --- | ---
*Still* | `renders` | **nicely**
1 | 2 | 3


## Blockquotes

```no-highlight
> Blockquotes are very handy in email to emulate reply text.
> This line is part of the same quote.

Quote break.

> This is a very long line that will still be quoted properly when it wraps. Oh boy let's keep writing to make sure this is long enough to actually wrap for everyone. Oh, you can *put* **Markdown** into a blockquote. 
```

> Blockquotes are very handy in email to emulate reply text.
> This line is part of the same quote.

Quote break.

> This is a very long line that will still be quoted properly when it wraps. Oh boy let's keep writing to make sure this is long enough to actually wrap for everyone. Oh, you can *put* **Markdown** into a blockquote. 


## Inline HTML

You can also use raw HTML in your Markdown, and it'll mostly work pretty well. 

```no-highlight
<dl>
  <dt>Definition list</dt>
  <dd>Is something people use sometimes.</dd>

  <dt>Markdown in HTML</dt>
  <dd>Does *not* work **very** well. Use HTML <em>tags</em>.</dd>
</dl>
```

<dl>
  <dt>Definition list</dt>
  <dd>Is something people use sometimes.</dd>

  <dt>Markdown in HTML</dt>
  <dd>Does *not* work **very** well. Use HTML <em>tags</em>.</dd>
</dl>


## Horizontal Rule

```
Three or more...

---

Hyphens

***

Asterisks

___

Underscores
```

Three or more...

---

Hyphens

***

Asterisks

___

Underscores


## Line Breaks

My basic recommendation for learning how line breaks work is to experiment and discover -- hit &lt;Enter&gt; once (i.e., insert one newline), then hit it twice (i.e., insert two newlines), see what happens. You'll soon learn to get what you want. "Markdown Toggle" is your friend. 

Here are some things to try out:

```
Here's a line for us to start with.

This line is separated from the one above by two newlines, so it will be a *separate paragraph*.

This line is also a separate paragraph, but...
This line is only separated by a single newline, so it's a separate line in the *same paragraph*.
```

Here's a line for us to start with.

This line is separated from the one above by two newlines, so it will be a *separate paragraph*.

This line is also begins a separate paragraph, but...  
This line is only separated by a single newline, so it's a separate line in the *same paragraph*.

(Technical note: *Markdown Here* uses GFM line breaks, so there's no need to use MD's two-space line breaks.)


## Youtube videos

They can't be added directly but you can add an image with a link to the video like this:

```no-highlight
<a href="http://www.youtube.com/watch?feature=player_embedded&v=YOUTUBE_VIDEO_ID_HERE
" target="_blank"><img src="http://img.youtube.com/vi/YOUTUBE_VIDEO_ID_HERE/0.jpg" 
alt="IMAGE ALT TEXT HERE" width="240" height="180" border="10" /></a>
```

Or, in pure Markdown, but losing the image sizing and border:

```no-highlight
[![IMAGE ALT TEXT HERE](http://img.youtube.com/vi/YOUTUBE_VIDEO_ID_HERE/0.jpg)](http://www.youtube.com/watch?v=YOUTUBE_VIDEO_ID_HERE)
```

Referencing a bug by #bugID in your git commit links it to the slip. For example #1. 

---

License: [CC-BY](https://creativecommons.org/licenses/by/3.0/)    
    """
    raw_rendered_html = MarkupRenderer.markdown(test_md, clean_html=False)
    bleached_rendered_html = MarkupRenderer.markdown(test_md, clean_html=True)
    assert raw_rendered_html == bleached_rendered_html


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
        'ancestor_commit_id': 'aaabbbcccdddeee',
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
    * `A /path/a.py <#a_c-aaabbbcccddd-68ed34923b68>`_
    * `A /path/b.js <#a_c-aaabbbcccddd-64f90608b607>`_
    * `M /path/d.js <#a_c-aaabbbcccddd-85842bf30c6e>`_
    * `M /path/ę.py <#a_c-aaabbbcccddd-d713adf009cd>`_
    * `R /path/ź.py`

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
        'ancestor_commit_id': 'aaabbbcccdddeee',
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
